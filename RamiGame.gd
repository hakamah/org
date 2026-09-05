class_name RamiGame
extends RefCounted

const SUITS: Array[String] = ["spades", "hearts", "diamonds", "clubs"]
const RANKS: Array[String] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
const PLAYER_NAMES: Array[String] = ["Vous", "IA 1", "IA 2"]

var stock: Array[String] = []
var discard_pile: Array[String] = []
var player_hand: Array[String] = []
var ai1_hand: Array[String] = []
var ai2_hand: Array[String] = []
var table_melds: Array[Dictionary] = []

var player_opened: bool = false
var ai1_opened: bool = false
var ai2_opened: bool = false
var turn_index: int = 0
var phase: String = "draw"
var winner_index: int = -1
var last_message: String = ""
var ranking: Array[Dictionary] = []

var sort_mode: int = -1
var must_replay_jokers: Array[String] = []

func new_round() -> void:
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
	phase = "draw"
	winner_index = -1
	sort_mode = -1
	last_message = "À vous : piochez une carte."

	var deck: Array[String] = []
	for _copy_index: int in range(2):
		for suit: String in SUITS:
			for rank: String in RANKS:
				deck.append("%s_%s" % [suit, rank])
		deck.append("joker_black")
		deck.append("joker_red")
	deck.shuffle()

	for _deal_index: int in range(13):
		player_hand.append(deck.pop_back())
		ai1_hand.append(deck.pop_back())
		ai2_hand.append(deck.pop_back())

	discard_pile.append(deck.pop_back())
	stock = deck

func draw_stock() -> bool:
	if not _human_can_draw():
		return false
	_recycle_stock_if_needed()
	if stock.is_empty():
		last_message = "La pioche est vide."
		return false
	player_hand.append(stock.pop_back())
	phase = "action"
	last_message = "Posez vos combinaisons puis défaussez une carte."
	return true

func draw_discard() -> bool:
	if not _human_can_draw() or discard_pile.is_empty():
		return false
	player_hand.append(discard_pile.pop_back())
	phase = "action"
	last_message = "Carte récupérée. Posez puis défaussez une carte."
	return true

func _human_can_draw() -> bool:
	return winner_index < 0 and turn_index == 0 and phase == "draw"

func top_discard() -> String:
	if discard_pile.is_empty():
		return ""
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
	if winner_index >= 0 or turn_index != 0 or phase != "action":
		return {"ok": false, "message": "Vous devez d'abord piocher."}
	var check: Dictionary = _selection_cards(player_hand, indices)
	if not bool(check.get("ok", false)):
		return check
	var cards: Array[String] = _dictionary_cards(check)
	if cards.size() < 3:
		return {"ok": false, "message": "Une combinaison contient au moins 3 cartes."}
	var info: Dictionary = validate_meld(cards)
	if not bool(info.get("valid", false)):
		return {"ok": false, "message": "Ces cartes ne forment pas une combinaison valide."}
	if player_hand.size() - indices.size() <= 0:
		return {"ok": false, "message": "Gardez une dernière carte pour la défausse finale."}

	_remove_indices(player_hand, indices)
	_consume_required_jokers(cards)
	table_melds.append({
		"owner": 0,
		"cards": _ordered_meld(cards, info),
		"kind": String(info.get("kind", ""))
	})
	if not player_opened:
		player_opened = true
		last_message = "Vous êtes ouvert ! Vous devez finir par une défausse."
	else:
		last_message = "Combinaison posée. Défaussez pour terminer le tour."
	return {"ok": true, "message": last_message}

func play_player_on_meld(indices: Array[int], meld_index: int) -> Dictionary:
	if winner_index >= 0 or turn_index != 0 or phase != "action":
		return {"ok": false, "message": "Vous devez d'abord piocher."}
	if not player_opened:
		return {"ok": false, "message": "Posez d'abord votre propre combinaison pour vous ouvrir."}
	if meld_index < 0 or meld_index >= table_melds.size():
		return {"ok": false, "message": "Combinaison de table introuvable."}
	var check: Dictionary = _selection_cards(player_hand, indices)
	if not bool(check.get("ok", false)):
		return check
	var selected: Array[String] = _dictionary_cards(check)
	if selected.is_empty():
		return {"ok": false, "message": "Sélectionnez au moins une carte."}
	if player_hand.size() - indices.size() <= 0:
		return {"ok": false, "message": "Gardez une dernière carte pour la défausse finale."}

	var meld: Dictionary = table_melds[meld_index]
	var existing: Array[String] = _dictionary_cards(meld)
	var simulation: Dictionary = _simulate_add_to_meld(existing, selected, true)
	if not bool(simulation.get("ok", false)):
		return {"ok": false, "message": "Ces cartes ne peuvent pas compléter cette combinaison."}

	_remove_indices(player_hand, indices)
	_consume_required_jokers(selected)
	var new_cards: Array[String] = _dictionary_cards(simulation)
	table_melds[meld_index]["cards"] = new_cards
	var new_info: Dictionary = validate_meld(new_cards)
	table_melds[meld_index]["kind"] = String(new_info.get("kind", ""))

	var recovered: Array[String] = _dictionary_string_array(simulation, "recovered")
	for joker: String in recovered:
		player_hand.append(joker)
		must_replay_jokers.append(joker)
	if recovered.is_empty():
		last_message = "Carte(s) ajoutée(s) à la combinaison."
	else:
		last_message = "Joker récupéré : vous devez le rejouer pendant ce tour."
	return {"ok": true, "message": last_message, "recovered": recovered.size()}

func discard_player(index: int) -> Dictionary:
	if winner_index >= 0 or turn_index != 0 or phase != "action":
		return {"ok": false, "message": "Vous ne pouvez pas défausser maintenant."}
	if not must_replay_jokers.is_empty():
		return {"ok": false, "message": "Vous devez d'abord rejouer le Joker récupéré."}
	if index < 0 or index >= player_hand.size():
		return {"ok": false, "message": "Sélectionnez exactement une carte à défausser."}

	var discarded: String = player_hand[index]
	player_hand.remove_at(index)
	discard_pile.append(discarded)
	if player_hand.is_empty():
		_finish_game(0)
		return {"ok": true, "game_over": true}

	phase = "ai"
	turn_index = 1
	_run_ai_turn(1)
	if winner_index < 0:
		turn_index = 2
		_run_ai_turn(2)
	if winner_index < 0:
		turn_index = 0
		phase = "draw"
		last_message = "À vous : piochez une carte ou prenez la défausse."
	return {"ok": true, "game_over": winner_index >= 0}

func validate_meld(cards: Array[String]) -> Dictionary:
	if cards.size() < 3:
		return {"valid": false}
	var jokers: int = 0
	var natural: Array[String] = []
	for card: String in cards:
		if is_joker(card):
			jokers += 1
		else:
			natural.append(card)
	if natural.is_empty():
		return {"valid": false}

	var set_info: Dictionary = _validate_set(natural, jokers, cards.size())
	if bool(set_info.get("valid", false)):
		return set_info
	return _validate_run(natural, jokers, cards.size())

func _validate_set(natural: Array[String], _jokers: int, total: int) -> Dictionary:
	if total < 3 or total > 4:
		return {"valid": false}
	var rank: String = card_rank(natural[0])
	var used_suits: Array[String] = []
	for card: String in natural:
		if card_rank(card) != rank:
			return {"valid": false}
		var suit: String = card_suit(card)
		if used_suits.has(suit):
			return {"valid": false}
		used_suits.append(suit)
	return {
		"valid": true,
		"kind": "set",
		"points": rank_points(rank) * total,
		"high_ace": false,
		"family": "set_%s" % rank
	}

func _validate_run(natural: Array[String], jokers: int, total: int) -> Dictionary:
	if total > 13:
		return {"valid": false}
	var suit: String = card_suit(natural[0])
	var values: Array[int] = []
	for card: String in natural:
		if card_suit(card) != suit:
			return {"valid": false}
		var value: int = rank_value(card_rank(card))
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

func detect_player_melds() -> Array[Dictionary]:
	return detect_melds(player_hand)

func detect_melds(hand: Array[String]) -> Array[Dictionary]:
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
		var cards: Array[String] = []
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
		if filtered.size() >= 10:
			break
	return filtered

func _candidate_better(a: Dictionary, b: Dictionary) -> bool:
	var ac: int = int(a.get("count", 0))
	var bc: int = int(b.get("count", 0))
	if ac != bc:
		return ac > bc
	return int(a.get("points", 0)) > int(b.get("points", 0))

func _simulate_add_to_meld(existing: Array[String], selected: Array[String], allow_replace: bool) -> Dictionary:
	var current: Array[String] = existing.duplicate()
	var remaining: Array[String] = selected.duplicate()
	var recovered: Array[String] = []

	if allow_replace:
		var scan: int = 0
		while scan < remaining.size():
			var card: String = remaining[scan]
			if is_joker(card):
				scan += 1
				continue
			var replaced: bool = false
			for j: int in range(current.size()):
				if not is_joker(current[j]):
					continue
				var test: Array[String] = current.duplicate()
				var joker: String = test[j]
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

	for card: String in remaining:
		var test_add: Array[String] = current.duplicate()
		test_add.append(card)
		var add_info: Dictionary = validate_meld(test_add)
		if not bool(add_info.get("valid", false)):
			return {"ok": false}
		current = _ordered_meld(test_add, add_info)
	return {"ok": true, "cards": current, "recovered": recovered}

func _run_ai_turn(ai_index: int) -> void:
	if winner_index >= 0:
		return
	var hand: Array[String] = get_hand(ai_index)
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
		var opening: Dictionary = _best_ai_candidate(hand)
		if not opening.is_empty():
			_ai_play_candidate(ai_index, opening)
			_set_opened(ai_index, true)
			opened = true

	if opened:
		_ai_add_to_table(ai_index)
		var safety: int = 0
		while safety < 4:
			safety += 1
			var next_meld: Dictionary = _best_ai_candidate(hand)
			if next_meld.is_empty():
				break
			_ai_play_candidate(ai_index, next_meld)

	if hand.is_empty():
		# La règle impose une dernière défausse : l'IA ne doit jamais vider sa main par pose.
		return
	var discard_index: int = _ai_discard_index(hand)
	discard_pile.append(hand[discard_index])
	hand.remove_at(discard_index)
	if hand.is_empty():
		_finish_game(ai_index)
		return
	last_message = "%s a joué%s." % [PLAYER_NAMES[ai_index], " après avoir pris la défausse" if took_discard else ""]

func _ai_should_take_discard(hand: Array[String], card: String) -> bool:
	var test: Array[String] = hand.duplicate()
	test.append(card)
	var candidates: Array[Dictionary] = detect_melds(test)
	var new_index: int = test.size() - 1
	for candidate: Dictionary in candidates:
		var indices: Array[int] = _dictionary_int_array(candidate, "indices")
		if indices.has(new_index):
			return true
	return false

func _best_ai_candidate(hand: Array[String]) -> Dictionary:
	var candidates: Array[Dictionary] = detect_melds(hand)
	for candidate: Dictionary in candidates:
		var indices: Array[int] = _dictionary_int_array(candidate, "indices")
		if hand.size() - indices.size() >= 1:
			return candidate
	return {}

func _ai_play_candidate(ai_index: int, candidate: Dictionary) -> void:
	var hand: Array[String] = get_hand(ai_index)
	var indices: Array[int] = _dictionary_int_array(candidate, "indices")
	var cards: Array[String] = _dictionary_string_array(candidate, "cards")
	_remove_indices(hand, indices)
	var info: Dictionary = validate_meld(cards)
	table_melds.append({"owner": ai_index, "cards": _ordered_meld(cards, info), "kind": String(info.get("kind", ""))})

func _ai_add_to_table(ai_index: int) -> void:
	var hand: Array[String] = get_hand(ai_index)
	var changed: bool = true
	var safety: int = 0
	while changed and safety < 8 and hand.size() > 1:
		safety += 1
		changed = false
		for card_index: int in range(hand.size()):
			if hand.size() <= 1:
				return
			var card: String = hand[card_index]
			for meld_index: int in range(table_melds.size()):
				var existing: Array[String] = _dictionary_cards(table_melds[meld_index])
				var selected: Array[String] = [card]
				var simulation: Dictionary = _simulate_add_to_meld(existing, selected, false)
				if bool(simulation.get("ok", false)):
					hand.remove_at(card_index)
					table_melds[meld_index]["cards"] = _dictionary_cards(simulation)
					changed = true
					break
			if changed:
				break

func _ai_discard_index(hand: Array[String]) -> int:
	var best_index: int = 0
	var best_value: int = -1
	for i: int in range(hand.size()):
		var card: String = hand[i]
		var value: int = card_points(card)
		if value > best_value:
			best_value = value
			best_index = i
	return best_index

func _finish_game(winner: int) -> void:
	winner_index = winner
	turn_index = winner
	phase = "game_over"
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

func hand_score(hand: Array[String]) -> int:
	var total: int = 0
	for card: String in hand:
		total += card_points(card)
	return total

func card_points(card_id: String) -> int:
	if is_joker(card_id):
		return 20
	return rank_points(card_rank(card_id))

func rank_points(rank: String) -> int:
	if rank == "A":
		return 11
	if rank == "J" or rank == "Q" or rank == "K":
		return 10
	return int(rank)

func rank_value(rank: String) -> int:
	return RANKS.find(rank) + 1

func get_hand(player_index: int) -> Array[String]:
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

func is_joker(card_id: String) -> bool:
	return card_id.begins_with("joker")

func card_suit(card_id: String) -> String:
	if is_joker(card_id):
		return "joker"
	var split_at: int = card_id.rfind("_")
	return card_id.substr(0, split_at)

func card_rank(card_id: String) -> String:
	if is_joker(card_id):
		return "JOKER"
	var split_at: int = card_id.rfind("_")
	return card_id.substr(split_at + 1)

func _selection_cards(hand: Array[String], indices: Array[int]) -> Dictionary:
	var unique: Array[int] = []
	for idx: int in indices:
		if idx < 0 or idx >= hand.size() or unique.has(idx):
			return {"ok": false, "message": "Sélection invalide."}
		unique.append(idx)
	var cards: Array[String] = []
	for idx: int in unique:
		cards.append(hand[idx])
	return {"ok": true, "cards": cards}

func _ordered_meld(cards: Array[String], info: Dictionary) -> Array[String]:
	var natural: Array[String] = []
	var jokers: Array[String] = []
	for card: String in cards:
		if is_joker(card):
			jokers.append(card)
		else:
			natural.append(card)
	if String(info.get("kind", "")) == "set":
		natural.sort_custom(_card_less_suit)
		natural.append_array(jokers)
		return natural
	var high_ace: bool = bool(info.get("high_ace", false))
	natural.sort_custom(func(a: String, b: String) -> bool:
		var av: int = rank_value(card_rank(a))
		var bv: int = rank_value(card_rank(b))
		if high_ace:
			av = 14 if av == 1 else av
			bv = 14 if bv == 1 else bv
		return av < bv
	)
	natural.append_array(jokers)
	return natural

func _consume_required_jokers(cards: Array[String]) -> void:
	for card: String in cards:
		if not is_joker(card):
			continue
		var idx: int = must_replay_jokers.find(card)
		if idx >= 0:
			must_replay_jokers.remove_at(idx)

func _dictionary_cards(item: Dictionary) -> Array[String]:
	return _dictionary_string_array(item, "cards")

func _dictionary_string_array(item: Dictionary, key: String) -> Array[String]:
	var out: Array[String] = []
	var raw: Array = item.get(key, [])
	for value: Variant in raw:
		out.append(String(value))
	return out

func _dictionary_int_array(item: Dictionary, key: String) -> Array[int]:
	var out: Array[int] = []
	var raw: Array = item.get(key, [])
	for value: Variant in raw:
		out.append(int(value))
	return out

func _remove_indices(hand: Array[String], indices: Array[int]) -> void:
	var sorted: Array[int] = indices.duplicate()
	sorted.sort()
	sorted.reverse()
	for idx: int in sorted:
		hand.remove_at(idx)

func _recycle_stock_if_needed() -> void:
	if not stock.is_empty() or discard_pile.size() <= 1:
		return
	var top: String = discard_pile.pop_back()
	stock = discard_pile.duplicate()
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

func _card_less_suit(a: String, b: String) -> bool:
	var a_suit: int = 99 if is_joker(a) else SUITS.find(card_suit(a))
	var b_suit: int = 99 if is_joker(b) else SUITS.find(card_suit(b))
	if a_suit != b_suit:
		return a_suit < b_suit
	var a_rank: int = 99 if is_joker(a) else RANKS.find(card_rank(a))
	var b_rank: int = 99 if is_joker(b) else RANKS.find(card_rank(b))
	return a_rank < b_rank

func _card_less_rank(a: String, b: String) -> bool:
	var a_rank: int = 99 if is_joker(a) else RANKS.find(card_rank(a))
	var b_rank: int = 99 if is_joker(b) else RANKS.find(card_rank(b))
	if a_rank != b_rank:
		return a_rank < b_rank
	var a_suit: int = 99 if is_joker(a) else SUITS.find(card_suit(a))
	var b_suit: int = 99 if is_joker(b) else SUITS.find(card_suit(b))
	return a_suit < b_suit