extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _assert_true(condition: bool, message: String) -> void:
	if not condition:
		push_error("RAMI_TABLE_EXT_TEST: FAIL: %s" % message)
		quit(1)

func _card(uid: int, suit: String, rank: String) -> CardInstance:
	return CardInstance.new(uid, 0, suit, rank, "")

func _joker(uid: int) -> CardInstance:
	return CardInstance.new(uid, 0, "", "", "black")

func _setup_action_game() -> RamiGame:
	var game := RamiGame.new()
	game.phase = RamiGame.Phase.ACTION
	game.turn_index = 0
	game.player_opened = true
	return game

func _run() -> void:
	# 1) A 9♣ extends 5♣-6♣-Joker-8♣. It must NOT incorrectly steal the Joker,
	# because that Joker logically represents 7♣.
	var g1 := _setup_action_game()
	var j1 := _joker(50)
	var base1: Array[CardInstance] = [_card(1,"clubs","5"), _card(2,"clubs","6"), j1, _card(3,"clubs","8")]
	var info1: Dictionary = g1.validate_meld(base1)
	_assert_true(bool(info1.get("valid", false)), "5♣ 6♣ Joker 8♣ must be a valid run")
	g1.table_melds = [{"owner": 2, "cards": g1._ordered_meld(base1, info1), "kind": "run"}]
	g1.player_hand = [_card(10,"clubs","9"), _card(11,"diamonds","K")]
	var add9: Dictionary = g1.play_player_on_meld([0], 0)
	_assert_true(bool(add9.get("ok", false)), "9♣ must extend the run")
	_assert_true(int(add9.get("recovered", 0)) == 0, "9♣ must not recover a Joker representing 7♣")
	_assert_true((g1.table_melds[0]["cards"] as Array).size() == 5, "extended run must contain 5 cards")

	# 2) 7♣ replaces the Joker in the same run and recovers that exact physical Joker.
	var g2 := _setup_action_game()
	var j2 := _joker(60)
	var base2: Array[CardInstance] = [_card(21,"clubs","5"), _card(22,"clubs","6"), j2, _card(23,"clubs","8")]
	var info2: Dictionary = g2.validate_meld(base2)
	g2.table_melds = [{"owner": 2, "cards": g2._ordered_meld(base2, info2), "kind": "run"}]
	g2.player_hand = [_card(24,"clubs","7"), _card(25,"diamonds","K")]
	var replace7: Dictionary = g2.play_player_on_meld([0], 0)
	_assert_true(bool(replace7.get("ok", false)), "7♣ must replace the Joker")
	_assert_true(int(replace7.get("recovered", 0)) == 1, "replacing 7♣ must recover one Joker")
	_assert_true(g2.must_replay_jokers.size() == 1 and g2.must_replay_jokers[0].uid == j2.uid, "recovered physical Joker must be marked for immediate replay")
	_assert_true(g2.player_hand.any(func(c: CardInstance) -> bool: return c.uid == j2.uid), "recovered Joker must return to player's hand")

	# 3) Several selected cards may extend a table run regardless of selection/hand order.
	var g3 := _setup_action_game()
	var base3: Array[CardInstance] = [_card(31,"hearts","5"), _card(32,"hearts","6"), _card(33,"hearts","7")]
	var info3: Dictionary = g3.validate_meld(base3)
	g3.table_melds = [{"owner": 1, "cards": g3._ordered_meld(base3, info3), "kind": "run"}]
	# Deliberately 9 before 8: old sequential-add algorithm failed on this valid final run.
	g3.player_hand = [_card(34,"hearts","9"), _card(35,"hearts","8"), _card(36,"spades","K")]
	var add_many: Dictionary = g3.play_player_on_meld([0, 1], 0)
	_assert_true(bool(add_many.get("ok", false)), "8♥ and 9♥ must extend 5♥-6♥-7♥ even when selected in reverse order")
	_assert_true((g3.table_melds[0]["cards"] as Array).size() == 5, "multi-extension must leave a 5-card run")

	print("RAMI_TABLE_EXT_TEST: PASS joker_replace=true extend_anywhere=true multi_add=true")
	quit(0)
