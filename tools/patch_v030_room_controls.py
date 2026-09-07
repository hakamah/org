from pathlib import Path

# RAMI v0.0.30 — explicit room controls:
# - join a room by ID
# - leave a room as any member
# - close a room only as its owner

# -----------------------------------------------------------------------------
# Network API
# -----------------------------------------------------------------------------
net_path = Path('RamiNetwork.gd')
net = net_path.read_text(encoding='utf-8')

anchor = '''func search_room(players: int) -> bool:\n\treturn _request("search_room", HTTPClient.METHOD_POST, "/api/matchmaking/search", {"players": players}, true)\n\nfunc get_room(room_id: int) -> bool:\n'''
assert anchor in net, 'RamiNetwork matchmaking anchor missing'
net = net.replace(anchor, '''func search_room(players: int) -> bool:\n\treturn _request("search_room", HTTPClient.METHOD_POST, "/api/matchmaking/search", {"players": players}, true)\n\nfunc join_room(room_id: int) -> bool:\n\treturn _request("join_room", HTTPClient.METHOD_POST, "/api/matchmaking/join", {"room_id": room_id}, true)\n\nfunc close_room(room_id: int) -> bool:\n\treturn _request("close_room", HTTPClient.METHOD_POST, "/api/matchmaking/close", {"room_id": room_id}, true)\n\nfunc get_room(room_id: int) -> bool:\n''', 1)

net_path.write_text(net, encoding='utf-8')

# -----------------------------------------------------------------------------
# Multiplayer UI
# -----------------------------------------------------------------------------
mp_path = Path('Multiplayer.gd')
mp = mp_path.read_text(encoding='utf-8')

fields = '''var search_button: Button\nvar create_button: Button\nvar leave_button: Button\nvar count_buttons: Dictionary = {}\n'''
assert fields in mp, 'Multiplayer fields anchor missing'
mp = mp.replace(fields, '''var search_button: Button\nvar create_button: Button\nvar join_button: Button\nvar join_room_input: LineEdit\nvar leave_button: Button\nvar close_button: Button\nvar count_buttons: Dictionary = {}\n''', 1)

# Left panel: add join-by-id controls without changing the rest of the DA.
left_anchor = '''\tcreate_button = _button_in("CRÉER UN SALON", Vector2(50, 390), Vector2(510, 82), 24, Color("#183B4A"), Color("#4B8FA8"), left)\n\tcreate_button.pressed.connect(_on_create)\n\t_label("La recherche rejoint automatiquement le salon compatible\\ndont l'ELO de base est le plus proche du vôtre.", Vector2(55, 505), Vector2(500, 72), 17, MUTED, left)\n\tstatus_label = _label("", Vector2(50, 590), Vector2(510, 44), 18, GOLD, left)\n'''
assert left_anchor in mp, 'Multiplayer left panel anchor missing'
mp = mp.replace(left_anchor, '''\tcreate_button = _button_in("CRÉER UN SALON", Vector2(50, 385), Vector2(510, 72), 23, Color("#183B4A"), Color("#4B8FA8"), left)\n\tcreate_button.pressed.connect(_on_create)\n\n\tjoin_room_input = LineEdit.new()\n\tjoin_room_input.placeholder_text = "ID DU SALON (ex. 123)"\n\tjoin_room_input.position = Vector2(50, 480)\n\tjoin_room_input.size = Vector2(320, 58)\n\tjoin_room_input.add_theme_font_size_override("font_size", 19)\n\tjoin_room_input.add_theme_color_override("font_color", TEXT)\n\tjoin_room_input.add_theme_color_override("font_placeholder_color", Color(0.82,0.82,0.78,0.55))\n\tjoin_room_input.add_theme_stylebox_override("normal", _style(Color("#142D34"), Color("#4D7972"), 3, 16))\n\tleft.add_child(join_room_input)\n\n\tjoin_button = _button_in("REJOINDRE", Vector2(385, 480), Vector2(175, 58), 20, Color("#315E22"), Color("#9CCB43"), left)\n\tjoin_button.pressed.connect(_on_join)\n\n\t_label("Recherche automatique ou entrée directe avec l'ID du salon.", Vector2(55, 548), Vector2(500, 34), 16, MUTED, left)\n\tstatus_label = _label("", Vector2(50, 590), Vector2(510, 54), 18, GOLD, left)\n''', 1)

# Right panel: split close-owner and leave-member controls.
right_anchor = '''\tleave_button = _button_in("QUITTER LE SALON", Vector2(170, 505), Vector2(430, 76), 22, Color("#6E1B1B"), RED, right)\n\tleave_button.pressed.connect(_on_leave)\n\tleave_button.disabled = true\n'''
assert right_anchor in mp, 'Multiplayer leave button anchor missing'
mp = mp.replace(right_anchor, '''\tclose_button = _button_in("FERMER LE SALON", Vector2(85, 500), Vector2(285, 72), 20, Color("#6E1B1B"), RED, right)\n\tclose_button.pressed.connect(_on_close_room)\n\tclose_button.disabled = true\n\tclose_button.visible = false\n\n\tleave_button = _button_in("QUITTER LE SALON", Vector2(400, 500), Vector2(285, 72), 20, Color("#3B3030"), Color("#C98787"), right)\n\tleave_button.pressed.connect(_on_leave)\n\tleave_button.disabled = true\n''', 1)

# Auth enablement.
auth_good = '''\t\tsearch_button.disabled = false\n\t\tcreate_button.disabled = false\n\t\tstatus_label.text = "Prêt. Choisissez 2, 3 ou 4 joueurs."\n'''
assert auth_good in mp, 'Multiplayer authenticated block missing'
mp = mp.replace(auth_good, '''\t\tsearch_button.disabled = false\n\t\tcreate_button.disabled = false\n\t\tjoin_button.disabled = false\n\t\tjoin_room_input.editable = true\n\t\tstatus_label.text = "Prêt. Choisissez 2, 3 ou 4 joueurs."\n''', 1)

auth_bad = '''\t\tsearch_button.disabled = true\n\t\tcreate_button.disabled = true\n'''
assert auth_bad in mp, 'Multiplayer unauthenticated block missing'
mp = mp.replace(auth_bad, '''\t\tsearch_button.disabled = true\n\t\tcreate_button.disabled = true\n\t\tjoin_button.disabled = true\n\t\tjoin_room_input.editable = false\n''', 1)

# Join handler.
create_handler = '''func _on_create() -> void:\n\tif current_room_id >= 0:\n\t\treturn\n\t_set_busy(true)\n\tstatus_label.text = "Création d'un salon %d joueurs…" % selected_players\n\tRamiNetwork.create_room(selected_players)\n\nfunc _on_leave() -> void:\n'''
assert create_handler in mp, 'Multiplayer create handler anchor missing'
mp = mp.replace(create_handler, '''func _on_create() -> void:\n\tif current_room_id >= 0:\n\t\treturn\n\t_set_busy(true)\n\tstatus_label.text = "Création d'un salon %d joueurs…" % selected_players\n\tRamiNetwork.create_room(selected_players)\n\nfunc _on_join() -> void:\n\tif current_room_id >= 0:\n\t\treturn\n\tvar raw := join_room_input.text.strip_edges()\n\tif raw.is_empty() or not raw.is_valid_int():\n\t\tstatus_label.text = "Entre un ID de salon valide."\n\t\treturn\n\tvar room_id := int(raw)\n\tif room_id <= 0:\n\t\tstatus_label.text = "ID de salon invalide."\n\t\treturn\n\t_set_busy(true)\n\tstatus_label.text = "Connexion au salon #%d…" % room_id\n\tRamiNetwork.join_room(room_id)\n\nfunc _on_close_room() -> void:\n\tif current_room_id < 0 or not _is_current_room_owner():\n\t\treturn\n\tclose_button.disabled = true\n\tleave_button.disabled = true\n\tstatus_label.text = "Fermeture du salon…"\n\tRamiNetwork.close_room(current_room_id)\n\nfunc _on_leave() -> void:\n''', 1)

# Network error kinds.
err_anchor = '''\tif not bool(payload.get("ok", false)):\n\t\tif kind in ["create_room", "search_room", "leave_room"]:\n\t\t\t_set_busy(false)\n'''
assert err_anchor in mp, 'Multiplayer error handling anchor missing'
mp = mp.replace(err_anchor, '''\tif not bool(payload.get("ok", false)):\n\t\tif kind in ["create_room", "search_room", "join_room", "leave_room", "close_room"]:\n\t\t\t_set_busy(false)\n''', 1)

# Success handling: join joins same flow, close resets room.
match_anchor = '''\tmatch kind:\n\t\t"create_room", "search_room":\n'''
assert match_anchor in mp, 'Multiplayer match result anchor missing'
mp = mp.replace(match_anchor, '''\tmatch kind:\n\t\t"create_room", "search_room", "join_room":\n''', 1)

leave_block = '''\t\t"leave_room":\n\t\t\tpoll_timer.stop()\n\t\t\tcurrent_room_id = -1\n\t\t\tcurrent_match_id = -1\n\t\t\troom_label.text = "Aucun salon actif"\n\t\t\tplayers_label.text = ""\n\t\t\tleave_button.disabled = true\n\t\t\t_set_busy(false)\n\t\t\tstatus_label.text = "Salon quitté."\n'''
assert leave_block in mp, 'Multiplayer leave result block missing'
mp = mp.replace(leave_block, '''\t\t"leave_room":\n\t\t\t_reset_room_ui("Salon quitté.")\n\t\t"close_room":\n\t\t\t_reset_room_ui("Salon fermé.")\n''', 1)

# Handle room closed by owner while guests are polling.
room_case = '''\t\t"room":\n\t\t\t_show_room(payload.get("room", {}) as Dictionary)\n\t\t\tvar match_value: Variant = payload.get("match_id", null)\n'''
assert room_case in mp, 'Multiplayer room polling block missing'
mp = mp.replace(room_case, '''\t\t"room":\n\t\t\tvar polled_room: Dictionary = payload.get("room", {}) as Dictionary\n\t\t\tif String(polled_room.get("status", "open")) != "open":\n\t\t\t\t_reset_room_ui("Le salon a été fermé par son propriétaire.")\n\t\t\t\treturn\n\t\t\t_show_room(polled_room)\n\t\t\tvar match_value: Variant = payload.get("match_id", null)\n''', 1)

# Show correct owner controls.
show_anchor = '''\tplayers_label.text = "\\n".join(lines)\n\tleave_button.disabled = false\n\tstatus_label.text = "En attente… Le salon conserve l'ELO du créateur : %d." % base_elo\n'''
assert show_anchor in mp, 'Multiplayer show room anchor missing'
mp = mp.replace(show_anchor, '''\tplayers_label.text = "\\n".join(lines)\n\tleave_button.disabled = false\n\tclose_button.visible = _is_current_room_owner(room)\n\tclose_button.disabled = not close_button.visible\n\tif close_button.visible:\n\t\tstatus_label.text = "Vous êtes propriétaire du salon • ELO base %d." % base_elo\n\telse:\n\t\tstatus_label.text = "En attente… ELO base du salon : %d." % base_elo\n''', 1)

# Match start hides controls.
match_found = '''func _on_match_found() -> void:\n\tpoll_timer.stop()\n\tleave_button.disabled = true\n\tstatus_label.text = "PARTIE TROUVÉE • Match #%d — synchronisation du jeu en préparation." % current_match_id\n'''
assert match_found in mp, 'Multiplayer match found anchor missing'
mp = mp.replace(match_found, '''func _on_match_found() -> void:\n\tpoll_timer.stop()\n\tleave_button.disabled = true\n\tclose_button.disabled = true\n\tclose_button.visible = false\n\tstatus_label.text = "PARTIE TROUVÉE • Match #%d — synchronisation du jeu en préparation." % current_match_id\n''', 1)

# Busy includes join.
busy_anchor = '''func _set_busy(value: bool) -> void:\n\tsearch_button.disabled = value or not RamiNetwork.is_authenticated()\n\tcreate_button.disabled = value or not RamiNetwork.is_authenticated()\n\tfor b_value: Variant in count_buttons.values():\n'''
assert busy_anchor in mp, 'Multiplayer busy anchor missing'
mp = mp.replace(busy_anchor, '''func _set_busy(value: bool) -> void:\n\tsearch_button.disabled = value or not RamiNetwork.is_authenticated() or current_room_id >= 0\n\tcreate_button.disabled = value or not RamiNetwork.is_authenticated() or current_room_id >= 0\n\tjoin_button.disabled = value or not RamiNetwork.is_authenticated() or current_room_id >= 0\n\tjoin_room_input.editable = not value and RamiNetwork.is_authenticated() and current_room_id < 0\n\tfor b_value: Variant in count_buttons.values():\n''', 1)

# Helpers + friendly errors before _friendly_error.
friend_anchor = '''func _friendly_error(code: String) -> String:\n'''
assert friend_anchor in mp, 'Multiplayer friendly error anchor missing'
helpers = '''func _is_current_room_owner(room: Dictionary = {}) -> bool:\n\tif not RamiNetwork.is_authenticated():\n\t\treturn false\n\tvar owner_id := -1\n\tif not room.is_empty():\n\t\towner_id = int(room.get("creator_account_id", -1))\n\telse:\n\t\t# The last room payload is represented by the visible current room; owner state\n\t\t# is refreshed each time _show_room runs, so visibility is also a safe fallback.\n\t\treturn close_button != null and close_button.visible\n\treturn owner_id == int(RamiNetwork.account.get("id", -2))\n\nfunc _reset_room_ui(message: String) -> void:\n\tpoll_timer.stop()\n\tcurrent_room_id = -1\n\tcurrent_match_id = -1\n\troom_label.text = "Aucun salon actif"\n\tplayers_label.text = ""\n\tleave_button.disabled = true\n\tclose_button.disabled = true\n\tclose_button.visible = false\n\tjoin_room_input.text = ""\n\t_set_busy(false)\n\tstatus_label.text = message\n\n'''
mp = mp.replace(friend_anchor, helpers + friend_anchor, 1)

# Friendly errors.
friend_cases = '''\t\t"INVALID_TOKEN": return "Session expirée. Reconnectez-vous."\n\t\t_: return "Erreur : %s" % code\n'''
assert friend_cases in mp, 'Multiplayer friendly error cases missing'
mp = mp.replace(friend_cases, '''\t\t"INVALID_TOKEN": return "Session expirée. Reconnectez-vous."\n\t\t"INVALID_ROOM_ID": return "ID de salon invalide."\n\t\t"ROOM_NOT_FOUND": return "Ce salon n'existe pas."\n\t\t"ROOM_NOT_OPEN": return "Ce salon n'est plus ouvert."\n\t\t"ROOM_FULL": return "Ce salon est déjà complet."\n\t\t"ALREADY_IN_ANOTHER_ROOM": return "Quittez d'abord votre salon actuel."\n\t\t"NOT_ROOM_OWNER": return "Seul le propriétaire peut fermer ce salon."\n\t\t"ROOM_JOIN_RACE_RETRY": return "Le salon vient de changer. Réessayez."\n\t\t_: return "Erreur : %s" % code\n''', 1)

# Version/footer marker.
mp = mp.replace('RAMI v0.0.27 • AUTH / ELO / MATCHMAKING FOUNDATION', 'RAMI v0.0.30 • SALONS : REJOINDRE / QUITTER / FERMER')
mp_path.write_text(mp, encoding='utf-8')

# -----------------------------------------------------------------------------
# Version bump
# -----------------------------------------------------------------------------
preset_path = Path('export_presets.cfg')
preset = preset_path.read_text(encoding='utf-8')
preset = preset.replace('export_path="Rami_v0.0.29.apk"', 'export_path="Rami_v0.0.30.apk"')
preset = preset.replace('version/code=31', 'version/code=32')
preset = preset.replace('version/name="0.0.29"', 'version/name="0.0.30"')
preset_path.write_text(preset, encoding='utf-8')

game_path = Path('GameTable.gd')
game = game_path.read_text(encoding='utf-8')
marker = 'print("RAMI_V029: prehome_google_gate=true logrami=true final_auth=true")'
assert marker in game, 'RAMI v029 marker missing'
game = game.replace(marker, marker + '\n\tprint("RAMI_V030: room_join=true room_leave=true owner_close=true")', 1)
game_path.write_text(game, encoding='utf-8')

print('RAMI_PATCH_V030: explicit join/leave/owner-close room controls')
