from pathlib import Path
import re

# =============================================================================
# GameTable.gd — exact same visual layout, fewer allocations/rebuilds.
# =============================================================================
ui_path = Path('GameTable.gd')
ui = ui_path.read_text(encoding='utf-8')

needle = 'var drag_distance: float = 0.0\n'
assert needle in ui, 'drag vars marker not found'
ui = ui.replace(needle, needle + '\nvar _texture_cache: Dictionary = {}\nvar _display_card_material: ShaderMaterial\n', 1)

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

old = '''\tif target != drag_index:\n\t\t_move_hand_card_for_drag(drag_index, target)\n\t\tdrag_index = target\n\t\t# Fast path while dragging: never enumerate all possible meld subsets here.\n\t\t_refresh_player()'''
new = '''\tif target != drag_index:\n\t\t_move_hand_card_for_drag(drag_index, target)\n\t\tdrag_index = target\n\t\t# Fast path: preserve the same CardViews and only move them.\n\t\t_reposition_player_nodes_fast()'''
assert old in ui, 'v019 drag fast-path block not found'
ui = ui.replace(old, new, 1)

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

old = '''\t\tvar shader := Shader.new()\n\t\tshader.code = "shader_type canvas_item; render_mode unshaded; void fragment(){ COLOR = texture(TEXTURE, UV); }"\n\t\tvar mat := ShaderMaterial.new()\n\t\tmat.shader = shader\n\t\timage.material = mat'''
new = '''\t\timage.material = _get_display_card_material()'''
assert old in ui, 'per-card shader block not found'
ui = ui.replace(old, new, 1)

ui = ui.replace('v0.0.21', 'v0.0.22')
ready_marker = 'print("RAMI_V021: button_shadow_alpha=0.0 parameter_kept=true")'
if ready_marker in ui:
    ui = ui.replace(ready_marker, ready_marker + '\n\tprint("RAMI_V022: pooled_hand_nodes=true texture_cache=true shared_card_shader=true fast_meld_detector=true visual_layout_unchanged=true")', 1)
ui_path.write_text(ui, encoding='utf-8')

# =============================================================================
# RamiGame.gd — replace 2^N subset enumeration by rule-directed generation.
# validate_meld() remains the final authority, so gameplay rules stay identical.
# =============================================================================
engine_path = Path('RamiGame.gd')
engine = engine_path.read_text(encoding='utf-8')

pattern = r'''func detect_melds\(hand: Array\[CardInstance\]\) -> Array\[Dictionary\]:\n.*?(?=func _candidate_better\()'''
replacement = '''func detect_melds(hand: Array[CardInstance]) -> Array[Dictionary]:
	var candidates: Array[Dictionary] = []
	if hand.size() < 3:
		return candidates

	var joker_indices: Array[int] = []
	var natural_by_rank: Dictionary = {}
	var natural_by_suit_rank: Dictionary = {}
	for i: int in range(hand.size()):
		var card: CardInstance = hand[i]
		if card.is_joker():
			joker_indices.append(i)
			continue
		if not natural_by_rank.has(card.rank):
			natural_by_rank[card.rank] = {}
		var by_suit: Dictionary = natural_by_rank[card.rank]
		if not by_suit.has(card.suit):
			by_suit[card.suit] = []
		(by_suit[card.suit] as Array).append(i)
		var sr_key: String = "%s|%s" % [card.suit, card.rank]
		if not natural_by_suit_rank.has(sr_key):
			natural_by_suit_rank[sr_key] = []
		(natural_by_suit_rank[sr_key] as Array).append(i)

	# Groups: same rank, one card per suit, total size 3 or 4, Jokers fill gaps.
	for rank: String in RANKS:
		if not natural_by_rank.has(rank):
			continue
		var by_suit: Dictionary = natural_by_rank[rank]
		var suit_pools: Array = []
		for suit: String in SUITS:
			if by_suit.has(suit):
				suit_pools.append(by_suit[suit])
		var natural_choices: Array = _cartesian_index_choices(suit_pools)
		for chosen_variant: Variant in natural_choices:
			var chosen: Array[int] = []
			for value: Variant in (chosen_variant as Array):
				chosen.append(int(value))
			for total: int in [3, 4]:
				var needed_jokers: int = total - chosen.size()
				if needed_jokers < 0 or needed_jokers > joker_indices.size():
					continue
				if chosen.size() < 1:
					continue
				for joker_choice_variant: Variant in _choose_index_combinations(joker_indices, needed_jokers):
					var indices: Array[int] = chosen.duplicate()
					for jv: Variant in (joker_choice_variant as Array):
						indices.append(int(jv))
					_add_detected_candidate(hand, indices, candidates)

	# Runs: enumerate only legal same-suit windows (A low and A high). Missing ranks
	# are supplied by exactly that many Jokers. Duplicate physical copies generate
	# equivalent UID alternatives without scanning unrelated subsets.
	for suit: String in SUITS:
		for high_ace: bool in [false, true]:
			var max_rank: int = 14 if high_ace else 13
			for total: int in range(3, 14):
				var last_start: int = max_rank - total + 1
				for start: int in range(1, last_start + 1):
					if high_ace and start <= 1:
						continue
					var rank_pools: Array = []
					var missing: int = 0
					var impossible: bool = false
					for value: int in range(start, start + total):
						var rank_value_for_lookup: int = 1 if value == 14 else value
						if rank_value_for_lookup < 1 or rank_value_for_lookup > 13:
							impossible = true
							break
						var rank: String = RANKS[rank_value_for_lookup - 1]
						var key: String = "%s|%s" % [suit, rank]
						if natural_by_suit_rank.has(key):
							rank_pools.append(natural_by_suit_rank[key])
						else:
							missing += 1
					if impossible or missing > joker_indices.size():
						continue
					var natural_choices: Array = _cartesian_index_choices(rank_pools)
					for chosen_variant: Variant in natural_choices:
						var chosen: Array[int] = []
						for value: Variant in (chosen_variant as Array):
							chosen.append(int(value))
						if chosen.size() + missing != total:
							continue
						for joker_choice_variant: Variant in _choose_index_combinations(joker_indices, missing):
							var indices: Array[int] = chosen.duplicate()
							for jv: Variant in (joker_choice_variant as Array):
								indices.append(int(jv))
							_add_detected_candidate(hand, indices, candidates)

	# Same ordering/filter policy as the former brute-force detector.
	candidates.sort_custom(_candidate_better)
	var filtered: Array[Dictionary] = []
	for candidate: Dictionary in candidates:
		var dominated: bool = false
		for kept: Dictionary in filtered:
			if String(candidate.get("family", "")) != String(kept.get("family", "")):
				continue
			var cmask: int = int(candidate.get("mask", 0))
			var kmask: int = int(kept.get("mask", 0))
			if cmask != kmask and (cmask & kmask) == cmask:
				dominated = true
				break
		if not dominated:
			filtered.append(candidate)
		if filtered.size() >= 12:
			break
	return filtered

func _add_detected_candidate(hand: Array[CardInstance], indices: Array[int], candidates: Array[Dictionary]) -> void:
	if indices.size() < 3 or indices.size() > 13:
		return
	indices.sort()
	var mask: int = 0
	var cards: Array[CardInstance] = []
	for idx: int in indices:
		if idx < 0 or idx >= hand.size():
			return
		mask |= 1 << idx
		cards.append(hand[idx])
	for existing: Dictionary in candidates:
		if int(existing.get("mask", -1)) == mask:
			return
	var info: Dictionary = validate_meld(cards)
	if not bool(info.get("valid", false)):
		return
	candidates.append({
		"mask": mask,
		"indices": indices.duplicate(),
		"cards": _ordered_meld(cards, info),
		"kind": String(info.get("kind", "")),
		"family": String(info.get("family", "")),
		"points": int(info.get("points", 0)),
		"count": indices.size()
	})

func _choose_index_combinations(pool: Array[int], choose: int) -> Array:
	var out: Array = []
	if choose == 0:
		out.append([])
		return out
	if choose < 0 or choose > pool.size():
		return out
	_choose_index_combinations_rec(pool, choose, 0, [], out)
	return out

func _choose_index_combinations_rec(pool: Array[int], choose: int, start: int, current: Array, out: Array) -> void:
	if current.size() == choose:
		out.append(current.duplicate())
		return
	var remaining_needed: int = choose - current.size()
	var last: int = pool.size() - remaining_needed
	for i: int in range(start, last + 1):
		current.append(pool[i])
		_choose_index_combinations_rec(pool, choose, i + 1, current, out)
		current.pop_back()

func _cartesian_index_choices(pools: Array) -> Array:
	var out: Array = []
	if pools.is_empty():
		out.append([])
		return out
	_cartesian_index_choices_rec(pools, 0, [], out)
	return out

func _cartesian_index_choices_rec(pools: Array, depth: int, current: Array, out: Array) -> void:
	if depth >= pools.size():
		out.append(current.duplicate())
		return
	var pool: Array = pools[depth] as Array
	for value: Variant in pool:
		current.append(int(value))
		_cartesian_index_choices_rec(pools, depth + 1, current, out)
		current.pop_back()

'''
engine, n = re.subn(pattern, replacement, engine, flags=re.S)
assert n == 1, f'detect_melds replacement failed: {n}'
engine_path.write_text(engine, encoding='utf-8')
print('RAMI_PATCH_V022: pooled UI + cached resources + rule-directed meld detector; visuals unchanged')
