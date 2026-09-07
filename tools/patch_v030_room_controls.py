from pathlib import Path

# RAMI v0.0.30 — explicit room controls.

# --- RamiNetwork -------------------------------------------------------------
net_path = Path('RamiNetwork.gd')
net = net_path.read_text(encoding='utf-8')
anchor = 'func get_room(room_id: int) -> bool:\n'
assert anchor in net, 'RamiNetwork get_room anchor missing'
insert = '''func join_room(room_id: int) -> bool:\n\treturn _request("join_room", HTTPClient.METHOD_POST, "/api/matchmaking/join", {"room_id": room_id}, true)\n\nfunc close_room(room_id: int) -> bool:\n\treturn _request("close_room", HTTPClient.METHOD_POST, "/api/matchmaking/close", {"room_id": room_id}, true)\n\n'''
net = net.replace(anchor, insert + anchor, 1)
net_path.write_text(net, encoding='utf-8')

# --- Multiplayer -------------------------------------------------------------
mp_path = Path('Multiplayer.gd')
mp = mp_path.read_text(encoding='utf-8')

# Fields: v028 adds google_button after leave_button, so anchor only on one line.
field_anchor = 'var leave_button: Button\n'
assert field_anchor in mp, 'leave_button field missing'
mp = mp.replace(field_anchor, '''var join_button: Button\nvar join_room_input: LineEdit\nvar leave_button: Button\nvar close_button: Button\n''', 1)

# Left UI, replace only the create button area and the following descriptive label.
old_create = '''\tcreate_button = _button_in("CRÉER UN SALON", Vector2(50, 390), Vector2(510, 82), 24, Color("#183B4A"), Color("#4B8FA8"), left)\n\tcreate_button.pressed.connect(_on_create)\n'''
assert old_create in mp, 'create button block missing'
new_create = '''\tcreate_button = _button_in("CRÉER UN SALON", Vector2(50, 385), Vector2(510, 72), 23, Color("#183B4A"), Color("#4B8FA8"), left)\n\tcreate_button.pressed.connect(_on_create)\n\n\tjoin_room_input = LineEdit.new()\n\tjoin_room_input.placeholder_text = "ID DU SALON (ex. 123)"\n\tjoin_room_input.position = Vector2(50, 480)\n\tjoin_room_input.size = Vector2(320, 58)\n\tjoin_room_input.add_theme_font_size_override("font_size", 19)\n\tjoin_room_input.add_theme_color_override("font_color", TEXT)\n\tjoin_room_input.add_theme_color_override("font_placeholder_color", Color(0.82,0.82,0.78,0.55))\n\tjoin_room_input.add_theme_stylebox_override("normal", _style(Color("#142D34"), Color("#4D7972"), 3, 16))\n\tleft.add_child(join_room_input)\n\n\tjoin_button = _button_in("REJOINDRE", Vector2(385, 480), Vector2(175, 58), 20, Color("#315E22"), Color("#9CCB43"), left)\n\tjoin_button.pressed.connect(_on_join)\n'''
mp = mp.replace(old_create, new_create, 1)

old_desc = '\t_label("La recherche rejoint automatiquement le salon compatible\\ndont l\'ELO de base est le plus proche du vôtre.", Vector2(55, 505), Vector2(500, 72), 17, MUTED, left)\n'
assert old_desc in mp, 'matchmaking description missing'
mp = mp.replace(old_desc, '\t_label("Recherche automatique ou entrée directe avec l\'ID du salon.", Vector2(55, 548), Vector2(500, 34), 16, MUTED, left)\n', 1)

# Right UI.
old_leave = '''\tleave_button = _button_in("QUITTER LE SALON", Vector2(170, 505), Vector2(430, 76), 22, Color("#6E1B1B"), RED, right)\n\tleave_button.pressed.connect(_on_leave)\n\tleave_button.disabled = true\n'''
assert old_leave in mp, 'leave button block missing'
new_leave = '''\tclose_button = _button_in("FERMER LE SALON", Vector2(85, 500), Vector2(285, 72), 20, Color("#6E1B1B"), RED, right)\n\tclose_button.pressed.connect(_on_close_room)\n\tclose_button.disabled = true\n\tclose_button.visible = false\n\n\tleave_button = _button_in("QUITTER LE SALON", Vector2(400, 500), Vector2(285, 72), 20, Color("#3B3030"), Color("#C98787"), right)\n\tleave_button.pressed.connect(_on_leave)\n\tleave_button.disabled = true\n'''
mp = mp.replace(old_leave, new_leave, 1)

# Join/close handlers before _on_leave.
leave_handler_anchor = 'func _on_leave() -> void:\n'
assert leave_handler_anchor in mp, '_on_leave missing'
handlers = '''func _on_join() -> void:\n\tif current_room_id >= 0:\n\t\treturn\n\tvar raw := join_room_input.text.strip_edges()\n\tif raw.is_empty() or not raw.is_valid_int():\n\t\tstatus_label.text = "Entre un ID de salon valide."\n\t\treturn\n\tvar room_id := int(raw)\n\tif room_id <= 0:\n\t\tstatus_label.text = "ID de salon invalide."\n\t\treturn\n\t_set_busy(true)\n\tstatus_label.text = "Connexion au salon #%d…" % room_id\n\tRamiNetwork.join_room(room_id)\n\nfunc _on_close_room() -> void:\n\tif current_room_id < 0 or close_button == null or not close_button.visible:\n\t\treturn\n\tclose_button.disabled = true\n\tleave_button.disabled = true\n\tstatus_label.text = "Fermeture du salon…"\n\tRamiNetwork.close_room(current_room_id)\n\n'''
mp = mp.replace(leave_handler_anchor, handlers + leave_handler_anchor, 1)

# Result error list.
old_kinds = 'if kind in ["create_room", "search_room", "leave_room"]:'
assert old_kinds in mp, 'error kinds missing'
mp = mp.replace(old_kinds, 'if kind in ["create_room", "search_room", "join_room", "leave_room", "close_room"]:', 1)

# Success path joins create/search path.
old_match = '\t\t"create_room", "search_room":\n'
assert old_match in mp, 'create/search match arm missing'
mp = mp.replace(old_match, '\t\t"create_room", "search_room", "join_room":\n', 1)

# Add close result next to leave result, but keep existing leave implementation.
leave_case_anchor = '\t\t"leave_room":\n'
assert leave_case_anchor in mp, 'leave result arm missing'
# Insert close case before room display function by reusing a compact reset helper later.

# Room polling: if the owner closed it, guests are kicked back to no-room state.
room_show_line = '\t\t\t_show_room(payload.get("room", {}) as Dictionary)\n'
assert room_show_line in mp, 'room poll show line missing'
mp = mp.replace(room_show_line, '''\t\t\tvar polled_room: Dictionary = payload.get("room", {}) as Dictionary\n\t\t\tif String(polled_room.get("status", "open")) != "open":\n\t\t\t\t_reset_room_ui("Le salon a été fermé par son propriétaire.")\n\t\t\t\treturn\n\t\t\t_show_room(polled_room)\n''', 1)

# Show room: reveal close only for creator.
show_anchor = '\tplayers_label.text = "\\n".join(lines)\n\tleave_button.disabled = false\n'
assert show_anchor in mp, 'show_room end missing'
mp = mp.replace(show_anchor, '''\tplayers_label.text = "\\n".join(lines)\n\tleave_button.disabled = false\n\tvar owner_id := int(room.get("creator_account_id", -1))\n\tvar my_id := int(RamiNetwork.account.get("id", -2))\n\tclose_button.visible = owner_id == my_id\n\tclose_button.disabled = not close_button.visible\n''', 1)

# Match found hides room controls.
match_found_anchor = 'func _on_match_found() -> void:\n\tpoll_timer.stop()\n\tleave_button.disabled = true\n'
assert match_found_anchor in mp, 'match found block missing'
mp = mp.replace(match_found_anchor, 'func _on_match_found() -> void:\n\tpoll_timer.stop()\n\tleave_button.disabled = true\n\tclose_button.disabled = true\n\tclose_button.visible = false\n', 1)

# Busy state extends to join controls, regardless of v028 google additions.
busy_anchor = 'func _set_busy(value: bool) -> void:\n\tsearch_button.disabled = value or not RamiNetwork.is_authenticated()\n\tcreate_button.disabled = value or not RamiNetwork.is_authenticated()\n'
assert busy_anchor in mp, 'busy block missing'
mp = mp.replace(busy_anchor, '''func _set_busy(value: bool) -> void:\n\tsearch_button.disabled = value or not RamiNetwork.is_authenticated() or current_room_id >= 0\n\tcreate_button.disabled = value or not RamiNetwork.is_authenticated() or current_room_id >= 0\n\tjoin_button.disabled = value or not RamiNetwork.is_authenticated() or current_room_id >= 0\n\tjoin_room_input.editable = not value and RamiNetwork.is_authenticated() and current_room_id < 0\n''', 1)

# Auth state enables/disables the direct-join controls.
refresh_auth_ok = '\t\tcreate_button.disabled = false\n'
assert refresh_auth_ok in mp, 'authenticated create enable missing'
mp = mp.replace(refresh_auth_ok, '\t\tcreate_button.disabled = false\n\t\tjoin_button.disabled = false\n\t\tjoin_room_input.editable = true\n', 1)
refresh_auth_bad = '\t\tcreate_button.disabled = true\n'
assert refresh_auth_bad in mp, 'unauthenticated create disable missing'
mp = mp.replace(refresh_auth_bad, '\t\tcreate_button.disabled = true\n\t\tjoin_button.disabled = true\n\t\tjoin_room_input.editable = false\n', 1)

# Reset helper + close result arm.
friendly_anchor = 'func _friendly_error(code: String) -> String:\n'
assert friendly_anchor in mp, 'friendly error function missing'
helper = '''func _reset_room_ui(message: String) -> void:\n\tpoll_timer.stop()\n\tcurrent_room_id = -1\n\tcurrent_match_id = -1\n\troom_label.text = "Aucun salon actif"\n\tplayers_label.text = ""\n\tleave_button.disabled = true\n\tclose_button.disabled = true\n\tclose_button.visible = false\n\tif join_room_input != null:\n\t\tjoin_room_input.text = ""\n\t_set_busy(false)\n\tstatus_label.text = message\n\n'''
mp = mp.replace(friendly_anchor, helper + friendly_anchor, 1)

# Add close_room result block after leave block by using the next function as delimiter.
show_func = '\nfunc _show_room(room: Dictionary) -> void:\n'
assert show_func in mp, '_show_room delimiter missing'
close_case = '''\t\t"close_room":\n\t\t\t_reset_room_ui("Salon fermé.")\n'''
mp = mp.replace(show_func, close_case + show_func, 1)

# Friendly errors.
friend_default = '\t\t_: return "Erreur : %s" % code\n'
assert friend_default in mp, 'friendly default missing'
friend_extra = '''\t\t"INVALID_ROOM_ID": return "ID de salon invalide."\n\t\t"ROOM_NOT_FOUND": return "Ce salon n'existe pas."\n\t\t"ROOM_NOT_OPEN": return "Ce salon n'est plus ouvert."\n\t\t"ROOM_FULL": return "Ce salon est déjà complet."\n\t\t"ALREADY_IN_ANOTHER_ROOM": return "Quittez d'abord votre salon actuel."\n\t\t"NOT_ROOM_OWNER": return "Seul le propriétaire peut fermer ce salon."\n\t\t"ROOM_JOIN_RACE_RETRY": return "Le salon vient de changer. Réessayez."\n'''
mp = mp.replace(friend_default, friend_extra + friend_default, 1)

mp = mp.replace('RAMI v0.0.27 • AUTH / ELO / MATCHMAKING FOUNDATION', 'RAMI v0.0.30 • SALONS : REJOINDRE / QUITTER / FERMER')
mp_path.write_text(mp, encoding='utf-8')

# --- Version -----------------------------------------------------------------
preset_path = Path('export_presets.cfg')
preset = preset_path.read_text(encoding='utf-8')
preset = preset.replace('export_path="Rami_v0.0.29.apk"', 'export_path="Rami_v0.0.30.apk"')
preset = preset.replace('version/code=31', 'version/code=32')
preset = preset.replace('version/name="0.0.29"', 'version/name="0.0.30"')
preset_path.write_text(preset, encoding='utf-8')

game_path = Path('GameTable.gd')
game = game_path.read_text(encoding='utf-8')
marker = 'print("RAMI_V029: prehome_google_gate=true logrami=true final_auth=true")'
assert marker in game, 'v029 marker missing'
game = game.replace(marker, marker + '\n\tprint("RAMI_V030: room_join=true room_leave=true owner_close=true")', 1)
game_path.write_text(game, encoding='utf-8')

print('RAMI_PATCH_V030: room join/leave/owner close applied')
