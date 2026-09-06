from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# The discard pile must remain a real touch target even after the player takes its
# last visible card. In v0.0.13, when discard_pile became empty, _refresh_discard()
# created no TextureButton at all, so the player had nowhere to tap to end the turn.
pattern = r'''func _refresh_discard\(\) -> void:\n.*?(?=func _refresh_melds\(\) -> void:)'''
replacement = '''func _refresh_discard() -> void:
	_clear_children(discard_layer)
	var top: CardInstance = game.top_discard()
	var can_touch: bool = game.turn_index == 0 and (game.phase == RamiGame.Phase.DRAW or game.phase == RamiGame.Phase.ACTION)
	var accent: Color = GREEN if game.phase == RamiGame.Phase.ACTION and selected_indices.size() == 1 else GOLD

	# Visual card if a discard exists; otherwise keep a visible empty slot.
	if top != null:
		_make_card(top.face_id(), Vector2(10, 0), Vector2(132, 186), false, -2, discard_layer, false, accent)
	else:
		var empty_slot: Panel = Panel.new()
		empty_slot.position = Vector2(10, 0)
		empty_slot.size = Vector2(132, 186)
		empty_slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
		empty_slot.add_theme_stylebox_override("panel", _button_style(Color(0.03, 0.13, 0.09, 0.28), Color(0.78, 0.88, 0.82, 0.35), 2, 14))
		discard_layer.add_child(empty_slot)
		_make_label("POSEZ\nICI", Vector2(10, 54), Vector2(132, 72), 18, Color(0.82, 0.90, 0.85, 0.52), HORIZONTAL_ALIGNMENT_CENTER, discard_layer)

	# Always-on overlay: DRAW = take discard, ACTION = discard selected card.
	var touch: Button = Button.new()
	touch.name = "DiscardTouchArea"
	touch.position = Vector2(10, 0)
	touch.size = Vector2(132, 186)
	touch.disabled = not can_touch
	touch.focus_mode = Control.FOCUS_NONE
	touch.text = ""
	touch.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	touch.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))
	touch.add_theme_stylebox_override("hover", _button_style(Color(0.18, 0.70, 0.42, 0.05), accent, 3, 10))
	touch.add_theme_stylebox_override("pressed", _button_style(Color(0.18, 0.70, 0.42, 0.10), accent, 4, 10))
	touch.add_theme_stylebox_override("disabled", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 10))
	touch.tooltip_text = "Prendre la défausse" if game.phase == RamiGame.Phase.DRAW else "Défausser la carte sélectionnée"
	touch.pressed.connect(_on_discard_zone_pressed)
	discard_layer.add_child(touch)

	_make_label("Défausse", Vector2(0, 191), Vector2(150, 30), 23, TEXT, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)
	_make_label("Touchez la pile", Vector2(0, 220), Vector2(150, 22), 15, MUTED, HORIZONTAL_ALIGNMENT_CENTER, discard_layer)

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_refresh_discard replacement failed: {n}'

# Replace the legacy card-specific handler by one zone handler that works whether
# or not there is currently a visible discard card.
pattern = r'''func _on_draw_discard\(\) -> void:\n.*?(?=func _on_player_card_pressed\(index: int\) -> void:)'''
replacement = '''func _on_draw_discard() -> void:
	# Kept as compatibility alias for old connections.
	_on_discard_zone_pressed()

func _on_discard_zone_pressed() -> void:
	if game.turn_index != 0:
		return

	if game.phase == RamiGame.Phase.DRAW:
		if game.draw_discard():
			_reset_selection()
		else:
			game.last_message = "Aucune carte disponible dans la défausse. Piochez une carte."
		_refresh_all()
		return

	if game.phase == RamiGame.Phase.ACTION:
		if selected_indices.size() != 1:
			game.last_message = "Sélectionnez exactement 1 carte, puis touchez la défausse."
			_refresh_all()
			return
		var result: Dictionary = game.discard_player(selected_indices[0])
		if bool(result.get("ok", false)):
			_reset_selection()
			hand_scroll_offset = 0.0
		else:
			game.last_message = String(result.get("message", "Défausse impossible."))
		_refresh_all()

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'discard handler replacement failed: {n}'

text = text.replace('v0.0.13 • TABLE INTERACTIVE + JOKER', 'v0.0.14 • DÉFAUSSE FIX + ICÔNE AJUSTÉE')
text = text.replace(
    'print("RAMI_V013: meld_touch_anywhere=true extend_runs=true joker_slot_order=true joker_recovery=true")',
    'print("RAMI_V013: meld_touch_anywhere=true extend_runs=true joker_slot_order=true joker_recovery=true")\n\tprint("RAMI_V014: discard_zone_always=true empty_discard_touch=true icon_padded=true")'
)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V014: discard zone remains tappable even when pile is empty')
