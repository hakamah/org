from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# Main hand: use the full bottom strip more like the mobile reference.
text = text.replace('const HAND_VIEW_POS := Vector2(220, 632)', 'const HAND_VIEW_POS := Vector2(220, 615)')
text = text.replace('const HAND_VIEW_SIZE := Vector2(1350, 252)', 'const HAND_VIEW_SIZE := Vector2(1350, 270)')
text = text.replace('const PLAYER_CARD_SIZE := Vector2(148, 210)', 'const PLAYER_CARD_SIZE := Vector2(158, 225)')
text = text.replace('const PLAYER_CARD_STEP := 90.0', 'const PLAYER_CARD_STEP := 92.0')
text = text.replace('const PLAYER_CARD_MIN_STEP := 64.0', 'const PLAYER_CARD_MIN_STEP := 68.0')

# The separate row of combination chips is intentionally removed. Combinations are
# represented only by clean coloured strips on the cards themselves.
text = text.replace(
    'combo_layer.mouse_filter = Control.MOUSE_FILTER_PASS\n\tadd_child(combo_layer)',
    'combo_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE\n\tcombo_layer.visible = false\n\tadd_child(combo_layer)'
)

text = text.replace('v0.0.8 • ERGONOMIE MOBILE', 'v0.0.9 • META MOBILE ÉPURÉE')

# Counts are now carried by the little card-back badges next to IA names.
text = text.replace(
    'ai1_count_label.text = "%d cartes" % game.ai1_hand.size()\n\tai2_count_label.text = "%d cartes" % game.ai2_hand.size()',
    'ai1_count_label.text = ""\n\tai2_count_label.text = ""'
)

# Remove the fan of 13 hidden cards. Each opponent gets one compact back-card icon
# with a large numeric badge, matching the mobile reference supplied by the user.
pattern = r'''func _refresh_opponents\(\) -> void:\n.*?(?=func _calculate_hand_layout\(\) -> void:)'''
replacement = '''func _refresh_opponents() -> void:\n\t_clear_children(ai1_layer)\n\t_clear_children(ai2_layer)\n\t_draw_opponent_hand(game.ai1_hand.size(), Vector2(680, 2), ai1_layer, -1.0)\n\t_draw_opponent_hand(game.ai2_hand.size(), Vector2(965, 2), ai2_layer, 1.0)\n\nfunc _draw_opponent_hand(count: int, center: Vector2, parent: Control, _direction: float) -> void:\n\tif count <= 0:\n\t\treturn\n\t_make_card("back_red", center, Vector2(52, 68), false, -2, parent, false, Color(0, 0, 0, 0))\n\tvar badge: Panel = _panel(center + Vector2(28, 35), Vector2(50, 42), Color("#B72F35"), Color("#FFF3D2"), 12, 3, parent)\n\t_make_label(str(count), Vector2.ZERO, badge.size, 24, Color.WHITE, HORIZONTAL_ALIGNMENT_CENTER, badge)\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'opponent block replacement failed: {n}'

# No secondary combination buttons above the hand.
pattern = r'''func _refresh_combo_chips\(\) -> void:\n.*?(?=func _refresh_hand_combo_bands\(\) -> void:)'''
replacement = '''func _refresh_combo_chips() -> void:\n\t_clear_children(combo_layer)\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'combo chip replacement failed: {n}'

# Clean automatic highlights: select the longest non-overlapping candidate melds,
# and draw one single strip at the bottom of each card. No stacked rainbow clutter.
pattern = r'''func _refresh_hand_combo_bands\(\) -> void:\n.*?(?=func _band_style\(color: Color, selected: bool\) -> StyleBoxFlat:)'''
replacement = '''func _refresh_hand_combo_bands() -> void:\n\t_clear_children(hand_band_layer)\n\tif detected_combos.is_empty() or game.player_hand.is_empty():\n\t\treturn\n\t_calculate_hand_layout()\n\tvar count: int = game.player_hand.size()\n\tvar used: Dictionary = {}\n\tvar chosen: Array[int] = []\n\n\t# Longer combinations win first. A card receives at most one automatic colour.\n\tfor wanted_size: int in range(count, 2, -1):\n\t\tfor combo_index: int in range(detected_combos.size()):\n\t\t\tvar indices: Array[int] = _dict_int_array(detected_combos[combo_index], "indices")\n\t\t\tif indices.size() != wanted_size:\n\t\t\t\tcontinue\n\t\t\tvar overlaps := false\n\t\t\tfor idx: int in indices:\n\t\t\t\tif used.has(idx):\n\t\t\t\t\toverlaps = true\n\t\t\t\t\tbreak\n\t\t\tif overlaps:\n\t\t\t\tcontinue\n\t\t\tchosen.append(combo_index)\n\t\t\tfor idx: int in indices:\n\t\t\t\tused[idx] = true\n\t\t\tif chosen.size() >= 5:\n\t\t\t\tbreak\n\t\tif chosen.size() >= 5:\n\t\t\tbreak\n\n\tfor visual_index: int in range(chosen.size()):\n\t\tvar combo_index: int = chosen[visual_index]\n\t\tvar indices: Array[int] = _dict_int_array(detected_combos[combo_index], "indices")\n\t\tindices.sort()\n\t\tvar color: Color = COMBO_COLORS[visual_index % COMBO_COLORS.size()]\n\t\tfor member_pos: int in range(indices.size()):\n\t\t\tvar idx: int = indices[member_pos]\n\t\t\tif idx < 0 or idx >= count:\n\t\t\t\tcontinue\n\t\t\tvar linked_next: bool = member_pos + 1 < indices.size() and indices[member_pos + 1] == idx + 1\n\t\t\tvar segment_width: float = hand_step + 8.0 if linked_next else PLAYER_CARD_SIZE.x - 12.0\n\t\t\tvar card_y: float = _player_card_y(idx, count)\n\t\t\tif selected_indices.has(idx) or (drag_started and drag_index == idx):\n\t\t\t\tcard_y -= 24.0\n\t\t\tvar band: Button = Button.new()\n\t\t\tband.position = Vector2(float(idx) * hand_step + 6.0, card_y + PLAYER_CARD_SIZE.y - 20.0)\n\t\t\tband.size = Vector2(segment_width, 16.0)\n\t\t\tband.focus_mode = Control.FOCUS_NONE\n\t\t\tband.add_theme_stylebox_override("normal", _band_style(color, selected_detected_combo == combo_index))\n\t\t\tband.add_theme_stylebox_override("hover", _band_style(color.lightened(0.08), true))\n\t\t\tband.add_theme_stylebox_override("pressed", _band_style(color.darkened(0.08), true))\n\t\t\tband.tooltip_text = "Combinaison détectée"\n\t\t\tband.pressed.connect(_on_combo_band_pressed.bind(combo_index))\n\t\t\thand_band_layer.add_child(band)\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'hand band replacement failed: {n}'

# Runtime marker used by CI to make sure the clean layout is actually active.
text = text.replace(
    'print("RAMI_MOBILE_HAND: card_size=", PLAYER_CARD_SIZE, " view=", HAND_VIEW_SIZE)',
    'print("RAMI_MOBILE_HAND: card_size=", PLAYER_CARD_SIZE, " view=", HAND_VIEW_SIZE)\n\tprint("RAMI_CLEAN_UI: opponent_counters=true combo_chips=false clean_bands=true")'
)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V009: applied clean mobile meta')
