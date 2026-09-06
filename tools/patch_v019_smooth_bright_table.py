from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# 1) Bigger common table, using almost all space to the left of draw/discard UI.
#    The meld layer is clipped as a final safety net: no card may visually escape.
# -----------------------------------------------------------------------------
text = text.replace(
    '_panel(Vector2(85, 76), Vector2(1120, 530), Color(0.04, 0.27, 0.18, 0.24), Color(0.20, 0.65, 0.43, 0.42), 30, 3)',
    '_panel(Vector2(28, 70), Vector2(1170, 535), Color(0.04, 0.27, 0.18, 0.24), Color(0.20, 0.65, 0.43, 0.42), 30, 3)'
)
text = text.replace('table_button.position = Vector2(85, 76)', 'table_button.position = Vector2(28, 70)')
text = text.replace('table_button.size = Vector2(1120, 530)', 'table_button.size = Vector2(1170, 535)')
text = text.replace('meld_layer.position = Vector2(105, 154)', 'meld_layer.position = Vector2(44, 82)')
text = text.replace('meld_layer.size = Vector2(1080, 424)', 'meld_layer.size = Vector2(1138, 492)')
text = text.replace('status_label = _make_label("", Vector2(105, 582), Vector2(1080, 30)', 'status_label = _make_label("", Vector2(44, 578), Vector2(1138, 28)')
text = text.replace(
    '\tmeld_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE\n\tadd_child(meld_layer)',
    '\tmeld_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE\n\tmeld_layer.clip_contents = true\n\tadd_child(meld_layer)',
    1
)

# -----------------------------------------------------------------------------
# 2) Display-only cards are real TextureRects, never disabled TextureButtons.
#    This removes the Android/Godot disabled-state grey tint from table/discard.
# -----------------------------------------------------------------------------
pattern = r'''func _make_card\(card_id: String, pos: Vector2, card_size: Vector2, clickable: bool, index: int, parent: Control, selected: bool, accent: Color\) -> Control:\n.*?(?=func _card_style\()'''
replacement = '''func _make_card(card_id: String, pos: Vector2, card_size: Vector2, clickable: bool, index: int, parent: Control, selected: bool, accent: Color) -> Control:
	var wrapper: Control = Control.new()
	wrapper.position = pos
	wrapper.size = card_size
	wrapper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	wrapper.modulate = Color.WHITE
	wrapper.self_modulate = Color.WHITE
	parent.add_child(wrapper)

	var frame: Panel = Panel.new()
	frame.size = card_size
	frame.add_theme_stylebox_override("panel", _card_style(selected, accent))
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.modulate = Color.WHITE
	wrapper.add_child(frame)

	var texture: Texture2D = _load_card_texture(card_id)
	if clickable:
		var button: TextureButton = TextureButton.new()
		button.position = Vector2(4, 4)
		button.size = card_size - Vector2(8, 8)
		button.ignore_texture_size = true
		button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
		button.texture_normal = texture
		button.texture_disabled = texture
		button.disabled = false
		button.focus_mode = Control.FOCUS_NONE
		button.mouse_filter = Control.MOUSE_FILTER_STOP
		button.modulate = Color.WHITE
		button.self_modulate = Color.WHITE
		wrapper.add_child(button)
		if index >= 0:
			button.gui_input.connect(_on_player_card_gui_input.bind(index))
		elif index == -1:
			button.pressed.connect(_on_draw_discard)
	else:
		# Pure visual image: it has no disabled state, so it stays as bright as cards
		# in the player's hand on Android/Samsung.
		var image: TextureRect = TextureRect.new()
		image.position = Vector2(4, 4)
		image.size = card_size - Vector2(8, 8)
		image.texture = texture
		image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		image.mouse_filter = Control.MOUSE_FILTER_IGNORE
		image.modulate = Color.WHITE
		image.self_modulate = Color.WHITE
		wrapper.add_child(image)
	return wrapper

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_make_card replacement failed: {n}'

# -----------------------------------------------------------------------------
# 3) Smooth drag. The expensive 2^N meld detector is NOT executed while the
#    finger is moving. We update card order/visuals only when crossing a slot.
#    Full Joker/meld detection runs immediately on release through _refresh_all().
# -----------------------------------------------------------------------------
old = '''\tif target != drag_index:\n\t\t_move_hand_card_for_drag(drag_index, target)\n\t\tdrag_index = target\n\t\t_recompute_detected_combos()\n\t\t_refresh_player()\n\t\t_refresh_hand_combo_bands()\n\t\t_refresh_combo_chips()'''
new = '''\tif target != drag_index:\n\t\t_move_hand_card_for_drag(drag_index, target)\n\t\tdrag_index = target\n\t\t# Fast path while dragging: never enumerate all possible meld subsets here.\n\t\t_refresh_player()'''
assert old in text, 'v018 drag detection block not found'
text = text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# 4) Adaptive table layout. Cards start larger than v0.0.18. If the table gets
#    crowded, scale is reduced progressively until every meld fits inside the
#    available rectangle. Complete melds stay stacked; incomplete melds stay fans.
# -----------------------------------------------------------------------------
pattern = r'''func _refresh_melds\(\) -> void:\n.*?(?=func _is_table_meld_complete\()'''
replacement = '''func _refresh_melds() -> void:
	_clear_children(meld_layer)
	if game.table_melds.is_empty():
		return

	var usable_width: float = maxf(420.0, meld_layer.size.x - 16.0)
	var usable_height: float = maxf(300.0, meld_layer.size.y - 12.0)
	var candidate_scales: Array[float] = [1.0, 0.92, 0.84, 0.76, 0.68, 0.60, 0.52, 0.46]
	var chosen_scale: float = candidate_scales.back()

	# Pick the largest scale whose automatically wrapped rows fit vertically.
	for scale: float in candidate_scales:
		var card_w_test: float = 148.0 * scale
		var card_h_test: float = 209.0 * scale
		var fan_step_test: float = 74.0 * scale
		var stack_step_test: float = 10.0 * scale
		var stack_y_test: float = 2.0 * scale
		var gap_test: float = 26.0 * scale
		var row_h_test: float = card_h_test + 34.0 * scale
		var sx: float = 8.0
		var rows: int = 1

		for meld: Dictionary in game.table_melds:
			var cards_test: Array[CardInstance] = _dict_card_array(meld, "cards")
			var kind_test: String = String(meld.get("kind", ""))
			var complete_test: bool = _is_table_meld_complete(cards_test, kind_test)
			var step_test: float = stack_step_test if complete_test else fan_step_test
			if not complete_test and cards_test.size() > 1:
				# A single long run is always fitted to one row rather than overflowing.
				step_test = minf(step_test, maxf(22.0 * scale, (usable_width - card_w_test) / float(cards_test.size() - 1)))
			var width_test: float = step_test * float(maxi(0, cards_test.size() - 1)) + card_w_test
			if sx > 8.0 and sx + width_test > usable_width:
				rows += 1
				sx = 8.0
			sx += width_test + gap_test

		var total_h: float = 8.0 + float(rows) * row_h_test
		if total_h <= usable_height:
			chosen_scale = scale
			break

	var card_w: float = 148.0 * chosen_scale
	var card_h: float = 209.0 * chosen_scale
	var fan_step: float = 74.0 * chosen_scale
	var stack_step_x: float = 10.0 * chosen_scale
	var stack_step_y: float = 2.0 * chosen_scale
	var gap: float = 26.0 * chosen_scale
	var row_height: float = card_h + 34.0 * chosen_scale
	var x: float = 8.0
	var y: float = 8.0

	for meld_index: int in range(game.table_melds.size()):
		var meld: Dictionary = game.table_melds[meld_index]
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var kind: String = String(meld.get("kind", ""))
		var complete: bool = _is_table_meld_complete(cards, kind)

		var step_x: float = stack_step_x if complete else fan_step
		var step_y: float = stack_step_y if complete else 0.0
		if not complete and cards.size() > 1:
			step_x = minf(step_x, maxf(22.0 * chosen_scale, (usable_width - card_w) / float(cards.size() - 1)))
		var meld_width: float = step_x * float(maxi(0, cards.size() - 1)) + card_w
		var meld_height: float = card_h + step_y * float(maxi(0, cards.size() - 1))

		if x > 8.0 and x + meld_width > usable_width:
			x = 8.0
			y += row_height

		# The scale selection above should keep this inside. Clamp as a final guard.
		if y + meld_height > usable_height:
			y = maxf(0.0, usable_height - meld_height)

		for i: int in range(cards.size()):
			_make_card(
				cards[i].face_id(),
				Vector2(x + float(i) * step_x, y + float(i) * step_y),
				Vector2(card_w, card_h),
				false,
				-2,
				meld_layer,
				false,
				Color(0, 0, 0, 0)
			)

		var meld_touch: Button = Button.new()
		meld_touch.name = "MeldTouch_%d" % meld_index
		meld_touch.text = ""
		meld_touch.position = Vector2(x, y)
		meld_touch.size = Vector2(maxf(card_w, meld_width), maxf(card_h, meld_height))
		meld_touch.focus_mode = Control.FOCUS_NONE
		meld_touch.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		meld_touch.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 8))
		meld_touch.add_theme_stylebox_override("hover", _button_style(Color(0.12, 0.62, 0.36, 0.025), Color(0.40, 0.95, 0.62, 0.26), 2, 10))
		meld_touch.add_theme_stylebox_override("pressed", _button_style(Color(0.12, 0.62, 0.36, 0.06), Color(0.40, 0.95, 0.62, 0.48), 3, 10))
		meld_touch.pressed.connect(_on_meld_pressed.bind(meld_index))
		meld_layer.add_child(meld_touch)

		x += meld_width + gap

	print("RAMI_TABLE_V019: adaptive_fit=true melds=", game.table_melds.size(), " scale=", chosen_scale, " card=", Vector2(card_w, card_h))

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_refresh_melds adaptive replacement failed: {n}'

text = text.replace('v0.0.18', 'v0.0.19')
ready_marker = 'print("RAMI_V018: card_touch=true live_joker_detection=true detect_during_draw=true")'
if ready_marker in text:
    text = text.replace(
        ready_marker,
        ready_marker + '\n\tprint("RAMI_V019: bright_display_cards=true drag_fast_path=true adaptive_table_fit=true larger_table=true")',
        1
    )

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V019: bright display cards + smooth drag + adaptive larger table')
