from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# State for an auto-fit common table + player pinch zoom / pan.
# Visual card design stays identical; only the table camera/layout changes.
# -----------------------------------------------------------------------------
needle = 'var _display_card_material: ShaderMaterial\n'
assert needle in text, 'v022 material marker not found'
text = text.replace(needle, needle + '''
var meld_content: Control
var table_base_scale: float = 1.0
var table_user_zoom: float = 1.0
var table_pan: Vector2 = Vector2.ZERO
var table_content_size: Vector2 = Vector2.ZERO
var table_layout_rects: Array[Rect2] = []
var table_state_signature: String = ""
var table_touches: Dictionary = {}
var table_touch_started_inside: Dictionary = {}
var table_last_pinch_distance: float = 0.0
const TABLE_MAX_RENDER_SCALE: float = 2.0
''', 1)

# Create a dedicated content node inside the clipped table viewport. All cards and
# meld hitboxes live here and can be scaled/translated together like a camera.
old = '''\tmeld_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
\tmeld_layer.clip_contents = true
\tadd_child(meld_layer)'''
new = '''\tmeld_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
\tmeld_layer.clip_contents = true
\tadd_child(meld_layer)

\tmeld_content = Control.new()
\tmeld_content.name = "MeldContent"
\tmeld_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
\tmeld_content.position = Vector2.ZERO
\tmeld_content.size = meld_layer.size
\tmeld_layer.add_child(meld_content)'''
assert old in text, 'meld layer v019 block not found'
text = text.replace(old, new, 1)

# -----------------------------------------------------------------------------
# New layout rules:
# - every meld owns a separate rectangle;
# - rows wrap horizontally, never overlap;
# - default camera auto-fits ALL rows/cards inside the visible table;
# - completed melds remain compact stacks, incomplete melds remain readable fans;
# - a structurally complete meld may contain a Joker and remains tappable so the
#   Joker can still be replaced later.
# -----------------------------------------------------------------------------
pattern = r'''func _refresh_melds\(\) -> void:\n.*?(?=func _make_card\()'''
replacement = '''func _refresh_melds() -> void:
	if not is_instance_valid(meld_content):
		return
	_clear_children(meld_content)
	table_layout_rects.clear()

	var signature: String = _table_signature()
	var table_changed: bool = signature != table_state_signature
	if table_changed:
		table_state_signature = signature
		table_user_zoom = 1.0
		table_pan = Vector2.ZERO
		table_last_pinch_distance = 0.0

	if game.table_melds.is_empty():
		table_content_size = Vector2.ZERO
		table_base_scale = 1.0
		meld_content.scale = Vector2.ONE
		meld_content.position = Vector2.ZERO
		return

	# Virtual card dimensions are the same as before v0.0.23. We lay everything
	# out at scale 1, then auto-fit the complete virtual board into meld_layer.
	var card_w: float = 148.0
	var card_h: float = 209.0
	var fan_step: float = 74.0
	var stack_step_x: float = 10.0
	var stack_step_y: float = 2.0
	var gap_x: float = 30.0
	var gap_y: float = 26.0
	var padding: float = 10.0
	var virtual_wrap_width: float = maxf(420.0, meld_layer.size.x - padding * 2.0)

	var specs: Array[Dictionary] = []
	for meld_index: int in range(game.table_melds.size()):
		var meld: Dictionary = game.table_melds[meld_index]
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var kind: String = String(meld.get("kind", ""))
		var complete: bool = _is_table_meld_complete(cards, kind)
		var step_x: float = stack_step_x if complete else fan_step
		var step_y: float = stack_step_y if complete else 0.0
		var width: float = card_w + step_x * float(maxi(0, cards.size() - 1))
		var height: float = card_h + step_y * float(maxi(0, cards.size() - 1))
		specs.append({
			"index": meld_index,
			"cards": cards,
			"complete": complete,
			"step_x": step_x,
			"step_y": step_y,
			"width": width,
			"height": height,
		})

	# Shelf layout. A row's height is the tallest meld in that row, therefore the
	# next row can never intersect it. A horizontal gap guarantees meld separation.
	var cursor_x: float = padding
	var cursor_y: float = padding
	var row_height: float = 0.0
	var max_right: float = padding
	var max_bottom: float = padding

	for spec: Dictionary in specs:
		var width: float = float(spec["width"])
		var height: float = float(spec["height"])
		if cursor_x > padding and cursor_x + width > padding + virtual_wrap_width:
			cursor_x = padding
			cursor_y += row_height + gap_y
			row_height = 0.0

		var rect := Rect2(Vector2(cursor_x, cursor_y), Vector2(width, height))
		table_layout_rects.append(rect)
		spec["rect"] = rect
		cursor_x += width + gap_x
		row_height = maxf(row_height, height)
		max_right = maxf(max_right, rect.end.x)
		max_bottom = maxf(max_bottom, rect.end.y)

	table_content_size = Vector2(max_right + padding, max_bottom + padding)
	var fit_w: float = meld_layer.size.x / maxf(1.0, table_content_size.x)
	var fit_h: float = meld_layer.size.y / maxf(1.0, table_content_size.y)
	table_base_scale = minf(1.0, minf(fit_w, fit_h))

	for spec: Dictionary in specs:
		var rect: Rect2 = spec["rect"]
		var cards: Array[CardInstance] = spec["cards"]
		var step_x: float = float(spec["step_x"])
		var step_y: float = float(spec["step_y"])
		for i: int in range(cards.size()):
			_make_card(
				cards[i].face_id(),
				rect.position + Vector2(float(i) * step_x, float(i) * step_y),
				Vector2(card_w, card_h),
				false,
				-2,
				meld_content,
				false,
				Color(0, 0, 0, 0)
			)

		var meld_index: int = int(spec["index"])
		var meld_touch: Button = Button.new()
		meld_touch.name = "MeldTouch_%d" % meld_index
		meld_touch.text = ""
		meld_touch.position = rect.position
		meld_touch.size = rect.size
		meld_touch.focus_mode = Control.FOCUS_NONE
		meld_touch.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		meld_touch.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 8))
		meld_touch.add_theme_stylebox_override("hover", _button_style(Color(0.12, 0.62, 0.36, 0.025), Color(0.40, 0.95, 0.62, 0.26), 2, 10))
		meld_touch.add_theme_stylebox_override("pressed", _button_style(Color(0.12, 0.62, 0.36, 0.06), Color(0.40, 0.95, 0.62, 0.48), 3, 10))
		meld_touch.pressed.connect(_on_meld_pressed.bind(meld_index))
		meld_content.add_child(meld_touch)

	_apply_table_camera()
	print("RAMI_TABLE_V023: autofit=true no_overlap=true content=", table_content_size, " base_scale=", table_base_scale, " user_zoom=", table_user_zoom)

func _is_table_meld_complete(cards: Array[CardInstance], kind: String) -> bool:
	# Structural completion is independent of Jokers. A full pile containing a
	# Joker stays compact but remains tappable so the natural replacement can recover it.
	if kind == "set":
		return cards.size() == 4
	if kind == "run":
		if cards.size() != 13:
			return false
		var info: Dictionary = game.validate_meld(cards)
		return bool(info.get("valid", false)) and String(info.get("kind", "")) == "run"
	return false

func _table_signature() -> String:
	var parts := PackedStringArray()
	for meld: Dictionary in game.table_melds:
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var ids := PackedStringArray()
		for card: CardInstance in cards:
			ids.append(str(card.uid))
		parts.append(String(meld.get("kind", "")) + ":" + ",".join(ids))
	return "|".join(parts)

func _apply_table_camera() -> void:
	if not is_instance_valid(meld_content):
		return
	if table_content_size == Vector2.ZERO:
		meld_content.scale = Vector2.ONE
		meld_content.position = Vector2.ZERO
		return

	var max_user_zoom: float = maxf(1.0, TABLE_MAX_RENDER_SCALE / maxf(0.01, table_base_scale))
	table_user_zoom = clampf(table_user_zoom, 1.0, max_user_zoom)
	var render_scale: float = table_base_scale * table_user_zoom
	var scaled_size: Vector2 = table_content_size * render_scale
	var centered: Vector2 = (meld_layer.size - scaled_size) * 0.5
	var max_pan := Vector2(
		maxf(0.0, (scaled_size.x - meld_layer.size.x) * 0.5),
		maxf(0.0, (scaled_size.y - meld_layer.size.y) * 0.5)
	)
	table_pan.x = clampf(table_pan.x, -max_pan.x, max_pan.x)
	table_pan.y = clampf(table_pan.y, -max_pan.y, max_pan.y)
	meld_content.scale = Vector2(render_scale, render_scale)
	meld_content.position = centered + table_pan

func _set_table_zoom_around(new_user_zoom: float, focus_in_layer: Vector2) -> void:
	if table_content_size == Vector2.ZERO:
		return
	var old_scale: float = table_base_scale * table_user_zoom
	if old_scale <= 0.0:
		return
	var content_point: Vector2 = (focus_in_layer - meld_content.position) / old_scale
	var max_user_zoom: float = maxf(1.0, TABLE_MAX_RENDER_SCALE / maxf(0.01, table_base_scale))
	table_user_zoom = clampf(new_user_zoom, 1.0, max_user_zoom)
	var new_scale: float = table_base_scale * table_user_zoom
	var scaled_size: Vector2 = table_content_size * new_scale
	var centered: Vector2 = (meld_layer.size - scaled_size) * 0.5
	var desired_position: Vector2 = focus_in_layer - content_point * new_scale
	table_pan = desired_position - centered
	_apply_table_camera()

func _table_local_from_viewport(viewport_position: Vector2) -> Vector2:
	var inv: Transform2D = get_global_transform_with_canvas().affine_inverse()
	return inv * viewport_position

func _point_in_table(local_surface: Vector2) -> bool:
	return Rect2(meld_layer.position, meld_layer.size).has_point(local_surface)

func _handle_table_gesture(event: InputEvent) -> bool:
	if event is InputEventScreenTouch:
		var touch := event as InputEventScreenTouch
		var local_surface: Vector2 = _table_local_from_viewport(touch.position)
		if touch.pressed:
			var inside: bool = _point_in_table(local_surface)
			table_touch_started_inside[touch.index] = inside
			if inside:
				table_touches[touch.index] = local_surface - meld_layer.position
		else:
			table_touches.erase(touch.index)
			table_touch_started_inside.erase(touch.index)
			if table_touches.size() < 2:
				table_last_pinch_distance = 0.0
		return false

	if event is InputEventScreenDrag:
		var drag := event as InputEventScreenDrag
		if not bool(table_touch_started_inside.get(drag.index, false)):
			return false
		var now_surface: Vector2 = _table_local_from_viewport(drag.position)
		var prev_surface: Vector2 = _table_local_from_viewport(drag.position - drag.relative)
		var now_in_layer: Vector2 = now_surface - meld_layer.position
		var delta_local: Vector2 = now_surface - prev_surface
		table_touches[drag.index] = now_in_layer

		if table_touches.size() >= 2:
			var keys: Array = table_touches.keys()
			var p1: Vector2 = table_touches[keys[0]]
			var p2: Vector2 = table_touches[keys[1]]
			var distance: float = p1.distance_to(p2)
			var center: Vector2 = (p1 + p2) * 0.5
			if table_last_pinch_distance > 0.0 and distance > 1.0:
				var ratio: float = distance / table_last_pinch_distance
				_set_table_zoom_around(table_user_zoom * ratio, center)
			table_last_pinch_distance = distance
			get_viewport().set_input_as_handled()
			return true

		if table_user_zoom > 1.001:
			table_pan += delta_local
			_apply_table_camera()
			get_viewport().set_input_as_handled()
			return true
	return false

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'v023 meld replacement failed: {n}'

# Root input already owns card dragging. Give table gestures first refusal, then keep
# the existing hand behaviour untouched.
old = '''func _input(event: InputEvent) -> void:
	if drag_index < 0:
		return'''
new = '''func _input(event: InputEvent) -> void:
	if _handle_table_gesture(event):
		return
	if drag_index < 0:
		return'''
assert old in text, '_input header not found'
text = text.replace(old, new, 1)

# Version marker.
text = text.replace('v0.0.22', 'v0.0.23')
marker = 'print("RAMI_V022: pooled_hand_nodes=true texture_cache=true shared_card_shader=true fast_meld_detector=true visual_layout_unchanged=true")'
if marker in text:
	text = text.replace(marker, marker + '\n\tprint("RAMI_V023: table_autofit=true pinch_zoom=true pan=true no_meld_overlap=true auto_reset_on_table_change=true")', 1)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V023: auto-fit rows + pinch zoom/pan + strict non-overlap common table')
