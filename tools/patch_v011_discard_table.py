from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# Remember which visible highlighted meld owns each hand-card index.
needle = 'var detected_combos: Array[Dictionary] = []\nvar deal_animation_done: bool = false'
assert needle in text, 'detected combo vars not found'
text = text.replace(needle, 'var detected_combos: Array[Dictionary] = []\nvar highlighted_card_to_combo: Dictionary = {}\nvar deal_animation_done: bool = false', 1)

# Remove the dedicated discard button entirely.
old = '''\tdiscard_button = _make_button("DÉFAUSSER\\nFin du tour", Vector2(14, 553), Vector2(190, 86), 20, Color("#0B5E40"), GREEN)\n\tdiscard_button.pressed.connect(_on_discard_pressed)\n\n'''
assert old in text, 'discard button creation not found'
text = text.replace(old, '', 1)

# No refresh logic may depend on the removed button.
text = text.replace('\t\tdiscard_button.disabled = true\n', '')
text = text.replace('\t\tdiscard_button.disabled = selected_indices.size() != 1\n', '')

# The discard pile is interactive both for drawing it in DRAW phase and for discarding
# a selected card in ACTION phase.
old = '''\tif top != null:\n\t\t_make_card(top.face_id(), Vector2(10, 0), Vector2(132, 186), game.phase == RamiGame.Phase.DRAW and game.turn_index == 0, -1, discard_layer, false, GOLD)'''
new = '''\tif top != null:\n\t\tvar discard_touchable: bool = game.turn_index == 0 and (game.phase == RamiGame.Phase.DRAW or game.phase == RamiGame.Phase.ACTION)\n\t\tvar discard_accent: Color = GREEN if game.phase == RamiGame.Phase.ACTION and selected_indices.size() == 1 else GOLD\n\t\t_make_card(top.face_id(), Vector2(10, 0), Vector2(132, 186), discard_touchable, -1, discard_layer, false, discard_accent)'''
assert old in text, 'discard card rendering block not found'
text = text.replace(old, new, 1)

# The same discard pile now performs context-sensitive action.
pattern = r'''func _on_draw_discard\(\) -> void:\n.*?(?=func _on_player_card_pressed\(index: int\) -> void:)'''
replacement = '''func _on_draw_discard() -> void:\n\tif game.turn_index != 0:\n\t\treturn\n\tif game.phase == RamiGame.Phase.DRAW:\n\t\tif game.draw_discard():\n\t\t\t_reset_selection()\n\t\t\t_refresh_all()\n\t\treturn\n\tif game.phase == RamiGame.Phase.ACTION:\n\t\tif selected_indices.size() != 1:\n\t\t\tgame.last_message = "Sélectionnez exactement 1 carte, puis touchez la défausse."\n\t\t\t_refresh_all()\n\t\t\treturn\n\t\tvar result: Dictionary = game.discard_player(selected_indices[0])\n\t\tif bool(result.get("ok", false)):\n\t\t\t_reset_selection()\n\t\t\thand_scroll_offset = 0.0\n\t\telse:\n\t\t\tgame.last_message = String(result.get("message", "Défausse impossible."))\n\t\t_refresh_all()\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'discard handler replacement failed: {n}'

# Clicking any card belonging to a visible automatic highlight selects the full meld.
pattern = r'''func _on_player_card_pressed\(index: int\) -> void:\n.*?(?=func _on_combo_band_pressed\(combo_index: int\) -> void:)'''
replacement = '''func _on_player_card_pressed(index: int) -> void:\n\tif game.phase != RamiGame.Phase.ACTION or game.turn_index != 0:\n\t\treturn\n\tif index < 0 or index >= game.player_hand.size():\n\t\treturn\n\n\tif highlighted_card_to_combo.has(index):\n\t\tvar combo_index: int = int(highlighted_card_to_combo[index])\n\t\tif combo_index >= 0 and combo_index < detected_combos.size():\n\t\t\tselected_detected_combo = combo_index\n\t\t\tselected_indices = _dict_int_array(detected_combos[combo_index], "indices")\n\t\t\tselected_indices.sort()\n\t\t\tgame.last_message = "Combinaison sélectionnée. Touchez directement la table commune pour la poser."\n\t\t\t_refresh_all()\n\t\t\treturn\n\n\tselected_detected_combo = -1\n\tif selected_indices.has(index):\n\t\tselected_indices.erase(index)\n\telse:\n\t\tselected_indices.append(index)\n\tselected_indices.sort()\n\t_refresh_all()\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'card selection replacement failed: {n}'

# Strict per-card highlight segments. A band never reaches under an unrelated card.
pattern = r'''func _refresh_hand_combo_bands\(\) -> void:\n.*?(?=func _band_style\(color: Color, selected: bool\) -> StyleBoxFlat:)'''
replacement = '''func _refresh_hand_combo_bands() -> void:\n\t_clear_children(hand_band_layer)\n\thighlighted_card_to_combo.clear()\n\tif detected_combos.is_empty() or game.player_hand.is_empty():\n\t\treturn\n\t_calculate_hand_layout()\n\tvar count: int = game.player_hand.size()\n\tvar used: Dictionary = {}\n\tvar chosen: Array[int] = []\n\n\tfor wanted_size: int in range(count, 2, -1):\n\t\tfor combo_index: int in range(detected_combos.size()):\n\t\t\tvar indices: Array[int] = _dict_int_array(detected_combos[combo_index], "indices")\n\t\t\tif indices.size() != wanted_size:\n\t\t\t\tcontinue\n\t\t\tindices.sort()\n\t\t\tvar contiguous := true\n\t\t\tfor p: int in range(1, indices.size()):\n\t\t\t\tif indices[p] != indices[p - 1] + 1:\n\t\t\t\t\tcontiguous = false\n\t\t\t\t\tbreak\n\t\t\tif not contiguous:\n\t\t\t\tcontinue\n\t\t\tvar overlaps := false\n\t\t\tfor idx: int in indices:\n\t\t\t\tif used.has(idx):\n\t\t\t\t\toverlaps = true\n\t\t\t\t\tbreak\n\t\t\tif overlaps:\n\t\t\t\tcontinue\n\t\t\tchosen.append(combo_index)\n\t\t\tfor idx: int in indices:\n\t\t\t\tused[idx] = true\n\t\t\t\thighlighted_card_to_combo[idx] = combo_index\n\n\tfor visual_index: int in range(chosen.size()):\n\t\tvar combo_index: int = chosen[visual_index]\n\t\tvar indices: Array[int] = _dict_int_array(detected_combos[combo_index], "indices")\n\t\tindices.sort()\n\t\tvar color: Color = COMBO_COLORS[visual_index % COMBO_COLORS.size()]\n\t\tfor idx: int in indices:\n\t\t\tvar card_y: float = _player_card_y(idx, count)\n\t\t\tif selected_indices.has(idx) or (drag_started and drag_index == idx):\n\t\t\t\tcard_y -= 24.0\n\t\t\tvar visible_slot_width: float = maxf(30.0, minf(PLAYER_CARD_SIZE.x - 16.0, hand_step - 6.0))\n\t\t\tvar band: Button = Button.new()\n\t\t\tband.position = Vector2(float(idx) * hand_step + 8.0, card_y + PLAYER_CARD_SIZE.y - 20.0)\n\t\t\tband.size = Vector2(visible_slot_width, 16.0)\n\t\t\tband.focus_mode = Control.FOCUS_NONE\n\t\t\tband.add_theme_stylebox_override("normal", _band_style(color, selected_detected_combo == combo_index))\n\t\t\tband.add_theme_stylebox_override("hover", _band_style(color.lightened(0.08), true))\n\t\t\tband.add_theme_stylebox_override("pressed", _band_style(color.darkened(0.08), true))\n\t\t\tband.tooltip_text = "Touchez la bande ou une carte pour sélectionner toute la combinaison"\n\t\t\tband.pressed.connect(_on_combo_band_pressed.bind(combo_index))\n\t\t\thand_band_layer.add_child(band)\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'combo band replacement failed: {n}'

# Make table melds much easier to read on a phone. Match the full block with exact indentation.
old_meld_size = '''\t\tvar w: float = 68.0\n\t\tvar h: float = 96.0\n\t\tvar step: float = 31.0'''
new_meld_size = '''\t\tvar w: float = 96.0\n\t\tvar h: float = 136.0\n\t\tvar step: float = 46.0'''
assert old_meld_size in text, 'meld size block not found'
text = text.replace(old_meld_size, new_meld_size, 1)
text = text.replace('\t\t\ty += 122.0', '\t\t\ty += 150.0', 1)
text = text.replace('\t\tif y > 150.0:', '\t\tif y > 165.0:', 1)
text = text.replace('\t\tx += meld_width + 24.0', '\t\tx += meld_width + 34.0', 1)

text = text.replace('turn_label.text = "À VOUS • JOUEZ PUIS DÉFAUSSEZ"', 'turn_label.text = "À VOUS • POSEZ OU SÉLECTIONNEZ 1 CARTE → DÉFAUSSE"')
text = text.replace('v0.0.10 • COMBOS + TABLE TACTILE', 'v0.0.11b • DÉFAUSSE TACTILE + TABLE XL')
text = text.replace(
    'print("RAMI_V010: contiguous_combo_hints=true full_table_touch=true")',
    'print("RAMI_V010: contiguous_combo_hints=true full_table_touch=true")\n\tprint("RAMI_V011: discard_pile_action=true card_combo_select=true strict_band_slots=true table_melds_xl=true")'
)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V011: applied discard-pile flow + strict combo bands + XL table melds')
