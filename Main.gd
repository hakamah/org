extends Control

const GOLD := Color("#F0C86A")
const TEXT := Color("#F7F3E8")
const MUTED := Color("#CFC8B8")

func _ready() -> void:
	_build_background()
	_build_menu()

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
	bottom.offset_top = -72
	add_child(bottom)

	var felt_glow := ColorRect.new()
	felt_glow.color = Color(0.15, 0.6, 0.38, 0.12)
	felt_glow.set_anchors_preset(Control.PRESET_CENTER)
	felt_glow.position = Vector2(-520, -220)
	felt_glow.size = Vector2(1040, 440)
	add_child(felt_glow)

func _build_menu() -> void:
	var center := VBoxContainer.new()
	center.set_anchors_preset(Control.PRESET_CENTER)
	center.position = Vector2(-360, -260)
	center.size = Vector2(720, 520)
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_theme_constant_override("separation", 22)
	add_child(center)

	var title := Label.new()
	title.text = "RAMI"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 108)
	title.add_theme_color_override("font_color", GOLD)
	title.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.75))
	title.add_theme_constant_override("shadow_offset_x", 4)
	title.add_theme_constant_override("shadow_offset_y", 6)
	center.add_child(title)

	var suit := Label.new()
	suit.text = "♠   ♥   ♦   ♣"
	suit.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	suit.add_theme_font_size_override("font_size", 44)
	suit.add_theme_color_override("font_color", Color("#F3E0B2"))
	center.add_child(suit)

	var subtitle := Label.new()
	subtitle.text = "LE JEU DE CARTES"
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.add_theme_font_size_override("font_size", 28)
	subtitle.add_theme_color_override("font_color", MUTED)
	center.add_child(subtitle)

	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(1, 34)
	center.add_child(spacer)

	var play := Button.new()
	play.text = "▶   JOUER"
	play.custom_minimum_size = Vector2(540, 118)
	play.add_theme_font_size_override("font_size", 42)
	play.add_theme_color_override("font_color", TEXT)
	play.add_theme_color_override("font_hover_color", Color.WHITE)
	play.add_theme_stylebox_override("normal", _button_style(Color("#0F6644"), Color("#43CE8B"), 4))
	play.add_theme_stylebox_override("hover", _button_style(Color("#147A52"), Color("#6CE6A9"), 5))
	play.add_theme_stylebox_override("pressed", _button_style(Color("#0B5237"), Color("#A3F2C9"), 5))
	play.pressed.connect(_on_play_pressed)
	center.add_child(play)

	var version := Label.new()
	version.text = "3 joueurs • Roadmap jouable • v0.0.5"
	version.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	version.add_theme_font_size_override("font_size", 20)
	version.add_theme_color_override("font_color", Color(0.85, 0.85, 0.80, 0.85))
	center.add_child(version)

func _button_style(bg: Color, border: Color, width: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.set_border_width_all(width)
	style.set_corner_radius_all(24)
	style.shadow_color = Color(0, 0, 0, 0.42)
	style.shadow_size = 12
	style.content_margin_left = 28
	style.content_margin_right = 28
	style.content_margin_top = 18
	style.content_margin_bottom = 18
	return style

func _on_play_pressed() -> void:
	get_tree().change_scene_to_file("res://GameTable.tscn")