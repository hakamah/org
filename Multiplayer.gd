extends Control

const GOLD := Color("#F0C86A")
const TEXT := Color("#F7F3E8")
const MUTED := Color("#CFC8B8")
const GREEN := Color("#39D28A")
const RED := Color("#E65A61")
const BLUE := Color("#4BA3FF")

var selected_players: int = 3
var current_room_id: int = -1
var current_match_id: int = -1
var poll_timer: Timer

var account_label: Label
var status_label: Label
var room_label: Label
var players_label: Label
var search_button: Button
var create_button: Button
var leave_button: Button
var count_buttons: Dictionary = {}

func _ready() -> void:
	_build_background()
	_build_ui()
	poll_timer = Timer.new()
	poll_timer.wait_time = 1.5
	poll_timer.one_shot = false
	poll_timer.timeout.connect(_poll_room)
	add_child(poll_timer)
	RamiNetwork.auth_changed.connect(_on_auth_changed)
	RamiNetwork.request_finished.connect(_on_network_result)
	_refresh_account()
	_refresh_player_count_buttons()

func _exit_tree() -> void:
	if RamiNetwork.auth_changed.is_connected(_on_auth_changed):
		RamiNetwork.auth_changed.disconnect(_on_auth_changed)
	if RamiNetwork.request_finished.is_connected(_on_network_result):
		RamiNetwork.request_finished.disconnect(_on_network_result)

func _build_background() -> void:
	var bg := ColorRect.new()
	bg.color = Color("#0D5A3A")
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var top := ColorRect.new()
	top.color = Color("#2A160D")
	top.set_anchors_preset(Control.PRESET_TOP_WIDE)
	top.offset_bottom = 72
	add_child(top)
	var bottom := ColorRect.new()
	bottom.color = Color("#2A160D")
	bottom.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bottom.offset_top = -34
	add_child(bottom)

func _build_ui() -> void:
	var back := _button("←", Vector2(18, 10), Vector2(72, 52), 30, Color("#17343A"), Color("#4D7972"))
	back.pressed.connect(func(): get_tree().change_scene_to_file("res://Main.tscn"))

	var title := _label("MULTI JOUEURS", Vector2(110, 8), Vector2(400, 56), 38, GOLD)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	account_label = _label("", Vector2(1040, 10), Vector2(520, 52), 20, TEXT)
	account_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT

	var left := _panel(Vector2(90, 110), Vector2(610, 660), Color("#112D25"), Color("#4D8F70"), 28, 3)
	_label("MATCHMAKING", Vector2(35, 24), Vector2(540, 52), 32, GOLD, left)
	_label("Nombre de joueurs", Vector2(40, 105), Vector2(530, 38), 22, TEXT, left)

	for i in range(3):
		var count := i + 2
		var b := _button_in(str(count), Vector2(50 + i * 165, 155), Vector2(140, 74), 30, Color("#17343A"), Color("#4D7972"), left)
		b.pressed.connect(_on_count_pressed.bind(count))
		count_buttons[count] = b

	search_button = _button_in("RECHERCHER UNE PARTIE", Vector2(50, 275), Vector2(510, 92), 25, Color("#0F6644"), GREEN, left)
	search_button.pressed.connect(_on_search)
	create_button = _button_in("CRÉER UN SALON", Vector2(50, 390), Vector2(510, 82), 24, Color("#183B4A"), Color("#4B8FA8"), left)
	create_button.pressed.connect(_on_create)
	_label("La recherche rejoint automatiquement le salon compatible\ndont l'ELO de base est le plus proche du vôtre.", Vector2(55, 505), Vector2(500, 72), 17, MUTED, left)
	status_label = _label("", Vector2(50, 590), Vector2(510, 44), 18, GOLD, left)

	var right := _panel(Vector2(740, 110), Vector2(770, 660), Color("#102A28"), Color("#4D7972"), 28, 3)
	_label("SALON", Vector2(35, 24), Vector2(700, 52), 32, GOLD, right)
	room_label = _label("Aucun salon actif", Vector2(45, 105), Vector2(680, 54), 24, TEXT, right)
	room_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	players_label = _label("", Vector2(55, 180), Vector2(660, 270), 22, TEXT, right)
	players_label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	players_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	leave_button = _button_in("QUITTER LE SALON", Vector2(170, 505), Vector2(430, 76), 22, Color("#6E1B1B"), RED, right)
	leave_button.pressed.connect(_on_leave)
	leave_button.disabled = true

	_label("ELO initial : 100 • K = 32 • ELO minimum : 0", Vector2(90, 810), Vector2(1420, 34), 18, MUTED)
	_label("RAMI v0.0.27 • AUTH / ELO / MATCHMAKING FOUNDATION", Vector2(850, 860), Vector2(660, 22), 12, Color(1,1,1,0.45))

func _on_count_pressed(value: int) -> void:
	if current_room_id >= 0:
		return
	selected_players = value
	_refresh_player_count_buttons()

func _refresh_player_count_buttons() -> void:
	for k in count_buttons.keys():
		var b: Button = count_buttons[k]
		if int(k) == selected_players:
			b.add_theme_stylebox_override("normal", _style(Color("#315E22"), Color("#9CCB43"), 4, 20))
		else:
			b.add_theme_stylebox_override("normal", _style(Color("#17343A"), Color("#4D7972"), 3, 20))

func _refresh_account() -> void:
	if RamiNetwork.is_authenticated():
		var name := String(RamiNetwork.account.get("display_name", "Joueur"))
		var elo := int(RamiNetwork.account.get("elo", 100))
		account_label.text = "%s  •  %d ELO" % [name, elo]
		search_button.disabled = false
		create_button.disabled = false
		status_label.text = "Prêt. Choisissez 2, 3 ou 4 joueurs."
	else:
		account_label.text = "Non connecté • ELO 100 à la création du compte"
		search_button.disabled = true
		create_button.disabled = true
		if not RamiNetwork.is_server_configured():
			status_label.text = "Serveur RAMI isolé prêt côté code — déploiement à configurer."
		else:
			status_label.text = "Connexion Google requise."

func _on_auth_changed(_account: Dictionary) -> void:
	_refresh_account()

func _on_search() -> void:
	if current_room_id >= 0:
		return
	_set_busy(true)
	status_label.text = "Recherche du salon %d joueurs au meilleur ELO…" % selected_players
	RamiNetwork.search_room(selected_players)

func _on_create() -> void:
	if current_room_id >= 0:
		return
	_set_busy(true)
	status_label.text = "Création d'un salon %d joueurs…" % selected_players
	RamiNetwork.create_room(selected_players)

func _on_leave() -> void:
	if current_room_id < 0:
		return
	leave_button.disabled = true
	RamiNetwork.leave_room()

func _poll_room() -> void:
	if current_room_id >= 0:
		RamiNetwork.get_room(current_room_id)

func _on_network_result(kind: String, payload: Dictionary) -> void:
	if not bool(payload.get("ok", false)):
		if kind in ["create_room", "search_room", "leave_room"]:
			_set_busy(false)
		status_label.text = _friendly_error(String(payload.get("error", "Erreur réseau")))
		return
	match kind:
		"create_room", "search_room":
			_set_busy(false)
			var room: Dictionary = payload.get("room", {}) as Dictionary
			_show_room(room)
			var match_value: Variant = payload.get("match_id", null)
			if match_value != null:
				current_match_id = int(match_value)
				_on_match_found()
			else:
				poll_timer.start()
		"room":
			_show_room(payload.get("room", {}) as Dictionary)
			var match_value: Variant = payload.get("match_id", null)
			if match_value != null:
				current_match_id = int(match_value)
				_on_match_found()
		"leave_room":
			poll_timer.stop()
			current_room_id = -1
			current_match_id = -1
			room_label.text = "Aucun salon actif"
			players_label.text = ""
			leave_button.disabled = true
			_set_busy(false)
			status_label.text = "Salon quitté."

func _show_room(room: Dictionary) -> void:
	if room.is_empty():
		return
	current_room_id = int(room.get("id", -1))
	var count := int(room.get("player_count", 0))
	var target := int(room.get("target_players", selected_players))
	var base_elo := int(room.get("base_elo", 100))
	room_label.text = "Salon #%d  •  %d/%d joueurs  •  ELO base %d" % [current_room_id, count, target, base_elo]
	var lines := PackedStringArray()
	var players: Array = room.get("players", []) as Array
	for p_value: Variant in players:
		if p_value is Dictionary:
			var p := p_value as Dictionary
			lines.append("%d.  %s  —  %d ELO" % [int(p.get("seat", 0)) + 1, String(p.get("display_name", "Joueur")), int(p.get("elo", 100))])
	for i in range(players.size(), target):
		lines.append("%d.  En attente d'un joueur…" % (i + 1))
	players_label.text = "\n".join(lines)
	leave_button.disabled = false
	status_label.text = "En attente… Le salon conserve l'ELO du créateur : %d." % base_elo

func _on_match_found() -> void:
	poll_timer.stop()
	leave_button.disabled = true
	status_label.text = "PARTIE TROUVÉE • Match #%d — synchronisation du jeu en préparation." % current_match_id

func _set_busy(value: bool) -> void:
	search_button.disabled = value or not RamiNetwork.is_authenticated()
	create_button.disabled = value or not RamiNetwork.is_authenticated()
	for b_value: Variant in count_buttons.values():
		var b := b_value as Button
		b.disabled = value or current_room_id >= 0

func _friendly_error(code: String) -> String:
	match code:
		"SERVER_NOT_CONFIGURED": return "Serveur RAMI non configuré."
		"AUTH_REQUIRED": return "Connexion Google requise."
		"NETWORK_ERROR": return "Impossible de joindre le serveur RAMI."
		"INVALID_TOKEN": return "Session expirée. Reconnectez-vous."
		_: return "Erreur : %s" % code

func _label(text: String, pos: Vector2, size: Vector2, font_size: int, color: Color, parent: Control = self) -> Label:
	var l := Label.new()
	l.text = text
	l.position = pos
	l.size = size
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	parent.add_child(l)
	return l

func _panel(pos: Vector2, size: Vector2, bg: Color, border: Color, radius: int, width: int) -> Panel:
	var p := Panel.new()
	p.position = pos
	p.size = size
	p.add_theme_stylebox_override("panel", _style(bg, border, width, radius))
	add_child(p)
	return p

func _button(text: String, pos: Vector2, size: Vector2, font_size: int, bg: Color, border: Color) -> Button:
	var b := Button.new()
	b.text = text
	b.position = pos
	b.size = size
	b.add_theme_font_size_override("font_size", font_size)
	b.add_theme_color_override("font_color", TEXT)
	b.add_theme_stylebox_override("normal", _style(bg, border, 3, 18))
	b.add_theme_stylebox_override("hover", _style(bg.lightened(0.08), border.lightened(0.12), 4, 18))
	b.add_theme_stylebox_override("pressed", _style(bg.darkened(0.08), border.lightened(0.20), 4, 18))
	add_child(b)
	return b

func _button_in(text: String, pos: Vector2, size: Vector2, font_size: int, bg: Color, border: Color, parent: Control) -> Button:
	var b := Button.new()
	b.text = text
	b.position = pos
	b.size = size
	b.add_theme_font_size_override("font_size", font_size)
	b.add_theme_color_override("font_color", TEXT)
	b.add_theme_stylebox_override("normal", _style(bg, border, 3, 18))
	b.add_theme_stylebox_override("hover", _style(bg.lightened(0.08), border.lightened(0.12), 4, 18))
	b.add_theme_stylebox_override("pressed", _style(bg.darkened(0.08), border.lightened(0.20), 4, 18))
	parent.add_child(b)
	return b

func _style(bg: Color, border: Color, width: int, radius: int) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(width)
	s.set_corner_radius_all(radius)
	s.shadow_color = Color(0,0,0,0.28)
	s.shadow_size = 8
	return s
