from pathlib import Path

# RAMI v0.0.31 — fix the 2/3/4 player selector visual feedback.
# Root cause: only the Button "normal" StyleBox was changed after selection,
# while the original pressed/focus/hover StyleBoxes stayed blue. On touch this
# made the newly selected value flash light-blue before becoming green.

mp_path = Path('Multiplayer.gd')
mp = mp_path.read_text(encoding='utf-8')

# Apply selection as soon as the finger goes down, not only after release.
old_connect = '\t\tb.pressed.connect(_on_count_pressed.bind(count))\n'
assert old_connect in mp, 'player count pressed connection missing'
mp = mp.replace(old_connect, '\t\tb.button_down.connect(_on_count_pressed.bind(count))\n\t\tb.focus_mode = Control.FOCUS_NONE\n', 1)

old_refresh = '''func _refresh_player_count_buttons() -> void:\n\tfor k in count_buttons.keys():\n\t\tvar b: Button = count_buttons[k]\n\t\tif int(k) == selected_players:\n\t\t\tb.add_theme_stylebox_override("normal", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))\n\t\telse:\n\t\t\tb.add_theme_stylebox_override("normal", _style(Color("#17343A"), Color("#4D7972"), 3, 20))\n'''
assert old_refresh in mp, 'player count refresh function missing'

new_refresh = '''func _refresh_player_count_buttons() -> void:\n\tfor k in count_buttons.keys():\n\t\tvar b: Button = count_buttons[k]\n\t\tvar selected := int(k) == selected_players\n\t\tif selected:\n\t\t\t# Selected value stays green for every touch state.\n\t\t\tb.add_theme_stylebox_override("normal", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))\n\t\t\tb.add_theme_stylebox_override("hover", _style(Color("#376B27"), Color("#A9D84E"), 4, 20))\n\t\t\tb.add_theme_stylebox_override("pressed", _style(Color("#284F1C"), Color("#B6E35B"), 4, 20))\n\t\t\tb.add_theme_stylebox_override("focus", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))\n\t\t\tb.add_theme_stylebox_override("disabled", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))\n\t\telse:\n\t\t\t# Unselected values remain the same dark blue, including while touched.\n\t\t\tb.add_theme_stylebox_override("normal", _style(Color("#17343A"), Color("#4D7972"), 3, 20))\n\t\t\tb.add_theme_stylebox_override("hover", _style(Color("#1B4149"), Color("#5A8C84"), 3, 20))\n\t\t\tb.add_theme_stylebox_override("pressed", _style(Color("#17343A"), Color("#4D7972"), 3, 20))\n\t\t\tb.add_theme_stylebox_override("focus", _style(Color("#17343A"), Color("#4D7972"), 3, 20))\n\t\t\tb.add_theme_stylebox_override("disabled", _style(Color("#17343A"), Color("#4D7972"), 3, 20))\n'''
mp = mp.replace(old_refresh, new_refresh, 1)

mp = mp.replace('RAMI v0.0.30 • SALONS : REJOINDRE / QUITTER / FERMER', 'RAMI v0.0.31 • SÉLECTEUR JOUEURS CORRIGÉ')
mp_path.write_text(mp, encoding='utf-8')

preset_path = Path('export_presets.cfg')
preset = preset_path.read_text(encoding='utf-8')
preset = preset.replace('export_path="Rami_v0.0.30.apk"', 'export_path="Rami_v0.0.31.apk"')
preset = preset.replace('version/code=32', 'version/code=33')
preset = preset.replace('version/name="0.0.30"', 'version/name="0.0.31"')
preset_path.write_text(preset, encoding='utf-8')

game_path = Path('GameTable.gd')
game = game_path.read_text(encoding='utf-8')
marker = 'print("RAMI_V030: room_join=true room_leave=true owner_close=true")'
assert marker in game, 'v030 marker missing'
game = game.replace(marker, marker + '\n\tprint("RAMI_V031: player_count_touch_states_fixed=true")', 1)
game_path.write_text(game, encoding='utf-8')

print('RAMI_PATCH_V031: 2/3/4 selection stays green immediately on touch')
