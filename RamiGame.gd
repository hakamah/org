class_name RamiGame
extends RefCounted

const SUITS: Array[String] = ["spades", "hearts", "diamonds", "clubs"]
const RANKS: Array[String] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

var stock: Array[String] = []
var discard_pile: Array[String] = []
var player_hand: Array[String] = []
var ai_hand: Array[String] = []
var phase: String = "draw"

func new_round() -> void:
	stock.clear()
	discard_pile.clear()
	player_hand.clear()
	ai_hand.clear()
	phase = "draw"

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
	return phase == "draw"

func can_discard() -> bool:
	return phase == "discard"

func draw_stock() -> bool:
	if not can_draw() or stock.is_empty():
		return false
	player_hand.append(stock.pop_back())
	phase = "discard"
	return true

func draw_discard() -> bool:
	if not can_draw() or discard_pile.is_empty():
		return false
	player_hand.append(discard_pile.pop_back())
	phase = "discard"
	return true

func discard_player(index: int) -> bool:
	if not can_discard() or index < 0 or index >= player_hand.size():
		return false
	discard_pile.append(player_hand.pop_at(index))
	_run_ai_stub()
	phase = "draw"
	return true

func sort_player_hand() -> void:
	player_hand.sort_custom(_card_less)

func top_discard() -> String:
	if discard_pile.is_empty():
		return ""
	return discard_pile.back()

func _run_ai_stub() -> void:
	# IA minimale de transition : elle pioche puis défausse une carte.
	# Le vrai moteur de décision Rami arrivera après le validateur de combinaisons.
	if not stock.is_empty():
		ai_hand.append(stock.pop_back())
	if ai_hand.is_empty():
		return
	var index: int = randi_range(0, ai_hand.size() - 1)
	discard_pile.append(ai_hand.pop_at(index))

func _card_less(a: String, b: String) -> bool:
	var ka: Array = _sort_key(a)
	var kb: Array = _sort_key(b)
	if ka[0] == kb[0]:
		return int(ka[1]) < int(kb[1])
	return int(ka[0]) < int(kb[0])

func _sort_key(card_id: String) -> Array:
	if card_id.begins_with("joker"):
		return [99, 99]
	var split_at: int = card_id.rfind("_")
	var suit: String = card_id.substr(0, split_at)
	var rank: String = card_id.substr(split_at + 1)
	return [SUITS.find(suit), RANKS.find(rank)]
