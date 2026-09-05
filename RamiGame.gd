class_name RamiGame
extends RefCounted

const SUITS: Array[String] = ["spades", "hearts", "diamonds", "clubs"]
const RANKS: Array[String] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

var stock: Array[String] = []
var discard_pile: Array[String] = []
var player_hand: Array[String] = []
var ai_hand: Array[String] = []
var table_melds: Array = []

var phase: String = "draw"
var player_opened := false
var ai_opened := false
var winner := ""
var last_message := "Piochez une carte."

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
	for _copy in range(2):
		for suit in SUITS:
			for rank in RANKS:
				deck.append("%s_%s" % [suit, rank])
		deck.append("joker_black")
		deck.append("joker_red")
	deck.shuffle()

	for _i in range(14):
		player_hand.append(deck.pop_back())
		ai_hand.append(deck.pop_back())
	discard_pile.append(deck.pop_back())
	stock = deck

func can_draw() -> bool:
	return winner == "" and phase == "draw"

func can_play() -> bool:
	return winner == "" and phase == "discard"

func draw_stock() -> bool:
	if not can_draw():
		return false
	_recycle_stock_if_needed()
	if stock.is_empty():
		last_message = "La pioche est vide."
		return false
	player_hand.append(stock.pop_back())
	phase = "discard"
	last_message = "Sélectionnez des cartes à poser ou une carte à défausser."
	return true

func draw_discard() -> bool:
	if not can_draw() or discard_pile.is_empty():
		return false
	player_hand.append(discard_pile.pop_back())
	phase = "discard"
	last_message = "Carte prise dans la défausse."
	return true

func play_player_selection(indices: Array[int]) -> Dictionary:
	if not can_play():
		return {"ok": false, "message": "Vous devez d'abord piocher."}
	if indices.size() < 3:
		return {"ok": false, "message": "Sélectionnez au moins 3 cartes."}

	var unique: Array[int] = []
	for idx in indices:
		if idx >= 0 and idx < player_hand.size() and not unique.has(idx):
			unique.append(idx)
	if unique.size() != indices.size():
		return {"ok": false, "message": "Sélection invalide."}

	var selected_cards: Array[String] = []
	for idx in unique:
		selected_cards.append(player_hand[idx])

	if not player_opened:
		var partition: Array = _find_opening_partition(selected_cards)
		if partition.is_empty():
			return {"ok": false, "message": "Première pose : 51 points minimum + une tierce franche sans Joker."}
		_remove_indices(player_hand, unique)
		for meld in partition:
			table_melds.append({"owner": "player", "cards": meld.duplicate()})
		player_opened = true
		last_message = "Ouverture validée ! Vous pouvez maintenant poser librement."
	else:
		var info := validate_meld(selected_cards)
		if not info.valid:
			return {"ok": false, "message": "Ces cartes ne forment pas une combinaison valide."}
		_remove_indices(player_hand, unique)
		table_melds.append({"owner": "player", "cards": _ordered_meld(selected_cards, info)})
		last_message = "Combinaison posée."

	if player_hand.is_empty():
		winner = "player"
		phase = "game_over"
		last_message = "Victoire ! Vous n'avez plus de cartes."
	return {"ok": true, "message": last_message}

func discard_player(index: int) -> bool:
	if not can_play() or index < 0 or index >= player_hand.size():
		return false
	discard_pile.append(player_hand.pop_at(index))
	if player_hand.is_empty():
		winner = "player"
		phase = "game_over"
		last_message = "Victoire !"
		return true
	phase = "ai"
	last_message = "L'IA joue..."
	_run_ai_turn()
	if winner == "":
		phase = "draw"
		last_message = "À vous : piochez une carte."
	return true

func sort_player_hand() -> void:
	player_hand.sort_custom(_card_less)

func top_discard() -> String:
	return "" if discard_pile.is_empty() else discard_pile.back()

func validate_meld(cards: Array[String]) -> Dictionary:
	if cards.size() < 3:
		return {"valid": false, "kind": "", "points": 0, "pure_run": false}

	var joker_count := 0
	var natural: Array[String] = []
	for c in cards:
		if is_joker(c):
			joker_count += 1
		else:
			natural.append(c)

	var set_info := _validate_set(natural, joker_count, cards.size())
	if set_info.valid:
		return set_info
	var run_info := _validate_run(natural, joker_count, cards.size())
	if run_info.valid:
		return run_info
	return {"valid": false, "kind": "", "points": 0, "pure_run": false}

func _validate_set(natural: Array[String], jokers: int, total: int) -> Dictionary:
	if total < 3 or total > 4 or natural.is_empty():
		return {"valid": false}
	var rank := card_rank(natural[0])
	var suits: Array[String] = []
	for c in natural:
		if card_rank(c) != rank:
			return {"valid": false}
		var s := card_suit(c)
		if suits.has(s):
			return {"valid": false}
		suits.append(s)
	return {"valid": true, "kind": "set", "points": meld_points(natural) + jokers * rank_points(rank), "pure_run": false, "high_ace": false}

func _validate_run(natural: Array[String], jokers: int, total: int) -> Dictionary:
	if total < 3 or natural.is_empty():
		return {"valid": false}
	var suit := card_suit(natural[0])
	var vals: Array[int] = []
	for c in natural:
		if card_suit(c) != suit:
			return {"valid": false}
		var v := rank_value(card_rank(c))
		if vals.has(v):
			return {"valid": false}
		vals.append(v)
	vals.sort()

	var best := _run_fit(vals, jokers, total, false)
	if vals.has(1):
		var high_vals: Array[int] = []
		for v in vals:
			high_vals.append(14 if v == 1 else v)
		high_vals.sort()
		var high := _run_fit(high_vals, jokers, total, true)
		if high.valid and (not best.valid or int(high.points) > int(best.points)):
			best = high
	if best.valid:
		best.kind = "run"
		best.pure_run = jokers == 0 and total >= 3
	return best

func _run_fit(vals: Array[int], jokers: int, total: int, high_ace: bool) -> Dictionary:
	var min_start := 1
	var max_end := 14 if high_ace else 13
	for start in range(min_start, max_end - total + 2):
		var finish := start + total - 1
		var missing := 0
		var points := 0
		var all_inside := true
		for v in vals:
			if v < start or v > finish:
				all_inside = false
				break
		if not all_inside:
			continue
		for target in range(start, finish + 1):
			if vals.has(target):
				points += 11 if target == 14 else min(target, 10)
			else:
				missing += 1
				points += 11 if target == 14 else min(target, 10)
		if missing == jokers:
			return {"valid": true, "points": points, "high_ace": high_ace, "start": start}
	return {"valid": false}

func _find_opening_partition(cards: Array[String], require_all: bool = true) -> Array:
	var n := cards.size()
	if n < 3:
		return []
	var melds: Array = []
	var max_mask := 1 << n
	for mask in range(1, max_mask):
		var count := _bit_count(mask)
		if count < 3:
			continue
		var subset: Array[String] = []
		for i in range(n):
			if mask & (1 << i):
				subset.append(cards[i])
		var info := validate_meld(subset)
		if info.valid:
			melds.append({"mask": mask, "cards": _ordered_meld(subset, info), "points": int(info.points), "pure": bool(info.pure_run)})

	melds.sort_custom(func(a, b): return int(a.points) > int(b.points))
	var raw := _opening_dfs(melds, 0, 0, 0, false, [], (1 << n) - 1, require_all)
	var result: Array = []
	for x in raw:
		result.append(x.cards.duplicate())
	return result

func _opening_dfs(melds: Array, pos: int, used_mask: int, points: int, has_pure: bool, chosen: Array, target_mask: int, require_all: bool) -> Array:
	if points >= 51 and has_pure and (not require_all or used_mask == target_mask):
		return chosen.duplicate(true)
	if pos >= melds.size():
		return []
	for i in range(pos, melds.size()):
		var m = melds[i]
		if (int(m.mask) & used_mask) != 0:
			continue
		chosen.append(m)
		var found := _opening_dfs(melds, i + 1, used_mask | int(m.mask), points + int(m.points), has_pure or bool(m.pure), chosen, target_mask, require_all)
		if not found.is_empty():
			return found
		chosen.pop_back()
	return []

func _run_ai_turn() -> void:
	_recycle_stock_if_needed()
	if not stock.is_empty():
		ai_hand.append(stock.pop_back())

	if not ai_opened:
		var opening := _find_opening_partition(ai_hand, false)
		if not opening.is_empty():
			for meld in opening:
				_remove_cards_once(ai_hand, meld)
				table_melds.append({"owner": "ai", "cards": meld.duplicate()})
			ai_opened = true
	else:
		var keep_playing := true
		while keep_playing:
			keep_playing = false
			var best := _best_single_meld(ai_hand)
			if not best.is_empty():
				_remove_cards_once(ai_hand, best)
				table_melds.append({"owner": "ai", "cards": best.duplicate()})
				keep_playing = true

	if ai_hand.is_empty():
		winner = "ai"
		phase = "game_over"
		last_message = "L'IA gagne la manche."
		return

	var discard_index := _ai_discard_index()
	discard_pile.append(ai_hand.pop_at(discard_index))
	if ai_hand.is_empty():
		winner = "ai"
		phase = "game_over"
		last_message = "L'IA gagne la manche."

func _best_single_meld(hand: Array[String]) -> Array[String]:
	var n := hand.size()
	var best_cards: Array[String] = []
	var best_score := -1
	for mask in range(1, 1 << n):
		var count := _bit_count(mask)
		if count < 3 or count > 7:
			continue
		var subset: Array[String] = []
		for i in range(n):
			if mask & (1 << i):
				subset.append(hand[i])
		var info := validate_meld(subset)
		if info.valid:
			var score := count * 100 + int(info.points)
			if score > best_score:
				best_score = score
				best_cards = _ordered_meld(subset, info)
	return best_cards

func _ai_discard_index() -> int:
	var best_index := 0
	var best_value := -1
	for i in range(ai_hand.size()):
		var c := ai_hand[i]
		var value := 20 if is_joker(c) else rank_points(card_rank(c))
		if value > best_value:
			best_value = value
			best_index = i
	return best_index

func _ordered_meld(cards: Array[String], info: Dictionary) -> Array[String]:
	var out := cards.duplicate()
	if info.kind == "set":
		out.sort_custom(_card_less)
		return out
	var naturals: Array[String] = []
	var jokers: Array[String] = []
	for c in out:
		if is_joker(c):
			jokers.append(c)
		else:
			naturals.append(c)
	naturals.sort_custom(func(a, b):
		var av := rank_value(card_rank(a))
		var bv := rank_value(card_rank(b))
		if bool(info.get("high_ace", false)):
			av = 14 if av == 1 else av
			bv = 14 if bv == 1 else bv
		return av < bv
	)
	naturals.append_array(jokers)
	return naturals

func meld_points(cards: Array[String]) -> int:
	var total := 0
	for c in cards:
		if is_joker(c):
			total += 20
		else:
			total += rank_points(card_rank(c))
	return total

func rank_points(rank: String) -> int:
	if rank == "A":
		return 11
	if rank in ["J", "Q", "K"]:
		return 10
	return int(rank)

func rank_value(rank: String) -> int:
	return RANKS.find(rank) + 1

func is_joker(card_id: String) -> bool:
	return card_id.begins_with("joker")

func card_suit(card_id: String) -> String:
	if is_joker(card_id):
		return "joker"
	var split_at := card_id.rfind("_")
	return card_id.substr(0, split_at)

func card_rank(card_id: String) -> String:
	if is_joker(card_id):
		return "JOKER"
	var split_at := card_id.rfind("_")
	return card_id.substr(split_at + 1)

func _remove_indices(hand: Array[String], indices: Array[int]) -> void:
	var sorted := indices.duplicate()
	sorted.sort()
	sorted.reverse()
	for idx in sorted:
		hand.remove_at(idx)

func _remove_cards_once(hand: Array[String], cards: Array[String]) -> void:
	for c in cards:
		var idx := hand.find(c)
		if idx >= 0:
			hand.remove_at(idx)

func _recycle_stock_if_needed() -> void:
	if not stock.is_empty() or discard_pile.size() <= 1:
		return
	var top := discard_pile.pop_back()
	stock = discard_pile.duplicate()
	stock.shuffle()
	discard_pile.clear()
	discard_pile.append(top)

func _bit_count(mask: int) -> int:
	var x := mask
	var count := 0
	while x != 0:
		count += x & 1
		x >>= 1
	return count

func _card_less(a: String, b: String) -> bool:
	var ka: Array = _sort_key(a)
	var kb: Array = _sort_key(b)
	if ka[0] == kb[0]:
		return int(ka[1]) < int(kb[1])
	return int(ka[0]) < int(kb[0])

func _sort_key(card_id: String) -> Array:
	if is_joker(card_id):
		return [99, 99]
	return [SUITS.find(card_suit(card_id)), RANKS.find(card_rank(card_id))]
