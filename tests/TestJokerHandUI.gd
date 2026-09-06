extends SceneTree

func _assert_true(condition: bool, message: String) -> void:
	if not condition:
		push_error("RAMI_V018_TEST: FAIL: %s" % message)
		quit(1)

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var scene: PackedScene = load("res://GameTable.tscn")
	_assert_true(scene != null, "GameTable must load")
	var root_node: Node = scene.instantiate()
	root.add_child(root_node)
	await process_frame
	await process_frame

	var surface: Node = root_node.get_node("DesignSurface")
	_assert_true(surface != null, "DesignSurface must exist")
	var game: RamiGame = surface.get("game") as RamiGame
	_assert_true(game != null, "game must exist")

	# Explicit hand: 5 clubs + Joker + 7 clubs should be detected as 5-6-7,
	# with Joker logically occupying the missing 6 clubs slot.
	game.player_hand.clear()
	game.player_hand.append(CardInstance.new(1001, 0, "clubs", "5", ""))
	game.player_hand.append(CardInstance.new(1002, 0, "", "", "black"))
	game.player_hand.append(CardInstance.new(1003, 0, "clubs", "7", ""))
	game.player_hand.append(CardInstance.new(1004, 0, "hearts", "K", ""))
	game.turn_index = 0
	game.phase = RamiGame.Phase.DRAW
	surface.call("_refresh_all")
	await process_frame

	var detected: Array = surface.get("detected_combos")
	var found_joker_run := false
	for item: Variant in detected:
		if item is Dictionary:
			var d := item as Dictionary
			var indices: Array = d.get("indices", [])
			if String(d.get("kind", "")) == "run" and indices.size() == 3 and int(indices[0]) == 0 and int(indices[1]) == 1 and int(indices[2]) == 2:
				found_joker_run = true
				break
	_assert_true(found_joker_run, "5 clubs + Joker + 7 clubs must be detected during DRAW")

	# Tapping a highlighted card during DRAW must visibly select the suggested combo.
	surface.call("_on_player_card_pressed", 0)
	await process_frame
	var selected: Array = surface.get("selected_indices")
	_assert_true(selected.size() == 3, "tapping a highlighted card during DRAW must select full combo")
	_assert_true(int(selected[0]) == 0 and int(selected[1]) == 1 and int(selected[2]) == 2, "selected combo indices must include Joker run")

	# A second tap on a card of the selected combo must allow individual selection.
	surface.call("_on_player_card_pressed", 1)
	await process_frame
	selected = surface.get("selected_indices")
	_assert_true(selected.size() == 1 and int(selected[0]) == 1, "second tap must allow selecting Joker individually")

	print("RAMI_V018_TEST: PASS card_touch=true joker_live_detect=true draw_phase=true")
	quit(0)
