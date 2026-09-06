from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# v0.0.25 TABLE BEHAVIOUR
# 1) Prefer using all horizontal space and keep the table on <= 2 rows whenever
#    a readable two-row plan is possible. A third row is only introduced when
#    two rows would shrink the table too far.
# 2) A truly complete meld (full structural capacity, NO Joker) is stacked.
#    Tapping that stack with no hand selection expands it for inspection; tapping
#    again folds it back. Joker-containing full melds stay open/readable because
#    the Joker can still be replaced by its natural card.
# No card art, card dimensions, colours or general screen geometry are changed.
# -----------------------------------------------------------------------------
needle = 'const TABLE_MAX_RENDER_SCALE: float = 2.0\n'
assert needle in text, 'v023 table scale marker not found'
text = text.replace(needle, needle + 'const TABLE_TWO_ROW_MIN_SCALE: float = 0.72\n', 1)

pattern = r'''func _refresh_melds\(\) -> void:\n.*?(?=func _table_signature\(\) -> String:)'''
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
		# A changed table may invalidate the previously expanded stack.
		expanded_meld_index = -1

	if game.table_melds.is_empty():
		table_content_size = Vector2.ZERO
		table_base_scale = 1.0
		meld_content.scale = Vector2.ONE
		meld_content.position = Vector2.ZERO
		return

	# Keep the exact v0.0.23/v0.0.24 virtual card geometry.
	var card_w: float = 148.0
	var card_h: float = 209.0
	var fan_step: float = 74.0
	var stack_step_x: float = 10.0
	var stack_step_y: float = 2.0
	var gap_x: float = 30.0
	var gap_y: float = 26.0
	var padding: float = 10.0

	var specs: Array[Dictionary] = []
	for meld_index: int in range(game.table_melds.size()):
		var meld: Dictionary = game.table_melds[meld_index]
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var kind: String = String(meld.get("kind", ""))
		var complete: bool = _is_table_meld_complete(cards, kind)
		var expanded: bool = complete and expanded_meld_index == meld_index
		var compact: bool = complete and not expanded
		var step_x: float = stack_step_x if compact else fan_step
		var step_y: float = stack_step_y if compact else 0.0
		var width: float = card_w + step_x * float(maxi(0, cards.size() - 1))
		var height: float = card_h + step_y * float(maxi(0, cards.size() - 1))
		specs.append({
			"index": meld_index,
			"cards": cards,
			"complete": complete,
			"expanded": expanded,
			"step_x": step_x,
			"step_y": step_y,
			"width": width,
			"height": height,
		})

	# Choose the number of rows BEFORE positioning. This avoids the old shelf-layout
	# problem where a third row could be created even though redistributing the melds
	# horizontally would comfortably fit them on two rows.
	var plan: Dictionary = _choose_table_layout_plan(specs, gap_x, gap_y, padding)
	var rows: Array = plan.get("rows", [])
	var content_width: float = float(plan.get("width", 1.0))
	var content_height: float = float(plan.get("height", 1.0))

	table_layout_rects.resize(specs.size())
	var cursor_y: float = padding
	for row_value: Variant in rows:
		var row: Array = row_value as Array
		var cursor_x: float = padding
		var row_height: float = 0.0
		for spec_index_value: Variant in row:
			var spec_index: int = int(spec_index_value)
			var spec: Dictionary = specs[spec_index]
			var width: float = float(spec["width"])
			var height: float = float(spec["height"])
			var rect := Rect2(Vector2(cursor_x, cursor_y), Vector2(width, height))
			table_layout_rects[spec_index] = rect
			spec["rect"] = rect
			specs[spec_index] = spec
			cursor_x += width + gap_x
			row_height = maxf(row_height, height)
		cursor_y += row_height + gap_y

	table_content_size = Vector2(content_width, content_height)
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
	print("RAMI_TABLE_V025: rows=", int(plan.get("row_count", rows.size())), " autofit=true horizontal_first=true content=", table_content_size, " base_scale=", table_base_scale, " expanded=", expanded_meld_index)

func _balanced_table_rows(specs: Array[Dictionary], row_count: int, gap_x: float) -> Array:
	var count: int = clampi(row_count, 1, maxi(1, specs.size()))
	var rows: Array = []
	var loads: Array[float] = []
	for _i: int in range(count):
		rows.append([])
		loads.append(0.0)

	# Largest meld first gives a much denser horizontal packing than the former
	# sequential shelf while preserving card order inside every individual meld.
	var pending: Array[int] = []
	for i: int in range(specs.size()):
		pending.append(i)
	pending.sort_custom(func(a: int, b: int) -> bool:
		return float(specs[a]["width"]) > float(specs[b]["width"])
	)

	for spec_index: int in pending:
		var best_row: int = 0
		for r: int in range(1, count):
			if loads[r] < loads[best_row]:
				best_row = r
		var row: Array = rows[best_row]
		if not row.is_empty():
			loads[best_row] += gap_x
		row.append(spec_index)
		rows[best_row] = row
		loads[best_row] += float(specs[spec_index]["width"])

	# Stable left-to-right reading inside a row: original meld order is restored.
	for r: int in range(rows.size()):
		var row: Array = rows[r]
		row.sort()
		rows[r] = row
	return rows

func _table_plan_for_rows(specs: Array[Dictionary], row_count: int, gap_x: float, gap_y: float, padding: float) -> Dictionary:
	var rows: Array = _balanced_table_rows(specs, row_count, gap_x)
	var max_row_width: float = 0.0
	var total_height: float = padding * 2.0
	var non_empty_rows: int = 0
	for row_value: Variant in rows:
		var row: Array = row_value as Array
		if row.is_empty():
			continue
		non_empty_rows += 1
		var row_width: float = 0.0
		var row_height: float = 0.0
		for item_pos: int in range(row.size()):
			var spec_index: int = int(row[item_pos])
			if item_pos > 0:
				row_width += gap_x
			row_width += float(specs[spec_index]["width"])
			row_height = maxf(row_height, float(specs[spec_index]["height"]))
		max_row_width = maxf(max_row_width, row_width)
		total_height += row_height
	if non_empty_rows > 1:
		total_height += gap_y * float(non_empty_rows - 1)
	var total_width: float = max_row_width + padding * 2.0
	var fit_w: float = meld_layer.size.x / maxf(1.0, total_width)
	var fit_h: float = meld_layer.size.y / maxf(1.0, total_height)
	var fit_scale: float = minf(1.0, minf(fit_w, fit_h))
	return {
		"rows": rows,
		"row_count": non_empty_rows,
		"width": total_width,
		"height": total_height,
		"scale": fit_scale,
	}

func _choose_table_layout_plan(specs: Array[Dictionary], gap_x: float, gap_y: float, padding: float) -> Dictionary:
	if specs.is_empty():
		return {"rows": [], "row_count": 0, "width": 1.0, "height": 1.0, "scale": 1.0}

	# One row is used only when it fits at native size. Otherwise, two rows are the
	# preferred table shape. We accept a modest auto-fit reduction to avoid an
	# unnecessary third row; only below the readability threshold do we add rows.
	var one: Dictionary = _table_plan_for_rows(specs, 1, gap_x, gap_y, padding)
	if float(one["scale"]) >= 0.999:
		return one

	var two: Dictionary = _table_plan_for_rows(specs, mini(2, specs.size()), gap_x, gap_y, padding)
	if specs.size() <= 2 or float(two["scale"]) >= TABLE_TWO_ROW_MIN_SCALE:
		return two

	var best: Dictionary = two
	var best_scale: float = float(two["scale"])
	for row_count: int in range(3, specs.size() + 1):
		var candidate: Dictionary = _table_plan_for_rows(specs, row_count, gap_x, gap_y, padding)
		var candidate_scale: float = float(candidate["scale"])
		if candidate_scale > best_scale + 0.001:
			best = candidate
			best_scale = candidate_scale
		# Once the board is essentially native-sized, extra rows only waste space.
		if best_scale >= 0.999:
			break
	return best

func _is_table_meld_complete(cards: Array[CardInstance], kind: String) -> bool:
	# A Joker always means the meld is still "mature but editable": the exact
	# natural card can replace it. Such a meld must therefore remain open/readable.
	for card: CardInstance in cards:
		if card.is_joker():
			return false

	if kind == "set":
		return cards.size() == 4
	if kind == "run":
		if cards.size() != 13:
			return false
		var info: Dictionary = game.validate_meld(cards)
		return bool(info.get("valid", false)) and String(info.get("kind", "")) == "run"
	return false

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'v025 meld/layout replacement failed: {n}'

# Re-enable inspection of a TRUE completed stack. Incomplete melds and Joker-full
# melds stay fanned; tapping them without a selected hand card does nothing.
pattern = r'''func _on_meld_pressed\(meld_index: int\) -> void:\n.*?(?=func _on_discard_pressed\(\) -> void:)'''
replacement = '''func _on_meld_pressed(meld_index: int) -> void:
	if meld_index < 0 or meld_index >= game.table_melds.size():
		return

	if selected_indices.is_empty():
		var meld: Dictionary = game.table_melds[meld_index]
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var kind: String = String(meld.get("kind", ""))
		if not _is_table_meld_complete(cards, kind):
			return
		expanded_meld_index = -1 if expanded_meld_index == meld_index else meld_index
		# v0.0.24 dirty refresh must be explicitly invalidated because expanding a
		# stack changes presentation but not the underlying table-card signature.
		_last_table_refresh_signature = ""
		_refresh_all()
		return

	var result: Dictionary = game.play_player_on_meld(selected_indices, meld_index)
	if bool(result.get("ok", false)):
		_reset_selection()
		expanded_meld_index = -1
		game.last_message = String(result.get("message", "Combinaison complétée."))
	else:
		game.last_message = String(result.get("message", "Cette carte ne peut pas compléter cette combinaison."))
	_refresh_all()

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'v025 meld press replacement failed: {n}'

# Runtime marker and APK version.
marker = 'print("RAMI_V024: dirty_refresh=true table_persistent=true style_cache=true score_single_pass=true visual_unchanged=true")'
assert marker in text, 'v024 runtime marker not found'
text = text.replace(marker, marker + '\n\tprint("RAMI_V025: horizontal_first=true prefer_two_rows=true fold_true_complete=true joker_not_complete=true")', 1)
path.write_text(text, encoding='utf-8')

preset = Path('export_presets.cfg')
preset_text = preset.read_text(encoding='utf-8')
preset_text = preset_text.replace('export_path="Rami_v0.0.24.apk"', 'export_path="Rami_v0.0.25.apk"')
preset_text = preset_text.replace('version/code=26', 'version/code=27')
preset_text = preset_text.replace('version/name="0.0.24"', 'version/name="0.0.25"')
preset.write_text(preset_text, encoding='utf-8')

print('RAMI_PATCH_V025: horizontal-first adaptive rows + foldable true-complete stacks + Joker stays open')
