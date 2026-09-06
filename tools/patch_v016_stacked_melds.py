from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# Real stack state: table melds are compact by default; tap one to expand it.
needle = 'var hand_swipe_active: bool = false\n'
assert needle in text, 'hand_swipe_active marker not found'
text = text.replace(needle, needle + 'var expanded_meld_index: int = -1\n', 1)

# Replace v0.0.15 compact fan with true stacked melds.
pattern = r'''func _refresh_melds\(\) -> void:\n.*?(?=func _make_card\()'''
replacement = '''func _refresh_melds() -> void:
	_clear_children(meld_layer)
	if game.table_melds.is_empty():
		_make_label("Aucune combinaison posée", Vector2(230, 150), Vector2(620, 54), 26, Color(0.84, 0.94, 0.88, 0.62), HORIZONTAL_ALIGNMENT_CENTER, meld_layer)
		return

	if expanded_meld_index >= game.table_melds.size():
		expanded_meld_index = -1

	var card_w: float = 132.0
	var card_h: float = 186.0
	var stack_step_x: float = 13.0
	var stack_step_y: float = 4.0
	var expanded_step: float = 58.0
	var x: float = 10.0
	var y: float = 38.0
	var row_height: float = card_h + 58.0
	var usable_width: float = maxf(320.0, meld_layer.size.x - 18.0)

	for meld_index: int in range(game.table_melds.size()):
		var meld: Dictionary = game.table_melds[meld_index]
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var owner: int = int(meld.get("owner", 0))
		var expanded: bool = expanded_meld_index == meld_index

		# Closed meld = a true stack. Open meld = readable fan for inspection/editing.
		var step_x: float = expanded_step if expanded else stack_step_x
		var step_y: float = 0.0 if expanded else stack_step_y
		var meld_width: float = step_x * float(maxi(0, cards.size() - 1)) + card_w
		var meld_height: float = card_h + step_y * float(maxi(0, cards.size() - 1))

		if x > 10.0 and x + meld_width > usable_width:
			x = 10.0
			y += row_height

		var owner_color: Color = GREEN if owner == 0 else RED
		var state_text: String = "OUVERTE" if expanded else "EMPILÉE"
		_make_label(
			"%s • %d cartes • %s" % [RamiGame.PLAYER_NAMES[owner], cards.size(), state_text],
			Vector2(x, y - 30.0),
			Vector2(maxf(150.0, meld_width), 26.0),
			14,
			owner_color,
			HORIZONTAL_ALIGNMENT_CENTER,
			meld_layer
		)

		# Draw every physical card. In stack mode only the edge of lower cards peeks out.
		for i: int in range(cards.size()):
			_make_card(
				cards[i].face_id(),
				Vector2(x + float(i) * step_x, y + float(i) * step_y),
				Vector2(card_w, card_h),
				false,
				-2,
				meld_layer,
				false,
				Color(0, 0, 0, 0)
			)

		# Number badge makes the compact pile explicit.
		if not expanded:
			var badge: Panel = _panel(
				Vector2(x + meld_width - 43.0, y + meld_height - 39.0),
				Vector2(48, 34),
				Color("#173E2D"),
				GOLD,
				12,
				2,
				meld_layer
			)
			_make_label("×%d" % cards.size(), Vector2.ZERO, badge.size, 16, TEXT, HORIZONTAL_ALIGNMENT_CENTER, badge)

		# Entire stack/fan is tappable. No selected hand card = open/close.
		# Selected hand card(s) = existing extension/Joker-replacement logic.
		var meld_touch: Button = Button.new()
		meld_touch.name = "MeldTouch_%d" % meld_index
		meld_touch.text = ""
		meld_touch.position = Vector2(x, y)
		meld_touch.size = Vector2(maxf(card_w, meld_width), maxf(card_h, meld_height))
		meld_touch.focus_mode = Control.FOCUS_NONE
		meld_touch.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		meld_touch.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 8))
		meld_touch.add_theme_stylebox_override("hover", _button_style(Color(0.12, 0.62, 0.36, 0.04), Color(0.40, 0.95, 0.62, 0.38), 2, 10))
		meld_touch.add_theme_stylebox_override("pressed", _button_style(Color(0.12, 0.62, 0.36, 0.08), Color(0.40, 0.95, 0.62, 0.62), 3, 10))
		meld_touch.tooltip_text = "Touchez pour ouvrir/fermer la pile ou y ajouter vos cartes"
		meld_touch.pressed.connect(_on_meld_pressed.bind(meld_index))
		meld_layer.add_child(meld_touch)

		x += meld_width + 34.0

	print("RAMI_TABLE_V016: true_stacks=true melds=", game.table_melds.size(), " expanded=", expanded_meld_index)

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_refresh_melds replacement failed: {n}'

# Tap a stack with no hand selection to expand/collapse it. With selected hand cards,
# keep the existing gameplay action (extend run/set or replace/recover Joker).
pattern = r'''func _on_meld_pressed\(meld_index: int\) -> void:\n.*?(?=func _on_discard_pressed\(\) -> void:)'''
replacement = '''func _on_meld_pressed(meld_index: int) -> void:
	if meld_index < 0 or meld_index >= game.table_melds.size():
		return

	if selected_indices.is_empty():
		if expanded_meld_index == meld_index:
			expanded_meld_index = -1
			game.last_message = "Combinaison empilée pour libérer de la place."
		else:
			expanded_meld_index = meld_index
			game.last_message = "Combinaison ouverte. Sélectionnez une carte de votre main pour la compléter."
		_refresh_all()
		return

	var result: Dictionary = game.play_player_on_meld(selected_indices, meld_index)
	if bool(result.get("ok", false)):
		_reset_selection()
		expanded_meld_index = -1
		game.last_message = String(result.get("message", "Combinaison complétée puis empilée."))
	else:
		game.last_message = String(result.get("message", "Cette carte ne peut pas compléter cette combinaison."))
	_refresh_all()

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_on_meld_pressed replacement failed: {n}'

text = text.replace('v0.0.15 • TABLE XXL + SÉLECTION LIBRE', 'v0.0.16 • COMBINAISONS EMPILÉES')
text = text.replace(
    'print("RAMI_V015: combo_single_card=true table_brighter=true table_bigger=true compact_melds=true app_icon_final=true")',
    'print("RAMI_V015: combo_single_card=true table_brighter=true table_bigger=true compact_melds=true app_icon_final=true")\n\tprint("RAMI_V016: true_stacked_melds=true tap_expand=true auto_restack_after_edit=true")'
)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V016: true stacked melds with tap-to-expand behavior applied')
