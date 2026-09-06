from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# v0.0.24 PERFORMANCE ONLY
# No dimensions, positions, colors, layout, assets, rules or interactions change.
# We only skip rebuilding UI sections whose visible state is identical and cache
# immutable StyleBox resources.
# -----------------------------------------------------------------------------
needle = 'const TABLE_MAX_RENDER_SCALE: float = 2.0\n'
assert needle in text, 'v023 table state marker not found'
text = text.replace(needle, needle + '''

# Performance caches. Signatures represent everything that can affect the visible
# output of each section, so a skipped refresh is pixel-equivalent to rebuilding it.
var _last_detect_signature: String = ""
var _last_opponents_signature: String = ""
var _last_player_signature: String = ""
var _last_discard_signature: String = ""
var _last_table_refresh_signature: String = ""
var _last_bands_signature: String = ""
var _button_style_cache: Dictionary = {}
var _card_style_cache: Dictionary = {}
var _band_style_cache: Dictionary = {}
''', 1)

# Replace the broad refresh with signature-gated section refreshes.
pattern = r'''func _refresh_all\(\) -> void:\n.*?(?=func _refresh_opponents\(\) -> void:)'''
replacement = '''func _refresh_all() -> void:
	var detect_signature: String = _detect_signature()
	if detect_signature != _last_detect_signature:
		_last_detect_signature = detect_signature
		detected_combos.clear()
		if game.phase == RamiGame.Phase.ACTION and game.turn_index == 0:
			var found: Array = game.detect_player_melds()
			for value: Variant in found:
				if value is Dictionary:
					detected_combos.append(value as Dictionary)
	if selected_detected_combo >= detected_combos.size():
		selected_detected_combo = -1

	var opponents_signature := "%d|%d" % [game.ai1_hand.size(), game.ai2_hand.size()]
	if opponents_signature != _last_opponents_signature:
		_last_opponents_signature = opponents_signature
		_refresh_opponents()

	var player_signature: String = _player_visual_signature()
	if player_signature != _last_player_signature:
		_last_player_signature = player_signature
		_refresh_player()

	var discard_signature: String = _discard_visual_signature()
	if discard_signature != _last_discard_signature:
		_last_discard_signature = discard_signature
		_refresh_discard()

	var table_signature_now: String = _table_signature()
	if table_signature_now != _last_table_refresh_signature:
		_last_table_refresh_signature = table_signature_now
		_refresh_melds()

	# Combo chips are hidden since v0.0.9. Keep their layer empty without rebuilding it.
	if combo_layer.get_child_count() > 0:
		_clear_children(combo_layer)

	var bands_signature: String = _bands_visual_signature()
	if bands_signature != _last_bands_signature:
		_last_bands_signature = bands_signature
		_refresh_hand_combo_bands()

	stock_count_label.text = "%d cartes" % game.stock.size()
	player_count_label.text = "%d cartes" % game.player_hand.size()
	ai1_count_label.text = ""
	ai2_count_label.text = ""
	status_label.text = game.last_message
	var hand_points: int = game.hand_score(game.player_hand)
	score_label.text = "Valeur de votre main : %d pts" % hand_points
	if is_instance_valid(mobile_hand_score_label):
		mobile_hand_score_label.text = "%d pts" % hand_points

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

func _uid_order_signature(hand: Array[CardInstance]) -> String:
	var parts := PackedStringArray()
	for card: CardInstance in hand:
		parts.append(str(card.uid))
	return ",".join(parts)

func _selected_signature() -> String:
	var parts := PackedStringArray()
	for index: int in selected_indices:
		parts.append(str(index))
	return ",".join(parts)

func _detect_signature() -> String:
	return "%d|%d|%s" % [game.turn_index, int(game.phase), _uid_order_signature(game.player_hand)]

func _player_visual_signature() -> String:
	return "%s|sel=%s|drag=%d|started=%s" % [
		_uid_order_signature(game.player_hand),
		_selected_signature(),
		drag_index,
		str(drag_started)
	]

func _discard_visual_signature() -> String:
	var top: CardInstance = game.top_discard()
	var top_uid: int = -1 if top == null else top.uid
	return "%d|phase=%d|turn=%d|sel=%d" % [top_uid, int(game.phase), game.turn_index, selected_indices.size()]

func _bands_visual_signature() -> String:
	var combo_parts := PackedStringArray()
	for combo: Dictionary in detected_combos:
		combo_parts.append(str(int(combo.get("mask", 0))))
	return "%s|combos=%s|selected_combo=%d|sel=%s|drag=%d|started=%s" % [
		_uid_order_signature(game.player_hand),
		",".join(combo_parts),
		selected_detected_combo,
		_selected_signature(),
		drag_index,
		str(drag_started)
	]

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_refresh_all replacement failed: {n}'

# Cache immutable card frame styles. Key includes every visual input.
pattern = r'''func _card_style\(selected: bool, accent: Color\) -> StyleBoxFlat:\n.*?(?=func _load_card_texture\()'''
replacement = '''func _card_style(selected: bool, accent: Color) -> StyleBoxFlat:
	var key: String = "%s|%.5f,%.5f,%.5f,%.5f" % [str(selected), accent.r, accent.g, accent.b, accent.a]
	if _card_style_cache.has(key):
		return _card_style_cache[key] as StyleBoxFlat
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
	_card_style_cache[key] = st
	return st

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_card_style replacement failed: {n}'

# Cache band styles; output is identical, only allocation disappears.
pattern = r'''func _band_style\(color: Color, selected: bool\) -> StyleBoxFlat:\n.*?(?=func _refresh_discard\()'''
replacement = '''func _band_style(color: Color, selected: bool) -> StyleBoxFlat:
	var key: String = "%.5f,%.5f,%.5f,%.5f|%s" % [color.r, color.g, color.b, color.a, str(selected)]
	if _band_style_cache.has(key):
		return _band_style_cache[key] as StyleBoxFlat
	var st := StyleBoxFlat.new()
	st.bg_color = Color(color.r, color.g, color.b, 0.95 if selected else 0.78)
	st.border_color = Color(1, 1, 1, 0.85) if selected else color.lightened(0.18)
	st.set_border_width_all(2 if selected else 1)
	st.set_corner_radius_all(7)
	st.shadow_color = Color(0, 0, 0, 0.22)
	st.shadow_size = 3
	_band_style_cache[key] = st
	return st

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_band_style replacement failed: {n}'

# Cache generic button styles. The shadow alpha stays exactly as v0.0.23 (0.0 after
# patch v021), so this cannot alter the final rendered appearance.
pattern = r'''func _button_style\(bg: Color, border: Color, width: int, radius: int\) -> StyleBoxFlat:\n.*?(?=func _clear_children\()'''
replacement = '''func _button_style(bg: Color, border: Color, width: int, radius: int) -> StyleBoxFlat:
	var key: String = "%.5f,%.5f,%.5f,%.5f|%.5f,%.5f,%.5f,%.5f|%d|%d" % [
		bg.r, bg.g, bg.b, bg.a, border.r, border.g, border.b, border.a, width, radius
	]
	if _button_style_cache.has(key):
		return _button_style_cache[key] as StyleBoxFlat
	var st: StyleBoxFlat = StyleBoxFlat.new()
	st.bg_color = bg
	st.border_color = border
	st.set_border_width_all(width)
	st.set_corner_radius_all(radius)
	st.shadow_color = Color(0, 0, 0, 0.0)
	st.shadow_size = 6
	_button_style_cache[key] = st
	return st

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_button_style replacement failed: {n}'

# On a new round, invalidate signatures once so every section rebuilds exactly once.
old = '''\tgame.new_round()\n\tdeal_animation_done = false\n\t_refresh_all()'''
new = '''\tgame.new_round()\n\tdeal_animation_done = false\n\t_invalidate_visual_caches()\n\t_refresh_all()'''
assert old in text, 'replay refresh block not found'
text = text.replace(old, new, 1)

marker = 'func _dict_int_array(item: Dictionary, key: String) -> Array[int]:\n'
assert marker in text, 'dict helper marker not found'
helper = '''func _invalidate_visual_caches() -> void:
	_last_detect_signature = ""
	_last_opponents_signature = ""
	_last_player_signature = ""
	_last_discard_signature = ""
	_last_table_refresh_signature = ""
	_last_bands_signature = ""

'''
text = text.replace(marker, helper + marker, 1)

text = text.replace('v0.0.23', 'v0.0.24')
marker = 'print("RAMI_V023: table_autofit=true pinch_zoom=true pan=true no_meld_overlap=true auto_reset_on_table_change=true")'
if marker in text:
	text = text.replace(marker, marker + '\n\tprint("RAMI_V024: dirty_refresh=true table_persistent=true style_cache=true score_single_pass=true visual_unchanged=true")', 1)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V024: dirty UI refresh + shared immutable styles; zero visual changes')
