extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _assert_true(condition: bool, message: String) -> void:
	if not condition:
		push_error("RAMI_DISCARD_TEST: FAIL: %s" % message)
		quit(1)

func _run() -> void:
	var scene: PackedScene = load("res://GameTable.tscn")
	_assert_true(scene != null, "GameTable must load")
	var root_node: Node = scene.instantiate()
	root.add_child(root_node)
	await process_frame
	await process_frame
	await process_frame

	var surface: Node = root_node.get_node("DesignSurface")
	_assert_true(surface != null, "DesignSurface must exist")
	var game: RamiGame = surface.get("game") as RamiGame
	_assert_true(game != null, "game must exist")

	# Simulate the exact failure reported by the user: take the last discard,
	# leaving the pile empty, then select one card and tap the empty discard zone.
	game.discard_pile.clear()
	game.phase = RamiGame.Phase.ACTION
	game.turn_index = 0
	var before_count: int = game.player_hand.size()
	_assert_true(before_count > 1, "player needs cards")

	var selected: Array[int] = [0]
	surface.set("selected_indices", selected)
	surface.call("_refresh_all")
	await process_frame

	var discard_layer: Control = surface.get("discard_layer") as Control
	_assert_true(discard_layer != null, "discard layer must exist")
	var touch: Node = discard_layer.get_node_or_null("DiscardTouchArea")
	_assert_true(touch is Button, "empty discard must still expose DiscardTouchArea")
	_assert_true(not (touch as Button).disabled, "discard touch area must be enabled in ACTION")

	surface.call("_on_discard_zone_pressed")
	await process_frame
	_assert_true(game.player_hand.size() == before_count - 1, "selected card must be removed from hand")
	_assert_true(game.discard_pile.size() >= 1, "discarded card must be placed into discard pile")
	print("RAMI_DISCARD_TEST: PASS empty_discard_touch=true hand_after=", game.player_hand.size(), " discard=", game.discard_pile.size())
	quit(0)
