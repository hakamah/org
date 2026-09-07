from pathlib import Path

# RAMI v0.0.29 final Google gate + sanitized auth diagnostics.
# This patch runs after v028 and stays strictly inside the RAMI project.

main_path = Path('Main.gd')
main = main_path.read_text(encoding='utf-8')

# Gate fields.
field_anchor = 'var auth_status: Label\n'
assert field_anchor in main, 'Main auth fields anchor missing'
main = main.replace(field_anchor, field_anchor + '''var auth_gate: Control\nvar auth_gate_button: Button\nvar auth_gate_status: Label\n''', 1)

# Build gate after menu/auth signals are ready.
ready_anchor = '\t_refresh_google_ui()\n'
assert ready_anchor in main, 'Main ready auth refresh missing'
main = main.replace(ready_anchor, ready_anchor + '\t_build_auth_gate()\n\t_refresh_auth_gate()\n', 1)

# Keep the existing home UI but cover it completely until RAMI auth succeeds.
insert_before = '\nfunc _refresh_google_ui() -> void:\n'
assert insert_before in main, 'Main refresh function missing'
gate_code = r'''
func _build_auth_gate() -> void:
	auth_gate = Control.new()
	auth_gate.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	auth_gate.mouse_filter = Control.MOUSE_FILTER_STOP
	auth_gate.z_index = 1000
	add_child(auth_gate)

	var shade := ColorRect.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.025, 0.035, 0.045, 0.98)
	shade.mouse_filter = Control.MOUSE_FILTER_STOP
	auth_gate.add_child(shade)

	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.position = Vector2(-360, -245)
	panel.size = Vector2(720, 490)
	panel.add_theme_stylebox_override("panel", _button_style(Color("#111C20"), Color("#7EAAB2"), 3))
	auth_gate.add_child(panel)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 22)
	panel.add_child(box)

	var spacer_top := Control.new()
	spacer_top.custom_minimum_size = Vector2(1, 26)
	box.add_child(spacer_top)

	var title := Label.new()
	title.text = "RAMI"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 46)
	title.add_theme_color_override("font_color", TEXT)
	box.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "CONNEXION AU COMPTE"
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.add_theme_font_size_override("font_size", 23)
	subtitle.add_theme_color_override("font_color", Color("#BFD5D9"))
	box.add_child(subtitle)

	var info := Label.new()
	info.text = "Choisissez votre compte Google pour accéder à RAMI."
	info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_theme_font_size_override("font_size", 18)
	info.add_theme_color_override("font_color", Color(0.88, 0.88, 0.84, 0.92))
	box.add_child(info)

	auth_gate_button = Button.new()
	auth_gate_button.text = "SE CONNECTER AVEC GOOGLE"
	auth_gate_button.custom_minimum_size = Vector2(580, 68)
	auth_gate_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	auth_gate_button.add_theme_font_size_override("font_size", 21)
	auth_gate_button.add_theme_color_override("font_color", TEXT)
	auth_gate_button.add_theme_stylebox_override("normal", _button_style(Color("#17343A"), Color("#7FB6C0"), 3))
	auth_gate_button.add_theme_stylebox_override("hover", _button_style(Color("#20515A"), Color("#B6E4EC"), 3))
	auth_gate_button.add_theme_stylebox_override("pressed", _button_style(Color("#102B31"), Color("#D4F5F8"), 3))
	auth_gate_button.pressed.connect(_on_gate_google_pressed)
	box.add_child(auth_gate_button)

	auth_gate_status = Label.new()
	auth_gate_status.text = "Prêt pour la connexion Google."
	auth_gate_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	auth_gate_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	auth_gate_status.custom_minimum_size = Vector2(620, 55)
	auth_gate_status.add_theme_font_size_override("font_size", 17)
	auth_gate_status.add_theme_color_override("font_color", Color(0.92, 0.92, 0.88, 0.95))
	box.add_child(auth_gate_status)

	var privacy := Label.new()
	privacy.text = "RAMI ne journalise ni mot de passe ni jeton Google."
	privacy.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	privacy.add_theme_font_size_override("font_size", 14)
	privacy.add_theme_color_override("font_color", Color(0.72, 0.76, 0.76, 0.8))
	box.add_child(privacy)

func _refresh_auth_gate() -> void:
	if auth_gate == null:
		return
	var connected := RamiNetwork.is_authenticated()
	auth_gate.visible = not connected
	if auth_gate_button != null:
		auth_gate_button.disabled = RamiNetwork.is_google_busy()
	if connected and auth_gate_status != null:
		auth_gate_status.text = "Connexion réussie."

func _on_gate_google_pressed() -> void:
	if RamiNetwork.is_authenticated():
		_refresh_auth_gate()
		return
	if auth_gate_button != null:
		auth_gate_button.disabled = true
	RamiNetwork.begin_google_login()

'''
main = main.replace(insert_before, '\n' + gate_code + 'func _refresh_google_ui() -> void:\n', 1)

# Existing auth callbacks now keep the gate in sync.
old_changed = '''func _on_auth_changed(_account: Dictionary) -> void:\n\t_refresh_google_ui()'''
assert old_changed in main, 'Main auth changed callback missing'
main = main.replace(old_changed, old_changed + '\n\t_refresh_auth_gate()', 1)

old_progress = '''func _on_auth_progress(message: String) -> void:\n\tif auth_status != null:\n\t\tauth_status.text = message'''
assert old_progress in main, 'Main auth progress callback missing'
main = main.replace(old_progress, old_progress + '''\n\tif auth_gate_status != null:\n\t\tauth_gate_status.text = message\n\tif auth_gate_button != null:\n\t\tauth_gate_button.disabled = RamiNetwork.is_google_busy()''', 1)

old_failed = '''func _on_auth_failed(message: String) -> void:\n\tif auth_status != null:\n\t\tauth_status.text = message'''
assert old_failed in main, 'Main auth failed callback missing'
main = main.replace(old_failed, old_failed + '''\n\tif auth_gate_status != null:\n\t\tauth_gate_status.text = message\n\tif auth_gate_button != null:\n\t\tauth_gate_button.disabled = false''', 1)

main_path.write_text(main, encoding='utf-8')

# Sanitized auth logs in user://logrami/google_auth.log. Never write Google ID tokens,
# RAMI session tokens, e-mail addresses or client secrets.
net_path = Path('RamiNetwork.gd')
net = net_path.read_text(encoding='utf-8')

ready_anchor = '''\t_http.request_completed.connect(_on_request_completed)\n\t_load_token()'''
assert ready_anchor in net, 'RamiNetwork ready anchor missing'
net = net.replace(ready_anchor, '''\t_http.request_completed.connect(_on_request_completed)\n\tauth_progress.connect(_on_logrami_progress)\n\tauth_failed.connect(_on_logrami_failed)\n\tauth_changed.connect(_on_logrami_changed)\n\t_logrami("BOOT", "RamiNetwork ready")\n\t_load_token()''', 1)

login_anchor = '''func begin_google_login() -> void:\n\tif _google_busy:'''
assert login_anchor in net, 'RamiNetwork login anchor missing'
net = net.replace(login_anchor, '''func begin_google_login() -> void:\n\t_logrami("GOOGLE_START", "begin requested")\n\tif _google_busy:''', 1)

net += r'''

func _logrami(event_name: String, detail: String) -> void:
	var dir_path := ProjectSettings.globalize_path("user://logrami")
	DirAccess.make_dir_recursive_absolute(dir_path)
	var file_path := dir_path.path_join("google_auth.log")
	var f := FileAccess.open(file_path, FileAccess.READ_WRITE)
	if f == null:
		f = FileAccess.open(file_path, FileAccess.WRITE)
	if f == null:
		return
	f.seek_end()
	var stamp := Time.get_datetime_string_from_system(false, true)
	var safe_detail := detail.replace("\n", " ").replace("\r", " ")
	if safe_detail.length() > 300:
		safe_detail = safe_detail.left(300)
	f.store_line("%s | %s | %s" % [stamp, event_name, safe_detail])

func _on_logrami_progress(message: String) -> void:
	_logrami("AUTH_PROGRESS", message)

func _on_logrami_failed(message: String) -> void:
	_logrami("AUTH_FAILED", message)

func _on_logrami_changed(new_account: Dictionary) -> void:
	_logrami("AUTH_CHANGED", "authenticated=%s" % str(not new_account.is_empty()))
'''
net_path.write_text(net, encoding='utf-8')

# Version bump for the final auth-gated build.
preset_path = Path('export_presets.cfg')
preset = preset_path.read_text(encoding='utf-8')
preset = preset.replace('export_path="Rami_v0.0.28.apk"', 'export_path="Rami_v0.0.29.apk"')
preset = preset.replace('version/code=30', 'version/code=31')
preset = preset.replace('version/name="0.0.28"', 'version/name="0.0.29"')
preset_path.write_text(preset, encoding='utf-8')

# Runtime marker.
game_path = Path('GameTable.gd')
game = game_path.read_text(encoding='utf-8')
marker = 'print("RAMI_V028: supabase_online=true google_native=true nonce_bound=true")'
assert marker in game, 'RAMI v028 marker missing'
game = game.replace(marker, marker + '\n\tprint("RAMI_V029: prehome_google_gate=true logrami=true final_auth=true")', 1)
game_path.write_text(game, encoding='utf-8')

print('RAMI_PATCH_V029: pre-home Google gate + sanitized logrami + v0.0.29')
