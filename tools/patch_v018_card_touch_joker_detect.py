from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# Recompute suggested melds in both DRAW and ACTION so moving a Joker immediately
# updates the visual hints, even before the mandatory draw is taken.
pattern = r'''func _refresh_all\(\) -> void:\n\tdetected_combos.clear\(\)\n\tif game.phase == RamiGame.Phase.ACTION and game.turn_index == 0:\n\t\tvar found: Array = game.detect_player_melds\(\)\n\t\tfor value: Variant in found:\n\t\t\tif value is Dictionary:\n\t\t\t\tdetected_combos.append\(value as Dictionary\)'''
replacement = '''func _refresh_all() -> void:\n\t_recompute_detected_combos()'''
text, n = re.subn(pattern, replacement, text, count=1)
assert n == 1, f'_refresh_all detector replacement failed: {n}'

insert_marker = 'func _refresh_opponents() -> void:\n'
assert insert_marker in text, 'refresh opponents marker not found'
helper = '''func _recompute_detected_combos() -> void:\n\tdetected_combos.clear()\n\tif game.winner_index >= 0 or game.turn_index != 0:\n\t\treturn\n\tif game.phase != RamiGame.Phase.DRAW and game.phase != RamiGame.Phase.ACTION:\n\t\treturn\n\tvar found: Array = game.detect_player_melds()\n\tfor value: Variant in found:\n\t\tif value is Dictionary:\n\t\t\tdetected_combos.append(value as Dictionary)\n\n'''
text = text.replace(insert_marker, helper + insert_marker, 1)

# While a card is dragged/reordered, recalculate candidates immediately before
# repainting the coloured bands. This makes a Joker act as a visible wildcard in
# real time as soon as it is placed between the natural cards of a run/set.
old = '''\tif target != drag_index:\n\t\t_move_hand_card_for_drag(drag_index, target)\n\t\tdrag_index = target\n\t\t_refresh_player()\n\t\t_refresh_hand_combo_bands()\n\t\t_refresh_combo_chips()'''
new = '''\tif target != drag_index:\n\t\t_move_hand_card_for_drag(drag_index, target)\n\t\tdrag_index = target\n\t\t_recompute_detected_combos()\n\t\t_refresh_player()\n\t\t_refresh_hand_combo_bands()\n\t\t_refresh_combo_chips()'''
assert old in text, 'drag refresh block not found'
text = text.replace(old, new, 1)

# Cards remain tappable in DRAW phase for visual selection/inspection and manual
# organisation. Playing/discarding is still blocked by the engine until after draw.
pattern = r'''func _on_player_card_pressed\(index: int\) -> void:\n.*?(?=func _on_combo_band_pressed\(combo_index: int\) -> void:)'''
replacement = '''func _on_player_card_pressed(index: int) -> void:\n\tif game.turn_index != 0:\n\t\treturn\n\tif game.phase != RamiGame.Phase.DRAW and game.phase != RamiGame.Phase.ACTION:\n\t\treturn\n\tif index < 0 or index >= game.player_hand.size():\n\t\treturn\n\n\tif highlighted_card_to_combo.has(index):\n\t\tvar combo_index: int = int(highlighted_card_to_combo[index])\n\t\tif combo_index >= 0 and combo_index < detected_combos.size():\n\t\t\tif selected_detected_combo == combo_index:\n\t\t\t\tselected_detected_combo = -1\n\t\t\t\tselected_indices.clear()\n\t\t\t\tselected_indices.append(index)\n\t\t\t\tgame.last_message = "Carte sélectionnée individuellement."\n\t\t\telse:\n\t\t\t\tselected_detected_combo = combo_index\n\t\t\t\tselected_indices = _dict_int_array(detected_combos[combo_index], "indices")\n\t\t\t\tselected_indices.sort()\n\t\t\t\tgame.last_message = "Combinaison détectée." if game.phase == RamiGame.Phase.DRAW else "Combinaison sélectionnée. Touchez la table commune pour la poser."\n\t\t\t_refresh_all()\n\t\t\treturn\n\n\tselected_detected_combo = -1\n\tif selected_indices.has(index):\n\t\tselected_indices.erase(index)\n\telse:\n\t\tselected_indices.append(index)\n\tselected_indices.sort()\n\tif game.phase == RamiGame.Phase.DRAW:\n\t\tgame.last_message = "Carte sélectionnée. Piochez avant de jouer."\n\t_refresh_all()\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'card pressed replacement failed: {n}'

# Keep combo bands selectable in DRAW too, but the table itself remains disabled
# until ACTION by existing rules.
pattern = r'''func _on_combo_band_pressed\(combo_index: int\) -> void:\n.*?(?=func _on_table_pressed\(\) -> void:)'''
replacement = '''func _on_combo_band_pressed(combo_index: int) -> void:\n\tif combo_index < 0 or combo_index >= detected_combos.size():\n\t\treturn\n\tif game.turn_index != 0:\n\t\treturn\n\tselected_detected_combo = combo_index\n\tselected_indices = _dict_int_array(detected_combos[combo_index], "indices")\n\tselected_indices.sort()\n\tif game.phase == RamiGame.Phase.DRAW:\n\t\tgame.last_message = "Combinaison détectée. Piochez d'abord pour pouvoir la poser."\n\telse:\n\t\tgame.last_message = "Combinaison sélectionnée. Touchez directement la table commune pour la poser."\n\t_refresh_all()\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'combo band replacement failed: {n}'

# Strengthen card input routing after the v0.0.15 visual-card change.
old = '''\tif clickable:\n\t\tif index >= 0:\n\t\t\tbutton.gui_input.connect(_on_player_card_gui_input.bind(index))\n\t\telif index == -1:\n\t\t\tbutton.pressed.connect(_on_draw_discard)'''
new = '''\tif clickable:\n\t\tbutton.mouse_filter = Control.MOUSE_FILTER_STOP\n\t\tif index >= 0:\n\t\t\tbutton.gui_input.connect(_on_player_card_gui_input.bind(index))\n\t\telif index == -1:\n\t\t\tbutton.pressed.connect(_on_draw_discard)'''
assert old in text, 'clickable card input block not found'
text = text.replace(old, new, 1)

text = text.replace('v0.0.17', 'v0.0.18')
ready_marker = 'print("RAMI_RUNTIME: refresh_ok player_nodes=", player_layer.get_child_count(), " ai1_nodes=", ai1_layer.get_child_count(), " ai2_nodes=", ai2_layer.get_child_count())'
if ready_marker in text:
    text = text.replace(ready_marker, ready_marker + '\n\tprint("RAMI_V018: card_touch=true live_joker_detection=true detect_during_draw=true")', 1)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V018: card touch restored + live Joker wildcard detection')
