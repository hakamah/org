from pathlib import Path
import re

# --- Engine: order Jokers in the actual missing slot of a run -----------------
engine_path = Path('RamiGame.gd')
engine = engine_path.read_text(encoding='utf-8')

pattern = r'''func _ordered_meld\(cards: Array\[CardInstance\], info: Dictionary\) -> Array\[CardInstance\]:\n.*?(?=func _consume_required_jokers\()'''
replacement = '''func _ordered_meld(cards: Array[CardInstance], info: Dictionary) -> Array[CardInstance]:
	var natural: Array[CardInstance] = []
	var jokers: Array[CardInstance] = []
	for card: CardInstance in cards:
		if card.is_joker():
			jokers.append(card)
		else:
			natural.append(card)

	if String(info.get("kind", "")) == "set":
		natural.sort_custom(_card_less_suit)
		natural.append_array(jokers)
		return natural

	# For runs, display every Joker exactly in the logical missing rank slot.
	# Example: 5♣ 6♣ Joker 8♣, never 5♣ 6♣ 8♣ Joker.
	var high_ace: bool = bool(info.get("high_ace", false))
	var start: int = int(info.get("start", 1))
	var by_value: Dictionary = {}
	for card: CardInstance in natural:
		var value: int = rank_value(card.rank)
		if high_ace and value == 1:
			value = 14
		by_value[value] = card

	var ordered: Array[CardInstance] = []
	var joker_index: int = 0
	for target: int in range(start, start + cards.size()):
		if by_value.has(target):
			ordered.append(by_value[target] as CardInstance)
		elif joker_index < jokers.size():
			ordered.append(jokers[joker_index])
			joker_index += 1

	while joker_index < jokers.size():
		ordered.append(jokers[joker_index])
		joker_index += 1
	return ordered

'''
engine, n = re.subn(pattern, replacement, engine, flags=re.S)
assert n == 1, f'_ordered_meld replacement failed: {n}'

# Allow several selected cards to complete/extend a table meld in any hand order.
# First recover Jokers when a selected natural card exactly replaces one, then validate
# all remaining selected cards together instead of one-by-one.
pattern = r'''func _simulate_add_to_meld\(existing: Array\[CardInstance\], selected: Array\[CardInstance\], allow_replace: bool\) -> Dictionary:\n.*?(?=func _run_ai_turn\()'''
replacement = '''func _simulate_add_to_meld(existing: Array[CardInstance], selected: Array[CardInstance], allow_replace: bool) -> Dictionary:
	var current: Array[CardInstance] = []
	for card: CardInstance in existing:
		current.append(card)
	var remaining: Array[CardInstance] = []
	for card: CardInstance in selected:
		remaining.append(card)
	var recovered: Array[CardInstance] = []

	if allow_replace:
		var scan: int = 0
		while scan < remaining.size():
			var card: CardInstance = remaining[scan]
			if card.is_joker():
				scan += 1
				continue
			var replaced: bool = false
			for j: int in range(current.size()):
				if not current[j].is_joker():
					continue
				var test: Array[CardInstance] = []
				for existing_card: CardInstance in current:
					test.append(existing_card)
				var joker: CardInstance = test[j]
				test.remove_at(j)
				test.append(card)
				var info: Dictionary = validate_meld(test)
				if bool(info.get("valid", false)):
					current = _ordered_meld(test, info)
					recovered.append(joker)
					remaining.remove_at(scan)
					replaced = true
					break
			if not replaced:
				scan += 1

	# Validate all remaining cards as one final table state. This permits, for example,
	# selecting 9♥ then 8♥ to extend 5♥-6♥-7♥, because the final 5-6-7-8-9 is valid.
	if not remaining.is_empty():
		var combined: Array[CardInstance] = []
		for existing_card: CardInstance in current:
			combined.append(existing_card)
		for extra: CardInstance in remaining:
			combined.append(extra)
		var combined_info: Dictionary = validate_meld(combined)
		if not bool(combined_info.get("valid", false)):
			return {"ok": false}
		current = _ordered_meld(combined, combined_info)

	return {"ok": true, "cards": current, "recovered": recovered}

'''
engine, n = re.subn(pattern, replacement, engine, flags=re.S)
assert n == 1, f'_simulate_add_to_meld replacement failed: {n}'
engine_path.write_text(engine, encoding='utf-8')

# --- UI: make the whole meld tappable, not only its owner label ---------------
ui_path = Path('GameTable.gd')
ui = ui_path.read_text(encoding='utf-8')

needle = '''		for i: int in range(cards.size()):
			_make_card(cards[i].face_id(), Vector2(x + float(i) * card_step, y), Vector2(card_w, card_h), false, -2, meld_layer, false, Color(0, 0, 0, 0))
		x += meld_width + 30.0'''
replacement_ui = '''		for i: int in range(cards.size()):
			_make_card(cards[i].face_id(), Vector2(x + float(i) * card_step, y), Vector2(card_w, card_h), false, -2, meld_layer, false, Color(0, 0, 0, 0))

		# Entire visible meld is a touch target. Select card(s) in hand, then tap
		# anywhere on this combination to add/extend or replace a Joker.
		var meld_touch: Button = Button.new()
		meld_touch.name = "MeldTouch_%d" % meld_index
		meld_touch.text = ""
		meld_touch.position = Vector2(x, y)
		meld_touch.size = Vector2(maxf(card_w, meld_width), card_h)
		meld_touch.focus_mode = Control.FOCUS_NONE
		meld_touch.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		meld_touch.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 8))
		meld_touch.add_theme_stylebox_override("hover", _button_style(Color(0.12, 0.62, 0.36, 0.06), Color(0.40, 0.95, 0.62, 0.45), 3, 10))
		meld_touch.add_theme_stylebox_override("pressed", _button_style(Color(0.12, 0.62, 0.36, 0.10), Color(0.40, 0.95, 0.62, 0.72), 4, 10))
		meld_touch.tooltip_text = "Touchez pour ajouter les cartes sélectionnées à cette combinaison"
		meld_touch.pressed.connect(_on_meld_pressed.bind(meld_index))
		meld_layer.add_child(meld_touch)
		x += meld_width + 30.0'''
assert needle in ui, 'v012 meld card loop not found'
ui = ui.replace(needle, replacement_ui, 1)

# Better guidance for manual extension/replacement.
ui = ui.replace(
    'game.last_message = "Sélectionnez d\'abord la ou les cartes à ajouter à cette combinaison."',
    'game.last_message = "Sélectionnez une ou plusieurs cartes de votre main, puis touchez directement la combinaison de table à compléter."'
)
ui = ui.replace(
    'game.last_message = String(result.get("message", "Ajout impossible."))',
    'game.last_message = String(result.get("message", "Cette carte ne peut pas compléter cette combinaison."))'
)

ui = ui.replace('v0.0.12 • TABLE XXL + ICÔNE RAMI', 'v0.0.13 • TABLE INTERACTIVE + JOKER')
ui = ui.replace(
    'print("RAMI_V012: table_xxl=true persistent_meld_render=true app_icon=true")',
    'print("RAMI_V012: table_xxl=true persistent_meld_render=true app_icon=true")\n\tprint("RAMI_V013: meld_touch_anywhere=true extend_runs=true joker_slot_order=true joker_recovery=true")'
)
ui_path.write_text(ui, encoding='utf-8')

print('RAMI_PATCH_V013: table melds fully tappable; runs extendable; Joker displayed/recovered correctly')
