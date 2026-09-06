from pathlib import Path

# -----------------------------------------------------------------------------
# Project configuration: isolated RAMI Supabase endpoints.
# -----------------------------------------------------------------------------
project_path = Path('project.godot')
project = project_path.read_text(encoding='utf-8')
project = project.replace('server_url=""', 'server_url="https://ukuiymqlfldglsowqjcn.supabase.co/functions/v1/rami-api"', 1)
if 'google_auth_url=' not in project:
    project = project.replace(
        'server_url="https://ukuiymqlfldglsowqjcn.supabase.co/functions/v1/rami-api"',
        'server_url="https://ukuiymqlfldglsowqjcn.supabase.co/functions/v1/rami-api"\ngoogle_auth_url="https://ukuiymqlfldglsowqjcn.supabase.co/functions/v1/rami-google"',
        1,
    )
project_path.write_text(project, encoding='utf-8')

# -----------------------------------------------------------------------------
# Home screen: Google login/account button and status.
# Runs after v026/v027, therefore MULTI JOUEURS already exists and is active.
# -----------------------------------------------------------------------------
main_path = Path('Main.gd')
main = main_path.read_text(encoding='utf-8')

# Add state fields after constants.
anchor = 'const MUTED := Color("#CFC8B8")\n'
assert anchor in main, 'Main constants anchor missing'
main = main.replace(anchor, anchor + '''\nvar google_button: Button\nvar auth_status: Label\n''', 1)

# Hook auth signals from ready.
old_ready = '''func _ready() -> void:\n\t_build_background()\n\t_build_menu()'''
assert old_ready in main, 'Main ready block missing'
new_ready = '''func _ready() -> void:\n\t_build_background()\n\t_build_menu()\n\tRamiNetwork.auth_changed.connect(_on_auth_changed)\n\tRamiNetwork.auth_progress.connect(_on_auth_progress)\n\tRamiNetwork.auth_failed.connect(_on_auth_failed)\n\t_refresh_google_ui()'''
main = main.replace(old_ready, new_ready, 1)

# Inject login UI just after version label is added to center.
needle = '''\tversion.add_theme_color_override("font_color", Color(0.85, 0.85, 0.80, 0.85))\n\tcenter.add_child(version)'''
assert needle in main, 'Main version block missing'
inject = needle + '''\n\n\tgoogle_button = Button.new()\n\tgoogle_button.text = "SE CONNECTER AVEC GOOGLE"\n\tgoogle_button.set_anchors_preset(Control.PRESET_TOP_RIGHT)\n\tgoogle_button.position = Vector2(-410, 18)\n\tgoogle_button.size = Vector2(380, 52)\n\tgoogle_button.add_theme_font_size_override("font_size", 18)\n\tgoogle_button.add_theme_color_override("font_color", TEXT)\n\tgoogle_button.add_theme_stylebox_override("normal", _button_style(Color("#17343A"), Color("#6FA7B2"), 2))\n\tgoogle_button.add_theme_stylebox_override("hover", _button_style(Color("#20515A"), Color("#9ED5DF"), 3))\n\tgoogle_button.add_theme_stylebox_override("pressed", _button_style(Color("#102B31"), Color("#C7F0F5"), 3))\n\tgoogle_button.pressed.connect(_on_google_pressed)\n\tadd_child(google_button)\n\n\tauth_status = Label.new()\n\tauth_status.set_anchors_preset(Control.PRESET_TOP_RIGHT)\n\tauth_status.position = Vector2(-520, 74)\n\tauth_status.size = Vector2(490, 34)\n\tauth_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT\n\tauth_status.add_theme_font_size_override("font_size", 16)\n\tauth_status.add_theme_color_override("font_color", Color(0.9,0.9,0.86,0.9))\n\tadd_child(auth_status)'''
main = main.replace(needle, inject, 1)

# Add auth handlers at end.
main += '''\n\nfunc _refresh_google_ui() -> void:\n\tif google_button == null or auth_status == null:\n\t\treturn\n\tif RamiNetwork.is_authenticated():\n\t\tvar name := String(RamiNetwork.account.get("display_name", "Joueur"))\n\t\tvar elo := int(RamiNetwork.account.get("elo", 100))\n\t\tgoogle_button.text = "SE DÉCONNECTER"\n\t\tauth_status.text = "%s  •  %d ELO" % [name, elo]\n\t\tgoogle_button.disabled = false\n\telse:\n\t\tgoogle_button.text = "SE CONNECTER AVEC GOOGLE"\n\t\tauth_status.text = "Compte RAMI requis pour le multijoueur"\n\t\tgoogle_button.disabled = RamiNetwork.is_google_busy()\n\nfunc _on_google_pressed() -> void:\n\tif RamiNetwork.is_authenticated():\n\t\tRamiNetwork.logout()\n\telse:\n\t\tgoogle_button.disabled = true\n\t\tRamiNetwork.begin_google_login()\n\nfunc _on_auth_changed(_account: Dictionary) -> void:\n\t_refresh_google_ui()\n\nfunc _on_auth_progress(message: String) -> void:\n\tif auth_status != null:\n\t\tauth_status.text = message\n\tif google_button != null:\n\t\tgoogle_button.disabled = RamiNetwork.is_google_busy()\n\nfunc _on_auth_failed(message: String) -> void:\n\tif auth_status != null:\n\t\tauth_status.text = message\n\tif google_button != null:\n\t\tgoogle_button.disabled = false\n'''
main_path.write_text(main, encoding='utf-8')

# -----------------------------------------------------------------------------
# Multiplayer: expose Google login directly when unauthenticated.
# -----------------------------------------------------------------------------
mp_path = Path('Multiplayer.gd')
mp = mp_path.read_text(encoding='utf-8')

field_anchor = 'var leave_button: Button\n'
assert field_anchor in mp, 'Multiplayer field anchor missing'
mp = mp.replace(field_anchor, field_anchor + 'var google_button: Button\n', 1)

ready_anchor = '''\tRamiNetwork.auth_changed.connect(_on_auth_changed)\n\tRamiNetwork.request_finished.connect(_on_network_result)'''
assert ready_anchor in mp, 'Multiplayer ready signal anchor missing'
mp = mp.replace(ready_anchor, ready_anchor + '''\n\tRamiNetwork.auth_progress.connect(_on_auth_progress)\n\tRamiNetwork.auth_failed.connect(_on_auth_failed)''', 1)

exit_anchor = '''\tif RamiNetwork.request_finished.is_connected(_on_network_result):\n\t\tRamiNetwork.request_finished.disconnect(_on_network_result)'''
assert exit_anchor in mp, 'Multiplayer exit anchor missing'
mp = mp.replace(exit_anchor, exit_anchor + '''\n\tif RamiNetwork.auth_progress.is_connected(_on_auth_progress):\n\t\tRamiNetwork.auth_progress.disconnect(_on_auth_progress)\n\tif RamiNetwork.auth_failed.is_connected(_on_auth_failed):\n\t\tRamiNetwork.auth_failed.disconnect(_on_auth_failed)''', 1)

ui_anchor = '''\tstatus_label = _label("", Vector2(50, 590), Vector2(510, 44), 18, GOLD, left)'''
assert ui_anchor in mp, 'Multiplayer status label anchor missing'
mp = mp.replace(ui_anchor, ui_anchor + '''\n\tgoogle_button = _button_in("SE CONNECTER AVEC GOOGLE", Vector2(50, 535), Vector2(510, 50), 18, Color("#17343A"), Color("#6FA7B2"), left)\n\tgoogle_button.pressed.connect(_on_google_pressed)''', 1)

# Account refresh: show/hide login button.
old_auth = '''\t\tstatus_label.text = "Prêt. Choisissez 2, 3 ou 4 joueurs."\n\telse:\n\t\taccount_label.text = "Non connecté • ELO 100 à la création du compte"\n\t\tsearch_button.disabled = true\n\t\tcreate_button.disabled = true\n\t\tif not RamiNetwork.is_server_configured():\n\t\t\tstatus_label.text = "Serveur RAMI isolé prêt côté code — déploiement à configurer."\n\t\telse:\n\t\t\tstatus_label.text = "Connexion Google requise."'''
assert old_auth in mp, 'Multiplayer auth block missing'
new_auth = '''\t\tstatus_label.text = "Prêt. Choisissez 2, 3 ou 4 joueurs."\n\t\tgoogle_button.visible = false\n\telse:\n\t\taccount_label.text = "Non connecté • ELO 100 à la création du compte"\n\t\tsearch_button.disabled = true\n\t\tcreate_button.disabled = true\n\t\tgoogle_button.visible = true\n\t\tgoogle_button.disabled = RamiNetwork.is_google_busy()\n\t\tif not RamiNetwork.is_server_configured():\n\t\t\tstatus_label.text = "Serveur RAMI non configuré."\n\t\telse:\n\t\t\tstatus_label.text = "Connexion Google requise."'''
mp = mp.replace(old_auth, new_auth, 1)

mp += '''\n\nfunc _on_google_pressed() -> void:\n\tif RamiNetwork.is_authenticated():\n\t\tRamiNetwork.logout()\n\telse:\n\t\tgoogle_button.disabled = true\n\t\tRamiNetwork.begin_google_login()\n\nfunc _on_auth_progress(message: String) -> void:\n\tstatus_label.text = message\n\tif google_button != null:\n\t\tgoogle_button.disabled = RamiNetwork.is_google_busy()\n\nfunc _on_auth_failed(message: String) -> void:\n\tstatus_label.text = message\n\tif google_button != null:\n\t\tgoogle_button.disabled = false\n'''
mp_path.write_text(mp, encoding='utf-8')

# -----------------------------------------------------------------------------
# Marker and version bump.
# -----------------------------------------------------------------------------
game_path = Path('GameTable.gd')
game = game_path.read_text(encoding='utf-8')
marker = 'print("RAMI_V027: isolated_auth=true elo=100 elo_k=32 multiplayer_2_3_4=true")'
assert marker in game, 'v027 marker missing'
game = game.replace(marker, marker + '\n\tprint("RAMI_V028: supabase_online=true google_native=true nonce_bound=true")', 1)
game_path.write_text(game, encoding='utf-8')

preset = Path('export_presets.cfg')
p = preset.read_text(encoding='utf-8')
p = p.replace('export_path="Rami_v0.0.27.apk"', 'export_path="Rami_v0.0.28.apk"')
p = p.replace('version/code=29', 'version/code=30')
p = p.replace('version/name="0.0.27"', 'version/name="0.0.28"')
p = p.replace('gradle_build/use_gradle_build=false', 'gradle_build/use_gradle_build=true')
preset.write_text(p, encoding='utf-8')

print('RAMI_PATCH_V028: Supabase online + native Google login + nonce-bound auth')
