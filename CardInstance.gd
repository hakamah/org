class_name CardInstance
extends RefCounted

var uid: int
var deck_index: int
var suit: String
var rank: String
var joker_color: String

func _init(p_uid: int = 0, p_deck_index: int = 0, p_suit: String = "", p_rank: String = "", p_joker_color: String = "") -> void:
	uid = p_uid
	deck_index = p_deck_index
	suit = p_suit
	rank = p_rank
	joker_color = p_joker_color

func is_joker() -> bool:
	return joker_color != ""

func face_id() -> String:
	if is_joker():
		return "joker_%s" % joker_color
	return "%s_%s" % [suit, rank]

func debug_name() -> String:
	return "%s#%03d" % [face_id(), uid]
