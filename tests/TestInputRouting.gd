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
	await process_frame

	var surface: Node = root_node.get_node("DesignSurface")
	_assert_true(surface != null, "DesignSurface must exist")

	var player_layer: Variant = surface.get("player_layer")
	var player_view: Variant = surface.get("player_view")
	var ai1_layer: Variant = surface.get("ai1_layer")
	var ai2_layer: Variant = surface.get("ai2_layer")
	_assert_true(player_layer is Control, "player_layer must exist")
	_assert_true(player_view is Control, "player_view must exist")
	_assert_true(ai1_layer is Control, "ai1_layer must exist")
	_assert_true(ai2_layer is Control, "ai2_layer must exist")
	_assert_true((player_layer as Control).mouse_filter == Control.MOUSE_FILTER_IGNORE, "player visual layer must not block stock/table touches")
	_assert_true((ai1_layer as Control).mouse_filter == Control.MOUSE_FILTER_IGNORE, "ai1 layer must not block header touches")
	_assert_true((ai2_layer as Control).mouse_filter == Control.MOUSE_FILTER_IGNORE, "ai2 layer must not block header touches")
	_assert_true((player_view as Control).clip_contents, "mobile hand viewport must clip overflow")

	var game: RamiGame = surface.get("game") as RamiGame
	_assert_true(game != null, "game engine must exist")
	_assert_true(game.phase == RamiGame.Phase.DRAW, "round must start in DRAW")
	_assert_true(game.player_hand.size() == 13, "player must start with 13 cards")
	_assert_true(game.stock.size() == 68, "stock must start with 68 cards")

	# Verify manual drag reorder keeps physical card identity and card count.
	var first_uid: int = game.player_hand[0].uid
	var second_uid: int = game.player_hand[1].uid
	surface.call("_move_hand_card_for_drag", 0, 2)
	_assert_true(game.player_hand.size() == 13, "manual reorder must keep 13 cards")
	_assert_true(game.player_hand[2].uid == first_uid, "drag reorder must move the exact CardInstance")
	_assert_true(game.player_hand[0].uid == second_uid, "drag reorder must shift neighboring cards")
	_assert_true(game.sort_mode == -1, "manual reorder must leave automatic sort mode")

	# Verify draw still works after mobile hand changes.
	surface.call("_on_draw_stock")
	await process_frame
	_assert_true(game.phase == RamiGame.Phase.ACTION, "stock press handler must enter ACTION")
	_assert_true(game.player_hand.size() == 14, "stock press handler must add one card")
	_assert_true(game.stock.size() == 67, "stock press handler must remove one stock card")
	_assert_true((surface.get("hand_content_width") as float) > 0.0, "mobile hand must calculate a content width")
	print("RAMI_INPUT_TEST: PASS stock_touch_route hand=", game.player_hand.size(), " stock=", game.stock.size(), " manual_reorder=true")
	quit(0)
