from pathlib import Path

# RAMI v0.0.33 — fix the 2/3/4 selector for real touch/click behaviour.
# v0.0.32 introduced toggle_mode/ButtonGroup, which made the controls behave
# incorrectly on the target Android device. Return to ordinary buttons:
#   - a normal press is the only input path,
#   - the pressed choice becomes persistently PURPLE,
#   - the previous choice returns to dark blue,
#   - buttons remain clickable even while a room is active (the choice is for
#     the next search/create action and does not mutate the existing room),
#   - only an actual network busy state temporarily disables the selector.

mp_path = Path('Multiplayer.gd')
mp = mp_path.read_text(encoding='utf-8')

# Remove v032's shared ButtonGroup field.
mp = mp.replace('var count_button_group: ButtonGroup = ButtonGroup.new()\n', '', 1)

old_loop_tail = '''\t\tb.toggle_mode = true\n\t\tb.button_group = count_button_group\n\t\tb.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS\n\t\tb.focus_mode = Control.FOCUS_NONE\n\t\tb.toggled.connect(_on_count_toggled.bind(count))\n\t\tcount_buttons[count] = b\n'''
assert old_loop_tail in mp, 'v032 toggle connection block missing'
new_loop_tail = '''\t\tb.toggle_mode = false\n\t\tb.focus_mode = Control.FOCUS_NONE\n\t\tb.pressed.connect(_on_count_pressed.bind(count))\n\t\tcount_buttons[count] = b\n'''
mp = mp.replace(old_loop_tail, new_loop_tail, 1)

old_handler = '''func _on_count_toggled(pressed: bool, value: int) -> void:\n\tif not pressed:\n\t\treturn\n\tif current_room_id >= 0:\n\t\t# A room already has a fixed player count. Restore the real selection.\n\t\t_refresh_player_count_buttons()\n\t\treturn\n\tselected_players = value\n\t_refresh_player_count_buttons()\n\n'''
assert old_handler in mp, 'v032 toggle handler missing'
new_handler = '''func _on_count_pressed(value: int) -> void:\n\tselected_players = clampi(value, 2, 4)\n\t_refresh_player_count_buttons()\n\n'''
mp = mp.replace(old_handler, new_handler, 1)

start = mp.index('func _refresh_player_count_buttons() -> void:\n')
end = mp.index('\nfunc _refresh_account() -> void:\n', start)
new_refresh = '''func _refresh_player_count_buttons() -> void:\n\tfor k in count_buttons.keys():\n\t\tvar b: Button = count_buttons[k]\n\t\tvar selected := int(k) == selected_players\n\t\tvar bg := Color("#6A3FA0") if selected else Color("#17343A")\n\t\tvar border := Color("#C49BFF") if selected else Color("#4D7972")\n\t\tvar width := 4 if selected else 3\n\n\t\t# Every visual state uses the persistent selection colour. This prevents\n\t\t# Android hover/press/focus feedback from replacing purple with light blue.\n\t\tb.add_theme_stylebox_override("normal", _style(bg, border, width, 20))\n\t\tb.add_theme_stylebox_override("hover", _style(bg, border, width, 20))\n\t\tb.add_theme_stylebox_override("pressed", _style(bg, border, width, 20))\n\t\tb.add_theme_stylebox_override("focus", _style(bg, border, width, 20))\n\t\tb.add_theme_stylebox_override("disabled", _style(bg, border, width, 20))\n'''
mp = mp[:start] + new_refresh + mp[end:]

# Keep selector clickable whenever the UI is not in a real network request.
mp = mp.replace('b.disabled = value or current_room_id >= 0', 'b.disabled = value', 1)

mp = mp.replace('RAMI v0.0.32 • SÉLECTEUR 2/3/4 TOGGLE RÉEL', 'RAMI v0.0.33 • SÉLECTEUR 2/3/4 VIOLET CLIQUABLE')
mp_path.write_text(mp, encoding='utf-8')

preset_path = Path('export_presets.cfg')
preset = preset_path.read_text(encoding='utf-8')
preset = preset.replace('export_path="Rami_v0.0.32.apk"', 'export_path="Rami_v0.0.33.apk"')
preset = preset.replace('version/code=34', 'version/code=35')
preset = preset.replace('version/name="0.0.32"', 'version/name="0.0.33"')
preset_path.write_text(preset, encoding='utf-8')

game_path = Path('GameTable.gd')
game = game_path.read_text(encoding='utf-8')
marker = 'print("RAMI_V032: player_count_real_toggle_group=true")'
assert marker in game, 'v032 marker missing'
game = game.replace(marker, marker + '\n\tprint("RAMI_V033: player_count_purple_click_selector=true")', 1)
game_path.write_text(game, encoding='utf-8')

# Add a real scene-level regression test. It emits each Button's actual pressed
# signal (not a direct handler call), checks that the value changes, checks that
# the selector remains enabled with an active room, and checks purple/blue state.
test_gd = Path('tests/TestMultiplayerSelector.gd')
test_gd.write_text(r'''extends Node

const PURPLE := Color("#6A3FA0")
const BLUE_DARK := Color("#17343A")

func _ready() -> void:
    var scene := load("res://Multiplayer.tscn")
    assert(scene != null)
    var ui = scene.instantiate()
    add_child(ui)
    await get_tree().process_frame

    assert(ui.count_buttons.size() == 3)
    assert(ui.selected_players == 3)

    _press_and_check(ui, 2, 3)
    _press_and_check(ui, 4, 2)
    _press_and_check(ui, 3, 4)

    # An existing room must not make the selector unclickable anymore.
    ui.current_room_id = 999
    ui._set_busy(false)
    for b in ui.count_buttons.values():
        assert(not b.disabled)
    _press_and_check(ui, 2, 3)

    print("RAMI_SELECTOR_TESTS: PASS")
    get_tree().quit(0)

func _press_and_check(ui, value: int, previous: int) -> void:
    var b: Button = ui.count_buttons[value]
    assert(not b.disabled)
    b.emit_signal("pressed")
    assert(ui.selected_players == value)
    var selected_box = b.get_theme_stylebox("normal")
    assert(selected_box is StyleBoxFlat)
    assert((selected_box as StyleBoxFlat).bg_color.is_equal_approx(PURPLE))
    var old_b: Button = ui.count_buttons[previous]
    var old_box = old_b.get_theme_stylebox("normal")
    assert(old_box is StyleBoxFlat)
    assert((old_box as StyleBoxFlat).bg_color.is_equal_approx(BLUE_DARK))
''', encoding='utf-8')

Path('tests/TestMultiplayerSelector.tscn').write_text('''[gd_scene load_steps=2 format=3]\n\n[ext_resource path="res://tests/TestMultiplayerSelector.gd" type="Script" id="1"]\n\n[node name="TestMultiplayerSelector" type="Node"]\nscript = ExtResource("1")\n''', encoding='utf-8')

print('RAMI_PATCH_V033: ordinary clickable buttons + persistent purple selection')
