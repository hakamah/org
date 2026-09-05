class_name RamiGame
extends RefCounted

const SUITS: Array[String] = ["spades", "hearts", "diamonds", "clubs"]
const RANKS: Array[String] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

var stock: Array[String] = []
var discard_pile: Array[String] = []
var player_hand: Array[String] = []
var ai_hand: Array[String] = []
var table_melds: Array[Dictionary] = []
var phase: String = "draw"
var player_opened: bool = false
var ai_opened: bool = false
var winner: String = ""
var last_message: String = ""

func new_round() -> void:
	stock.clear()
	discard_pile.clear()
	player_hand.clear()
	ai_hand.clear()
	table_melds.clear()
	phase = "draw"
	player_opened = false
	ai_opened = false
	winner = ""
	last_message = "Piochez une carte."

	var deck: Array[String] = []
	for copy_index: int in range(2):
		for suit: String in SUITS:
			for rank: String in RANKS:
				deck.append("%s_%s" % [suit, rank])
		deck.append("joker_black")
		deck.append("joker_red")
	deck.shuffle()
	for deal_index: int in range(14):
		player_hand.append(deck.pop_back())
		ai_hand.append(deck.pop_back())
	discard_pile.append(deck.pop_back())
	stock = deck

func draw_stock() -> bool:
	if phase != "draw" or winner != "":
		return false
	_recycle_stock_if_needed()
	if stock.is_empty():
		last_message = "La pioche est vide."
		return false
	var card: String = stock.pop_back()
	player_hand.append(card)
	phase = "discard"
	last_message = "Sélectionnez des cartes à poser ou 1 carte à défausser."
	return true

func draw_discard() -> bool:
	if phase != "draw" or winner != "" or discard_pile.is_empty():
		return false
	var card: String = discard_pile.pop_back()
	player_hand.append(card)
	phase = "discard"
	last_message = "Carte prise dans la défausse."
	return true

func top_discard() -> String:
	if discard_pile.is_empty():
		return ""
	return discard_pile.back()

func sort_player_hand() -> void:
	player_hand.sort_custom(_card_less)

func play_player_selection(indices: Array[int]) -> Dictionary:
	if phase != "discard" or winner != "":
		return {"ok": false, "message": "Vous devez d'abord piocher."}
	if indices.size() < 3:
		return {"ok": false, "message": "Sélectionnez au moins 3 cartes."}

	var unique: Array[int] = []
	for idx: int in indices:
		if idx < 0 or idx >= player_hand.size() or unique.has(idx):
			return {"ok": false, "message": "Sélection invalide."}
		unique.append(idx)

	var cards: Array[String] = []
	for idx: int in unique:
		cards.append(player_hand[idx])

	if not player_opened:
		var opening: Array[Dictionary] = _find_opening(cards, true)
		if opening.is_empty():
			return {"ok": false, "message": "Ouverture refusée : 51 points minimum + une tierce franche sans Joker."}
		_remove_indices(player_hand, unique)
		for item: Dictionary in opening:
			var meld_cards: Array[String] = _dictionary_cards(item)
			table_melds.append({"owner": "player", "cards": meld_cards})
		player_opened = true
		last_message = "Ouverture validée !"
	else:
		var info: Dictionary = validate_meld(cards)
		if not bool(info.get("valid", false)):
			return {"ok": false, "message": "Ces cartes ne forment pas une combinaison valide."}
		_remove_indices(player_hand, unique)
		table_melds.append({"owner": "player", "cards": _ordered_meld(cards, info)})
		last_message = "Combinaison posée."

	if player_hand.is_empty():
		winner = "player"
		phase = "game_over"
		last_message = "Victoire ! Vous avez vidé votre main."
	return {"ok": true, "message": last_message}

func discard_player(index: int) -> bool:
	if phase != "discard" or winner != "" or index < 0 or index >= player_hand.size():
		return false
	var card: String = player_hand[index]
	player_hand.remove_at(index)
	discard_pile.append(card)
	if player_hand.is_empty():
		winner = "player"
		phase = "game_over"
		last_message = "Victoire !"
		return true
	phase = "ai"
	_run_ai_turn()
	if winner == "":
		phase = "draw"
		last_message = "À vous : piochez une carte."
	return true

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

func _validate_set(natural: Array[String], jokers: int, total: int) -> Dictionary:
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
	var points: int = rank_points(rank) * total
	return {"valid": true, "kind": "set", "points": points, "pure_run": false, "high_ace": false}

func _validate_run(natural: Array[String], jokers: int, total: int) -> Dictionary:
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

	var low: Dictionary = _fit_run(values, jokers, total, false)
	var best: Dictionary = low
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
		best["pure_run"] = jokers == 0 and total >= 3
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

func _find_opening(cards: Array[String], require_all: bool) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var n: int = cards.size()
	if n < 3 or n > 16:
		return result
	var candidates: Array[Dictionary] = []
	var max_mask: int = 1 << n
	for mask: int in range(1, max_mask):
		var count: int = _bit_count(mask)
		if count < 3 or count > 7:
			continue
		var subset: Array[String] = []
		for i: int in range(n):
			if (mask & (1 << i)) != 0:
				subset.append(cards[i])
		var info: Dictionary = validate_meld(subset)
		if bool(info.get("valid", false)):
			candidates.append({
				"mask": mask,
				"cards": _ordered_meld(subset, info),
				"points": int(info.get("points", 0)),
				"pure": bool(info.get("pure_run", false))
			})
	candidates.sort_custom(_candidate_more_points)
	var target_mask: int = (1 << n) - 1
	return _opening_search(candidates, 0, 0, 0, false, [], target_mask, require_all)

func _opening_search(candidates: Array[Dictionary], start_index: int, used_mask: int, points: int, has_pure: bool, chosen: Array[Dictionary], target_mask: int, require_all: bool) -> Array[Dictionary]:
	if points >= 51 and has_pure and (not require_all or used_mask == target_mask):
		return chosen.duplicate(true)
	for i: int in range(start_index, candidates.size()):
		var candidate: Dictionary = candidates[i]
		var mask: int = int(candidate.get("mask", 0))
		if (mask & used_mask) != 0:
			continue
		chosen.append(candidate)
		var found: Array[Dictionary] = _opening_search(
			candidates,
			i + 1,
			used_mask | mask,
			points + int(candidate.get("points", 0)),
			has_pure or bool(candidate.get("pure", false)),
			chosen,
			target_mask,
			require_all
		)
		if not found.is_empty():
			return found
		chosen.pop_back()
	return []

func _candidate_more_points(a: Dictionary, b: Dictionary) -> bool:
	return int(a.get("points", 0)) > int(b.get("points", 0))

func _run_ai_turn() -> void:
	_recycle_stock_if_needed()
	if not stock.is_empty():
		var drawn: String = stock.pop_back()
		ai_hand.append(drawn)

	if not ai_opened:
		var opening: Array[Dictionary] = _find_opening(ai_hand, false)
		if not opening.is_empty():
			for item: Dictionary in opening:
				var cards: Array[String] = _dictionary_cards(item)
				_remove_cards_once(ai_hand, cards)
				table_melds.append({"owner": "ai", "cards": cards})
			ai_opened = true
	else:
		var safety: int = 0
		while safety < 5:
			safety += 1
			var best: Array[String] = _best_ai_meld()
			if best.is_empty():
				break
			_remove_cards_once(ai_hand, best)
			table_melds.append({"owner": "ai", "cards": best})

	if ai_hand.is_empty():
		winner = "ai"
		phase = "game_over"
		last_message = "L'IA gagne la manche."
		return

	var discard_index: int = _ai_discard_index()
	var discarded: String = ai_hand[discard_index]
	ai_hand.remove_at(discard_index)
	discard_pile.append(discarded)
	if ai_hand.is_empty():
		winner = "ai"
		phase = "game_over"
		last_message = "L'IA gagne la manche."

func _best_ai_meld() -> Array[String]:
	var best: Array[String] = []
	var best_score: int = -1
	var n: int = ai_hand.size()
	if n > 16:
		n = 16
	var max_mask: int = 1 << n
	for mask: int in range(1, max_mask):
		var count: int = _bit_count(mask)
		if count < 3 or count > 7:
			continue
		var subset: Array[String] = []
		for i: int in range(n):
			if (mask & (1 << i)) != 0:
				subset.append(ai_hand[i])
		var info: Dictionary = validate_meld(subset)
		if bool(info.get("valid", false)):
			var score: int = count * 100 + int(info.get("points", 0))
			if score > best_score:
				best_score = score
				best = _ordered_meld(subset, info)
	return best

func _ai_discard_index() -> int:
	var best_index: int = 0
	var best_value: int = -1
	for i: int in range(ai_hand.size()):
		var card: String = ai_hand[i]
		var value: int = 20 if is_joker(card) else rank_points(card_rank(card))
		if value > best_value:
			best_value = value
			best_index = i
	return best_index

func _ordered_meld(cards: Array[String], info: Dictionary) -> Array[String]:
	var natural: Array[String] = []
	var jokers: Array[String] = []
	for card: String in cards:
		if is_joker(card):
			jokers.append(card)
		else:
			natural.append(card)
	if String(info.get("kind", "")) == "set":
		natural.sort_custom(_card_less)
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

func _dictionary_cards(item: Dictionary) -> Array[String]:
	var out: Array[String] = []
	var raw: Array = item.get("cards", [])
	for value: Variant in raw:
		out.append(String(value))
	return out

func rank_points(rank: String) -> int:
	if rank == "A":
		return 11
	if rank == "J" or rank == "Q" or rank == "K":
		return 10
	return int(rank)

func rank_value(rank: String) -> int:
	return RANKS.find(rank) + 1

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

func _remove_indices(hand: Array[String], indices: Array[int]) -> void:
	var sorted: Array[int] = indices.duplicate()
	sorted.sort()
	sorted.reverse()
	for idx: int in sorted:
		hand.remove_at(idx)

func _remove_cards_once(hand: Array[String], cards: Array[String]) -> void:
	for card: String in cards:
		var idx: int = hand.find(card)
		if idx >= 0:
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

func _card_less(a: String, b: String) -> bool:
	var a_suit: int = 99 if is_joker(a) else SUITS.find(card_suit(a))
	var b_suit: int = 99 if is_joker(b) else SUITS.find(card_suit(b))
	if a_suit != b_suit:
		return a_suit < b_suit
	var a_rank: int = 99 if is_joker(a) else RANKS.find(card_rank(a))
	var b_rank: int = 99 if is_joker(b) else RANKS.find(card_rank(b))
	return a_rank < b_rank
