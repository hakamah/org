from pathlib import Path

# RAMI v0.0.32 — the 2/3/4 selector must behave like a real radio selector.
# v0.0.31 only repainted transient Button states. This patch gives the three
# controls persistent toggle state through a shared ButtonGroup:
#   - exactly one choice is selected,
#   - selected = green,
#   - the previous choice immediately returns to dark blue,
#   - touching a new choice never shows the old light-blue pressed feedback.

mp_path = Path('Multiplayer.gd')
mp = mp_path.read_text(encoding='utf-8')

# Shared mutually-exclusive group.
field_anchor = 'var count_buttons: Dictionary = {}\n'
assert field_anchor in mp, 'count_buttons field missing'
mp = mp.replace(field_anchor, field_anchor + 'var count_button_group: ButtonGroup = ButtonGroup.new()\n', 1)

# v031 changed the original connection to button_down. Replace that block with
# true toggle buttons using the same ButtonGroup.
old_loop_tail = '''\t\tb.button_down.connect(_on_count_pressed.bind(count))\n\t\tb.focus_mode = Control.FOCUS_NONE\n\t\tcount_buttons[count] = b\n'''
assert old_loop_tail in mp, 'v031 count-button connection block missing'
new_loop_tail = '''\t\tb.toggle_mode = true\n\t\tb.button_group = count_button_group\n\t\tb.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS\n\t\tb.focus_mode = Control.FOCUS_NONE\n\t\tb.toggled.connect(_on_count_toggled.bind(count))\n\t\tcount_buttons[count] = b\n'''
mp = mp.replace(old_loop_tail, new_loop_tail, 1)

# Replace the old momentary handler with a persistent toggle handler.
old_handler = '''func _on_count_pressed(value: int) -> void:\n\tif current_room_id >= 0:\n\t\treturn\n\tselected_players = value\n\t_refresh_player_count_buttons()\n\n'''
assert old_handler in mp, 'old count handler missing'
new_handler = '''func _on_count_toggled(pressed: bool, value: int) -> void:\n\tif not pressed:\n\t\treturn\n\tif current_room_id >= 0:\n\t\t# A room already has a fixed player count. Restore the real selection.\n\t\t_refresh_player_count_buttons()\n\t\treturn\n\tselected_players = value\n\t_refresh_player_count_buttons()\n\n'''
mp = mp.replace(old_handler, new_handler, 1)

# Replace v031's manual colour swapping with one semantic rule:
# normal/unselected = blue, pressed/selected = green. button_pressed is the
# single source of truth and ButtonGroup clears the previous button for us.
start = mp.index('func _refresh_player_count_buttons() -> void:\n')
end = mp.index('\nfunc _refresh_account() -> void:\n', start)
old_refresh = mp[start:end]
new_refresh = '''func _refresh_player_count_buttons() -> void:\n\tfor k in count_buttons.keys():\n\t\tvar b: Button = count_buttons[k]\n\t\tvar selected := int(k) == selected_players\n\n\t\t# Persistent state: exactly the selected value is button_pressed.\n\t\tif b.button_pressed != selected:\n\t\t\tb.set_pressed_no_signal(selected)\n\n\t\t# Unselected state = dark blue.\n\t\tb.add_theme_stylebox_override("normal", _style(Color("#17343A"), Color("#4D7972"), 3, 20))\n\t\tb.add_theme_stylebox_override("hover", _style(Color("#17343A"), Color("#4D7972"), 3, 20))\n\n\t\t# Selected / finger-down state = green. Because this is the persistent\n\t\t# pressed style of a toggle button, the newly chosen value remains green.\n\t\tb.add_theme_stylebox_override("pressed", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))\n\t\tb.add_theme_stylebox_override("focus", _style(Color("#17343A"), Color("#4D7972"), 3, 20))\n\n\t\t# While a room is active the selector is disabled, but its selected value\n\t\t# must still remain visually green instead of losing its state.\n\t\tif selected:\n\t\t\tb.add_theme_stylebox_override("disabled", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))\n\t\telse:\n\t\t\tb.add_theme_stylebox_override("disabled", _style(Color("#17343A"), Color("#4D7972"), 3, 20))\n'''
mp = mp[:start] + new_refresh + mp[end:]

# Footer/version marker.
mp = mp.replace('RAMI v0.0.31 • SÉLECTEUR JOUEURS CORRIGÉ', 'RAMI v0.0.32 • SÉLECTEUR 2/3/4 TOGGLE RÉEL')
mp_path.write_text(mp, encoding='utf-8')

preset_path = Path('export_presets.cfg')
preset = preset_path.read_text(encoding='utf-8')
preset = preset.replace('export_path="Rami_v0.0.31.apk"', 'export_path="Rami_v0.0.32.apk"')
preset = preset.replace('version/code=33', 'version/code=34')
preset = preset.replace('version/name="0.0.31"', 'version/name="0.0.32"')
preset_path.write_text(preset, encoding='utf-8')

game_path = Path('GameTable.gd')
game = game_path.read_text(encoding='utf-8')
marker = 'print("RAMI_V031: player_count_touch_states_fixed=true")'
assert marker in game, 'v031 marker missing'
game = game.replace(marker, marker + '\n\tprint("RAMI_V032: player_count_real_toggle_group=true")', 1)
game_path.write_text(game, encoding='utf-8')

print('RAMI_PATCH_V032: 2/3/4 are persistent mutually-exclusive toggle buttons')
