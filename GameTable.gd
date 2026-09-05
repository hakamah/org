extends Control

const GOLD := Color("#F1C96C")
const TEXT := Color("#F7F4EA")
const MUTED := Color("#CBC6B9")
const FELT := Color("#0B6A43")
const FELT_DARK := Color("#075437")
const WOOD := Color("#2A160D")
const PANEL := Color("#0C171B")
const GREEN := Color("#39D28A")

func _ready() -> void:
	_build_table()

func _build_table() -> void:
	_add_rect(FELT, Vector2.ZERO, Vector2(1600, 900))
	_add_rect(Color("#311A10"), Vector2(0, 0), Vector2(1600, 84))
	_add_rect(Color("#201009"), Vector2(0, 805), Vector2(1600, 95))
	_add_rect(Color(0.1, 0.45, 0.28, 0.16), Vector2(120, 90), Vector2(1360, 675))

	var back := _make_button("←", Vector2(22, 16), Vector2(72, 58), 34)
	back.pressed.connect(_on_back_pressed)

	var title := _make_label("Rami", Vector2(122, 8), Vector2(250, 72), 54, GOLD)
	title.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.72))
	title.add_theme_constant_override("shadow_offset_x", 3)
	title.add_theme_constant_override("shadow_offset_y", 4)
	_make_label("♠", Vector2(233, 58), Vector2(42, 32), 26, GOLD)

	_build_opponent_header()
	_build_score_panel()
	_build_opponent_hand()
	_build_center_zone()
	_build_piles()
	_build_turn_panel()
	_build_player_hand()
	_build_bottom_bar()

func _build_opponent_header() -> void:
	var p := _panel(Vector2(635, 10), Vector2(330, 75), Color("#0E2B28"), Color("#456F69"), 26, 2)
	var icon := _panel(Vector2(12, 9), Vector2(58, 58), Color("#14262A"), Color("#7D9895"), 30, 2, p)
	_make_label("IA", Vector2(0, 4), Vector2(58, 48), 23, TEXT, HORIZONTAL_ALIGNMENT_CENTER, icon)
	_make_label("IA", Vector2(86, 9), Vector2(150, 30), 24, TEXT, HORIZONTAL_ALIGNMENT_LEFT, p)
	_make_label("0 pts", Vector2(86, 38), Vector2(150, 28), 22, GOLD, HORIZONTAL_ALIGNMENT_LEFT, p)

func _build_score_panel() -> void:
	var p := _panel(Vector2(1320, 14), Vector2(250, 172), Color("#10151C"), Color("#41505F"), 18, 2)
	_make_label("Manche 1 / 1", Vector2(18, 10), Vector2(214, 32), 23, TEXT, HORIZONTAL_ALIGNMENT_CENTER, p)
	_make_label("Objectif : 51 points", Vector2(16, 42), Vector2(218, 28), 19, MUTED, HORIZONTAL_ALIGNMENT_CENTER, p)
	var sep := ColorRect.new()
	sep.color = Color(1, 1, 1, 0.10)
	sep.position = Vector2(14, 79)
	sep.size = Vector2(222, 2)
	p.add_child(sep)
	_make_label("Vous", Vector2(20, 92), Vector2(100, 28), 20, TEXT, HORIZONTAL_ALIGNMENT_LEFT, p)
	_make_label("0 pts", Vector2(140, 92), Vector2(88, 28), 20, TEXT, HORIZONTAL_ALIGNMENT_RIGHT, p)
	_make_label("IA", Vector2(20, 128), Vector2(100, 28), 20, TEXT, HORIZONTAL_ALIGNMENT_LEFT, p)
	_make_label("0 pts", Vector2(140, 128), Vector2(88, 28), 20, TEXT, HORIZONTAL_ALIGNMENT_RIGHT, p)

func _build_opponent_hand() -> void:
	var start_x := 500.0
	for i in range(14):
		var y := 112.0 + abs(float(i) - 6.5) * 1.2
		var card := PanelContainer.new()
		card.position = Vector2(start_x + i * 43.0, y)
		card.size = Vector2(60, 90)
		card.rotation_degrees = (float(i) - 6.5) * 0.38
		card.add_theme_stylebox_override("panel", _card_back_style())
		add_child(card)
		var inner := Panel.new()
		inner.position = Vector2(6, 6)
		inner.size = Vector2(48, 78)
		var s := StyleBoxFlat.new()
		s.bg_color = Color("#285A99")
		s.border_color = Color("#88A9D5")
		s.set_border_width_all(1)
		s.set_corner_radius_all(4)
		inner.add_theme_stylebox_override("panel", s)
		card.add_child(inner)
		_make_label("◇", Vector2(0, 17), Vector2(48, 42), 26, Color("#B7CAE6"), HORIZONTAL_ALIGNMENT_CENTER, inner)

func _build_center_zone() -> void:
	var zone := _panel(Vector2(420, 286), Vector2(720, 275), Color(0.04, 0.27, 0.18, 0.18), Color(0.20, 0.65, 0.43, 0.34), 24, 3)
	_make_label("♠     ♥     ♦     ♣", Vector2(125, 74), Vector2(470, 62), 42, Color(0.63, 0.86, 0.73, 0.26), HORIZONTAL_ALIGNMENT_CENTER, zone)
	_make_label("Combinaisons posées", Vector2(130, 144), Vector2(460, 40), 27, Color(0.74, 0.88, 0.80, 0.50), HORIZONTAL_ALIGNMENT_CENTER, zone)
	_make_label("La table sera interactive à l'étape suivante", Vector2(110, 188), Vector2(500, 32), 17, Color(0.78, 0.88, 0.82, 0.35), HORIZONTAL_ALIGNMENT_CENTER, zone)

func _build_piles() -> void:
	for i in range(5):
		var back := PanelContainer.new()
		back.position = Vector2(82 + i * 3, 345 - i * 3)
		back.size = Vector2(118, 166)
		back.add_theme_stylebox_override("panel", _card_back_style())
		add_child(back)
	var top_back := Panel.new()
	top_back.position = Vector2(94, 333)
	top_back.size = Vector2(118, 166)
	top_back.add_theme_stylebox_override("panel", _card_back_style())
	add_child(top_back)
	var inner := Panel.new()
	inner.position = Vector2(9, 9)
	inner.size = Vector2(100, 148)
	var s := StyleBoxFlat.new()
	s.bg_color = Color("#285A99")
	s.border_color = Color("#91B1DC")
	s.set_border_width_all(2)
	s.set_corner_radius_all(7)
	inner.add_theme_stylebox_override("panel", s)
	top_back.add_child(inner)
	_make_label("◇", Vector2(0, 43), Vector2(100, 60), 46, Color("#C5D6ED"), HORIZONTAL_ALIGNMENT_CENTER, inner)
	_make_label("Pioche", Vector2(74, 514), Vector2(150, 32), 24, TEXT, HORIZONTAL_ALIGNMENT_CENTER)
	_make_label("32 cartes", Vector2(74, 548), Vector2(150, 28), 18, TEXT, HORIZONTAL_ALIGNMENT_CENTER)

	_create_face_card("10", "♥", Vector2(265, 345), Vector2(118, 166))
	_make_label("Défausse", Vector2(248, 514), Vector2(155, 32), 24, TEXT, HORIZONTAL_ALIGNMENT_CENTER)

func _build_turn_panel() -> void:
	var p := _panel(Vector2(1180, 350), Vector2(330, 90), Color("#0C171B"), Color("#1A443A"), 20, 2)
	var tri := Label.new()
	tri.text = "▶"
	tri.position = Vector2(25, 19)
	tri.size = Vector2(55, 52)
	tri.add_theme_font_size_override("font_size", 36)
	tri.add_theme_color_override("font_color", GREEN)
	p.add_child(tri)
	_make_label("À vous de jouer", Vector2(83, 22), Vector2(220, 46), 25, TEXT, HORIZONTAL_ALIGNMENT_CENTER, p)

func _build_player_hand() -> void:
	var cards := [
		["3", "♣"], ["5", "♣"], ["6", "♣"], ["7", "♣"],
		["9", "♥"], ["10", "♥"], ["J", "♥"], ["Q", "♥"],
		["4", "♠"], ["4", "♦"], ["4", "♣"], ["8", "♦"],
		["K", "♠"], ["A", "♥"]
	]
	var start_x := 243.0
	for i in range(cards.size()):
		var lift := abs(float(i) - 6.5) * 1.1
		_create_face_card(cards[i][0], cards[i][1], Vector2(start_x + i * 78.0, 606 + lift), Vector2(112, 190), (float(i) - 6.5) * 0.20)

func _build_bottom_bar() -> void:
	var sort_btn := _make_button("▣  Trier", Vector2(28, 820), Vector2(195, 64), 25)
	sort_btn.pressed.connect(_noop)

	var player := _panel(Vector2(638, 814), Vector2(330, 74), Color("#101A20"), Color("#7C8E9A"), 28, 2)
	var avatar := _panel(Vector2(12, 8), Vector2(58, 58), Color("#E9ECEC"), Color.WHITE, 30, 2, player)
	_make_label("●", Vector2(0, 4), Vector2(58, 48), 30, Color("#23323C"), HORIZONTAL_ALIGNMENT_CENTER, avatar)
	_make_label("Vous", Vector2(88, 8), Vector2(150, 30), 24, TEXT, HORIZONTAL_ALIGNMENT_LEFT, player)
	_make_label("0 pts", Vector2(88, 38), Vector2(150, 26), 21, GOLD, HORIZONTAL_ALIGNMENT_LEFT, player)

	var pose := _make_button("▣  Poser", Vector2(1060, 820), Vector2(180, 64), 25)
	pose.disabled = true
	pose.add_theme_stylebox_override("disabled", _button_style(Color("#303331"), Color("#505451"), 2, 18))
	pose.add_theme_color_override("font_disabled_color", Color(0.65, 0.65, 0.62, 0.75))

	var end := _make_button("▶  Fin du tour", Vector2(1255, 820), Vector2(315, 64), 25, Color("#0B5E40"), GREEN)
	end.pressed.connect(_noop)
	_make_label("v0.0.2", Vector2(8, 884), Vector2(90, 16), 13, Color(1, 1, 1, 0.40))

func _create_face_card(rank: String, suit: String, pos: Vector2, card_size: Vector2, rotation: float = 0.0) -> void:
	var red := suit == "♥" or suit == "♦"
	var ink := Color("#C7272D") if red else Color("#101820")
	var card := PanelContainer.new()
	card.position = pos
	card.size = card_size
	card.rotation_degrees = rotation
	var st := StyleBoxFlat.new()
	st.bg_color = Color("#FFFDF8")
	st.border_color = Color("#DFDDD5")
	st.set_border_width_all(2)
	st.set_corner_radius_all(10)
	st.shadow_color = Color(0, 0, 0, 0.30)
	st.shadow_size = 8
	card.add_theme_stylebox_override("panel", st)
	add_child(card)
	_make_label(rank, Vector2(10, 7), Vector2(card_size.x - 20, 34), int(card_size.y * 0.18), ink, HORIZONTAL_ALIGNMENT_LEFT, card)
	_make_label(suit, Vector2(8, 36), Vector2(card_size.x - 16, card_size.y - 60), int(card_size.y * 0.34), ink, HORIZONTAL_ALIGNMENT_CENTER, card)

func _card_back_style() -> StyleBoxFlat:
	var st := StyleBoxFlat.new()
	st.bg_color = Color("#F1EEE8")
	st.border_color = Color("#D8D7D3")
	st.set_border_width_all(2)
	st.set_corner_radius_all(8)
	st.shadow_color = Color(0, 0, 0, 0.30)
	st.shadow_size = 7
	return st

func _panel(pos: Vector2, sz: Vector2, bg: Color, border: Color, radius: int, width: int, parent: Control = self) -> Panel:
	var p := Panel.new()
	p.position = pos
	p.size = sz
	var st := StyleBoxFlat.new()
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
	var r := ColorRect.new()
	r.color = color
	r.position = pos
	r.size = sz
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(r)
	return r

func _make_label(text_value: String, pos: Vector2, sz: Vector2, font_size: int, color: Color, align: HorizontalAlignment = HORIZONTAL_ALIGNMENT_LEFT, parent: Control = self) -> Label:
	var l := Label.new()
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
	var b := Button.new()
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
	var st := StyleBoxFlat.new()
	st.bg_color = bg
	st.border_color = border
	st.set_border_width_all(width)
	st.set_corner_radius_all(radius)
	st.shadow_color = Color(0, 0, 0, 0.32)
	st.shadow_size = 7
	return st

func _on_back_pressed() -> void:
	get_tree().change_scene_to_file("res://Main.tscn")

func _noop() -> void:
	pass
