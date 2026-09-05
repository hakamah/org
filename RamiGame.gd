class_name RamiGame
extends RefCounted

const SUITS: Array[String] = ["spades", "hearts", "diamonds", "clubs"]
const RANKS: Array[String] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
const PLAYER_NAMES: Array[String] = ["Vous", "IA 1", "IA 2"]

enum Phase {
	DEAL,
	DRAW,
	ACTION,
	AI,
	GAME_OVER,
}

enum OpeningRule {
	SIMPLE_MELD,
	RAMI_51,
}

var stock: Array[CardInstance] = []
var discard_pile: Array[CardInstance] = []
var player_hand: Array[CardInstance] = []
var ai1_hand: Array[CardInstance] = []
var ai2_hand: Array[CardInstance] = []
var table_melds: Array[Dictionary] = []

var player_opened: bool = false
var ai1_opened: bool = false
var ai2_opened: bool = false
var turn_index: int = 0
var phase: Phase = Phase.DEAL
var winner_index: int = -1
var last_message: String = ""
var ranking: Array[Dictionary] = []

var sort_mode: int = -1
var opening_rule: OpeningRule = OpeningRule.SIMPLE_MELD
var must_replay_jokers: Array[CardInstance] = []

func set_opening_rule(rule: OpeningRule) -> void:
	opening_rule = rule

func opening_rule_name() -> String:
	if opening_rule == OpeningRule.RAMI_51:
		return "Rami 51"
	return "Ouverture simple"

func new_round() -> void:
	phase = Phase.DEAL
	stock.clear()
	discard_pile.clear()
	player_hand.clear()
	ai1_hand.clear()
	ai2_hand.clear()
	table_melds.clear()
	ranking.clear()
	must_replay_jokers.clear()
	player_opened = false
	ai1_opened = false
	ai2_opened = false
	turn_index = 0
	winner_index = -1
	sort_mode = -1
	last_message = "Distribution en cours..."

	var deck: Array[CardInstance] = []
	var uid: int = 1
	for deck_index: int in range(2):
		for suit: String in SUITS:
			for rank: String in RANKS:
				deck.append(CardInstance.new(uid, deck_index, suit, rank, ""))
				uid += 1
		deck.append(CardInstance.new(uid, deck_index, "", "", "black"))
		uid += 1
		deck.append(CardInstance.new(uid, deck_index, "", "", "red"))
		uid += 1

	deck.shuffle()
	for _deal_index: int in range(13):
		player_hand.append(deck.pop_back())
		ai1_hand.append(deck.pop_back())
		ai2_hand.append(deck.pop_back())

	discard_pile.append(deck.pop_back())
	for card: CardInstance in deck:
		stock.append(card)
	phase = Phase.DRAW
	last_message = "À vous : piochez une carte ou prenez la défausse."

func draw_stock() -> bool:
	if not _human_can_draw():
		return false
	_recycle_stock_if_needed()
	if stock.is_empty():
		last_message = "La pioche est vide."
		return false
	player_hand.append(stock.pop_back())
	phase = Phase.ACTION
	last_message = "Posez si vous le souhaitez, puis défaussez exactement une carte."
	return true

func draw_discard() -> bool:
	if not _human_can_draw() or discard_pile.is_empty():
		return false
	player_hand.append(discard_pile.pop_back())
	phase = Phase.ACTION
	last_message = "Défausse récupérée. Posez si vous le souhaitez, puis défaussez."
	return true

func _human_can_draw() -> bool:
	return winner_index < 0 and turn_index == 0 and phase == Phase.DRAW

func top_discard() -> CardInstance:
	if discard_pile.is_empty():
		return null
	return discard_pile.back()

func toggle_sort_player_hand() -> int:
	if sort_mode == -1 or sort_mode == 1:
		sort_mode = 0
		player_hand.sort_custom(_card_less_suit)
	else:
		sort_mode = 1
		player_hand.sort_custom(_card_less_rank)
	return sort_mode

func current_sort_name() -> String:
	if sort_mode == 0:
		return "Couleur"
	if sort_mode == 1:
		return "Valeur"
	return ""

func play_player_selection(indices: Array[int]) -> Dictionary:
	if winner_index >= 0 or turn_index != 0 or phase != Phase.ACTION:
		return {"ok": false, "message": "Vous devez d'abord piocher."}
	var check: Dictionary = _selection_cards(player_hand, indices)
	if not bool(check.get("ok", false)):
		return check
	var cards: Array[CardInstance] = _dictionary_cards(check)
	if cards.size() < 3:
		return {"ok": false, "message": "Une combinaison contient au moins 3 cartes."}
	var info: Dictionary = validate_meld(cards)
	if not bool(info.get("valid", false)):
		return {"ok": false, "message": "Ces cartes ne forment pas une combinaison valide."}
	if player_hand.size() - indices.size() <= 0:
		return {"ok": false, "message": "Gardez une dernière carte pour la défausse finale."}
	if not player_opened and not _opening_is_valid(cards, info):
		return {"ok": false, "message": _opening_error_message()}

	_remove_indices(player_hand, indices)
	_consume_required_jokers(cards)
	table_melds.append({
		"owner": 0,
		"cards": _ordered_meld(cards, info),
		"kind": String(info.get("kind", ""))
	})
	if not player_opened:
		player_opened = true
		last_message = "Vous êtes ouvert ! Terminez votre tour par une défausse."
	else:
		last_message = "Combinaison posée. Terminez votre tour par une défausse."
	return {"ok": true, "message": last_message}

func play_player_on_meld(indices: Array[int], meld_index: int) -> Dictionary:
	if winner_index >= 0 or turn_index != 0 or phase != Phase.ACTION:
		return {"ok": false, "message": "Vous devez d'abord piocher."}
	if not player_opened:
		return {"ok": false, "message": "Posez d'abord votre propre combinaison pour vous ouvrir."}
	if meld_index < 0 or meld_index >= table_melds.size():
		return {"ok": false, "message": "Combinaison de table introuvable."}
	var check: Dictionary = _selection_cards(player_hand, indices)
	if not bool(check.get("ok", false)):
		return check
	var selected: Array[CardInstance] = _dictionary_cards(check)
	if selected.is_empty():
		return {"ok": false, "message": "Sélectionnez au moins une carte."}
	if player_hand.size() - indices.size() <= 0:
		return {"ok": false, "message": "Gardez une dernière carte pour la défausse finale."}

	var meld: Dictionary = table_melds[meld_index]
	var existing: Array[CardInstance] = _dictionary_cards(meld)
	var simulation: Dictionary = _simulate_add_to_meld(existing, selected, true)
	if not bool(simulation.get("ok", false)):
		return {"ok": false, "message": "Ces cartes ne peuvent pas compléter cette combinaison."}

	_remove_indices(player_hand, indices)
	_consume_required_jokers(selected)
	var new_cards: Array[CardInstance] = _dictionary_cards(simulation)
	table_melds[meld_index]["cards"] = new_cards
	var new_info: Dictionary = validate_meld(new_cards)
	table_melds[meld_index]["kind"] = String(new_info.get("kind", ""))

	var recovered: Array[CardInstance] = _dictionary_card_array(simulation, "recovered")
	for joker: CardInstance in recovered:
		player_hand.append(joker)
		must_replay_jokers.append(joker)
	if recovered.is_empty():
		last_message = "Carte(s) ajoutée(s) à la combinaison."
	else:
		last_message = "Joker récupéré : vous devez le rejouer pendant ce tour."
	return {"ok": true, "message": last_message, "recovered": recovered.size()}

func discard_player(index: int) -> Dictionary:
	if winner_index >= 0 or turn_index != 0 or phase != Phase.ACTION:
		return {"ok": false, "message": "Vous ne pouvez pas défausser maintenant."}
	if not must_replay_jokers.is_empty():
		return {"ok": false, "message": "Vous devez d'abord rejouer le Joker récupéré."}
	if index < 0 or index >= player_hand.size():
		return {"ok": false, "message": "Sélectionnez exactement une carte à défausser."}

	var discarded: CardInstance = player_hand[index]
	player_hand.remove_at(index)
	discard_pile.append(discarded)
	if player_hand.is_empty():
		_finish_game(0)
		return {"ok": true, "game_over": true}

	phase = Phase.AI
	turn_index = 1
	_run_ai_turn(1)
	if winner_index < 0:
		turn_index = 2
		_run_ai_turn(2)
	if winner_index < 0:
		turn_index = 0
		phase = Phase.DRAW
		last_message = "À vous : piochez une carte ou prenez la dernière défausse."
	return {"ok": true, "game_over": winner_index >= 0}

func validate_meld(cards: Array[CardInstance]) -> Dictionary:
	if cards.size() < 3:
		return {"valid": false}
	var jokers: int = 0
	var natural: Array[CardInstance] = []
	for card: CardInstance in cards:
		if card.is_joker():
			jokers += 1
		else:
			natural.append(card)
	if natural.is_empty():
		return {"valid": false}

	var set_info: Dictionary = _validate_set(natural, jokers, cards.size())
	if bool(set_info.get("valid", false)):
		return set_info
	return _validate_run(natural, jokers, cards.size())

func _validate_set(natural: Array[CardInstance], _jokers: int, total: int) -> Dictionary:
	if total < 3 or total > 4:
		return {"valid": false}
	var rank: String = natural[0].rank
	var used_suits: Array[String] = []
	for card: CardInstance in natural:
		if card.rank != rank:
			return {"valid": false}
		if used_suits.has(card.suit):
			return {"valid": false}
		used_suits.append(card.suit)
	return {
		"valid": true,
		"kind": "set",
		"points": rank_points(rank) * total,
		"high_ace": false,
		"family": "set_%s" % rank
	}

func _validate_run(natural: Array[CardInstance], jokers: int, total: int) -> Dictionary:
	if total > 13:
		return {"valid": false}
	var suit: String = natural[0].suit
	var values: Array[int] = []
	for card: CardInstance in natural:
		if card.suit != suit:
			return {"valid": false}
		var value: int = rank_value(card.rank)
		if values.has(value):
			return {"valid": false}
		values.append(value)
	values.sort()

	var best: Dictionary = _fit_run(values, jokers, total, false)
	if values.has(1):
		var high_values: Array[int] = []
		for value: int in values:
			high_values.append(14 if value == 1 else value)
		high_values.sort()
		var high: Dictionary = _fit_run(high_values, jokers, total, true)
		if bool(high.get("valid", false)) and (not bool(best.get("valid", false)) or int(high.get("points", 0)) > int(best.get("points", 0))):
			best = high
	if bool(best.get("valid", false)):
		best["kind"] = "run"
		best["family"] = "run_%s" % suit
	return best

func _fit_run(values: Array[int], jokers: int, total: int, high_ace: bool) -> Dictionary:
	var max_rank: int = 14 if high_ace else 13
	var last_start: int = max_rank - total + 1
	if last_start < 1:
		return {"valid": false}
	for start: int in range(1, last_start + 1):
		var finish: int = start + total - 1
		var inside: bool = true
		for value: int in values:
			if value < start or value > finish:
				inside = false
				break
		if not inside:
			continue
		var missing: int = 0
		var points: int = 0
		for target: int in range(start, finish + 1):
			if not values.has(target):
				missing += 1
			points += _sequence_points(target)
		if missing == jokers:
			return {"valid": true, "points": points, "high_ace": high_ace, "start": start}
	return {"valid": false}

func _sequence_points(value: int) -> int:
	if value == 1 or value == 14:
		return 11
	return mini(value, 10)

func _opening_is_valid(cards: Array[CardInstance], info: Dictionary) -> bool:
	if opening_rule == OpeningRule.SIMPLE_MELD:
		return true
	if int(info.get("points", 0)) < 51:
		return false
	return _has_natural_tierce(cards)

func _opening_error_message() -> String:
	if opening_rule == OpeningRule.RAMI_51:
		return "Ouverture Rami 51 : 51 points minimum et une tierce franche sans Joker."
	return "Ouverture invalide."

func _has_natural_tierce(cards: Array[CardInstance]) -> bool:
	for suit: String in SUITS:
		var values: Array[int] = []
		for card: CardInstance in cards:
			if card.is_joker() or card.suit != suit:
				continue
			var value: int = rank_value(card.rank)
			if not values.has(value):
				values.append(value)
		values.sort()
		if _contains_three_consecutive(values):
			return true
		if values.has(1):
			var high: Array[int] = []
			for value: int in values:
				high.append(14 if value == 1 else value)
			high.sort()
			if _contains_three_consecutive(high):
				return true
	return false

func _contains_three_consecutive(values: Array[int]) -> bool:
	if values.size() < 3:
		return false
	var streak: int = 1
	for i: int in range(1, values.size()):
		if values[i] == values[i - 1] + 1:
			streak += 1
			if streak >= 3:
				return true
		else:
			streak = 1
	return false

func detect_player_melds() -> Array[Dictionary]:
	return detect_melds(player_hand)

func detect_melds(hand: Array[CardInstance]) -> Array[Dictionary]:
	var candidates: Array[Dictionary] = []
	var n: int = hand.size()
	if n < 3:
		return candidates
	if n > 15:
		n = 15
	var max_mask: int = 1 << n
	for mask: int in range(1, max_mask):
		var count: int = _bit_count(mask)
		if count < 3 or count > 13:
			continue
		var cards: Array[CardInstance] = []
		var indices: Array[int] = []
		for i: int in range(n):
			if (mask & (1 << i)) != 0:
				cards.append(hand[i])
				indices.append(i)
		var info: Dictionary = validate_meld(cards)
		if not bool(info.get("valid", false)):
			continue
		candidates.append({
			"mask": mask,
			"indices": indices,
			"cards": _ordered_meld(cards, info),
			"kind": String(info.get("kind", "")),
			"family": String(info.get("family", "")),
			"points": int(info.get("points", 0)),
			"count": count
		})

	candidates.sort_custom(_candidate_better)
	var filtered: Array[Dictionary] = []
	for candidate: Dictionary in candidates:
		var dominated: bool = false
		for kept: Dictionary in filtered:
			if String(candidate.get("family", "")) != String(kept.get("family", "")):
				continue
			var cmask: int = int(candidate.get("mask", 0))
			var kmask: int = int(kept.get("mask", 0))
			if cmask != kmask and (cmask & kmask) == cmask:
				dominated = true
				break
		if not dominated:
			filtered.append(candidate)
		if filtered.size() >= 12:
			break
	return filtered

func _candidate_better(a: Dictionary, b: Dictionary) -> bool:
	var ac: int = int(a.get("count", 0))
	var bc: int = int(b.get("count", 0))
	if ac != bc:
		return ac > bc
	return int(a.get("points", 0)) > int(b.get("points", 0))

func _simulate_add_to_meld(existing: Array[CardInstance], selected: Array[CardInstance], allow_replace: bool) -> Dictionary:
	var current: Array[CardInstance] = []
	for card: CardInstance in existing:
		current.append(card)
	var remaining: Array[CardInstance] = []
	for card: CardInstance in selected:
		remaining.append(card)
	var recovered: Array[CardInstance] = []

	if allow_replace:
		var scan: int = 0
		while scan < remaining.size():
			var card: CardInstance = remaining[scan]
			if card.is_joker():
				scan += 1
				continue
			var replaced: bool = false
			for j: int in range(current.size()):
				if not current[j].is_joker():
					continue
				var test: Array[CardInstance] = []
				for existing_card: CardInstance in current:
					test.append(existing_card)
				var joker: CardInstance = test[j]
				test.remove_at(j)
				test.append(card)
				var info: Dictionary = validate_meld(test)
				if bool(info.get("valid", false)):
					current = _ordered_meld(test, info)
					recovered.append(joker)
					remaining.remove_at(scan)
					replaced = true
					break
			if not replaced:
				scan += 1

	for card: CardInstance in remaining:
		var test_add: Array[CardInstance] = []
		for existing_card: CardInstance in current:
			test_add.append(existing_card)
		test_add.append(card)
		var add_info: Dictionary = validate_meld(test_add)
		if not bool(add_info.get("valid", false)):
			return {"ok": false}
		current = _ordered_meld(test_add, add_info)
	return {"ok": true, "cards": current, "recovered": recovered}

func _run_ai_turn(ai_index: int) -> void:
	if winner_index >= 0:
		return
	var hand: Array[CardInstance] = get_hand(ai_index)
	_recycle_stock_if_needed()
	var took_discard: bool = false
	if not discard_pile.is_empty() and _ai_should_take_discard(hand, discard_pile.back()):
		hand.append(discard_pile.pop_back())
		took_discard = true
	elif not stock.is_empty():
		hand.append(stock.pop_back())
	elif not discard_pile.is_empty():
		hand.append(discard_pile.pop_back())
		took_discard = true

	var opened: bool = is_opened(ai_index)
	if not opened:
		var opening: Dictionary = _best_ai_candidate(hand, true)
		if not opening.is_empty():
			_ai_play_candidate(ai_index, opening)
			_set_opened(ai_index, true)
			opened = true

	if opened:
		_ai_add_to_table(ai_index)
		var safety: int = 0
		while safety < 4:
			safety += 1
			var next_meld: Dictionary = _best_ai_candidate(hand, false)
			if next_meld.is_empty():
				break
			_ai_play_candidate(ai_index, next_meld)

	if hand.is_empty():
		return
	var discard_index: int = _ai_discard_index(hand)
	discard_pile.append(hand[discard_index])
	hand.remove_at(discard_index)
	if hand.is_empty():
		_finish_game(ai_index)
		return
	last_message = "%s a joué%s." % [PLAYER_NAMES[ai_index], " après avoir pris la défausse" if took_discard else ""]

func _ai_should_take_discard(hand: Array[CardInstance], card: CardInstance) -> bool:
	var test: Array[CardInstance] = []
	for held: CardInstance in hand:
		test.append(held)
	test.append(card)
	var candidates: Array[Dictionary] = detect_melds(test)
	var new_index: int = test.size() - 1
	for candidate: Dictionary in candidates:
		var indices: Array[int] = _dictionary_int_array(candidate, "indices")
		if indices.has(new_index):
			return true
	return false

func _best_ai_candidate(hand: Array[CardInstance], opening_only: bool) -> Dictionary:
	var candidates: Array[Dictionary] = detect_melds(hand)
	for candidate: Dictionary in candidates:
		var indices: Array[int] = _dictionary_int_array(candidate, "indices")
		if hand.size() - indices.size() < 1:
			continue
		if opening_only:
			var cards: Array[CardInstance] = _dictionary_cards(candidate)
			var info: Dictionary = validate_meld(cards)
			if not _opening_is_valid(cards, info):
				continue
		return candidate
	return {}

func _ai_play_candidate(ai_index: int, candidate: Dictionary) -> void:
	var hand: Array[CardInstance] = get_hand(ai_index)
	var indices: Array[int] = _dictionary_int_array(candidate, "indices")
	var cards: Array[CardInstance] = _dictionary_cards(candidate)
	_remove_indices(hand, indices)
	var info: Dictionary = validate_meld(cards)
	table_melds.append({"owner": ai_index, "cards": _ordered_meld(cards, info), "kind": String(info.get("kind", ""))})

func _ai_add_to_table(ai_index: int) -> void:
	var hand: Array[CardInstance] = get_hand(ai_index)
	var changed: bool = true
	var safety: int = 0
	while changed and safety < 8 and hand.size() > 1:
		safety += 1
		changed = false
		for card_index: int in range(hand.size()):
			if hand.size() <= 1:
				return
			var card: CardInstance = hand[card_index]
			for meld_index: int in range(table_melds.size()):
				var existing: Array[CardInstance] = _dictionary_cards(table_melds[meld_index])
				var selected: Array[CardInstance] = []
				selected.append(card)
				var simulation: Dictionary = _simulate_add_to_meld(existing, selected, false)
				if bool(simulation.get("ok", false)):
					hand.remove_at(card_index)
					table_melds[meld_index]["cards"] = _dictionary_cards(simulation)
					changed = true
					break
			if changed:
				break

func _ai_discard_index(hand: Array[CardInstance]) -> int:
	var best_index: int = 0
	var best_value: int = -1
	for i: int in range(hand.size()):
		var value: int = card_points(hand[i])
		if value > best_value:
			best_value = value
			best_index = i
	return best_index

func _finish_game(winner: int) -> void:
	winner_index = winner
	turn_index = winner
	phase = Phase.GAME_OVER
	ranking = _build_ranking()
	last_message = "%s termine la manche !" % PLAYER_NAMES[winner]

func _build_ranking() -> Array[Dictionary]:
	var rows: Array[Dictionary] = []
	for i: int in range(3):
		rows.append({"player": i, "name": PLAYER_NAMES[i], "points": hand_score(get_hand(i))})
	rows.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return int(a.get("points", 0)) < int(b.get("points", 0))
	)
	var previous_points: int = -1
	var previous_place: int = 0
	for i: int in range(rows.size()):
		var points: int = int(rows[i].get("points", 0))
		var place: int = i + 1
		if i > 0 and points == previous_points:
			place = previous_place
		rows[i]["place"] = place
		previous_points = points
		previous_place = place
	return rows

func hand_score(hand: Array[CardInstance]) -> int:
	var total: int = 0
	for card: CardInstance in hand:
		total += card_points(card)
	return total

func card_points(card: CardInstance) -> int:
	if card.is_joker():
		return 20
	return rank_points(card.rank)

func rank_points(rank: String) -> int:
	if rank == "A":
		return 11
	if rank == "J" or rank == "Q" or rank == "K":
		return 10
	return int(rank)

func rank_value(rank: String) -> int:
	return RANKS.find(rank) + 1

func get_hand(player_index: int) -> Array[CardInstance]:
	if player_index == 0:
		return player_hand
	if player_index == 1:
		return ai1_hand
	return ai2_hand

func is_opened(player_index: int) -> bool:
	if player_index == 0:
		return player_opened
	if player_index == 1:
		return ai1_opened
	return ai2_opened

func _set_opened(player_index: int, value: bool) -> void:
	if player_index == 0:
		player_opened = value
	elif player_index == 1:
		ai1_opened = value
	else:
		ai2_opened = value

func _selection_cards(hand: Array[CardInstance], indices: Array[int]) -> Dictionary:
	var unique: Array[int] = []
	for idx: int in indices:
		if idx < 0 or idx >= hand.size() or unique.has(idx):
			return {"ok": false, "message": "Sélection invalide."}
		unique.append(idx)
	var cards: Array[CardInstance] = []
	for idx: int in unique:
		cards.append(hand[idx])
	return {"ok": true, "cards": cards}

func _ordered_meld(cards: Array[CardInstance], info: Dictionary) -> Array[CardInstance]:
	var natural: Array[CardInstance] = []
	var jokers: Array[CardInstance] = []
	for card: CardInstance in cards:
		if card.is_joker():
			jokers.append(card)
		else:
			natural.append(card)
	if String(info.get("kind", "")) == "set":
		natural.sort_custom(_card_less_suit)
		natural.append_array(jokers)
		return natural
	var high_ace: bool = bool(info.get("high_ace", false))
	natural.sort_custom(func(a: CardInstance, b: CardInstance) -> bool:
		var av: int = rank_value(a.rank)
		var bv: int = rank_value(b.rank)
		if high_ace:
			av = 14 if av == 1 else av
			bv = 14 if bv == 1 else bv
		return av < bv
	)
	natural.append_array(jokers)
	return natural

func _consume_required_jokers(cards: Array[CardInstance]) -> void:
	for card: CardInstance in cards:
		if not card.is_joker():
			continue
		var idx: int = -1
		for i: int in range(must_replay_jokers.size()):
			if must_replay_jokers[i].uid == card.uid:
				idx = i
				break
		if idx >= 0:
			must_replay_jokers.remove_at(idx)

func _dictionary_cards(item: Dictionary) -> Array[CardInstance]:
	return _dictionary_card_array(item, "cards")

func _dictionary_card_array(item: Dictionary, key: String) -> Array[CardInstance]:
	var out: Array[CardInstance] = []
	var raw: Array = item.get(key, [])
	for value: Variant in raw:
		if value is CardInstance:
			out.append(value as CardInstance)
	return out

func _dictionary_int_array(item: Dictionary, key: String) -> Array[int]:
	var out: Array[int] = []
	var raw: Array = item.get(key, [])
	for value: Variant in raw:
		out.append(int(value))
	return out

func _remove_indices(hand: Array[CardInstance], indices: Array[int]) -> void:
	var sorted: Array[int] = []
	for idx: int in indices:
		sorted.append(idx)
	sorted.sort()
	sorted.reverse()
	for idx: int in sorted:
		hand.remove_at(idx)

func _recycle_stock_if_needed() -> void:
	if not stock.is_empty() or discard_pile.size() <= 1:
		return
	var top: CardInstance = discard_pile.pop_back()
	stock.clear()
	for card: CardInstance in discard_pile:
		stock.append(card)
	stock.shuffle()
	discard_pile.clear()
	discard_pile.append(top)

func _bit_count(mask: int) -> int:
	var value: int = mask
	var count: int = 0
	while value != 0:
		count += value & 1
		value >>= 1
	return count

func _card_less_suit(a: CardInstance, b: CardInstance) -> bool:
	var a_suit: int = 99 if a.is_joker() else SUITS.find(a.suit)
	var b_suit: int = 99 if b.is_joker() else SUITS.find(b.suit)
	if a_suit != b_suit:
		return a_suit < b_suit
	var a_rank: int = 99 if a.is_joker() else RANKS.find(a.rank)
	var b_rank: int = 99 if b.is_joker() else RANKS.find(b.rank)
	if a_rank != b_rank:
		return a_rank < b_rank
	return a.uid < b.uid

func _card_less_rank(a: CardInstance, b: CardInstance) -> bool:
	var a_rank: int = 99 if a.is_joker() else RANKS.find(a.rank)
	var b_rank: int = 99 if b.is_joker() else RANKS.find(b.rank)
	if a_rank != b_rank:
		return a_rank < b_rank
	var a_suit: int = 99 if a.is_joker() else SUITS.find(a.suit)
	var b_suit: int = 99 if b.is_joker() else SUITS.find(b.suit)
	if a_suit != b_suit:
		return a_suit < b_suit
	return a.uid < b.uid
