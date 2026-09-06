from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# Remove decorative/instruction text from inside the common table.
text = re.sub(r'''\n\t_make_label\("TABLE COMMUNE"[^\n]*\)''', '', text, count=1)
text = re.sub(r'''\n\t_make_label\("Touchez n'importe où dans la table pour poser la combinaison sélectionnée"[^\n]*\)''', '', text, count=1)

# v0.0.16 allowed any pile to be manually expanded/collapsed. v0.0.17 follows the
# actual game state instead: only a meld that cannot ever receive another card is
# stacked. Incomplete melds remain permanently readable as a fan.
pattern = r'''func _refresh_melds\(\) -> void:\n.*?(?=func _make_card\()'''
replacement = '''func _refresh_melds() -> void:
	_clear_children(meld_layer)
	if game.table_melds.is_empty():
		return

	var card_w: float = 132.0
	var card_h: float = 186.0
	var fan_step: float = 62.0
	var stack_step_x: float = 10.0
	var stack_step_y: float = 4.0
	var x: float = 8.0
	var y: float = 12.0
	var row_height: float = 202.0
	var usable_width: float = maxf(320.0, meld_layer.size.x - 16.0)

	for meld_index: int in range(game.table_melds.size()):
		var meld: Dictionary = game.table_melds[meld_index]
		var cards: Array[CardInstance] = _dict_card_array(meld, "cards")
		var kind: String = String(meld.get("kind", ""))
		var complete: bool = _is_table_meld_complete(cards, kind)

		# Completed melds are true piles. Incomplete melds stay fully readable in a fan.
		var step_x: float = stack_step_x if complete else fan_step
		var step_y: float = stack_step_y if complete else 0.0
		var meld_width: float = step_x * float(maxi(0, cards.size() - 1)) + card_w
		var meld_height: float = card_h + step_y * float(maxi(0, cards.size() - 1))

		if x > 8.0 and x + meld_width > usable_width:
			x = 8.0
			y += row_height

		# Keep every card bright. A completed meld shows only thin edges underneath;
		# an incomplete one keeps enough horizontal reveal to read every rank/suit.
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

		# The meld remains tappable for adding cards / replacing a Joker. Completed
		# melds naturally reject impossible extensions through the engine validator.
		var meld_touch: Button = Button.new()
		meld_touch.name = "MeldTouch_%d" % meld_index
		meld_touch.text = ""
		meld_touch.position = Vector2(x, y)
		meld_touch.size = Vector2(maxf(card_w, meld_width), maxf(card_h, meld_height))
		meld_touch.focus_mode = Control.FOCUS_NONE
		meld_touch.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		meld_touch.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 8))
		meld_touch.add_theme_stylebox_override("hover", _button_style(Color(0.12, 0.62, 0.36, 0.03), Color(0.40, 0.95, 0.62, 0.30), 2, 10))
		meld_touch.add_theme_stylebox_override("pressed", _button_style(Color(0.12, 0.62, 0.36, 0.07), Color(0.40, 0.95, 0.62, 0.55), 3, 10))
		meld_touch.pressed.connect(_on_meld_pressed.bind(meld_index))
		meld_layer.add_child(meld_touch)

		x += meld_width + 28.0

	print("RAMI_TABLE_V017: smart_completion_layout=true melds=", game.table_melds.size())

func _is_table_meld_complete(cards: Array[CardInstance], kind: String) -> bool:
	# A same-rank group is complete once all four suits are present (4 cards total).
	if kind == "set":
		return cards.size() == 4

	# A run is complete only when it contains all 13 ranks of one suit. Under the
	# game rules this is A-2-3-...-Q-K (Ace can also be high in shorter runs, but a
	# full run still contains exactly 13 physical cards and cannot be extended).
	if kind == "run":
		if cards.size() != 13:
			return false
		var info: Dictionary = game.validate_meld(cards)
		return bool(info.get("valid", false)) and String(info.get("kind", "")) == "run"
	return false

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_refresh_melds replacement failed: {n}'

# No manual open/close state anymore: a meld's visual state is determined only by
# whether it is complete. Tapping without a hand selection therefore does nothing.
pattern = r'''func _on_meld_pressed\(meld_index: int\) -> void:\n.*?(?=func _on_discard_pressed\(\) -> void:)'''
replacement = '''func _on_meld_pressed(meld_index: int) -> void:
	if meld_index < 0 or meld_index >= game.table_melds.size():
		return
	if selected_indices.is_empty():
		return

	var result: Dictionary = game.play_player_on_meld(selected_indices, meld_index)
	if bool(result.get("ok", false)):
		_reset_selection()
		game.last_message = String(result.get("message", "Combinaison complétée."))
	else:
		game.last_message = String(result.get("message", "Cette carte ne peut pas compléter cette combinaison."))
	_refresh_all()

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_on_meld_pressed replacement failed: {n}'

text = text.replace('v0.0.16 • COMBINAISONS EMPILÉES', 'v0.0.17 • TABLE INTELLIGENTE')
text = text.replace(
    'print("RAMI_V016: true_stacked_melds=true tap_expand=true auto_restack_after_edit=true")',
    'print("RAMI_V016: true_stacked_melds=true tap_expand=true auto_restack_after_edit=true")\n\tprint("RAMI_V017: stack_only_complete=true incomplete_fan=true no_table_text=true")'
)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V017: completed-only stacks + readable incomplete fans + clean table')
