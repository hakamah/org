extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _assert_true(condition: bool, message: String) -> void:
	if not condition:
		push_error("RAMI_INPUT_TEST: FAIL: %s" % message)
		quit(1)

func _run() -> void:
	var scene: PackedScene = load("res://GameTable.tscn")
	_assert_true(scene != null, "GameTable scene must load")
	var root_node: Node = scene.instantiate()
	root.add_child(root_node)
	await process_frame
	await process_frame

	var surface: Node = root_node.get_node("DesignSurface")
	_assert_true(surface != null, "DesignSurface must exist")
	_assert_true(surface.player_layer.mouse_filter == Control.MOUSE_FILTER_IGNORE, "player_layer must not block stock/table touches")
	_assert_true(surface.ai1_layer.mouse_filter == Control.MOUSE_FILTER_IGNORE, "ai1_layer must not block header touches")
	_assert_true(surface.ai2_layer.mouse_filter == Control.MOUSE_FILTER_IGNORE, "ai2_layer must not block header touches")
	_assert_true(surface.stock_button != null, "stock button must exist")
	_assert_true(not surface.stock_button.disabled, "stock button must be enabled at turn start")
	_assert_true(surface.game.phase == RamiGame.Phase.DRAW, "round must start in DRAW")
	_assert_true(surface.game.player_hand.size() == 13, "player must start with 13 cards")

	surface.stock_button.emit_signal("pressed")
	await process_frame
	_assert_true(surface.game.phase == RamiGame.Phase.ACTION, "pressing stock must enter ACTION")
	_assert_true(surface.game.player_hand.size() == 14, "pressing stock must add exactly one card")
	print("RAMI_INPUT_TEST: PASS stock_press hand=", surface.game.player_hand.size(), " phase=", surface.game.phase)
	quit(0)
