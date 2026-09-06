from pathlib import Path
import re

# -----------------------------------------------------------------------------
# Main menu
# -----------------------------------------------------------------------------
main_path = Path('Main.gd')
main = main_path.read_text(encoding='utf-8')

main = main.replace('play.text = "▶   JOUER"', 'play.text = "▶   JOUER IA"', 1)

needle = '''\tplay.pressed.connect(_on_play_pressed)\n\tcenter.add_child(play)\n\n\tvar version := Label.new()'''
assert needle in main, 'Main play block not found'
replacement = '''\tplay.pressed.connect(_on_play_pressed)\n\tcenter.add_child(play)\n\n\tvar multiplayer := Button.new()\n\tmultiplayer.text = "MULTI JOUEURS"\n\tmultiplayer.custom_minimum_size = Vector2(540, 82)\n\tmultiplayer.add_theme_font_size_override("font_size", 30)\n\tmultiplayer.add_theme_color_override("font_color", TEXT)\n\tmultiplayer.add_theme_color_override("font_hover_color", Color.WHITE)\n\tmultiplayer.add_theme_stylebox_override("normal", _button_style(Color("#183B4A"), Color("#4B8FA8"), 3))\n\tmultiplayer.add_theme_stylebox_override("hover", _button_style(Color("#205166"), Color("#71BAD4"), 4))\n\tmultiplayer.add_theme_stylebox_override("pressed", _button_style(Color("#12313E"), Color("#9CD7E9"), 4))\n\tmultiplayer.pressed.connect(_on_multiplayer_pressed)\n\tcenter.add_child(multiplayer)\n\n\tvar version := Label.new()'''
main = main.replace(needle, replacement, 1)

# Add compact Quit button anchored bottom-right, outside the central layout.
needle = '''\tversion.add_theme_color_override("font_color", Color(0.85, 0.85, 0.80, 0.85))\n\tcenter.add_child(version)\n'''
assert needle in main, 'Main version block not found'
replacement = needle + '''\n\tvar quit := Button.new()\n\tquit.text = "QUITTER"\n\tquit.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)\n\tquit.position = Vector2(-190, -58)\n\tquit.size = Vector2(170, 42)\n\tquit.add_theme_font_size_override("font_size", 17)\n\tquit.add_theme_color_override("font_color", TEXT)\n\tquit.add_theme_stylebox_override("normal", _button_style(Color("#5A1C1C"), Color("#D45A5A"), 2))\n\tquit.add_theme_stylebox_override("hover", _button_style(Color("#762626"), Color("#F07A7A"), 3))\n\tquit.add_theme_stylebox_override("pressed", _button_style(Color("#441313"), Color("#FF9B9B"), 3))\n\tquit.pressed.connect(_on_quit_pressed)\n\tadd_child(quit)\n'''
main = main.replace(needle, replacement, 1)

main += '''\nfunc _on_multiplayer_pressed() -> void:\n\t# Intentionally wired but inactive for now.\n\tpass\n\nfunc _on_quit_pressed() -> void:\n\tget_tree().quit()\n'''
main_path.write_text(main, encoding='utf-8')

# -----------------------------------------------------------------------------
# End-game modal: Replay + Return to home, side by side.
# -----------------------------------------------------------------------------
game_path = Path('GameTable.gd')
game = game_path.read_text(encoding='utf-8')

old = '''\tvar replay: Button = _make_button_in("REJOUER", Vector2(165, 410), Vector2(410, 70), 27, Color("#0B5E40"), GREEN, box)\n\treplay.pressed.connect(_on_replay)'''
assert old in game, 'Replay modal block not found'
new = '''\tvar replay: Button = _make_button_in("REJOUER", Vector2(75, 410), Vector2(280, 70), 25, Color("#0B5E40"), GREEN, box)\n\treplay.pressed.connect(_on_replay)\n\tvar home: Button = _make_button_in("RETOUR À L'ACCUEIL", Vector2(385, 410), Vector2(280, 70), 21, Color("#6E1B1B"), Color("#E65A61"), box)\n\thome.pressed.connect(_on_game_over_home)'''
game = game.replace(old, new, 1)

# Add handler near replay handler.
needle = 'func _on_replay() -> void:\n'
assert needle in game, '_on_replay marker not found'
game = game.replace(needle, '''func _on_game_over_home() -> void:\n\tget_tree().change_scene_to_file("res://Main.tscn")\n\n''' + needle, 1)

marker = 'print("RAMI_V025: horizontal_first=true prefer_two_rows=true fold_true_complete=true joker_not_complete=true")'
assert marker in game, 'v025 marker not found'
game = game.replace(marker, marker + '\n\tprint("RAMI_V026: game_over_home=true home_quit=true play_ai=true multiplayer_placeholder=true")', 1)
game_path.write_text(game, encoding='utf-8')

# Version bump
preset = Path('export_presets.cfg')
p = preset.read_text(encoding='utf-8')
p = p.replace('export_path="Rami_v0.0.25.apk"', 'export_path="Rami_v0.0.26.apk"')
p = p.replace('version/code=27', 'version/code=28')
p = p.replace('version/name="0.0.25"', 'version/name="0.0.26"')
preset.write_text(p, encoding='utf-8')

print('RAMI_PATCH_V026: end-game home + quit + play IA + multiplayer placeholder')
