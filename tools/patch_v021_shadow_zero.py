from pathlib import Path

path = Path('GameTable.gd')
text = path.read_text(encoding='utf-8')

old = 'st.shadow_color = Color(0, 0, 0, 0.30)'
new = 'st.shadow_color = Color(0, 0, 0, 0.0)'

count = text.count(old)
assert count == 1, f'Expected exactly one 30% button shadow, found {count}'
text = text.replace(old, new, 1)

# Keep the parameter in place intentionally: only the alpha changes from 30% to 0%.
marker = 'print("RAMI_V020: exact_card_colors=true joker_melds_never_stacked=true")'
if marker in text:
    text = text.replace(marker, marker + '\n\tprint("RAMI_V021: button_shadow_alpha=0.0 parameter_kept=true")', 1)

text = text.replace('v0.0.20', 'v0.0.21')
path.write_text(text, encoding='utf-8')
print('RAMI_PATCH_V021: _button_style shadow alpha changed 0.30 -> 0.0; parameter retained')
