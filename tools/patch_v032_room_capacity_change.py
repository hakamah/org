from pathlib import Path
import re

# RAMI v0.0.32 — owner can change an open room's target player count
# without destroying/recreating the room. The change is explicitly confirmed
# by the owner. Confirmed/current-or-higher capacities are green, the pending
# capacity is purple, and lower alternatives stay blue.


def replace_func(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(r"(?ms)^func " + re.escape(name) + r"\([^\n]*\).*?(?=^func |\Z)")
    m = pattern.search(text)
    assert m, f"function {name} missing"
    return text[:m.start()] + replacement.rstrip() + "\n\n" + text[m.end():]

# --- RamiNetwork -------------------------------------------------------------
net_path = Path('RamiNetwork.gd')
net = net_path.read_text(encoding='utf-8')
anchor = '''func close_room(room_id: int) -> bool:\n\treturn _request("close_room", HTTPClient.METHOD_POST, "/api/matchmaking/close", {"room_id": room_id}, true)\n\n'''
assert anchor in net, 'v030 close_room API missing'
net = net.replace(anchor, anchor + '''func resize_room(room_id: int, players: int) -> bool:\n\treturn _request("resize_room", HTTPClient.METHOD_POST, "/api/matchmaking/resize", {"room_id": room_id, "players": players}, true)\n\n''', 1)
net_path.write_text(net, encoding='utf-8')

# --- Multiplayer -------------------------------------------------------------
mp_path = Path('Multiplayer.gd')
mp = mp_path.read_text(encoding='utf-8')

color_anchor = 'const BLUE := Color("#4BA3FF")\n'
assert color_anchor in mp, 'BLUE color anchor missing'
mp = mp.replace(color_anchor, color_anchor + 'const PURPLE := Color("#B46CFF")\n', 1)

field_anchor = 'var count_buttons: Dictionary = {}\n'
assert field_anchor in mp, 'count_buttons field missing'
mp = mp.replace(field_anchor, field_anchor + '''\nvar confirmed_room_players: int = -1\nvar pending_room_players: int = -1\nvar current_room_player_count: int = 0\nvar current_room_is_owner: bool = false\n''', 1)

mp = replace_func(mp, '_on_count_pressed', '''func _on_count_pressed(value: int) -> void:
\tif current_room_id < 0:
\t\tselected_players = value
\t\t_refresh_player_count_buttons()
\t\treturn
\tif not current_room_is_owner:
\t\treturn
\tif value < current_room_player_count:
\t\tstatus_label.text = "Impossible : %d joueurs sont déjà dans le salon." % current_room_player_count
\t\treturn
\tif value == confirmed_room_players:
\t\tpending_room_players = -1
\telse:
\t\tpending_room_players = value
\t_refresh_player_count_buttons()
\t_refresh_room_primary_action()''')

mp = replace_func(mp, '_refresh_player_count_buttons', '''func _refresh_player_count_buttons() -> void:
\tfor k in count_buttons.keys():
\t\tvar value := int(k)
\t\tvar b: Button = count_buttons[k]
\t\tvar mode := "blue"
\t\tif current_room_id < 0:
\t\t\tmode = "green" if value == selected_players else "blue"
\t\telse:
\t\t\tif value >= confirmed_room_players:
\t\t\t\tmode = "green"
\t\t\tif value == pending_room_players:
\t\t\t\tmode = "purple"

\t\tif mode == "green":
\t\t\tb.add_theme_stylebox_override("normal", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))
\t\t\tb.add_theme_stylebox_override("hover", _style(Color("#376B27"), Color("#A9D84E"), 4, 20))
\t\t\tb.add_theme_stylebox_override("pressed", _style(Color("#284F1C"), Color("#B6E35B"), 4, 20))
\t\t\tb.add_theme_stylebox_override("focus", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))
\t\t\tb.add_theme_stylebox_override("disabled", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))
\t\telif mode == "purple":
\t\t\tb.add_theme_stylebox_override("normal", _style(Color("#56316D"), Color("#C884F4"), 4, 20))
\t\t\tb.add_theme_stylebox_override("hover", _style(Color("#643A7D"), Color("#D596FF"), 4, 20))
\t\t\tb.add_theme_stylebox_override("pressed", _style(Color("#49285D"), Color("#DDA4FF"), 4, 20))
\t\t\tb.add_theme_stylebox_override("focus", _style(Color("#56316D"), Color("#C884F4"), 4, 20))
\t\t\tb.add_theme_stylebox_override("disabled", _style(Color("#56316D"), Color("#C884F4"), 4, 20))
\t\telse:
\t\t\tb.add_theme_stylebox_override("normal", _style(Color("#17343A"), Color("#4D7972"), 3, 20))
\t\t\tb.add_theme_stylebox_override("hover", _style(Color("#1B4149"), Color("#5A8C84"), 3, 20))
\t\t\tb.add_theme_stylebox_override("pressed", _style(Color("#17343A"), Color("#4D7972"), 3, 20))
\t\t\tb.add_theme_stylebox_override("focus", _style(Color("#17343A"), Color("#4D7972"), 3, 20))
\t\t\tb.add_theme_stylebox_override("disabled", _style(Color("#17343A"), Color("#4D7972"), 3, 20))''')

mp = replace_func(mp, '_on_create', '''func _on_create() -> void:
\tif current_room_id < 0:
\t\t_set_busy(true)
\t\tstatus_label.text = "Création d'un salon %d joueurs…" % selected_players
\t\tRamiNetwork.create_room(selected_players)
\t\treturn
\tif not current_room_is_owner:
\t\treturn
\tif pending_room_players >= 2:
\t\t_on_confirm_room_change()
\telse:
\t\t_on_close_room()''')

close_marker = 'func _on_close_room() -> void:\n'
assert close_marker in mp, '_on_close_room missing'
helpers = '''func _on_confirm_room_change() -> void:\n\tif current_room_id < 0 or not current_room_is_owner or pending_room_players < 2:\n\t\treturn\n\tif pending_room_players < current_room_player_count:\n\t\tstatus_label.text = "Impossible : %d joueurs sont déjà dans le salon." % current_room_player_count\n\t\treturn\n\tvar requested := pending_room_players\n\t_set_busy(true)\n\tstatus_label.text = "Confirmation : salon à %d joueurs…" % requested\n\tRamiNetwork.resize_room(current_room_id, requested)\n\nfunc _refresh_room_primary_action() -> void:\n\tif create_button == null:\n\t\treturn\n\tif current_room_id < 0:\n\t\tcreate_button.text = "CRÉER UN SALON"\n\t\tcreate_button.disabled = not RamiNetwork.is_authenticated()\n\t\tcreate_button.add_theme_stylebox_override("normal", _style(Color("#183B4A"), Color("#4B8FA8"), 3, 18))\n\t\tcreate_button.add_theme_stylebox_override("hover", _style(Color("#204B5B"), Color("#61A7C0"), 4, 18))\n\t\tcreate_button.add_theme_stylebox_override("pressed", _style(Color("#132F3B"), Color("#69B3CC"), 4, 18))\n\t\treturn\n\tif not current_room_is_owner:\n\t\tcreate_button.text = "SALON ACTIF"\n\t\tcreate_button.disabled = true\n\t\treturn\n\tif pending_room_players >= 2:\n\t\tcreate_button.text = "CONFIRMER CHANGEMENT"\n\t\tcreate_button.disabled = false\n\t\tcreate_button.add_theme_stylebox_override("normal", _style(Color("#0F6644"), GREEN, 4, 18))\n\t\tcreate_button.add_theme_stylebox_override("hover", _style(Color("#147A52"), Color("#55E4A0"), 4, 18))\n\t\tcreate_button.add_theme_stylebox_override("pressed", _style(Color("#0B5136"), Color("#6AF0B2"), 4, 18))\n\telse:\n\t\tcreate_button.text = "FERMER LE SALON"\n\t\tcreate_button.disabled = false\n\t\tcreate_button.add_theme_stylebox_override("normal", _style(Color("#6E1B1B"), RED, 4, 18))\n\t\tcreate_button.add_theme_stylebox_override("hover", _style(Color("#842323"), Color("#F2767D"), 4, 18))\n\t\tcreate_button.add_theme_stylebox_override("pressed", _style(Color("#571515"), Color("#F58B90"), 4, 18))\n\n'''
mp = mp.replace(close_marker, helpers + close_marker, 1)

mp = replace_func(mp, '_on_network_result', '''func _on_network_result(kind: String, payload: Dictionary) -> void:
\tif not bool(payload.get("ok", false)):
\t\tif kind in ["create_room", "search_room", "join_room", "leave_room", "close_room", "resize_room"]:
\t\t\t_set_busy(false)
\t\tstatus_label.text = _friendly_error(String(payload.get("error", "Erreur réseau")))
\t\t_refresh_player_count_buttons()
\t\t_refresh_room_primary_action()
\t\treturn
\tmatch kind:
\t\t"create_room", "search_room", "join_room":
\t\t\t_set_busy(false)
\t\t\tpending_room_players = -1
\t\t\tvar room: Dictionary = payload.get("room", {}) as Dictionary
\t\t\t_show_room(room)
\t\t\tvar match_value: Variant = payload.get("match_id", null)
\t\t\tif match_value != null:
\t\t\t\tcurrent_match_id = int(match_value)
\t\t\t\t_on_match_found()
\t\t\telse:
\t\t\t\tpoll_timer.start()
\t\t"room":
\t\t\tvar polled_room: Dictionary = payload.get("room", {}) as Dictionary
\t\t\tif String(polled_room.get("status", "open")) != "open":
\t\t\t\tvar room_match_value: Variant = payload.get("match_id", null)
\t\t\t\tif room_match_value != null:
\t\t\t\t\tcurrent_match_id = int(room_match_value)
\t\t\t\t\t_on_match_found()
\t\t\t\telse:
\t\t\t\t\t_reset_room_ui("Le salon a été fermé par son propriétaire.")
\t\t\t\treturn
\t\t\t_show_room(polled_room)
\t\t\tvar polled_match_value: Variant = payload.get("match_id", null)
\t\t\tif polled_match_value != null:
\t\t\t\tcurrent_match_id = int(polled_match_value)
\t\t\t\t_on_match_found()
\t\t"resize_room":
\t\t\t_set_busy(false)
\t\t\tpending_room_players = -1
\t\t\tvar resized_room: Dictionary = payload.get("room", {}) as Dictionary
\t\t\t_show_room(resized_room)
\t\t\tvar resized_match_value: Variant = payload.get("match_id", null)
\t\t\tif resized_match_value != null:
\t\t\t\tcurrent_match_id = int(resized_match_value)
\t\t\t\t_on_match_found()
\t\t\telse:
\t\t\t\tstatus_label.text = "Nombre de joueurs confirmé : %d." % confirmed_room_players
\t\t"leave_room":
\t\t\t_reset_room_ui("Salon quitté.")
\t\t"close_room":
\t\t\t_reset_room_ui("Salon fermé.")''')

mp = replace_func(mp, '_show_room', '''func _show_room(room: Dictionary) -> void:
\tif room.is_empty():
\t\treturn
\tcurrent_room_id = int(room.get("id", -1))
\tvar count := int(room.get("player_count", 0))
\tvar target := int(room.get("target_players", selected_players))
\tvar base_elo := int(room.get("base_elo", 100))
\tcurrent_room_player_count = count
\tconfirmed_room_players = target
\tselected_players = target
\tvar owner_id := int(room.get("creator_account_id", -1))
\tvar my_id := int(RamiNetwork.account.get("id", -2))
\tcurrent_room_is_owner = owner_id == my_id
\troom_label.text = "Salon #%d  •  %d/%d joueurs  •  ELO base %d" % [current_room_id, count, target, base_elo]
\tvar lines := PackedStringArray()
\tvar players: Array = room.get("players", []) as Array
\tfor p_value: Variant in players:
\t\tif p_value is Dictionary:
\t\t\tvar p := p_value as Dictionary
\t\t\tlines.append("%d.  %s  —  %d ELO" % [int(p.get("seat", 0)) + 1, String(p.get("display_name", "Joueur")), int(p.get("elo", 100))])
\tfor i in range(players.size(), target):
\t\tlines.append("%d.  En attente d'un joueur…" % (i + 1))
\tplayers_label.text = "\\n".join(lines)
\tleave_button.disabled = false
\tclose_button.visible = false
\tclose_button.disabled = true
\t_refresh_player_count_buttons()
\t_refresh_room_primary_action()
\tif current_room_is_owner:
\t\tstatus_label.text = "En attente… Vous pouvez modifier la capacité puis confirmer."
\telse:
\t\tstatus_label.text = "En attente… Le salon conserve l'ELO du créateur : %d." % base_elo''')

mp = replace_func(mp, '_on_match_found', '''func _on_match_found() -> void:
\tpoll_timer.stop()
\tleave_button.disabled = true
\tclose_button.disabled = true
\tclose_button.visible = false
\tfor b_value: Variant in count_buttons.values():
\t\tvar b := b_value as Button
\t\tb.disabled = true
\tcreate_button.disabled = true
\tstatus_label.text = "PARTIE TROUVÉE • Match #%d — synchronisation du jeu en préparation." % current_match_id''')

mp = replace_func(mp, '_set_busy', '''func _set_busy(value: bool) -> void:
\tsearch_button.disabled = value or not RamiNetwork.is_authenticated() or current_room_id >= 0
\tjoin_button.disabled = value or not RamiNetwork.is_authenticated() or current_room_id >= 0
\tjoin_room_input.editable = not value and RamiNetwork.is_authenticated() and current_room_id < 0
\tif current_room_id < 0:
\t\tcreate_button.disabled = value or not RamiNetwork.is_authenticated()
\telse:
\t\tcreate_button.disabled = value or not current_room_is_owner
\tfor b_value: Variant in count_buttons.values():
\t\tvar b := b_value as Button
\t\tb.disabled = value or (current_room_id >= 0 and not current_room_is_owner)''')

mp = replace_func(mp, '_reset_room_ui', '''func _reset_room_ui(message: String) -> void:
\tpoll_timer.stop()
\tcurrent_room_id = -1
\tcurrent_match_id = -1
\tconfirmed_room_players = -1
\tpending_room_players = -1
\tcurrent_room_player_count = 0
\tcurrent_room_is_owner = false
\troom_label.text = "Aucun salon actif"
\tplayers_label.text = ""
\tleave_button.disabled = true
\tclose_button.disabled = true
\tclose_button.visible = false
\tif join_room_input != null:
\t\tjoin_room_input.text = ""
\t_set_busy(false)
\t_refresh_player_count_buttons()
\t_refresh_room_primary_action()
\tstatus_label.text = message''')

mp = replace_func(mp, '_friendly_error', '''func _friendly_error(code: String) -> String:
\tmatch code:
\t\t"SERVER_NOT_CONFIGURED": return "Serveur RAMI non configuré."
\t\t"AUTH_REQUIRED": return "Connexion Google requise."
\t\t"NETWORK_ERROR": return "Impossible de joindre le serveur RAMI."
\t\t"INVALID_TOKEN": return "Session expirée. Reconnectez-vous."
\t\t"INVALID_ROOM_ID": return "ID de salon invalide."
\t\t"ROOM_NOT_FOUND": return "Ce salon n'existe pas."
\t\t"ROOM_NOT_OPEN": return "Ce salon n'est plus ouvert."
\t\t"ROOM_FULL": return "Ce salon est déjà complet."
\t\t"ALREADY_IN_ANOTHER_ROOM": return "Quittez d'abord votre salon actuel."
\t\t"NOT_ROOM_OWNER": return "Seul le propriétaire peut modifier ou fermer ce salon."
\t\t"ROOM_JOIN_RACE_RETRY": return "Le salon vient de changer. Réessayez."
\t\t"ROOM_HAS_TOO_MANY_PLAYERS": return "Impossible : trop de joueurs sont déjà présents pour cette capacité."
\t\t"PLAYERS_MUST_BE_2_3_OR_4": return "Choisissez 2, 3 ou 4 joueurs."
\t\t_: return "Erreur : %s" % code''')

mp = mp.replace('RAMI v0.0.31 • SÉLECTEUR JOUEURS CORRIGÉ', 'RAMI v0.0.32 • CAPACITÉ SALON MODIFIABLE')
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
game = game.replace(marker, marker + '\n\tprint("RAMI_V032: owner_room_capacity_change=true explicit_confirm=true")', 1)
game_path.write_text(game, encoding='utf-8')

print('RAMI_PATCH_V032: owner room capacity change + explicit confirm applied')
