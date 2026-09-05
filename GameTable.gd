extends Control

const GOLD := Color("#F1C96C")
const TEXT := Color("#F7F4EA")
const MUTED := Color("#CBC6B9")
const FELT := Color("#0B6A43")
const GREEN := Color("#39D28A")
const CARD_RATIO := 5.0 / 7.0

var game: RamiGame = RamiGame.new()
var selected_index: int = -1

var player_layer: Control
var opponent_layer: Control
var discard_layer: Control
var stock_layer: Control
var stock_count_label: Label
var turn_label: Label
var hand_count_label: Label
var end_button: Button
var pose_button: Button

func _ready() -> void:
	_build_static_table()
	game.new_round()
	_refresh_all()

func _build_static_table() -> void:
	_add_rect(FELT, Vector2.ZERO, Vector2(1600, 900))
	_add_rect(Color("#311A10"), Vector2(0, 0), Vector2(1600, 82))
	_add_rect(Color("#201009"), Vector2(0, 806), Vector2(1600, 94))
	_add_rect(Color(0.10, 0.45, 0.28, 0.15), Vector2(120, 92), Vector2(1360, 675))

	var back: Button = _make_button("←", Vector2(20, 14), Vector2(72, 56), 34)
	back.pressed.connect(_on_back_pressed)

	var title: Label = _make_label("Rami", Vector2(118, 4), Vector2(240, 72), 52, GOLD)
	title.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.72))
	title.add_theme_constant_override("shadow_offset_x", 3)
	title.add_theme_constant_override("shadow_offset_y", 4)

	_build_opponent_header()
	_build_score_panel()
	_build_center_zone()
	_build_piles()
	_build_turn_panel()
	_build_bottom_bar()

	opponent_layer = Control.new()
	opponent_layer.position = Vector2.ZERO
	opponent_layer.size = Vector2(1600, 260)
	add_child(opponent_layer)

	player_layer = Control.new()
	player_layer.position = Vector2.ZERO
	player_layer.size = Vector2(1600, 900)
	add_child(player_layer)

func _build_opponent_header() -> void:
	var p: Panel = _panel(Vector2(630, 8), Vector2(340, 72), Color("#0E2B28"), Color("#456F69"), 26, 2)
	var icon: Panel = _panel(Vector2(12, 8), Vector2(56, 56), Color("#14262A"), Color("#7D9895"), 28, 2, p)
	_make_label("IA", Vector2(0, 4), Vector2(56, 48), 22, TEXT, HORIZONTAL_ALIGNMENT_CENTER, icon)
	_make_label("Adversaire", Vector2(84, 7), Vector2(180, 30), 23, TEXT, HORIZONTAL_ALIGNMENT_LEFT, p)
	_make_label("14 cartes", Vector2(84, 36), Vector2(180, 26), 19, GOLD, HORIZONTAL_ALIGNMENT_LEFT, p)

func _build_score_panel() -> void:
	var p: Panel = _panel(Vector2(1324, 12), Vector2(246, 166), Color("#10151C"), Color("#41505F"), 18, 2)
	_make_label("Manche 1 / 1", Vector2(16, 8), Vector2(214, 30), 22, TEXT, HORIZONTAL_ALIGNMENT_CENTER, p)
	_make_label("Ouverture : 51 pts", Vector2(14, 40), Vector2(218, 26), 18, MUTED, HORIZONTAL_ALIGNMENT_CENTER, p)
	var sep: ColorRect = ColorRect.new()
	sep.color = Color(1, 1, 1, 0.10)
	sep.position = Vector2(14, 75)
	sep.size = Vector2(218, 2)
	p.add_child(sep)
	_make_label("Vous", Vector2(18, 87), Vector2(100, 28), 20, TEXT, HORIZONTAL_ALIGNMENT_LEFT, p)
	_make_label("0 pts", Vector2(138, 87), Vector2(88, 28), 20, TEXT, HORIZONTAL_ALIGNMENT_RIGHT, p)
	_make_label("IA", Vector2(18, 123), Vector2(100, 28), 20, TEXT, HORIZONTAL_ALIGNMENT_LEFT, p)
	_make_label("0 pts", Vector2(138, 123), Vector2(88, 28), 20, TEXT, HORIZONTAL_ALIGNMENT_RIGHT, p)

func _build_center_zone() -> void:
	var zone: Panel = _panel(Vector2(420, 275), Vector2(720, 286), Color(0.04, 0.27, 0.18, 0.18), Color(0.20, 0.65, 0.43, 0.34), 24, 3)
	_make_label("♠     ♥     ♦     ♣", Vector2(125, 70), Vector2(470, 62), 42, Color(0.63, 0.86, 0.73, 0.25), HORIZONTAL_ALIGNMENT_CENTER, zone)
	_make_label("Combinaisons posées", Vector2(125, 139), Vector2(470, 40), 27, Color(0.74, 0.88, 0.80, 0.52), HORIZONTAL_ALIGNMENT_CENTER, zone)
	_make_label("Le moteur de combinaisons arrive à l'étape suivante", Vector2(85, 187), Vector2(550, 32), 17, Color(0.78, 0.88, 0.82, 0.38), HORIZONTAL_ALIGNMENT_CENTER, zone)

func _build_piles() -> void:
	stock_layer = Control.new()
	stock_layer.position = Vector2(78, 332)
	stock_layer.size = Vector2(150, 235)
	add_child(stock_layer)

	for i in range(4):
		var p: Panel = Panel.new()
		p.position = Vector2(float(i) * 3.0, 12.0 - float(i) * 3.0)
		p.size = Vector2(118, 166)
		p.add_theme_stylebox_override("panel", _card_shadow_style())
		stock_layer.add_child(p)

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

	discard_layer = Control.new()
	discard_layer.position = Vector2(260, 332)
	discard_layer.size = Vector2(150, 235)
	add_child(discard_layer)

func _build_turn_panel() -> void:
	var p: Panel = _panel(Vector2(1175, 345), Vector2(338, 92), Color("#0C171B"), Color("#1A443A"), 20, 2)
	_make_label("▶", Vector2(20, 18), Vector2(56, 52), 34, GREEN, HORIZONTAL_ALIGNMENT_CENTER, p)
	turn_label = _make_label("", Vector2(80, 18), Vector2(238, 54), 23, TEXT, HORIZONTAL_ALIGNMENT_CENTER, p)

func _build_bottom_bar() -> void:
	var sort_button: Button = _make_button("▣  Trier", Vector2(28, 820), Vector2(195, 64), 25)
	sort_button.pressed.connect(_on_sort_pressed)

	var player: Panel = _panel(Vector2(630, 814), Vector2(340, 74), Color("#101A20"), Color("#7C8E9A"), 28, 2)
	var avatar: Panel = _panel(Vector2(12, 8), Vector2(58, 58), Color("#E9ECEC"), Color.WHITE, 30, 2, player)
	_make_label("●", Vector2(0, 4), Vector2(58, 48), 30, Color("#23323C"), HORIZONTAL_ALIGNMENT_CENTER, avatar)
	_make_label("Vous", Vector2(88, 7), Vector2(150, 30), 24, TEXT, HORIZONTAL_ALIGNMENT_LEFT, player)
	hand_count_label = _make_label("", Vector2(88, 37), Vector2(180, 26), 19, GOLD, HORIZONTAL_ALIGNMENT_LEFT, player)

	pose_button = _make_button("▣  Poser", Vector2(1035, 820), Vector2(180, 64), 25)
	pose_button.disabled = true
	pose_button.add_theme_stylebox_override("disabled", _button_style(Color("#303331"), Color("#505451"), 2, 18))
	pose_button.add_theme_color_override("font_disabled_color", Color(0.65, 0.65, 0.62, 0.75))

	end_button = _make_button("Défausser • Fin du tour", Vector2(1230, 820), Vector2(340, 64), 23, Color("#0B5E40"), GREEN)
	end_button.pressed.connect(_on_end_turn)
	_make_label("v0.0.3", Vector2(8, 884), Vector2(90, 16), 13, Color(1, 1, 1, 0.40))

func _refresh_all() -> void:
	_refresh_opponent_hand()
	_refresh_player_hand()
	_refresh_discard()
	stock_count_label.text = "%d cartes" % game.stock.size()
	hand_count_label.text = "%d cartes en main" % game.player_hand.size()
	if game.phase == "draw":
		turn_label.text = "Piochez une carte"
		end_button.disabled = true
	else:
		turn_label.text = "Choisissez une carte à défausser"
		end_button.disabled = selected_index < 0

func _refresh_opponent_hand() -> void:
	_clear_children(opponent_layer)
	var count: int = game.ai_hand.size()
	var start_x: float = 500.0
	for i in range(count):
		var y: float = 112.0 + abs(float(i) - float(count - 1) / 2.0) * 1.15
		_make_card_widget("back_red", Vector2(start_x + float(i) * 43.0, y), Vector2(60, 84), (float(i) - float(count - 1) / 2.0) * 0.38, false, -1, opponent_layer, false)

func _refresh_player_hand() -> void:
	_clear_children(player_layer)
	var count: int = game.player_hand.size()
	if count == 0:
		return
	var card_w: float = 112.0
	var card_h: float = card_w / CARD_RATIO
	var overlap: float = min(78.0, 1080.0 / max(1.0, float(count - 1)))
	var total_width: float = card_w + overlap * float(count - 1)
	var start_x: float = 800.0 - total_width / 2.0
	for i in range(count):
		var center_delta: float = float(i) - float(count - 1) / 2.0
		var lift: float = abs(center_delta) * 1.05
		var y: float = 613.0 + lift
		if i == selected_index:
			y -= 24.0
		_make_card_widget(game.player_hand[i], Vector2(start_x + float(i) * overlap, y), Vector2(card_w, card_h), center_delta * 0.18, true, i, player_layer, i == selected_index)

func _refresh_discard() -> void:
	_clear_children(discard_layer)
	var top: String = game.top_discard()
	if top != "":
		var clickable: bool = game.phase == "draw"
		_make_card_widget(top, Vector2(12, 0), Vector2(118, 166), 0.0, clickable, -1, discard_layer, false)
	_make_label("Défausse", Vector2(0, 177), Vector2(145, 28), 23, TEXT, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)
	_make_label("Touchez pour piocher", Vector2(-10, 206), Vector2(165, 24), 15, MUTED, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)

func _make_card_widget(card_id: String, pos: Vector2, card_size: Vector2, rotation: float, clickable: bool, index: int, parent: Control, selected: bool) -> Control:
	var wrapper: Control = Control.new()
	wrapper.position = pos
	wrapper.size = card_size
	wrapper.rotation_degrees = rotation
	wrapper.pivot_offset = card_size / 2.0
	parent.add_child(wrapper)

	var frame: Panel = Panel.new()
	frame.position = Vector2.ZERO
	frame.size = card_size
	var st: StyleBoxFlat = StyleBoxFlat.new()
	st.bg_color = Color("#FFFDF8")
	st.border_color = GREEN if selected else Color(0, 0, 0, 0.52)
	st.set_border_width_all(4 if selected else 2)
	st.set_corner_radius_all(9)
	st.shadow_color = Color(0, 0, 0, 0.34)
	st.shadow_size = 8
	frame.add_theme_stylebox_override("panel", st)
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
		else:
			button.pressed.connect(_on_draw_discard)
	return wrapper

func _load_card_texture(card_id: String) -> Texture2D:
	var path: String = "res://assets/cards/%s.png" % card_id
	var tex: Resource = load(path)
	if tex is Texture2D:
		return tex as Texture2D
	return null

func _on_draw_stock() -> void:
	if game.draw_stock():
		selected_index = game.player_hand.size() - 1
		_refresh_all()

func _on_draw_discard() -> void:
	if game.draw_discard():
		selected_index = game.player_hand.size() - 1
		_refresh_all()

func _on_player_card_pressed(index: int) -> void:
	if index < 0 or index >= game.player_hand.size():
		return
	selected_index = -1 if selected_index == index else index
	_refresh_all()

func _on_end_turn() -> void:
	if selected_index < 0:
		return
	if game.discard_player(selected_index):
		selected_index = -1
		_refresh_all()

func _on_sort_pressed() -> void:
	game.sort_player_hand()
	selected_index = -1
	_refresh_all()

func _card_shadow_style() -> StyleBoxFlat:
	var st: StyleBoxFlat = StyleBoxFlat.new()
	st.bg_color = Color("#F3F0E9")
	st.border_color = Color(0, 0, 0, 0.45)
	st.set_border_width_all(2)
	st.set_corner_radius_all(8)
	st.shadow_color = Color(0, 0, 0, 0.30)
	st.shadow_size = 7
	return st

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
	b.add_theme_color_override("font_hover_color", Color.WHITE)
	b.add_theme_stylebox_override("normal", _button_style(bg, border, 2, 18))
	b.add_theme_stylebox_override("hover", _button_style(bg.lightened(0.08), border.lightened(0.10), 3, 18))
	b.add_theme_stylebox_override("pressed", _button_style(bg.darkened(0.08), border.lightened(0.18), 3, 18))
	add_child(b)
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
	for child in node.get_children():
		child.queue_free()

func _on_back_pressed() -> void:
	get_tree().change_scene_to_file("res://Main.tscn")
