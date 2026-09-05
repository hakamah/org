extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _assert_true(condition: bool, message: String) -> void:
	if not condition:
		push_error("RAMI_TABLE_TEST: FAIL: %s" % message)
		quit(1)

func _card(uid: int, suit: String, rank: String) -> CardInstance:
	return CardInstance.new(uid, 0, suit, rank, "")

func _run() -> void:
	var scene: PackedScene = load("res://GameTable.tscn")
	_assert_true(scene != null, "GameTable scene must load")
	var root_node: Node = scene.instantiate()
	root.add_child(root_node)
	await process_frame
	await process_frame
	await process_frame

	var surface: Node = root_node.get_node("DesignSurface")
	_assert_true(surface != null, "DesignSurface must exist")
	var game: RamiGame = surface.get("game") as RamiGame
	var meld_layer: Control = surface.get("meld_layer") as Control
	_assert_true(game != null, "game must exist")
	_assert_true(meld_layer != null, "meld layer must exist")

	game.table_melds.clear()
	var uid: int = 5000
	for i: int in range(10):
		var cards: Array[CardInstance] = []
		var rank_value: int = (i % 9) + 2
		cards.append(_card(uid, "spades", str(rank_value))); uid += 1
		cards.append(_card(uid, "hearts", str(rank_value))); uid += 1
		cards.append(_card(uid, "diamonds", str(rank_value))); uid += 1
		game.table_melds.append({"owner": i % 3, "cards": cards, "kind": "set"})

	surface.call("_refresh_melds")
	await process_frame
	# Each meld produces one owner button and three card wrappers.
	_assert_true(meld_layer.get_child_count() >= 40, "all 10 melds must remain rendered")
	print("RAMI_TABLE_TEST: PASS melds=", game.table_melds.size(), " nodes=", meld_layer.get_child_count())
	quit(0)
