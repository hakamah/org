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
const COMBO_COLORS: Array[Color] = [GREEN, BLUE, VIOLET, ORANGE, PINK, CYAN, GOLD]

const HAND_VIEW_POS := Vector2(220, 632)
const HAND_VIEW_SIZE := Vector2(1350, 252)
const PLAYER_CARD_SIZE := Vector2(148, 210)
const PLAYER_CARD_STEP := 90.0
const PLAYER_CARD_MIN_STEP := 64.0
const DRAG_THRESHOLD := 12.0

var game: RamiGame = RamiGame.new()
var selected_indices: Array[int] = []
var selected_detected_combo: int = -1
var detected_combos: Array[Dictionary] = []
var deal_animation_done: bool = false

var player_view: Control
var player_layer: Control
var hand_band_layer: Control
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
var mobile_hand_score_label: Label
var sort_button: Button
var discard_button: Button
var table_button: Button

var hand_step: float = PLAYER_CARD_STEP
var hand_content_width: float = 0.0
var hand_scroll_offset: float = 0.0
var hand_swipe_active: bool = false

var drag_index: int = -1
var drag_start_viewport: Vector2 = Vector2.ZERO
var drag_last_viewport: Vector2 = Vector2.ZERO
var drag_started: bool = false
var drag_distance: float = 0.0

func _ready() -> void:
	print("RAMI_RUNTIME: ready_start")
	set_process_input(true)
	_build_ui()
	game.set_opening_rule(RamiGame.OpeningRule.SIMPLE_MELD)
	game.new_round()
	print("RAMI_RUNTIME: dealt player=", game.player_hand.size(), " ai1=", game.ai1_hand.size(), " ai2=", game.ai2_hand.size(), " stock=", game.stock.size(), " discard=", game.discard_pile.size())
	_refresh_all()
	print("RAMI_RUNTIME: refresh_ok player_nodes=", player_layer.get_child_count(), " ai1_nodes=", ai1_layer.get_child_count(), " ai2_nodes=", ai2_layer.get_child_count())
	print("RAMI_INPUT: visual_overlays_ignore=", player_layer.mouse_filter == Control.MOUSE_FILTER_IGNORE and ai1_layer.mouse_filter == Control.MOUSE_FILTER_IGNORE and ai2_layer.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	print("RAMI_MOBILE_HAND: card_size=", PLAYER_CARD_SIZE, " view=", HAND_VIEW_SIZE)
	_play_deal_animation()

func _build_ui() -> void:
	_add_rect(FELT, Vector2.ZERO, Vector2(1600, 900))
	_add_rect(Color("#2D160C"), Vector2(0, 0), Vector2(1600, 74))
	_add_rect(Color("#241109"), Vector2(0, 886), Vector2(1600, 14))
	_add_rect(Color(0.10, 0.45, 0.28, 0.13), Vector2(14, 78), Vector2(1572, 804))

	var back: Button = _make_button("←", Vector2(14, 10), Vector2(72, 52), 31)
	back.pressed.connect(_on_back_pressed)
	_make_label("RAMI", Vector2(98, 2), Vector2(210, 66), 44, GOLD)
	_make_label("3 JOUEURS", Vector2(300, 13), Vector2(160, 45), 18, MUTED, HORIZONTAL_ALIGNMENT_CENTER)

	var ai1_panel: Panel = _panel(Vector2(475, 5), Vector2(265, 64), Color("#102A28"), Color("#4D7972"), 22, 2)
	_make_label("IA 1", Vector2(15, 3), Vector2(100, 30), 23, TEXT, HORIZONTAL_ALIGNMENT_LEFT, ai1_panel)
	ai1_count_label = _make_label("", Vector2(15, 32), Vector2(180, 25), 18, GOLD, HORIZONTAL_ALIGNMENT_LEFT, ai1_panel)

	var ai2_panel: Panel = _panel(Vector2(760, 5), Vector2(265, 64), Color("#102A28"), Color("#4D7972"), 22, 2)
	_make_label("IA 2", Vector2(15, 3), Vector2(100, 30), 23, TEXT, HORIZONTAL_ALIGNMENT_LEFT, ai2_panel)
	ai2_count_label = _make_label("", Vector2(15, 32), Vector2(180, 25), 18, GOLD, HORIZONTAL_ALIGNMENT_LEFT, ai2_panel)

	var info: Panel = _panel(Vector2(1100, 5), Vector2(480, 64), Color("#10151C"), Color("#4B5D67"), 20, 2)
	turn_label = _make_label("", Vector2(10, 1), Vector2(460, 34), 21, TEXT, HORIZONTAL_ALIGNMENT_CENTER, info)
	score_label = _make_label("", Vector2(10, 33), Vector2(460, 26), 17, GOLD, HORIZONTAL_ALIGNMENT_CENTER, info)

	ai1_layer = Control.new()
	ai1_layer.size = Vector2(1600, 225)
	ai1_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(ai1_layer)
	ai2_layer = Control.new()
	ai2_layer.size = Vector2(1600, 225)
	ai2_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(ai2_layer)

	_panel(Vector2(205, 190), Vector2(980, 365), Color(0.04, 0.27, 0.18, 0.22), Color(0.20, 0.65, 0.43, 0.38), 26, 3)
	table_button = Button.new()
	table_button.text = "TABLE COMMUNE\nTouchez ici pour poser la combinaison sélectionnée"
	table_button.position = Vector2(220, 202)
	table_button.size = Vector2(950, 70)
	table_button.add_theme_font_size_override("font_size", 20)
	table_button.add_theme_color_override("font_color", Color(0.78, 0.92, 0.84, 0.78))
	table_button.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))
	table_button.add_theme_stylebox_override("disabled", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))
	table_button.pressed.connect(_on_table_pressed)
	add_child(table_button)

	meld_layer = Control.new()
	meld_layer.position = Vector2(220, 278)
	meld_layer.size = Vector2(950, 260)
	meld_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(meld_layer)

	status_label = _make_label("", Vector2(205, 558), Vector2(980, 38), 20, TEXT, HORIZONTAL_ALIGNMENT_CENTER)

	_build_stock()

	discard_layer = Control.new()
	discard_layer.position = Vector2(1235, 203)
	discard_layer.size = Vector2(155, 245)
	add_child(discard_layer)

	sort_button = _make_button("Trier", Vector2(1215, 482), Vector2(345, 64), 26, Color("#315E22"), Color("#9CCB43"))
	sort_button.pressed.connect(_on_sort_pressed)
	var clear_button: Button = _make_button("Annuler sélection", Vector2(1215, 553), Vector2(345, 58), 20)
	clear_button.pressed.connect(_on_clear_selection)

	combo_layer = Control.new()
	combo_layer.position = Vector2(220, 592)
	combo_layer.size = Vector2(980, 37)
	combo_layer.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(combo_layer)

	var me: Panel = _panel(Vector2(14, 652), Vector2(190, 220), Color("#4A2518"), Color("#8B5A43"), 28, 3)
	_make_label("VOUS", Vector2(18, 18), Vector2(154, 34), 26, TEXT, HORIZONTAL_ALIGNMENT_CENTER, me)
	player_count_label = _make_label("", Vector2(18, 58), Vector2(154, 28), 19, GOLD, HORIZONTAL_ALIGNMENT_CENTER, me)
	_make_label("Main", Vector2(18, 96), Vector2(154, 25), 17, MUTED, HORIZONTAL_ALIGNMENT_CENTER, me)
	mobile_hand_score_label = _make_label("", Vector2(18, 124), Vector2(154, 32), 20, GOLD, HORIZONTAL_ALIGNMENT_CENTER, me)
	_make_label("Glissez les cartes\npour les ranger", Vector2(10, 164), Vector2(170, 45), 14, Color(1, 1, 1, 0.68), HORIZONTAL_ALIGNMENT_CENTER, me)

	player_view = Control.new()
	player_view.position = HAND_VIEW_POS
	player_view.size = HAND_VIEW_SIZE
	player_view.clip_contents = true
	player_view.mouse_filter = Control.MOUSE_FILTER_PASS
	player_view.gui_input.connect(_on_hand_view_gui_input)
	add_child(player_view)

	player_layer = Control.new()
	player_layer.size = Vector2(2600, HAND_VIEW_SIZE.y)
	player_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	player_view.add_child(player_layer)

	hand_band_layer = Control.new()
	hand_band_layer.size = Vector2(2600, HAND_VIEW_SIZE.y)
	hand_band_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	player_view.add_child(hand_band_layer)

	discard_button = _make_button("DÉFAUSSER\nFin du tour", Vector2(14, 553), Vector2(190, 86), 20, Color("#0B5E40"), GREEN)
	discard_button.pressed.connect(_on_discard_pressed)

	_make_label("v0.0.8 • ERGONOMIE MOBILE", Vector2(1320, 880), Vector2(265, 16), 11, Color(1, 1, 1, 0.42), HORIZONTAL_ALIGNMENT_RIGHT)

	modal_layer = Control.new()
	modal_layer.size = Vector2(1600, 900)
	modal_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(modal_layer)

func _build_stock() -> void:
	var stock_layer: Control = Control.new()
	stock_layer.position = Vector2(1405, 203)
	stock_layer.size = Vector2(155, 245)
	add_child(stock_layer)
	for i: int in range(4):
		var shadow: Panel = Panel.new()
		shadow.position = Vector2(float(i) * 3.0, 12.0 - float(i) * 2.5)
		shadow.size = Vector2(132, 186)
		shadow.add_theme_stylebox_override("panel", _card_style(false, Color(0, 0, 0, 0)))
		shadow.mouse_filter = Control.MOUSE_FILTER_IGNORE
		stock_layer.add_child(shadow)
	var stock_button: TextureButton = TextureButton.new()
	stock_button.position = Vector2(10, 0)
	stock_button.size = Vector2(132, 186)
	stock_button.ignore_texture_size = true
	stock_button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	stock_button.texture_normal = _load_card_texture("back_red")
	stock_button.texture_disabled = stock_button.texture_normal
	stock_button.pressed.connect(_on_draw_stock)
	stock_layer.add_child(stock_button)
	_make_label("Pioche", Vector2(0, 191), Vector2(150, 30), 23, TEXT, HORIZONTAL_ALIGNMENT_CENTER, stock_layer)
	stock_count_label = _make_label("", Vector2(0, 220), Vector2(150, 22), 16, MUTED, HORIZONTAL_ALIGNMENT_CENTER, stock_layer)

func _refresh_all() -> void:
	detected_combos.clear()
	if game.phase == RamiGame.Phase.ACTION and game.turn_index == 0:
		var found: Array = game.detect_player_melds()
		for value: Variant in found:
			if value is Dictionary:
				detected_combos.append(value as Dictionary)
	if selected_detected_combo >= detected_combos.size():
		selected_detected_combo = -1

	_refresh_opponents()
	_refresh_player()
	_refresh_discard()
	_refresh_melds()
	_refresh_combo_chips()
	_refresh_hand_combo_bands()

	stock_count_label.text = "%d cartes" % game.stock.size()
	player_count_label.text = "%d cartes" % game.player_hand.size()
	ai1_count_label.text = "%d cartes" % game.ai1_hand.size()
	ai2_count_label.text = "%d cartes" % game.ai2_hand.size()
	status_label.text = game.last_message
	score_label.text = "Valeur de votre main : %d pts" % game.hand_score(game.player_hand)
	if is_instance_valid(mobile_hand_score_label):
		mobile_hand_score_label.text = "%d pts" % game.hand_score(game.player_hand)

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
		turn_label.text = "À VOUS • JOUEZ PUIS DÉFAUSSEZ"
		discard_button.disabled = selected_indices.size() != 1
		table_button.disabled = selected_indices.size() < 3 and selected_detected_combo < 0

	var mode_name: String = game.current_sort_name()
	sort_button.text = "Trier" if mode_name == "" else "Tri : %s" % mode_name

func _refresh_opponents() -> void:
	_clear_children(ai1_layer)
	_clear_children(ai2_layer)
	_draw_opponent_hand(game.ai1_hand.size(), Vector2(500, 116), ai1_layer, -1.0)
	_draw_opponent_hand(game.ai2_hand.size(), Vector2(1100, 116), ai2_layer, 1.0)

func _draw_opponent_hand(count: int, center: Vector2, parent: Control, direction: float) -> void:
	if count <= 0:
		return
	var card_w: float = 66.0
	var card_h: float = 94.0
	var overlap: float = minf(35.0, 330.0 / maxf(1.0, float(count - 1)))
	var total: float = card_w + overlap * float(count - 1)
	var start_x: float = center.x - total / 2.0
	for i: int in range(count):
		var delta: float = float(i) - float(count - 1) / 2.0
		var y: float = center.y + absf(delta) * 0.7
		var wrapper: Control = _make_card("back_red", Vector2(start_x + float(i) * overlap, y), Vector2(card_w, card_h), false, -2, parent, false, Color(0, 0, 0, 0))
		wrapper.rotation = direction * delta * 0.005

func _calculate_hand_layout() -> void:
	var count: int = game.player_hand.size()
	if count <= 1:
		hand_step = PLAYER_CARD_STEP
		hand_content_width = PLAYER_CARD_SIZE.x
	else:
		var fit_step: float = (HAND_VIEW_SIZE.x - PLAYER_CARD_SIZE.x - 14.0) / float(count - 1)
		hand_step = clampf(fit_step, PLAYER_CARD_MIN_STEP, PLAYER_CARD_STEP)
		hand_content_width = PLAYER_CARD_SIZE.x + hand_step * float(count - 1)
	_clamp_hand_scroll()
	player_layer.position.x = -hand_scroll_offset
	hand_band_layer.position.x = -hand_scroll_offset

func _clamp_hand_scroll() -> void:
	var max_scroll: float = maxf(0.0, hand_content_width - HAND_VIEW_SIZE.x + 10.0)
	hand_scroll_offset = clampf(hand_scroll_offset, 0.0, max_scroll)

func _refresh_player() -> void:
	_clear_children(player_layer)
	var count: int = game.player_hand.size()
	if count <= 0:
		return
	_calculate_hand_layout()
	for i: int in range(count):
		var y: float = _player_card_y(i, count)
		var selected: bool = selected_indices.has(i) or (drag_started and drag_index == i)
		if selected:
			y -= 24.0
		var card: CardInstance = game.player_hand[i]
		_make_card(card.face_id(), Vector2(float(i) * hand_step, y), PLAYER_CARD_SIZE, true, i, player_layer, selected, Color(0, 0, 0, 0))

func _player_card_y(index: int, count: int) -> float:
	var center_delta: float = float(index) - float(count - 1) / 2.0
	return 28.0 + absf(center_delta) * 0.65

func _refresh_combo_chips() -> void:
	_clear_children(combo_layer)
	if detected_combos.is_empty():
		_make_label("Après la pioche, vos combinaisons possibles seront surlignées directement dans la main.", Vector2(0, 0), Vector2(980, 34), 15, Color(0.88, 0.93, 0.89, 0.58), HORIZONTAL_ALIGNMENT_CENTER, combo_layer)
		return
	var max_visible: int = mini(5, detected_combos.size())
	var chip_w: float = 184.0
	for i: int in range(max_visible):
		var combo: Dictionary = detected_combos[i]
		var kind: String = String(combo.get("kind", ""))
		var count: int = int(combo.get("count", 0))
		var color: Color = COMBO_COLORS[i % COMBO_COLORS.size()]
		var label_text: String = ("Suite" if kind == "run" else "Groupe") + " • %d" % count
		var b: Button = _make_button_in(label_text, Vector2(float(i) * (chip_w + 10.0), 0), Vector2(chip_w, 34), 14, Color(0.04, 0.08, 0.08, 0.90), color, combo_layer)
		if selected_detected_combo == i:
			b.add_theme_stylebox_override("normal", _button_style(color.darkened(0.55), color, 4, 14))
		b.pressed.connect(_on_combo_band_pressed.bind(i))

func _refresh_hand_combo_bands() -> void:
	_clear_children(hand_band_layer)
	if detected_combos.is_empty() or game.player_hand.is_empty():
		return
	_calculate_hand_layout()
	var count: int = game.player_hand.size()
	for combo_index: int in range(detected_combos.size()):
		var indices: Array[int] = _dict_int_array(detected_combos[combo_index], "indices")
		if indices.is_empty():
			continue
		indices.sort()
		var color: Color = COMBO_COLORS[combo_index % COMBO_COLORS.size()]
		var lane: int = combo_index % 3
		for member_pos: int in range(indices.size()):
			var idx: int = indices[member_pos]
			if idx < 0 or idx >= count:
				continue
			var linked_next: bool = member_pos + 1 < indices.size() and indices[member_pos + 1] == idx + 1
			var segment_width: float = (hand_step + 8.0) if linked_next else (PLAYER_CARD_SIZE.x - 12.0)
			var card_y: float = _player_card_y(idx, count)
			if selected_indices.has(idx) or (drag_started and drag_index == idx):
				card_y -= 24.0
			var y: float = card_y + PLAYER_CARD_SIZE.y - 20.0 - float(lane) * 17.0
			var band: Button = Button.new()
			band.position = Vector2(float(idx) * hand_step + 6.0, y)
			band.size = Vector2(segment_width, 15.0)
			band.focus_mode = Control.FOCUS_NONE
			band.add_theme_stylebox_override("normal", _band_style(color, selected_detected_combo == combo_index))
			band.add_theme_stylebox_override("hover", _band_style(color.lightened(0.10), true))
			band.add_theme_stylebox_override("pressed", _band_style(color.darkened(0.08), true))
			band.tooltip_text = "Touchez pour sélectionner cette combinaison"
			band.pressed.connect(_on_combo_band_pressed.bind(combo_index))
			hand_band_layer.add_child(band)

func _band_style(color: Color, selected: bool) -> StyleBoxFlat:
	var st := StyleBoxFlat.new()
	st.bg_color = Color(color.r, color.g, color.b, 0.95 if selected else 0.78)
	st.border_color = Color(1, 1, 1, 0.85) if selected else color.lightened(0.18)
	st.set_border_width_all(2 if selected else 1)
	st.set_corner_radius_all(7)
	st.shadow_color = Color(0, 0, 0, 0.22)
	st.shadow_size = 3
	return st

func _refresh_discard() -> void:
	_clear_children(discard_layer)
	var top: CardInstance = game.top_discard()
	if top != null:
		_make_card(top.face_id(), Vector2(10, 0), Vector2(132, 186), game.phase == RamiGame.Phase.DRAW and game.turn_index == 0, -1, discard_layer, false, GOLD)
	_make_label("Défausse", Vector2(0, 191), Vector2(150, 30), 23, TEXT, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)
	_make_label("Dernière carte", Vector2(0, 220), Vector2(150, 22), 15, MUTED, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)

func _refresh_melds() -> void:
	_clear_children(meld_layer)
	if game.table_melds.is_empty():
		_make_label("Aucune combinaison posée", Vector2(205, 82), Vector2(540, 48), 23, Color(0.75, 0.88, 0.80, 0.45), HORIZONTAL_ALIGNMENT_CENTER, meld_layer)
		return
	var x: float = 8.0
	var y: float = 28.0
	for meld_index: int in range(game.table_melds.size()):
		var meld: Dictionary = game.table_melds[meld_index]
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var owner: int = int(meld.get("owner", 0))
		var w: float = 68.0
		var h: float = 96.0
		var step: float = 31.0
		var meld_width: float = step * float(maxi(0, cards.size() - 1)) + w
		if x + meld_width > 925.0:
			x = 8.0
			y += 122.0
		if y > 150.0:
			break
		var owner_color: Color = GREEN if owner == 0 else RED
		var hit: Button = Button.new()
		hit.text = RamiGame.PLAYER_NAMES[owner]
		hit.position = Vector2(x, y - 24)
		hit.size = Vector2(maxf(90.0, meld_width), 24)
		hit.add_theme_font_size_override("font_size", 12)
		hit.add_theme_color_override("font_color", owner_color)
		hit.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 2))
		hit.pressed.connect(_on_meld_pressed.bind(meld_index))
		meld_layer.add_child(hit)
		for i: int in range(cards.size()):
			_make_card(cards[i].face_id(), Vector2(x + float(i) * step, y), Vector2(w, h), false, -2, meld_layer, false, Color(0, 0, 0, 0))
		x += meld_width + 24.0

func _make_card(card_id: String, pos: Vector2, card_size: Vector2, clickable: bool, index: int, parent: Control, selected: bool, accent: Color) -> Control:
	var wrapper: Control = Control.new()
	wrapper.position = pos
	wrapper.size = card_size
	wrapper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(wrapper)

	var frame: Panel = Panel.new()
	frame.size = card_size
	frame.add_theme_stylebox_override("panel", _card_style(selected, accent))
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	wrapper.add_child(frame)

	var button: TextureButton = TextureButton.new()
	button.position = Vector2(4, 4)
	button.size = card_size - Vector2(8, 8)
	button.ignore_texture_size = true
	button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	button.texture_normal = _load_card_texture(card_id)
	button.texture_disabled = button.texture_normal
	button.disabled = not clickable
	button.focus_mode = Control.FOCUS_NONE
	wrapper.add_child(button)

	if clickable:
		if index >= 0:
			button.gui_input.connect(_on_player_card_gui_input.bind(index))
		elif index == -1:
			button.pressed.connect(_on_draw_discard)
	return wrapper

func _card_style(selected: bool, accent: Color) -> StyleBoxFlat:
	var st: StyleBoxFlat = StyleBoxFlat.new()
	st.bg_color = Color("#FFFDF8")
	if selected:
		st.border_color = GOLD
		st.set_border_width_all(6)
	elif accent.a > 0.0:
		st.border_color = accent
		st.set_border_width_all(3)
	else:
		st.border_color = Color(0, 0, 0, 0.50)
		st.set_border_width_all(2)
	st.set_corner_radius_all(11)
	st.shadow_color = Color(0, 0, 0, 0.34)
	st.shadow_size = 8
	return st

func _load_card_texture(card_id: String) -> Texture2D:
	var resource: Resource = load("res://assets/cards/%s.png" % card_id)
	if resource is Texture2D:
		return resource as Texture2D
	return null

func _on_player_card_gui_input(event: InputEvent, index: int) -> void:
	if event is InputEventScreenTouch:
		var touch := event as InputEventScreenTouch
		if touch.pressed:
			_begin_card_drag(index)
			get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and mb.pressed:
			_begin_card_drag(index)
			get_viewport().set_input_as_handled()

func _begin_card_drag(index: int) -> void:
	if index < 0 or index >= game.player_hand.size():
		return
	drag_index = index
	drag_started = false
	drag_distance = 0.0
	drag_start_viewport = Vector2.ZERO
	drag_last_viewport = Vector2.ZERO

func _input(event: InputEvent) -> void:
	if drag_index < 0:
		return
	if event is InputEventScreenDrag:
		var d := event as InputEventScreenDrag
		_update_card_drag(d.position, d.relative)
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		var motion := event as InputEventMouseMotion
		_update_card_drag(motion.position, motion.relative)
	elif event is InputEventScreenTouch:
		var t := event as InputEventScreenTouch
		if not t.pressed:
			_finish_card_drag()
	elif event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and not mb.pressed:
			_finish_card_drag()

func _update_card_drag(viewport_position: Vector2, motion_delta: Vector2) -> void:
	if drag_start_viewport == Vector2.ZERO:
		drag_start_viewport = viewport_position - motion_delta
	drag_last_viewport = viewport_position
	drag_distance += motion_delta.length()
	if not drag_started and drag_distance >= DRAG_THRESHOLD:
		drag_started = true
	if not drag_started:
		return
	var local_surface: Vector2 = get_global_transform_with_canvas().affine_inverse() * viewport_position
	var local_x: float = local_surface.x - HAND_VIEW_POS.x + hand_scroll_offset
	var target: int = clampi(int(round(local_x / maxf(1.0, hand_step))), 0, game.player_hand.size() - 1)
	if target != drag_index:
		_move_hand_card_for_drag(drag_index, target)
		drag_index = target
		_refresh_player()
		_refresh_hand_combo_bands()
		_refresh_combo_chips()
	var edge_x: float = local_surface.x - HAND_VIEW_POS.x
	if edge_x < 85.0:
		hand_scroll_offset -= 18.0
	elif edge_x > HAND_VIEW_SIZE.x - 85.0:
		hand_scroll_offset += 18.0
	_clamp_hand_scroll()
	player_layer.position.x = -hand_scroll_offset
	hand_band_layer.position.x = -hand_scroll_offset

func _finish_card_drag() -> void:
	var index: int = drag_index
	var was_drag: bool = drag_started
	drag_index = -1
	drag_started = false
	if not was_drag:
		_on_player_card_pressed(index)
	else:
		game.last_message = "Carte déplacée. Votre ordre manuel est conservé."
		_refresh_all()

func _move_hand_card_for_drag(from_index: int, to_index: int) -> void:
	if from_index < 0 or from_index >= game.player_hand.size():
		return
	to_index = clampi(to_index, 0, game.player_hand.size() - 1)
	if from_index == to_index:
		return
	var card: CardInstance = game.player_hand[from_index]
	game.player_hand.remove_at(from_index)
	game.player_hand.insert(to_index, card)
	game.sort_mode = -1
	_reset_selection()

func _on_hand_view_gui_input(event: InputEvent) -> void:
	if drag_index >= 0:
		return
	if event is InputEventScreenDrag:
		var d := event as InputEventScreenDrag
		hand_scroll_offset -= d.relative.x
		_clamp_hand_scroll()
		player_layer.position.x = -hand_scroll_offset
		hand_band_layer.position.x = -hand_scroll_offset
		hand_swipe_active = true
	elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		var motion := event as InputEventMouseMotion
		hand_scroll_offset -= motion.relative.x
		_clamp_hand_scroll()
		player_layer.position.x = -hand_scroll_offset
		hand_band_layer.position.x = -hand_scroll_offset

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
	if index < 0 or index >= game.player_hand.size():
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
	hand_scroll_offset = 0.0
	_refresh_all()

func _on_sort_pressed() -> void:
	game.toggle_sort_player_hand()
	hand_scroll_offset = 0.0
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
	player_view.modulate.a = 0.0
	var tween: Tween = create_tween()
	tween.tween_property(player_view, "modulate:a", 1.0, 0.55)

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
	hand_scroll_offset = 0.0
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
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
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
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(l)
	return l

func _make_button(text_value: String, pos: Vector2, sz: Vector2, font_size: int, bg: Color = Color("#14242B"), border: Color = Color("#4E6A7A")) -> Button:
	var b: Button = Button.new()
	b.text = text_value
	b.position = pos
	b.size = sz
	b.focus_mode = Control.FOCUS_NONE
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
	b.focus_mode = Control.FOCUS_NONE
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