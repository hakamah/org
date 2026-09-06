extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _assert_true(condition: bool, message: String) -> void:
	if not condition:
		push_error("RAMI_SMART_TABLE_TEST: FAIL: %s" % message)
		quit(1)

func _card(uid: int, suit: String, rank: String) -> CardInstance:
	return CardInstance.new(uid, 0, suit, rank, "")

func _run() -> void:
	var scene: PackedScene = load("res://GameTable.tscn")
	_assert_true(scene != null, "GameTable must load")
	var table: Node = scene.instantiate()
	root.add_child(table)
	await process_frame
	await process_frame
	var surface: Node = table.get_node("DesignSurface")
	_assert_true(surface != null, "DesignSurface must exist")

	var set3: Array[CardInstance] = [
		_card(1, "hearts", "7"), _card(2, "spades", "7"), _card(3, "diamonds", "7")
	]
	var set4: Array[CardInstance] = [
		_card(4, "hearts", "7"), _card(5, "spades", "7"), _card(6, "diamonds", "7"), _card(7, "clubs", "7")
	]
	_assert_true(not bool(surface.call("_is_table_meld_complete", set3, "set")), "3-card set must remain fanned")
	_assert_true(bool(surface.call("_is_table_meld_complete", set4, "set")), "4-card set must stack")

	var run12: Array[CardInstance] = []
	var run13: Array[CardInstance] = []
	var ranks: Array[String] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
	for i: int in range(ranks.size()):
		var c: CardInstance = _card(20 + i, "hearts", ranks[i])
		run13.append(c)
		if i < 12:
			run12.append(c)
	_assert_true(not bool(surface.call("_is_table_meld_complete", run12, "run")), "12-card run must remain fanned")
	_assert_true(bool(surface.call("_is_table_meld_complete", run13, "run")), "A-to-K 13-card run must stack")

	print("RAMI_SMART_TABLE_TEST: PASS set4_stack=true run13_stack=true incomplete_fan=true")
	quit(0)
