from pathlib import Path
import re

# =============================================================================
# GameTable.gd — keep the exact same visual layout, reduce allocations/rebuilds.
# =============================================================================
ui_path = Path('GameTable.gd')
ui = ui_path.read_text(encoding='utf-8')

# Cache loaded textures and share the display-only shader material.
needle = 'var drag_distance: float = 0.0\n'
assert needle in ui, 'drag vars marker not found'
ui = ui.replace(needle, needle + '\nvar _texture_cache: Dictionary = {}\nvar _display_card_material: ShaderMaterial\n', 1)

# Reuse player card nodes whenever the hand composition is unchanged.
pattern = r'''func _refresh_player\(\) -> void:\n.*?(?=func _player_card_y\()'''
replacement = '''func _refresh_player() -> void:
	var count: int = game.player_hand.size()
	if count <= 0:
		_clear_children(player_layer)
		return
	_calculate_hand_layout()
	if _can_reuse_player_nodes():
		_reposition_player_nodes_fast()
		return

	_clear_children(player_layer)
	for i: int in range(count):
		var y: float = _player_card_y(i, count)
		var selected: bool = selected_indices.has(i) or (drag_started and drag_index == i)
		if selected:
			y -= 24.0
		var card: CardInstance = game.player_hand[i]
		var wrapper: Control = _make_card(card.face_id(), Vector2(float(i) * hand_step, y), PLAYER_CARD_SIZE, true, i, player_layer, selected, Color(0, 0, 0, 0))
		wrapper.set_meta("card_uid", card.uid)

func _can_reuse_player_nodes() -> bool:
	if player_layer.get_child_count() != game.player_hand.size():
		return false
	var seen: Dictionary = {}
	for child: Node in player_layer.get_children():
		if not child.has_meta("card_uid"):
			return false
		seen[int(child.get_meta("card_uid"))] = true
	for card: CardInstance in game.player_hand:
		if not seen.has(card.uid):
			return false
	return true

func _reposition_player_nodes_fast() -> void:
	_calculate_hand_layout()
	var by_uid: Dictionary = {}
	for child: Node in player_layer.get_children():
		if child.has_meta("card_uid"):
			by_uid[int(child.get_meta("card_uid"))] = child

	var count: int = game.player_hand.size()
	for i: int in range(count):
		var card: CardInstance = game.player_hand[i]
		if not by_uid.has(card.uid):
			return
		var wrapper: Control = by_uid[card.uid] as Control
		var selected: bool = selected_indices.has(i) or (drag_started and drag_index == i)
		var y: float = _player_card_y(i, count)
		if selected:
			y -= 24.0
		wrapper.position = Vector2(float(i) * hand_step, y)
		player_layer.move_child(wrapper, i)
		if wrapper.get_child_count() > 0 and wrapper.get_child(0) is Panel:
			var frame := wrapper.get_child(0) as Panel
			frame.add_theme_stylebox_override("panel", _card_style(selected, Color(0, 0, 0, 0)))

'''
ui, n = re.subn(pattern, replacement, ui, flags=re.S)
assert n == 1, f'_refresh_player replacement failed: {n}'

# During drag, move/reorder existing nodes instead of deleting/recreating the hand.
old = '''\tif target != drag_index:\n\t\t_move_hand_card_for_drag(drag_index, target)\n\t\tdrag_index = target\n\t\t# Fast path while dragging: never enumerate all possible meld subsets here.\n\t\t_refresh_player()'''
new = '''\tif target != drag_index:\n\t\t_move_hand_card_for_drag(drag_index, target)\n\t\tdrag_index = target\n\t\t# Fast path: preserve the same CardViews and only move them.\n\t\t_reposition_player_nodes_fast()'''
assert old in ui, 'v019 drag fast-path block not found'
ui = ui.replace(old, new, 1)

# Bind player cards by immutable uid, so input remains correct after visual reordering.
old = '''\t\tif index >= 0:\n\t\t\tbutton.gui_input.connect(_on_player_card_gui_input.bind(index))\n\t\telif index == -1:\n\t\t\tbutton.pressed.connect(_on_draw_discard)'''
new = '''\t\tif index >= 0:\n\t\t\tvar uid: int = game.player_hand[index].uid if index < game.player_hand.size() else -1\n\t\t\twrapper.set_meta("card_uid", uid)\n\t\t\tbutton.gui_input.connect(_on_player_card_gui_input_uid.bind(uid))\n\t\telif index == -1:\n\t\t\tbutton.pressed.connect(_on_draw_discard)'''
assert old in ui, 'player input bind block not found'
ui = ui.replace(old, new, 1)

marker = 'func _on_player_card_gui_input(event: InputEvent, index: int) -> void:\n'
assert marker in ui, 'player gui input marker not found'
uid_handler = '''func _on_player_card_gui_input_uid(event: InputEvent, uid: int) -> void:
	var index: int = -1
	for i: int in range(game.player_hand.size()):
		if game.player_hand[i].uid == uid:
			index = i
			break
	if index >= 0:
		_on_player_card_gui_input(event, index)

'''
ui = ui.replace(marker, uid_handler + marker, 1)

# Texture Resource cache: same pixels, fewer repeated load() calls.
pattern = r'''func _load_card_texture\(card_id: String\) -> Texture2D:\n.*?(?=func _on_player_card_gui_input_uid\()'''
replacement = '''func _load_card_texture(card_id: String) -> Texture2D:
	if _texture_cache.has(card_id):
		return _texture_cache[card_id] as Texture2D
	var resource: Resource = load("res://assets/cards/%s.png" % card_id)
	if resource is Texture2D:
		var texture := resource as Texture2D
		_texture_cache[card_id] = texture
		return texture
	return null

func _get_display_card_material() -> ShaderMaterial:
	if is_instance_valid(_display_card_material):
		return _display_card_material
	var shader := Shader.new()
	shader.code = "shader_type canvas_item; render_mode unshaded; void fragment(){ COLOR = texture(TEXTURE, UV); }"
	_display_card_material = ShaderMaterial.new()
	_display_card_material.shader = shader
	return _display_card_material

'''
ui, n = re.subn(pattern, replacement, ui, flags=re.S)
assert n == 1, f'texture cache replacement failed: {n}'

# v0.0.20 created a Shader+ShaderMaterial for every display card; share one instead.
old = '''\t\tvar shader := Shader.new()\n\t\tshader.code = "shader_type canvas_item; render_mode unshaded; void fragment(){ COLOR = texture(TEXTURE, UV); }"\n\t\tvar mat := ShaderMaterial.new()\n\t\tmat.shader = shader\n\t\timage.material = mat'''
new = '''\t\timage.material = _get_display_card_material()'''
assert old in ui, 'per-card shader block not found'
ui = ui.replace(old, new, 1)

# Version/debug marker only; layout/style constants remain untouched.
ui = ui.replace('v0.0.21', 'v0.0.22')
ready_marker = 'print("RAMI_V021: button_shadow_alpha=0.0 parameter_kept=true")'
if ready_marker in ui:
    ui = ui.replace(ready_marker, ready_marker + '\n\tprint("RAMI_V022: pooled_hand_nodes=true texture_cache=true shared_card_shader=true visual_layout_unchanged=true")', 1)

ui_path.write_text(ui, encoding='utf-8')

# =============================================================================
# RamiGame.gd — cache meld detection results for unchanged hands.
# This preserves the exact existing detector and therefore its rule behaviour/order.
# =============================================================================
engine_path = Path('RamiGame.gd')
engine = engine_path.read_text(encoding='utf-8')

needle = 'var must_replay_jokers: Array[CardInstance] = []\n'
assert needle in engine, 'must_replay_jokers marker not found'
engine = engine.replace(needle, needle + '\nvar _meld_cache: Dictionary = {}\nvar _meld_cache_order: Array[String] = []\nconst MELD_CACHE_LIMIT: int = 48\n', 1)

pattern = r'''func detect_melds\(hand: Array\[CardInstance\]\) -> Array\[Dictionary\]:\n.*?(?=func _candidate_better\()'''
match = re.search(pattern, engine, flags=re.S)
assert match, 'detect_melds block not found'
original = match.group(0)
# Strip the next function marker because it belongs after the replacement.
body = original[:original.rfind('func _candidate_better(')]
# Rename original implementation and wrap it with a cache.
impl = body.replace('func detect_melds(hand: Array[CardInstance]) -> Array[Dictionary]:', 'func _detect_melds_uncached(hand: Array[CardInstance]) -> Array[Dictionary]:', 1)
wrapper = '''func detect_melds(hand: Array[CardInstance]) -> Array[Dictionary]:
	var key: String = _meld_cache_key(hand)
	if _meld_cache.has(key):
		return _meld_cache[key] as Array[Dictionary]
	var result: Array[Dictionary] = _detect_melds_uncached(hand)
	_meld_cache[key] = result
	_meld_cache_order.append(key)
	if _meld_cache_order.size() > MELD_CACHE_LIMIT:
		var oldest: String = _meld_cache_order.pop_front()
		_meld_cache.erase(oldest)
	return result

func _meld_cache_key(hand: Array[CardInstance]) -> String:
	var parts := PackedStringArray()
	for card: CardInstance in hand:
		parts.append(str(card.uid))
	return ",".join(parts)

'''
engine = engine[:match.start()] + wrapper + impl + engine[match.end()-len('func _candidate_better('):]

engine_path.write_text(engine, encoding='utf-8')
print('RAMI_PATCH_V022: runtime optimized; visual layout/assets unchanged')
