from pathlib import Path
import re

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

# Enlarge the common table to use most of the free center area while preserving the hand.
text = text.replace(
    '_panel(Vector2(205, 190), Vector2(980, 365), Color(0.04, 0.27, 0.18, 0.22), Color(0.20, 0.65, 0.43, 0.38), 26, 3)',
    '_panel(Vector2(145, 92), Vector2(1060, 500), Color(0.04, 0.27, 0.18, 0.24), Color(0.20, 0.65, 0.43, 0.42), 30, 3)'
)
text = text.replace('table_button.position = Vector2(205, 190)', 'table_button.position = Vector2(145, 92)')
text = text.replace('table_button.size = Vector2(980, 365)', 'table_button.size = Vector2(1060, 500)')
text = text.replace('_make_label("TABLE COMMUNE", Vector2(220, 202), Vector2(950, 30)', '_make_label("TABLE COMMUNE", Vector2(165, 104), Vector2(1020, 30)')
text = text.replace('_make_label("Touchez n\'importe où dans la table pour poser la combinaison sélectionnée", Vector2(220, 232), Vector2(950, 28)', '_make_label("Touchez n\'importe où dans la table pour poser la combinaison sélectionnée", Vector2(165, 134), Vector2(1020, 28)')
text = text.replace('meld_layer.position = Vector2(220, 278)', 'meld_layer.position = Vector2(165, 174)')
text = text.replace('meld_layer.size = Vector2(950, 260)', 'meld_layer.size = Vector2(1020, 392)')
text = text.replace('status_label = _make_label("", Vector2(205, 558), Vector2(980, 38)', 'status_label = _make_label("", Vector2(165, 572), Vector2(1020, 34)')

# Rebuild table rendering. The old version stopped drawing once y crossed a hard limit,
# which made already-played melds appear to disappear. This renderer never drops a meld.
pattern = r'''func _refresh_melds\(\) -> void:\n.*?(?=func _make_card\()'''
replacement = '''func _refresh_melds() -> void:\n\t_clear_children(meld_layer)\n\tif game.table_melds.is_empty():\n\t\t_make_label("Aucune combinaison posée", Vector2(210, 138), Vector2(600, 52), 25, Color(0.75, 0.88, 0.80, 0.48), HORIZONTAL_ALIGNMENT_CENTER, meld_layer)\n\t\treturn\n\n\tvar meld_count: int = game.table_melds.size()\n\tvar card_w: float = 116.0\n\tvar card_h: float = 164.0\n\tvar card_step: float = 58.0\n\tvar row_step: float = 182.0\n\tif meld_count > 5:\n\t\tcard_w = 102.0\n\t\tcard_h = 145.0\n\t\tcard_step = 50.0\n\t\trow_step = 158.0\n\tif meld_count > 8:\n\t\tcard_w = 88.0\n\t\tcard_h = 125.0\n\t\tcard_step = 43.0\n\t\trow_step = 136.0\n\n\tvar x: float = 8.0\n\tvar y: float = 32.0\n\tvar usable_width: float = maxf(300.0, meld_layer.size.x - 16.0)\n\tvar usable_height: float = maxf(220.0, meld_layer.size.y - 8.0)\n\tvar row_index: int = 0\n\n\tfor meld_index: int in range(game.table_melds.size()):\n\t\tvar meld: Dictionary = game.table_melds[meld_index]\n\t\tvar cards: Array[CardInstance] = _dict_card_array(meld, "cards")\n\t\tvar owner: int = int(meld.get("owner", 0))\n\t\tvar meld_width: float = card_step * float(maxi(0, cards.size() - 1)) + card_w\n\n\t\tif x > 8.0 and x + meld_width > usable_width:\n\t\t\tx = 8.0\n\t\t\trow_index += 1\n\t\t\ty = 32.0 + float(row_index) * row_step\n\n\t\t# If later rows would overflow, compress vertical spacing instead of hiding melds.\n\t\tif y + card_h > usable_height:\n\t\t\tvar needed_rows: int = row_index + 1\n\t\t\tvar available_for_rows: float = maxf(card_h, usable_height - 32.0)\n\t\t\trow_step = maxf(82.0, (available_for_rows - card_h) / maxf(1.0, float(needed_rows - 1)))\n\t\t\ty = 32.0 + float(row_index) * row_step\n\n\t\tvar owner_color: Color = GREEN if owner == 0 else RED\n\t\tvar hit: Button = Button.new()\n\t\thit.text = RamiGame.PLAYER_NAMES[owner]\n\t\thit.position = Vector2(x, y - 27.0)\n\t\thit.size = Vector2(maxf(96.0, meld_width), 26.0)\n\t\thit.add_theme_font_size_override("font_size", 13)\n\t\thit.add_theme_color_override("font_color", owner_color)\n\t\thit.add_theme_stylebox_override("normal", _button_style(Color(0, 0, 0, 0), Color(0, 0, 0, 0), 0, 2))\n\t\thit.pressed.connect(_on_meld_pressed.bind(meld_index))\n\t\tmeld_layer.add_child(hit)\n\n\t\tfor i: int in range(cards.size()):\n\t\t\t_make_card(cards[i].face_id(), Vector2(x + float(i) * card_step, y), Vector2(card_w, card_h), false, -2, meld_layer, false, Color(0, 0, 0, 0))\n\t\tx += meld_width + 30.0\n\n\tprint("RAMI_TABLE_V012: melds_rendered=", game.table_melds.size(), " nodes=", meld_layer.get_child_count(), " card=", Vector2(card_w, card_h))\n\n'''
text, n = re.subn(pattern, replacement, text, flags=re.S)
assert n == 1, f'_refresh_melds replacement failed: {n}'

text = text.replace('v0.0.11 • DÉFAUSSE TACTILE + TABLE XL', 'v0.0.12 • TABLE XXL + ICÔNE RAMI')
text = text.replace(
    'print("RAMI_V011: discard_pile_action=true card_combo_select=true strict_band_slots=true table_melds_xl=true")',
    'print("RAMI_V011: discard_pile_action=true card_combo_select=true strict_band_slots=true table_melds_xl=true")\n\tprint("RAMI_V012: table_xxl=true persistent_meld_render=true app_icon=true")'
)

path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V012: enlarged common table and removed meld disappearance cap')
