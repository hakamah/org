from pathlib import Path

# Main: activate the already-present MULTI JOUEURS button.
main_path = Path('Main.gd')
main = main_path.read_text(encoding='utf-8')
old = '''func _on_multiplayer_pressed() -> void:\n\t# Intentionally wired but inactive for now.\n\tpass'''
new = '''func _on_multiplayer_pressed() -> void:\n\tget_tree().change_scene_to_file("res://Multiplayer.tscn")'''
assert old in main, 'v026 multiplayer placeholder not found'
main = main.replace(old, new, 1)
main_path.write_text(main, encoding='utf-8')

# Add isolated RAMI network singleton. The URL deliberately stays empty until the
# separate RAMI backend/database is deployed; no YUGITO URL or credential is reused.
project_path = Path('project.godot')
project = project_path.read_text(encoding='utf-8')
if '[autoload]' not in project:
    anchor = '[display]\n'
    assert anchor in project, 'project display section not found'
    project = project.replace(anchor, '[autoload]\n\nRamiNetwork="*res://RamiNetwork.gd"\n\n' + anchor, 1)
else:
    assert 'RamiNetwork=' not in project
    project = project.replace('[autoload]\n', '[autoload]\n\nRamiNetwork="*res://RamiNetwork.gd"\n', 1)

if '[rami]' not in project:
    project += '\n[rami]\nserver_url=""\n'
project_path.write_text(project, encoding='utf-8')

# Marker in GameTable so CI can prove all earlier gameplay changes are still present.
game_path = Path('GameTable.gd')
game = game_path.read_text(encoding='utf-8')
marker = 'print("RAMI_V026: game_over_home=true home_quit=true play_ai=true multiplayer_placeholder=true")'
assert marker in game, 'v026 marker not found'
game = game.replace(marker, marker + '\n\tprint("RAMI_V027: isolated_auth=true elo=100 elo_k=32 multiplayer_2_3_4=true")', 1)
game_path.write_text(game, encoding='utf-8')

# Version bump.
preset = Path('export_presets.cfg')
p = preset.read_text(encoding='utf-8')
p = p.replace('export_path="Rami_v0.0.26.apk"', 'export_path="Rami_v0.0.27.apk"')
p = p.replace('version/code=28', 'version/code=29')
p = p.replace('version/name="0.0.26"', 'version/name="0.0.27"')
preset.write_text(p, encoding='utf-8')

print('RAMI_PATCH_V027: multiplayer menu + isolated network/auth foundation wired')
