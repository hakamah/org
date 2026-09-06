from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# 1) When a highlighted combo is already selected, tapping one of its cards switches
# to that single card instead of re-selecting the whole combo forever.
pattern = r'''func _on_player_card_pressed\(index: int\) -> void:\n.*?(?=func _on_combo_band_pressed\(combo_index: int\) -> void:)'''
replacement = '''func _on_player_card_pressed(index: int) -> void:
	if game.phase != RamiGame.Phase.ACTION or game.turn_index != 0:
		return
	if index < 0 or index >= game.player_hand.size():
		return

	if highlighted_card_to_combo.has(index):
		var combo_index: int = int(highlighted_card_to_combo[index])
		if combo_index >= 0 and combo_index < detected_combos.size():
			# First tap on a highlighted card selects the full suggested combo.
			# If that combo is already selected, tapping one of its cards selects only
			# that card so it can be discarded or used elsewhere.
			if selected_detected_combo == combo_index:
				selected_detected_combo = -1
				selected_indices.clear()
				selected_indices.append(index)
				game.last_message = "Carte sélectionnée individuellement."
			else:
				selected_detected_combo = combo_index
				selected_indices = _dict_int_array(detected_combos[combo_index], "indices")
				selected_indices.sort()
				game.last_message = "Combinaison sélectionnée. Touchez directement la table commune pour la poser."
			_refresh_all()
			return

	selected_detected_combo = -1
	if selected_indices.has(index):
		selected_indices.erase(index)
	else:
		selected_indices.append(index)
	selected_indices.sort()
	_refresh_all()

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'card selection replacement failed: {n}'

# 2) Display-only cards must stay fully bright. Previously they were disabled
# TextureButtons, which can be rendered grey by Android/Godot themes.
old = '''\tbutton.texture_normal = _load_card_texture(card_id)\n\tbutton.texture_disabled = button.texture_normal\n\tbutton.disabled = not clickable\n\tbutton.focus_mode = Control.FOCUS_NONE\n\twrapper.add_child(button)'''
new = '''\tbutton.texture_normal = _load_card_texture(card_id)\n\tbutton.texture_disabled = button.texture_normal\n\tbutton.disabled = false\n\tbutton.focus_mode = Control.FOCUS_NONE\n\tbutton.mouse_filter = Control.MOUSE_FILTER_STOP if clickable else Control.MOUSE_FILTER_IGNORE\n\twrapper.add_child(button)'''
assert old in text, '_make_card TextureButton block not found'
text = text.replace(old, new, 1)

# 3) Enlarge the common table again while keeping the right-side draw/discard area.
text = text.replace(
    '_panel(Vector2(145, 92), Vector2(1060, 500), Color(0.04, 0.27, 0.18, 0.24), Color(0.20, 0.65, 0.43, 0.42), 30, 3)',
    '_panel(Vector2(85, 76), Vector2(1120, 530), Color(0.04, 0.27, 0.18, 0.24), Color(0.20, 0.65, 0.43, 0.42), 30, 3)'
)
text = text.replace('table_button.position = Vector2(145, 92)', 'table_button.position = Vector2(85, 76)')
text = text.replace('table_button.size = Vector2(1060, 500)', 'table_button.size = Vector2(1120, 530)')
text = text.replace('_make_label("TABLE COMMUNE", Vector2(165, 104), Vector2(1020, 30)', '_make_label("TABLE COMMUNE", Vector2(105, 88), Vector2(1080, 30)')
text = text.replace('_make_label("Touchez n\'importe où dans la table pour poser la combinaison sélectionnée", Vector2(165, 134), Vector2(1020, 28)', '_make_label("Touchez n\'importe où dans la table pour poser la combinaison sélectionnée", Vector2(105, 118), Vector2(1080, 28)')
text = text.replace('meld_layer.position = Vector2(165, 174)', 'meld_layer.position = Vector2(105, 154)')
text = text.replace('meld_layer.size = Vector2(1020, 392)', 'meld_layer.size = Vector2(1080, 424)')
text = text.replace('status_label = _make_label("", Vector2(165, 572), Vector2(1020, 34)', 'status_label = _make_label("", Vector2(105, 582), Vector2(1080, 30)')

# 4) Bigger, bright table cards, but compact/stacked horizontally to preserve space.
# Every meld on the table is considered "finished for display" and is shown as a
# compact fan: big cards, only their useful left edge is overlapped.
pattern = r'''func _refresh_melds\(\) -> void:\n.*?(?=func _make_card\()'''
replacement = '''func _refresh_melds() -> void:
	_clear_children(meld_layer)
	if game.table_melds.is_empty():
		_make_label("Aucune combinaison posée", Vector2(230, 150), Vector2(620, 54), 26, Color(0.84, 0.94, 0.88, 0.62), HORIZONTAL_ALIGNMENT_CENTER, meld_layer)
		return

	var meld_count: int = game.table_melds.size()
	var card_w: float = 132.0
	var card_h: float = 186.0
	var card_step: float = 52.0
	var row_step: float = 198.0
	if meld_count > 5:
		card_w = 120.0
		card_h = 169.0
		card_step = 46.0
		row_step = 178.0
	if meld_count > 8:
		card_w = 108.0
		card_h = 152.0
		card_step = 42.0
		row_step = 160.0

	var x: float = 8.0
	var y: float = 34.0
	var usable_width: float = maxf(320.0, meld_layer.size.x - 16.0)
	var usable_height: float = maxf(240.0, meld_layer.size.y - 8.0)
	var row_index: int = 0

	for meld_index: int in range(game.table_melds.size()):
		var meld: Dictionary = game.table_melds[meld_index]
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var owner: int = int(meld.get("owner", 0))
		# Compact/fan every finished table meld. The cards stay large but overlap.
		var meld_width: float = card_step * float(maxi(0, cards.size() - 1)) + card_w

		if x > 8.0 and x + meld_width > usable_width:
			x = 8.0
			row_index += 1
			y = 34.0 + float(row_index) * row_step

		if y + card_h > usable_height:
			var needed_rows: int = row_index + 1
			var available_for_rows: float = maxf(card_h, usable_height - 34.0)
			row_step = maxf(88.0, (available_for_rows - card_h) / maxf(1.0, float(needed_rows - 1)))
			y = 34.0 + float(row_index) * row_step

		var owner_color: Color = GREEN if owner == 0 else RED
		var title: Label = _make_label(RamiGame.PLAYER_NAMES[owner], Vector2(x, y - 29.0), Vector2(maxf(98.0, meld_width), 26.0), 14, owner_color, HORIZONTAL_ALIGNMENT_CENTER, meld_layer)
		title.mouse_filter = Control.MOUSE_FILTER_IGNORE

		for i: int in range(cards.size()):
			_make_card(cards[i].face_id(), Vector2(x + float(i) * card_step, y), Vector2(card_w, card_h), false, -2, meld_layer, false, Color(0, 0, 0, 0))

		# Whole visible combination remains interactive for extension/Joker replacement.
		var meld_touch: Button = Button.new()
		meld_touch.name = "MeldTouch_%d" % meld_index
		meld_touch.text = ""
		meld_touch.position = Vector2(x, y)
		meld_touch.size = Vector2(maxf(card_w, meld_width), card_h)
		meld_touch.focus_mode = Control.FOCUS_NONE
		meld_touch.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		meld_touch.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 8))
		meld_touch.add_theme_stylebox_override("hover", _button_style(Color(0.12, 0.62, 0.36, 0.04), Color(0.40, 0.95, 0.62, 0.38), 2, 10))
		meld_touch.add_theme_stylebox_override("pressed", _button_style(Color(0.12, 0.62, 0.36, 0.08), Color(0.40, 0.95, 0.62, 0.62), 3, 10))
		meld_touch.tooltip_text = "Touchez pour compléter cette combinaison"
		meld_touch.pressed.connect(_on_meld_pressed.bind(meld_index))
		meld_layer.add_child(meld_touch)

		x += meld_width + 34.0

	print("RAMI_TABLE_V015: melds=", game.table_melds.size(), " card=", Vector2(card_w, card_h), " compact_step=", card_step)

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_refresh_melds replacement failed: {n}'

text = text.replace('v0.0.14 • DÉFAUSSE FIX + ICÔNE AJUSTÉE', 'v0.0.15 • TABLE XXL + SÉLECTION LIBRE')
text = text.replace(
    'print("RAMI_V014: discard_zone_always=true empty_discard_touch=true icon_padded=true")',
    'print("RAMI_V014: discard_zone_always=true empty_discard_touch=true icon_padded=true")\n\tprint("RAMI_V015: combo_single_card=true table_brighter=true table_bigger=true compact_melds=true app_icon_final=true")'
)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V015: free combo card selection + bright larger compact table')
