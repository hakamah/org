extends Control

const GOLD: Color = Color("#F1C96C")
const TEXT: Color = Color("#F7F4EA")
const MUTED: Color = Color("#CBC6B9")
const FELT: Color = Color("#0B6A43")
const GREEN: Color = Color("#39D28A")
const RED: Color = Color("#E65A61")
const BLUE: Color = Color("#4BA3FF")
const VIOLET: Color = Color("#B978FF")
const ORANGE: Color = Color("#F3A444")
const PINK: Color = Color("#F474B7")
const CYAN: Color = Color("#44D8D2")
const COMBO_COLORS: Array[Color] = [BLUE, VIOLET, ORANGE, PINK, CYAN, GOLD, GREEN]

var game: RamiGame = RamiGame.new()
var selected_indices: Array[int] = []
var selected_detected_combo: int = -1
var detected_combos: Array[Dictionary] = []
var deal_animation_done: bool = false

var player_layer: Control
var ai1_layer: Control
var ai2_layer: Control
var discard_layer: Control
var meld_layer: Control
var combo_layer: Control
var modal_layer: Control
var stock_count_label: Label
var player_count_label: Label
var ai1_count_label: Label
var ai2_count_label: Label
var status_label: Label
var turn_label: Label
var score_label: Label
var sort_button: Button
var discard_button: Button
var table_button: Button

func _ready() -> void:
	print("RAMI_RUNTIME: ready_start")
	_build_ui()
	game.set_opening_rule(RamiGame.OpeningRule.SIMPLE_MELD)
	game.new_round()
	print("RAMI_RUNTIME: dealt player=", game.player_hand.size(), " ai1=", game.ai1_hand.size(), " ai2=", game.ai2_hand.size(), " stock=", game.stock.size(), " discard=", game.discard_pile.size())
	_refresh_all()
	print("RAMI_RUNTIME: refresh_ok player_nodes=", player_layer.get_child_count(), " ai1_nodes=", ai1_layer.get_child_count(), " ai2_nodes=", ai2_layer.get_child_count())
	_play_deal_animation()

func _build_ui() -> void:
	_add_rect(FELT, Vector2.ZERO, Vector2(1600, 900))
	_add_rect(Color("#30180E"), Vector2(0, 0), Vector2(1600, 76))
	_add_rect(Color("#201009"), Vector2(0, 805), Vector2(1600, 95))
	_add_rect(Color(0.10, 0.45, 0.28, 0.14), Vector2(95, 84), Vector2(1410, 690))

	var back: Button = _make_button("←", Vector2(16, 10), Vector2(70, 54), 32)
	back.pressed.connect(_on_back_pressed)
	_make_label("RAMI", Vector2(100, 3), Vector2(245, 66), 46, GOLD)
	_make_label("3 JOUEURS", Vector2(350, 14), Vector2(170, 46), 18, MUTED, HORIZONTAL_ALIGNMENT_CENTER)

	var ai1_panel: Panel = _panel(Vector2(545, 6), Vector2(245, 64), Color("#102A28"), Color("#4D7972"), 22, 2)
	_make_label("IA 1", Vector2(12, 4), Vector2(90, 28), 21, TEXT, HORIZONTAL_ALIGNMENT_LEFT, ai1_panel)
	ai1_count_label = _make_label("", Vector2(12, 31), Vector2(130, 25), 16, GOLD, HORIZONTAL_ALIGNMENT_LEFT, ai1_panel)

	var ai2_panel: Panel = _panel(Vector2(810, 6), Vector2(245, 64), Color("#102A28"), Color("#4D7972"), 22, 2)
	_make_label("IA 2", Vector2(12, 4), Vector2(90, 28), 21, TEXT, HORIZONTAL_ALIGNMENT_LEFT, ai2_panel)
	ai2_count_label = _make_label("", Vector2(12, 31), Vector2(130, 25), 16, GOLD, HORIZONTAL_ALIGNMENT_LEFT, ai2_panel)

	var info: Panel = _panel(Vector2(1245, 5), Vector2(335, 66), Color("#10151C"), Color("#4B5D67"), 20, 2)
	turn_label = _make_label("", Vector2(10, 3), Vector2(315, 32), 18, TEXT, HORIZONTAL_ALIGNMENT_CENTER, info)
	score_label = _make_label("", Vector2(10, 32), Vector2(315, 28), 15, GOLD, HORIZONTAL_ALIGNMENT_CENTER, info)

	ai1_layer = Control.new()
	ai1_layer.size = Vector2(1600, 250)
	add_child(ai1_layer)
	ai2_layer = Control.new()
	ai2_layer.size = Vector2(1600, 250)
	add_child(ai2_layer)

	_panel(Vector2(388, 265), Vector2(820, 300), Color(0.04, 0.27, 0.18, 0.20), Color(0.20, 0.65, 0.43, 0.34), 24, 3)
	table_button = Button.new()
	table_button.text = "TABLE COMMUNE\nTouchez ici pour poser la combinaison sélectionnée"
	table_button.position = Vector2(402, 274)
	table_button.size = Vector2(790, 64)
	table_button.add_theme_font_size_override("font_size", 17)
	table_button.add_theme_color_override("font_color", Color(0.75, 0.9, 0.82, 0.72))
	table_button.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))
	table_button.add_theme_stylebox_override("disabled", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))
	table_button.pressed.connect(_on_table_pressed)
	add_child(table_button)

	meld_layer = Control.new()
	meld_layer.position = Vector2(400, 338)
	meld_layer.size = Vector2(796, 215)
	add_child(meld_layer)
	status_label = _make_label("", Vector2(375, 570), Vector2(850, 34), 17, TEXT, HORIZONTAL_ALIGNMENT_CENTER)

	_build_stock()
	discard_layer = Control.new()
	discard_layer.position = Vector2(245, 344)
	discard_layer.size = Vector2(140, 220)
	add_child(discard_layer)

	combo_layer = Control.new()
	combo_layer.position = Vector2(30, 606)
	combo_layer.size = Vector2(1540, 52)
	add_child(combo_layer)

	player_layer = Control.new()
	player_layer.size = Vector2(1600, 900)
	add_child(player_layer)

	sort_button = _make_button("Trier", Vector2(24, 817), Vector2(190, 62), 22)
	sort_button.pressed.connect(_on_sort_pressed)
	var clear_button: Button = _make_button("Annuler sélection", Vector2(225, 817), Vector2(220, 62), 19)
	clear_button.pressed.connect(_on_clear_selection)

	var me: Panel = _panel(Vector2(610, 812), Vector2(360, 70), Color("#101A20"), Color("#7C8E9A"), 26, 2)
	_make_label("VOUS", Vector2(18, 6), Vector2(110, 28), 22, TEXT, HORIZONTAL_ALIGNMENT_LEFT, me)
	player_count_label = _make_label("", Vector2(18, 34), Vector2(190, 26), 16, GOLD, HORIZONTAL_ALIGNMENT_LEFT, me)

	discard_button = _make_button("Défausser • Fin du tour", Vector2(1190, 817), Vector2(380, 62), 21, Color("#0B5E40"), GREEN)
	discard_button.pressed.connect(_on_discard_pressed)
	_make_label("v0.0.6 FOUNDATIONS", Vector2(8, 883), Vector2(210, 16), 12, Color(1, 1, 1, 0.42))

	modal_layer = Control.new()
	modal_layer.size = Vector2(1600, 900)
	modal_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(modal_layer)

func _build_stock() -> void:
	var stock_layer: Control = Control.new()
	stock_layer.position = Vector2(82, 344)
	stock_layer.size = Vector2(145, 220)
	add_child(stock_layer)
	for i: int in range(4):
		var shadow: Panel = Panel.new()
		shadow.position = Vector2(float(i) * 3.0, 10.0 - float(i) * 2.5)
		shadow.size = Vector2(112, 158)
		shadow.add_theme_stylebox_override("panel", _card_style(false, Color(0, 0, 0, 0)))
		stock_layer.add_child(shadow)
	var stock_button: TextureButton = TextureButton.new()
	stock_button.position = Vector2(12, 0)
	stock_button.size = Vector2(112, 158)
	stock_button.ignore_texture_size = true
	stock_button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	stock_button.texture_normal = _load_card_texture("back_red")
	stock_button.texture_disabled = stock_button.texture_normal
	stock_button.pressed.connect(_on_draw_stock)
	stock_layer.add_child(stock_button)
	_make_label("Pioche", Vector2(0, 168), Vector2(140, 27), 21, TEXT, HORIZONTAL_ALIGNMENT_CENTER, stock_layer)
	stock_count_label = _make_label("", Vector2(0, 194), Vector2(140, 22), 15, MUTED, HORIZONTAL_ALIGNMENT_CENTER, stock_layer)

func _refresh_all() -> void:
	detected_combos.clear()
	if game.phase == RamiGame.Phase.ACTION and game.turn_index == 0:
		detected_combos = game.detect_player_melds()
	if selected_detected_combo >= detected_combos.size():
		selected_detected_combo = -1
	_refresh_opponents()
	_refresh_player()
	_refresh_discard()
	_refresh_melds()
	_refresh_combo_bands()
	stock_count_label.text = "%d cartes" % game.stock.size()
	player_count_label.text = "%d cartes" % game.player_hand.size()
	ai1_count_label.text = "%d cartes" % game.ai1_hand.size()
	ai2_count_label.text = "%d cartes" % game.ai2_hand.size()
	status_label.text = game.last_message
	score_label.text = "Valeur main : %d pts" % game.hand_score(game.player_hand)

	if game.winner_index >= 0:
		turn_label.text = "MANCHE TERMINÉE"
		discard_button.disabled = true
		table_button.disabled = true
		_show_game_over()
	elif game.phase == RamiGame.Phase.DRAW:
		turn_label.text = "À VOUS • PIOCHE OBLIGATOIRE"
		discard_button.disabled = true
		table_button.disabled = true
	else:
		turn_label.text = "À VOUS • POSEZ PUIS DÉFAUSSEZ"
		discard_button.disabled = selected_indices.size() != 1
		table_button.disabled = selected_indices.size() < 3 and selected_detected_combo < 0

	var mode_name: String = game.current_sort_name()
	sort_button.text = "Trier" if mode_name == "" else "Tri : %s" % mode_name

func _refresh_opponents() -> void:
	_clear_children(ai1_layer)
	_clear_children(ai2_layer)
	_draw_opponent_hand(game.ai1_hand.size(), Vector2(520, 110), ai1_layer, -1.0)
	_draw_opponent_hand(game.ai2_hand.size(), Vector2(1080, 110), ai2_layer, 1.0)

func _draw_opponent_hand(count: int, center: Vector2, parent: Control, direction: float) -> void:
	if count <= 0:
		return
	var card_w: float = 58.0
	var card_h: float = 82.0
	var overlap: float = minf(33.0, 300.0 / maxf(1.0, float(count - 1)))
	var total: float = card_w + overlap * float(count - 1)
	var start_x: float = center.x - total / 2.0
	for i: int in range(count):
		var delta: float = float(i) - float(count - 1) / 2.0
		var y: float = center.y + absf(delta) * 0.75
		var wrapper: Control = _make_card("back_red", Vector2(start_x + float(i) * overlap, y), Vector2(card_w, card_h), false, -2, parent, false, Color(0, 0, 0, 0))
		wrapper.rotation = direction * delta * 0.006

func _refresh_player() -> void:
	_clear_children(player_layer)
	var count: int = game.player_hand.size()
	if count <= 0:
		return
	var card_w: float = 116.0
	var card_h: float = 164.0
	var overlap: float = minf(76.0, 1120.0 / maxf(1.0, float(count - 1)))
	var total_width: float = card_w + overlap * float(count - 1)
	var start_x: float = 800.0 - total_width / 2.0
	var membership: Dictionary = _combo_membership_map()
	for i: int in range(count):
		var center_delta: float = float(i) - float(count - 1) / 2.0
		var y: float = 650.0 + absf(center_delta) * 0.75
		var selected: bool = selected_indices.has(i)
		if selected:
			y -= 24.0
		var accent: Color = Color(0, 0, 0, 0)
		if membership.has(i):
			var combo_index: int = int(membership[i])
			accent = COMBO_COLORS[combo_index % COMBO_COLORS.size()]
		var card: CardInstance = game.player_hand[i]
		_make_card(card.face_id(), Vector2(start_x + float(i) * overlap, y), Vector2(card_w, card_h), game.phase == RamiGame.Phase.ACTION and game.turn_index == 0, i, player_layer, selected, accent)

func _combo_membership_map() -> Dictionary:
	var out: Dictionary = {}
	for combo_index: int in range(detected_combos.size()):
		var indices: Array[int] = _dict_int_array(detected_combos[combo_index], "indices")
		for idx: int in indices:
			if not out.has(idx):
				out[idx] = combo_index
	return out

func _refresh_combo_bands() -> void:
	_clear_children(combo_layer)
	if detected_combos.is_empty():
		_make_label("Après la pioche, les suites et groupes détectés apparaîtront ici.", Vector2(200, 4), Vector2(1140, 42), 16, Color(0.85, 0.9, 0.87, 0.52), HORIZONTAL_ALIGNMENT_CENTER, combo_layer)
		return
	var x: float = 0.0
	for i: int in range(detected_combos.size()):
		if x > 1460.0:
			break
		var combo: Dictionary = detected_combos[i]
		var kind: String = String(combo.get("kind", ""))
		var count: int = int(combo.get("count", 0))
		var color: Color = COMBO_COLORS[i % COMBO_COLORS.size()]
		var label_text: String = ("Suite" if kind == "run" else "Groupe") + " • %d cartes" % count
		var b: Button = _make_button_in(label_text, Vector2(x, 3), Vector2(180, 43), 15, Color(0.06, 0.09, 0.10, 0.88), color, combo_layer)
		if selected_detected_combo == i:
			b.add_theme_stylebox_override("normal", _button_style(color.darkened(0.55), color, 4, 15))
		b.pressed.connect(_on_combo_band_pressed.bind(i))
		x += 190.0

func _refresh_discard() -> void:
	_clear_children(discard_layer)
	var top: CardInstance = game.top_discard()
	if top != null:
		_make_card(top.face_id(), Vector2(10, 0), Vector2(112, 158), game.phase == RamiGame.Phase.DRAW and game.turn_index == 0, -1, discard_layer, false, GOLD)
	_make_label("Défausse", Vector2(0, 168), Vector2(135, 27), 21, TEXT, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)
	_make_label("Dernière carte", Vector2(0, 194), Vector2(135, 22), 14, MUTED, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)

func _refresh_melds() -> void:
	_clear_children(meld_layer)
	if game.table_melds.is_empty():
		_make_label("Aucune combinaison posée", Vector2(185, 62), Vector2(420, 44), 21, Color(0.75, 0.88, 0.80, 0.45), HORIZONTAL_ALIGNMENT_CENTER, meld_layer)
		return
	var x: float = 6.0
	var y: float = 20.0
	for meld_index: int in range(game.table_melds.size()):
		var meld: Dictionary = game.table_melds[meld_index]
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var owner: int = int(meld.get("owner", 0))
		var w: float = 55.0
		var h: float = 78.0
		var meld_width: float = 23.0 * float(maxi(0, cards.size() - 1)) + w
		if x + meld_width > 775.0:
			x = 6.0
			y += 105.0
		if y > 125.0:
			break
		var owner_color: Color = GREEN if owner == 0 else RED
		var hit: Button = Button.new()
		hit.text = RamiGame.PLAYER_NAMES[owner]
		hit.position = Vector2(x, y - 20)
		hit.size = Vector2(maxf(75.0, meld_width), 20)
		hit.add_theme_font_size_override("font_size", 11)
		hit.add_theme_color_override("font_color", owner_color)
		hit.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 2))
		hit.pressed.connect(_on_meld_pressed.bind(meld_index))
		meld_layer.add_child(hit)
		for i: int in range(cards.size()):
			_make_card(cards[i].face_id(), Vector2(x + float(i) * 23.0, y), Vector2(w, h), false, -2, meld_layer, false, Color(0, 0, 0, 0))
		x += meld_width + 20.0

func _make_card(card_id: String, pos: Vector2, card_size: Vector2, clickable: bool, index: int, parent: Control, selected: bool, accent: Color) -> Control:
	var wrapper: Control = Control.new()
	wrapper.position = pos
	wrapper.size = card_size
	parent.add_child(wrapper)
	var frame: Panel = Panel.new()
	frame.size = card_size
	frame.add_theme_stylebox_override("panel", _card_style(selected, accent))
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	wrapper.add_child(frame)
	if accent.a > 0.0:
		var band: ColorRect = ColorRect.new()
		band.color = accent
		band.position = Vector2(5, card_size.y - 12)
		band.size = Vector2(card_size.x - 10, 7)
		band.mouse_filter = Control.MOUSE_FILTER_IGNORE
		wrapper.add_child(band)
	var button: TextureButton = TextureButton.new()
	button.position = Vector2(3, 3)
	button.size = card_size - Vector2(6, 6)
	button.ignore_texture_size = true
	button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	button.texture_normal = _load_card_texture(card_id)
	button.texture_disabled = button.texture_normal
	button.disabled = not clickable
	wrapper.add_child(button)
	if clickable:
		if index >= 0:
			button.pressed.connect(_on_player_card_pressed.bind(index))
		elif index == -1:
			button.pressed.connect(_on_draw_discard)
	return wrapper

func _card_style(selected: bool, accent: Color) -> StyleBoxFlat:
	var st: StyleBoxFlat = StyleBoxFlat.new()
	st.bg_color = Color("#FFFDF8")
	if selected:
		st.border_color = GOLD
		st.set_border_width_all(5)
	elif accent.a > 0.0:
		st.border_color = accent
		st.set_border_width_all(3)
	else:
		st.border_color = Color(0, 0, 0, 0.55)
		st.set_border_width_all(2)
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
		_reset_selection()
		_refresh_all()

func _on_draw_discard() -> void:
	if game.draw_discard():
		_reset_selection()
		_refresh_all()

func _on_player_card_pressed(index: int) -> void:
	if game.phase != RamiGame.Phase.ACTION or game.turn_index != 0:
		return
	selected_detected_combo = -1
	if selected_indices.has(index):
		selected_indices.erase(index)
	else:
		selected_indices.append(index)
	selected_indices.sort()
	_refresh_all()

func _on_combo_band_pressed(combo_index: int) -> void:
	if combo_index < 0 or combo_index >= detected_combos.size():
		return
	selected_detected_combo = combo_index
	selected_indices = _dict_int_array(detected_combos[combo_index], "indices")
	game.last_message = "Combinaison sélectionnée. Touchez la table pour la poser."
	_refresh_all()

func _on_table_pressed() -> void:
	if selected_indices.size() < 3:
		game.last_message = "Sélectionnez une suite ou un groupe d'au moins 3 cartes."
		_refresh_all()
		return
	var result: Dictionary = game.play_player_selection(selected_indices)
	if bool(result.get("ok", false)):
		_reset_selection()
	else:
		game.last_message = String(result.get("message", "Pose invalide."))
	_refresh_all()

func _on_meld_pressed(meld_index: int) -> void:
	if selected_indices.is_empty():
		game.last_message = "Sélectionnez d'abord la ou les cartes à ajouter à cette combinaison."
		_refresh_all()
		return
	var result: Dictionary = game.play_player_on_meld(selected_indices, meld_index)
	if bool(result.get("ok", false)):
		_reset_selection()
	else:
		game.last_message = String(result.get("message", "Ajout impossible."))
	_refresh_all()

func _on_discard_pressed() -> void:
	if selected_indices.size() != 1:
		game.last_message = "Sélectionnez exactement 1 carte à jeter dans la défausse."
		_refresh_all()
		return
	var result: Dictionary = game.discard_player(selected_indices[0])
	if bool(result.get("ok", false)):
		_reset_selection()
	else:
		game.last_message = String(result.get("message", "Défausse impossible."))
	_refresh_all()

func _on_sort_pressed() -> void:
	game.toggle_sort_player_hand()
	_reset_selection()
	_refresh_all()

func _on_clear_selection() -> void:
	_reset_selection()
	_refresh_all()

func _reset_selection() -> void:
	selected_indices.clear()
	selected_detected_combo = -1

func _play_deal_animation() -> void:
	if deal_animation_done:
		return
	deal_animation_done = true
	player_layer.modulate.a = 0.0
	var tween: Tween = create_tween()
	tween.tween_property(player_layer, "modulate:a", 1.0, 0.55)

func _show_game_over() -> void:
	if modal_layer.get_child_count() > 0:
		return
	modal_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	var shade: ColorRect = ColorRect.new()
	shade.color = Color(0, 0, 0, 0.72)
	shade.size = Vector2(1600, 900)
	shade.mouse_filter = Control.MOUSE_FILTER_STOP
	modal_layer.add_child(shade)
	var box: Panel = _panel(Vector2(430, 190), Vector2(740, 510), Color("#101A20"), GOLD, 28, 4, modal_layer)
	_make_label("CLASSEMENT FINAL", Vector2(45, 25), Vector2(650, 70), 42, GOLD, HORIZONTAL_ALIGNMENT_CENTER, box)
	var y: float = 115.0
	for row: Dictionary in game.ranking:
		var place: int = int(row.get("place", 0))
		var name: String = String(row.get("name", ""))
		var points: int = int(row.get("points", 0))
		_make_label("%dᵉ  •  %s  •  %d points" % [place, name, points], Vector2(90, y), Vector2(560, 58), 27, TEXT, HORIZONTAL_ALIGNMENT_CENTER, box)
		y += 72.0
	_make_label("Moins de points = meilleur classement", Vector2(80, 346), Vector2(580, 38), 18, MUTED, HORIZONTAL_ALIGNMENT_CENTER, box)
	var replay: Button = _make_button_in("REJOUER", Vector2(165, 410), Vector2(410, 70), 27, Color("#0B5E40"), GREEN, box)
	replay.pressed.connect(_on_replay)

func _on_replay() -> void:
	_clear_children(modal_layer)
	modal_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_reset_selection()
	game.new_round()
	deal_animation_done = false
	_refresh_all()
	_play_deal_animation()

func _dict_int_array(item: Dictionary, key: String) -> Array[int]:
	var out: Array[int] = []
	var raw: Array = item.get(key, [])
	for value: Variant in raw:
		out.append(int(value))
	return out

func _dict_card_array(item: Dictionary, key: String) -> Array[CardInstance]:
	var out: Array[CardInstance] = []
	var raw: Array = item.get(key, [])
	for value: Variant in raw:
		if value is CardInstance:
			out.append(value as CardInstance)
	return out

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
	b.add_theme_stylebox_override("disabled", _button_style(bg.darkened(0.18), border.darkened(0.25), 2, 18))
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
	st.shadow_color = Color(0, 0, 0, 0.30)
	st.shadow_size = 6
	return st

func _clear_children(node: Node) -> void:
	for child: Node in node.get_children():
		child.free()

func _on_back_pressed() -> void:
	get_tree().change_scene_to_file("res://Main.tscn")
