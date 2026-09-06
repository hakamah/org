from pathlib import Path

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

old = '''\tif game.winner_index >= 0:\n\t\tturn_label.text = "MANCHE TERMINÉE"\n\t\tdiscard_button.disabled = true\n\t\ttable_button.disabled = true\n\t\t_show_game_over()\n\telif game.phase == RamiGame.Phase.DRAW:\n\t\tturn_label.text = "À VOUS • PIOCHE OBLIGATOIRE"\n\t\tdiscard_button.disabled = true\n\t\ttable_button.disabled = true\n\telse:\n\t\tturn_label.text = "À VOUS • JOUEZ PUIS DÉFAUSSEZ"\n\t\tdiscard_button.disabled = selected_indices.size() != 1\n\t\ttable_button.disabled = selected_indices.size() < 3 and selected_detected_combo < 0'''

new = '''\tif game.winner_index >= 0:\n\t\tturn_label.text = "MANCHE TERMINÉE"\n\t\tif is_instance_valid(discard_button):\n\t\t\tdiscard_button.disabled = true\n\t\tif is_instance_valid(table_button):\n\t\t\ttable_button.disabled = true\n\t\t_show_game_over()\n\telif game.phase == RamiGame.Phase.DRAW:\n\t\tturn_label.text = "À VOUS • PIOCHE OBLIGATOIRE"\n\t\tif is_instance_valid(discard_button):\n\t\t\tdiscard_button.disabled = true\n\t\tif is_instance_valid(table_button):\n\t\t\ttable_button.disabled = true\n\telse:\n\t\tturn_label.text = "À VOUS • JOUEZ PUIS DÉFAUSSEZ"\n\t\tif is_instance_valid(discard_button):\n\t\t\tdiscard_button.disabled = selected_indices.size() != 1\n\t\tif is_instance_valid(table_button):\n\t\t\ttable_button.disabled = selected_indices.size() < 3 and selected_detected_combo < 0'''

assert old in text, 'v024 legacy button state block not found'
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V024_GUARD: legacy nil controls guarded; no visual change')
