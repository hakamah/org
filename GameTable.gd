extends Control

const GOLD: Color = Color("#F1C96C")
const TEXT: Color = Color("#F7F4EA")
const MUTED: Color = Color("#CBC6B9")
const FELT: Color = Color("#0B6A43")
const GREEN: Color = Color("#39D28A")
const RED: Color = Color("#E65A61")

var game: RamiGame = RamiGame.new()
var selected_indices: Array[int] = []

var opponent_layer: Control
var player_layer: Control
var discard_layer: Control
var meld_layer: Control
var modal_layer: Control
var stock_count_label: Label
var opponent_count_label: Label
var player_count_label: Label
var player_open_label: Label
var ai_open_label: Label
var turn_label: Label
var status_label: Label
var pose_button: Button
var discard_button: Button

func _ready() -> void:
	_build_ui()
	game.new_round()
	_refresh_all()

func _build_ui() -> void:
	_add_rect(FELT, Vector2.ZERO, Vector2(1600, 900))
	_add_rect(Color("#311A10"), Vector2(0, 0), Vector2(1600, 82))
	_add_rect(Color("#201009"), Vector2(0, 806), Vector2(1600, 94))
	_add_rect(Color(0.10, 0.45, 0.28, 0.15), Vector2(120, 92), Vector2(1360, 675))

	var back: Button = _make_button("←", Vector2(20, 14), Vector2(72, 56), 34)
	back.pressed.connect(_on_back_pressed)
	var title: Label = _make_label("Rami", Vector2(118, 4), Vector2(250, 72), 52, GOLD)
	title.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.72))
	title.add_theme_constant_override("shadow_offset_x", 3)
	title.add_theme_constant_override("shadow_offset_y", 4)

	var ai_panel: Panel = _panel(Vector2(630, 8), Vector2(340, 72), Color("#0E2B28"), Color("#456F69"), 26, 2)
	_make_label("IA", Vector2(18, 8), Vector2(55, 55), 22, TEXT, HORIZONTAL_ALIGNMENT_CENTER, ai_panel)
	_make_label("Adversaire", Vector2(84, 5), Vector2(170, 28), 22, TEXT, HORIZONTAL_ALIGNMENT_LEFT, ai_panel)
	opponent_count_label = _make_label("", Vector2(84, 34), Vector2(105, 25), 18, GOLD, HORIZONTAL_ALIGNMENT_LEFT, ai_panel)
	ai_open_label = _make_label("", Vector2(190, 34), Vector2(135, 25), 16, MUTED, HORIZONTAL_ALIGNMENT_RIGHT, ai_panel)

	var info: Panel = _panel(Vector2(1322, 12), Vector2(250, 166), Color("#10151C"), Color("#41505F"), 18, 2)
	_make_label("PARTIE SOLO", Vector2(16, 8), Vector2(218, 30), 22, TEXT, HORIZONTAL_ALIGNMENT_CENTER, info)
	_make_label("Ouverture : 51 pts", Vector2(16, 40), Vector2(218, 26), 18, MUTED, HORIZONTAL_ALIGNMENT_CENTER, info)
	_make_label("+ tierce franche", Vector2(16, 66), Vector2(218, 22), 15, MUTED, HORIZONTAL_ALIGNMENT_CENTER, info)
	_make_label("Vous", Vector2(18, 96), Vector2(75, 26), 19, TEXT, HORIZONTAL_ALIGNMENT_LEFT, info)
	player_open_label = _make_label("", Vector2(94, 96), Vector2(138, 26), 16, MUTED, HORIZONTAL_ALIGNMENT_RIGHT, info)
	_make_label("IA", Vector2(18, 130), Vector2(75, 26), 19, TEXT, HORIZONTAL_ALIGNMENT_LEFT, info)
	_make_label("Même règle", Vector2(94, 130), Vector2(138, 26), 15, MUTED, HORIZONTAL_ALIGNMENT_RIGHT, info)

	_panel(Vector2(420, 275), Vector2(720, 286), Color(0.04, 0.27, 0.18, 0.20), Color(0.20, 0.65, 0.43, 0.34), 24, 3)
	_make_label("TABLE", Vector2(690, 282), Vector2(180, 28), 18, Color(0.75, 0.9, 0.82, 0.55), HORIZONTAL_ALIGNMENT_CENTER)
	meld_layer = Control.new()
	meld_layer.position = Vector2(425, 313)
	meld_layer.size = Vector2(710, 242)
	add_child(meld_layer)
	status_label = _make_label("", Vector2(420, 568), Vector2(720, 34), 18, TEXT, HORIZONTAL_ALIGNMENT_CENTER)

	_build_stock()
	discard_layer = Control.new()
	discard_layer.position = Vector2(260, 332)
	discard_layer.size = Vector2(150, 235)
	add_child(discard_layer)

	var turn_panel: Panel = _panel(Vector2(1175, 345), Vector2(338, 104), Color("#0C171B"), Color("#1A443A"), 20, 2)
	_make_label("▶", Vector2(18, 20), Vector2(50, 48), 32, GREEN, HORIZONTAL_ALIGNMENT_CENTER, turn_panel)
	turn_label = _make_label("", Vector2(70, 14), Vector2(250, 76), 20, TEXT, HORIZONTAL_ALIGNMENT_CENTER, turn_panel)

	opponent_layer = Control.new()
	opponent_layer.position = Vector2.ZERO
	opponent_layer.size = Vector2(1600, 260)
	add_child(opponent_layer)
	player_layer = Control.new()
	player_layer.position = Vector2.ZERO
	player_layer.size = Vector2(1600, 900)
	add_child(player_layer)

	var sort_button: Button = _make_button("▣  Trier", Vector2(28, 820), Vector2(185, 64), 24)
	sort_button.pressed.connect(_on_sort_pressed)
	var clear_button: Button = _make_button("Annuler sélection", Vector2(225, 820), Vector2(225, 64), 20)
	clear_button.pressed.connect(_on_clear_selection)

	var me: Panel = _panel(Vector2(610, 814), Vector2(350, 74), Color("#101A20"), Color("#7C8E9A"), 28, 2)
	_make_label("●", Vector2(12, 8), Vector2(58, 58), 30, Color("#D7E0E5"), HORIZONTAL_ALIGNMENT_CENTER, me)
	_make_label("Vous", Vector2(88, 7), Vector2(150, 30), 24, TEXT, HORIZONTAL_ALIGNMENT_LEFT, me)
	player_count_label = _make_label("", Vector2(88, 37), Vector2(210, 26), 18, GOLD, HORIZONTAL_ALIGNMENT_LEFT, me)

	pose_button = _make_button("▣  Poser", Vector2(1000, 820), Vector2(190, 64), 24, Color("#6A4A0C"), GOLD)
	pose_button.pressed.connect(_on_pose_pressed)
	discard_button = _make_button("Défausser • Fin du tour", Vector2(1205, 820), Vector2(365, 64), 22, Color("#0B5E40"), GREEN)
	discard_button.pressed.connect(_on_discard_pressed)
	_make_label("v0.0.4 PLAYABLE", Vector2(8, 884), Vector2(165, 16), 13, Color(1, 1, 1, 0.42))

	modal_layer = Control.new()
	modal_layer.position = Vector2.ZERO
	modal_layer.size = Vector2(1600, 900)
	modal_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(modal_layer)

func _build_stock() -> void:
	var stock_layer: Control = Control.new()
	stock_layer.position = Vector2(78, 332)
	stock_layer.size = Vector2(150, 235)
	add_child(stock_layer)
	for i: int in range(4):
		var shadow: Panel = Panel.new()
		shadow.position = Vector2(float(i) * 3.0, 12.0 - float(i) * 3.0)
		shadow.size = Vector2(118, 166)
		shadow.add_theme_stylebox_override("panel", _card_style(false))
		stock_layer.add_child(shadow)
	var stock_button: TextureButton = TextureButton.new()
	stock_button.position = Vector2(12, 0)
	stock_button.size = Vector2(118, 166)
	stock_button.ignore_texture_size = true
	stock_button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	stock_button.texture_normal = _load_card_texture("back_red")
	stock_button.pressed.connect(_on_draw_stock)
	stock_layer.add_child(stock_button)
	_make_label("Pioche", Vector2(0, 177), Vector2(145, 28), 23, TEXT, HORIZONTAL_ALIGNMENT_CENTER, stock_layer)
	stock_count_label = _make_label("", Vector2(0, 206), Vector2(145, 24), 17, MUTED, HORIZONTAL_ALIGNMENT_CENTER, stock_layer)

func _refresh_all() -> void:
	_refresh_opponent()
	_refresh_player()
	_refresh_discard()
	_refresh_melds()
	stock_count_label.text = "%d cartes" % game.stock.size()
	opponent_count_label.text = "%d cartes" % game.ai_hand.size()
	player_count_label.text = "%d cartes en main" % game.player_hand.size()
	player_open_label.text = "OUVERT" if game.player_opened else "Non ouvert"
	player_open_label.add_theme_color_override("font_color", GREEN if game.player_opened else MUTED)
	ai_open_label.text = "OUVERT" if game.ai_opened else "Non ouvert"
	ai_open_label.add_theme_color_override("font_color", GREEN if game.ai_opened else MUTED)
	status_label.text = game.last_message

	if game.winner != "":
		turn_label.text = "Partie terminée"
		pose_button.disabled = true
		discard_button.disabled = true
		_show_game_over()
	elif game.phase == "draw":
		turn_label.text = "À VOUS\nPiochez une carte"
		pose_button.disabled = true
		discard_button.disabled = true
	else:
		turn_label.text = "À VOUS\nPosez ou défaussez"
		pose_button.disabled = selected_indices.size() < 3
		discard_button.disabled = selected_indices.size() != 1

func _refresh_opponent() -> void:
	_clear_children(opponent_layer)
	var count: int = game.ai_hand.size()
	if count <= 0:
		return
	var overlap: float = 43.0
	if count > 16:
		overlap = 600.0 / maxf(1.0, float(count - 1))
	var total: float = 60.0 + overlap * float(maxi(0, count - 1))
	var start_x: float = 800.0 - total / 2.0
	for i: int in range(count):
		var y: float = 112.0 + absf(float(i) - float(count - 1) / 2.0) * 1.05
		_make_card("back_red", Vector2(start_x + float(i) * overlap, y), Vector2(60, 84), false, -1, opponent_layer, false)

func _refresh_player() -> void:
	_clear_children(player_layer)
	var count: int = game.player_hand.size()
	if count <= 0:
		return
	var card_w: float = 112.0
	var card_h: float = 157.0
	var divisor: float = maxf(1.0, float(count - 1))
	var overlap: float = minf(78.0, 1080.0 / divisor)
	var total_width: float = card_w + overlap * float(count - 1)
	var start_x: float = 800.0 - total_width / 2.0
	for i: int in range(count):
		var center_delta: float = float(i) - float(count - 1) / 2.0
		var y: float = 615.0 + absf(center_delta) * 0.9
		var selected: bool = selected_indices.has(i)
		if selected:
			y -= 28.0
		_make_card(game.player_hand[i], Vector2(start_x + float(i) * overlap, y), Vector2(card_w, card_h), game.phase == "discard", i, player_layer, selected)

func _refresh_discard() -> void:
	_clear_children(discard_layer)
	var top: String = game.top_discard()
	if top != "":
		_make_card(top, Vector2(12, 0), Vector2(118, 166), game.phase == "draw", -1, discard_layer, false)
	_make_label("Défausse", Vector2(0, 177), Vector2(145, 28), 23, TEXT, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)
	_make_label("Touchez pour prendre", Vector2(-10, 206), Vector2(165, 24), 15, MUTED, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)

func _refresh_melds() -> void:
	_clear_children(meld_layer)
	if game.table_melds.is_empty():
		_make_label("Aucune combinaison posée", Vector2(155, 82), Vector2(400, 40), 22, Color(0.75, 0.88, 0.80, 0.45), HORIZONTAL_ALIGNMENT_CENTER, meld_layer)
		return
	var x: float = 12.0
	var y: float = 25.0
	for meld: Dictionary in game.table_melds:
		var cards: Array = meld.get("cards", [])
		var owner: String = String(meld.get("owner", ""))
		var w: float = 54.0
		var h: float = 76.0
		var meld_width: float = 20.0 * float(maxi(0, cards.size() - 1)) + w
		if x + meld_width > 690.0:
			x = 12.0
			y += 105.0
		if y > 145.0:
			break
		var owner_color: Color = GREEN if owner == "player" else RED
		_make_label("VOUS" if owner == "player" else "IA", Vector2(x, y - 20), Vector2(65, 18), 11, owner_color, HORIZONTAL_ALIGNMENT_LEFT, meld_layer)
		for i: int in range(cards.size()):
			_make_card(String(cards[i]), Vector2(x + float(i) * 20.0, y), Vector2(w, h), false, -2, meld_layer, false)
		x += meld_width + 20.0

func _make_card(card_id: String, pos: Vector2, card_size: Vector2, clickable: bool, index: int, parent: Control, selected: bool) -> Control:
	var wrapper: Control = Control.new()
	wrapper.position = pos
	wrapper.size = card_size
	parent.add_child(wrapper)
	var frame: Panel = Panel.new()
	frame.position = Vector2.ZERO
	frame.size = card_size
	frame.add_theme_stylebox_override("panel", _card_style(selected))
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	wrapper.add_child(frame)
	var button: TextureButton = TextureButton.new()
	button.position = Vector2(3, 3)
	button.size = card_size - Vector2(6, 6)
	button.ignore_texture_size = true
	button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	button.texture_normal = _load_card_texture(card_id)
	button.disabled = not clickable
	wrapper.add_child(button)
	if clickable:
		if index >= 0:
			button.pressed.connect(_on_player_card_pressed.bind(index))
		elif index == -1:
			button.pressed.connect(_on_draw_discard)
	return wrapper

func _card_style(selected: bool) -> StyleBoxFlat:
	var st: StyleBoxFlat = StyleBoxFlat.new()
	st.bg_color = Color("#FFFDF8")
	st.border_color = GOLD if selected else Color(0, 0, 0, 0.48)
	st.set_border_width_all(5 if selected else 2)
	st.set_corner_radius_all(9)
	st.shadow_color = Color(0, 0, 0, 0.32)
	st.shadow_size = 7
	return st

func _load_card_texture(card_id: String) -> Texture2D:
	var resource: Resource = load("res://assets/cards/%s.png" % card_id)
	if resource is Texture2D:
		return resource as Texture2D
	return null

func _on_draw_stock() -> void:
	if game.draw_stock():
		selected_indices.clear()
		_refresh_all()

func _on_draw_discard() -> void:
	if game.draw_discard():
		selected_indices.clear()
		_refresh_all()

func _on_player_card_pressed(index: int) -> void:
	if game.phase != "discard":
		return
	if selected_indices.has(index):
		selected_indices.erase(index)
	else:
		selected_indices.append(index)
	selected_indices.sort()
	_refresh_all()

func _on_pose_pressed() -> void:
	if selected_indices.size() < 3:
		return
	var result: Dictionary = game.play_player_selection(selected_indices)
	if bool(result.get("ok", false)):
		selected_indices.clear()
	else:
		game.last_message = String(result.get("message", "Pose invalide."))
	_refresh_all()

func _on_discard_pressed() -> void:
	if selected_indices.size() != 1:
		game.last_message = "Sélectionnez exactement 1 carte à défausser."
		_refresh_all()
		return
	if game.discard_player(selected_indices[0]):
		selected_indices.clear()
		_refresh_all()

func _on_sort_pressed() -> void:
	game.sort_player_hand()
	selected_indices.clear()
	_refresh_all()

func _on_clear_selection() -> void:
	selected_indices.clear()
	_refresh_all()

func _show_game_over() -> void:
	if modal_layer.get_child_count() > 0:
		return
	modal_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	var shade: ColorRect = ColorRect.new()
	shade.color = Color(0, 0, 0, 0.68)
	shade.position = Vector2.ZERO
	shade.size = Vector2(1600, 900)
	shade.mouse_filter = Control.MOUSE_FILTER_STOP
	modal_layer.add_child(shade)
	var border: Color = GOLD if game.winner == "player" else RED
	var box: Panel = _panel(Vector2(480, 270), Vector2(640, 350), Color("#101A20"), border, 28, 4, modal_layer)
	var heading: String = "VICTOIRE !" if game.winner == "player" else "DÉFAITE"
	_make_label(heading, Vector2(40, 35), Vector2(560, 80), 54, border, HORIZONTAL_ALIGNMENT_CENTER, box)
	var detail: String = "Vous avez vidé votre main." if game.winner == "player" else "L'IA a vidé sa main."
	_make_label(detail, Vector2(45, 125), Vector2(550, 48), 24, TEXT, HORIZONTAL_ALIGNMENT_CENTER, box)
	var replay: Button = _make_button_in("REJOUER", Vector2(125, 220), Vector2(390, 76), 28, Color("#0B5E40"), GREEN, box)
	replay.pressed.connect(_on_replay)

func _on_replay() -> void:
	for child: Node in modal_layer.get_children():
		child.free()
	modal_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	selected_indices.clear()
	game.new_round()
	_refresh_all()

func _panel(pos: Vector2, sz: Vector2, bg: Color, border: Color, radius: int, width: int, parent: Control = self) -> Panel:
	var p: Panel = Panel.new()
	p.position = pos
	p.size = sz
	var st: StyleBoxFlat = StyleBoxFlat.new()
	st.bg_color = bg
	st.border_color = border
	st.set_border_width_all(width)
	st.set_corner_radius_all(radius)
	st.shadow_color = Color(0, 0, 0, 0.28)
	st.shadow_size = 7
	p.add_theme_stylebox_override("panel", st)
	parent.add_child(p)
	return p

func _add_rect(color: Color, pos: Vector2, sz: Vector2) -> ColorRect:
	var r: ColorRect = ColorRect.new()
	r.color = color
	r.position = pos
	r.size = sz
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(r)
	return r

func _make_label(text_value: String, pos: Vector2, sz: Vector2, font_size: int, color: Color, align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT, parent: Control = self) -> Label:
	var l: Label = Label.new()
	l.text = text_value
	l.position = pos
	l.size = sz
	l.horizontal_alignment = align
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	parent.add_child(l)
	return l

func _make_button(text_value: String, pos: Vector2, sz: Vector2, font_size: int, bg: Color = Color("#14242B"), border: Color = Color("#4E6A7A")) -> Button:
	var b: Button = Button.new()
	b.text = text_value
	b.position = pos
	b.size = sz
	b.add_theme_font_size_override("font_size", font_size)
	b.add_theme_color_override("font_color", TEXT)
	b.add_theme_stylebox_override("normal", _button_style(bg, border, 2, 18))
	b.add_theme_stylebox_override("hover", _button_style(bg.lightened(0.08), border.lightened(0.10), 3, 18))
	b.add_theme_stylebox_override("pressed", _button_style(bg.darkened(0.08), border.lightened(0.18), 3, 18))
	add_child(b)
	return b

func _make_button_in(text_value: String, pos: Vector2, sz: Vector2, font_size: int, bg: Color, border: Color, parent: Control) -> Button:
	var b: Button = Button.new()
	b.text = text_value
	b.position = pos
	b.size = sz
	b.add_theme_font_size_override("font_size", font_size)
	b.add_theme_color_override("font_color", TEXT)
	b.add_theme_stylebox_override("normal", _button_style(bg, border, 3, 20))
	b.add_theme_stylebox_override("hover", _button_style(bg.lightened(0.08), border.lightened(0.10), 4, 20))
	b.add_theme_stylebox_override("pressed", _button_style(bg.darkened(0.08), border.lightened(0.18), 4, 20))
	parent.add_child(b)
	return b

func _button_style(bg: Color, border: Color, width: int, radius: int) -> StyleBoxFlat:
	var st: StyleBoxFlat = StyleBoxFlat.new()
	st.bg_color = bg
	st.border_color = border
	st.set_border_width_all(width)
	st.set_corner_radius_all(radius)
	st.shadow_color = Color(0, 0, 0, 0.32)
	st.shadow_size = 7
	return st

func _clear_children(node: Node) -> void:
	for child: Node in node.get_children():
		child.queue_free()

func _on_back_pressed() -> void:
	get_tree().change_scene_to_file("res://Main.tscn")
