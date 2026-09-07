from pathlib import Path

# Runs after patch_v032_room_capacity_change.py.
# Keep rami-api untouched: room capacity changes go to the dedicated rami-resize
# edge function, using the same RAMI bearer token.

net_path = Path('RamiNetwork.gd')
net = net_path.read_text(encoding='utf-8')
old = '''\t_pending_kind = kind\n\tvar err := _http.request(base_url + path, headers, method, json_body)\n'''
assert old in net, 'RamiNetwork request URL anchor missing'
new = '''\t_pending_kind = kind\n\tvar request_url := base_url + path\n\tif kind == "resize_room":\n\t\trequest_url = base_url.replace("/rami-api", "/rami-resize")\n\tvar err := _http.request(request_url, headers, method, json_body)\n'''
net = net.replace(old, new, 1)
net_path.write_text(net, encoding='utf-8')

mp_path = Path('Multiplayer.gd')
mp = mp_path.read_text(encoding='utf-8')
old = '''\tcurrent_room_player_count = count\n\tconfirmed_room_players = target\n\tselected_players = target\n'''
assert old in mp, 'Multiplayer room state anchor missing'
new = '''\tcurrent_room_player_count = count\n\tconfirmed_room_players = target\n\tselected_players = target\n\t# A join may happen while the owner has a smaller capacity pending.\n\t# Never let confirmation kick an already-present player.\n\tif pending_room_players >= 0 and pending_room_players < current_room_player_count:\n\t\tpending_room_players = -1\n'''
mp = mp.replace(old, new, 1)
mp_path.write_text(mp, encoding='utf-8')

print('RAMI_PATCH_V032_ZZ: dedicated resize endpoint + pending-race guard applied')
