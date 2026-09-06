from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# Keep any meld containing a Joker visually open, even when it otherwise reaches
# the nominal maximum length. It is not considered 'finished' until every card is natural.
pattern = r'''func _is_table_meld_complete\(cards: Array\[CardInstance\], kind: String\) -> bool:\n.*?(?=func _make_card\()'''
replacement = '''func _is_table_meld_complete(cards: Array[CardInstance], kind: String) -> bool:
	# A meld containing any Joker is never visually final: the Joker can still be
	# replaced by its natural card, so the meld must stay open and readable.
	for card: CardInstance in cards:
		if card.is_joker():
			return false

	if kind == "set":
		return cards.size() == 4

	if kind == "run":
		if cards.size() != 13:
			return false
		var info: Dictionary = game.validate_meld(cards)
		return bool(info.get("valid", false)) and String(info.get("kind", "")) == "run"
	return false

'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_is_table_meld_complete replacement failed: {n}'

# Make display-only card art bypass inherited tint/modulation completely.
# A small canvas shader samples the PNG directly, preserving original whites/colors.
needle = '''\telse:\n\t\t# Pure visual image: it has no disabled state, so it stays as bright as cards\n\t\t# in the player's hand on Android/Samsung.\n\t\tvar image: TextureRect = TextureRect.new()'''
replacement2 = '''\telse:\n\t\t# Pure visual image: force exact source colours. This avoids any theme/parent\n\t\t# tint that could make table/discard cards appear grey on Android.\n\t\tvar image: TextureRect = TextureRect.new()'''
assert needle in text, 'display-only image block not found'
text = text.replace(needle, replacement2, 1)

needle2 = '''\t\timage.mouse_filter = Control.MOUSE_FILTER_IGNORE\n\t\timage.modulate = Color.WHITE\n\t\timage.self_modulate = Color.WHITE\n\t\twrapper.add_child(image)'''
replacement3 = '''\t\timage.mouse_filter = Control.MOUSE_FILTER_IGNORE\n\t\timage.modulate = Color.WHITE\n\t\timage.self_modulate = Color.WHITE\n\t\tvar shader := Shader.new()\n\t\tshader.code = "shader_type canvas_item; render_mode unshaded; void fragment(){ COLOR = texture(TEXTURE, UV); }"\n\t\tvar mat := ShaderMaterial.new()\n\t\tmat.shader = shader\n\t\timage.material = mat\n\t\twrapper.add_child(image)'''
assert needle2 in text, 'display image end block not found'
text = text.replace(needle2, replacement3, 1)

# The discard card gets the same untinted display treatment automatically because
# it is created with clickable=false under the always-on transparent touch overlay.

text = text.replace('v0.0.19', 'v0.0.20')
marker = 'print("RAMI_V019: bright_display_cards=true drag_fast_path=true adaptive_table_fit=true larger_table=true")'
if marker in text:
    text = text.replace(marker, marker + '\n\tprint("RAMI_V020: exact_card_colors=true joker_melds_never_stacked=true")', 1)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V020: exact source card colours + Joker melds remain open')
