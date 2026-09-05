from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# Full common-table surface is now the touch target, not just its title strip.
old = '''\ttable_button = Button.new()\n\ttable_button.text = "TABLE COMMUNE\\nTouchez ici pour poser la combinaison sélectionnée"\n\ttable_button.position = Vector2(220, 202)\n\ttable_button.size = Vector2(950, 70)\n\ttable_button.add_theme_font_size_override("font_size", 20)\n\ttable_button.add_theme_color_override("font_color", Color(0.78, 0.92, 0.84, 0.78))\n\ttable_button.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))\n\ttable_button.add_theme_stylebox_override("disabled", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))\n\ttable_button.pressed.connect(_on_table_pressed)\n\tadd_child(table_button)'''
new = '''\ttable_button = Button.new()\n\ttable_button.text = ""\n\ttable_button.position = Vector2(205, 190)\n\ttable_button.size = Vector2(980, 365)\n\ttable_button.focus_mode = Control.FOCUS_NONE\n\ttable_button.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))\n\ttable_button.add_theme_stylebox_override("hover", _button_style(Color(0.08, 0.50, 0.30, 0.05), Color(0.30, 0.85, 0.55, 0.20), 2, 20))\n\ttable_button.add_theme_stylebox_override("pressed", _button_style(Color(0.08, 0.50, 0.30, 0.09), Color(0.30, 0.85, 0.55, 0.32), 3, 20))\n\ttable_button.add_theme_stylebox_override("disabled", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))\n\ttable_button.pressed.connect(_on_table_pressed)\n\tadd_child(table_button)\n\t_make_label("TABLE COMMUNE", Vector2(220, 202), Vector2(950, 30), 20, Color(0.78, 0.92, 0.84, 0.78), HORIZONTAL_ALIGNMENT_CENTER)\n\t_make_label("Touchez n'importe où dans la table pour poser la combinaison sélectionnée", Vector2(220, 232), Vector2(950, 28), 16, Color(0.78, 0.92, 0.84, 0.62), HORIZONTAL_ALIGNMENT_CENTER)'''
assert old in text, 'table button block not found after v009 patch'
text = text.replace(old, new, 1)

# Keep meld visuals above the full-size invisible table button, but non-blocking.
text = text.replace('\tmeld_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE\n\tadd_child(meld_layer)', '\tmeld_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE\n\tadd_child(meld_layer)')

# Make automatic combo hints predictable: only show a coloured strip when all cards
# of that meld are next to each other in the current hand order. This removes the
# scattered, apparently-random coloured fragments seen with suit sorting.
pattern = r'''func _refresh_hand_combo_bands\(\) -> void:\n.*?(?=func _band_style\(color: Color, selected: bool\) -> StyleBoxFlat:)'''
replacement = '''func _refresh_hand_combo_bands() -> void:\n\t_clear_children(hand_band_layer)\n\tif detected_combos.is_empty() or game.player_hand.is_empty():\n\t\treturn\n\t_calculate_hand_layout()\n\tvar count: int = game.player_hand.size()\n\tvar used: Dictionary = {}\n\tvar chosen: Array[int] = []\n\n\t# A hint is displayed only when its cards form one contiguous block in the hand.\n\t# This keeps the visual language simple: one clean coloured strip = one visible meld.\n\tfor wanted_size: int in range(count, 2, -1):\n\t\tfor combo_index: int in range(detected_combos.size()):\n\t\t\tvar indices: Array[int] = _dict_int_array(detected_combos[combo_index], "indices")\n\t\t\tif indices.size() != wanted_size:\n\t\t\t\tcontinue\n\t\t\tindices.sort()\n\t\t\tvar contiguous := true\n\t\t\tfor p: int in range(1, indices.size()):\n\t\t\t\tif indices[p] != indices[p - 1] + 1:\n\t\t\t\t\tcontiguous = false\n\t\t\t\t\tbreak\n\t\t\tif not contiguous:\n\t\t\t\tcontinue\n\t\t\tvar overlaps := false\n\t\t\tfor idx: int in indices:\n\t\t\t\tif used.has(idx):\n\t\t\t\t\toverlaps = true\n\t\t\t\t\tbreak\n\t\t\tif overlaps:\n\t\t\t\tcontinue\n\t\t\tchosen.append(combo_index)\n\t\t\tfor idx: int in indices:\n\t\t\t\tused[idx] = true\n\n\tfor visual_index: int in range(chosen.size()):\n\t\tvar combo_index: int = chosen[visual_index]\n\t\tvar indices: Array[int] = _dict_int_array(detected_combos[combo_index], "indices")\n\t\tindices.sort()\n\t\tvar color: Color = COMBO_COLORS[visual_index % COMBO_COLORS.size()]\n\t\tfor member_pos: int in range(indices.size()):\n\t\t\tvar idx: int = indices[member_pos]\n\t\t\tvar card_y: float = _player_card_y(idx, count)\n\t\t\tif selected_indices.has(idx) or (drag_started and drag_index == idx):\n\t\t\t\tcard_y -= 24.0\n\t\t\tvar segment_width: float = hand_step + 8.0 if member_pos < indices.size() - 1 else PLAYER_CARD_SIZE.x - 12.0\n\t\t\tvar band: Button = Button.new()\n\t\t\tband.position = Vector2(float(idx) * hand_step + 6.0, card_y + PLAYER_CARD_SIZE.y - 20.0)\n\t\t\tband.size = Vector2(segment_width, 16.0)\n\t\t\tband.focus_mode = Control.FOCUS_NONE\n\t\t\tband.add_theme_stylebox_override("normal", _band_style(color, selected_detected_combo == combo_index))\n\t\t\tband.add_theme_stylebox_override("hover", _band_style(color.lightened(0.08), true))\n\t\t\tband.add_theme_stylebox_override("pressed", _band_style(color.darkened(0.08), true))\n\t\t\tband.tooltip_text = "Touchez pour sélectionner toute la combinaison"\n\t\t\tband.pressed.connect(_on_combo_band_pressed.bind(combo_index))\n\t\t\thand_band_layer.add_child(band)\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'combo band block replacement failed: {n}'

# Selection feedback explicitly tells the player that the whole table is tappable.
text = text.replace(
    'game.last_message = "Combinaison sélectionnée. Touchez la table pour la poser."',
    'game.last_message = "Combinaison sélectionnée. Touchez directement la table commune pour la poser."'
)

text = text.replace('v0.0.9 • META MOBILE ÉPURÉE', 'v0.0.10 • COMBOS + TABLE TACTILE')
text = text.replace(
    'print("RAMI_CLEAN_UI: opponent_counters=true combo_chips=false clean_bands=true")',
    'print("RAMI_CLEAN_UI: opponent_counters=true combo_chips=false clean_bands=true")\n\tprint("RAMI_V010: contiguous_combo_hints=true full_table_touch=true")'
)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V010: applied combo clarity + full table touch')
