extends Node

signal auth_changed(account: Dictionary)
signal request_finished(kind: String, payload: Dictionary)

var base_url: String = ""
var token: String = ""
var account: Dictionary = {}
var _http: HTTPRequest
var _pending_kind: String = ""

const TOKEN_PATH := "user://rami_auth_token.txt"

func _ready() -> void:
	base_url = String(ProjectSettings.get_setting("rami/server_url", "")).strip_edges().trim_suffix("/")
	_http = HTTPRequest.new()
	_http.timeout = 12.0
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)
	_load_token()
	if not token.is_empty() and not base_url.is_empty():
		request_me()

func is_server_configured() -> bool:
	return not base_url.is_empty()

func is_authenticated() -> bool:
	return not token.is_empty() and not account.is_empty()

func submit_google_id_token(google_id_token: String) -> bool:
	if google_id_token.is_empty():
		return false
	return _request("auth_google", HTTPClient.METHOD_POST, "/api/auth/google", {"id_token": google_id_token}, false)

func request_me() -> bool:
	return _request("me", HTTPClient.METHOD_GET, "/api/me", {}, true)

func create_room(players: int) -> bool:
	return _request("create_room", HTTPClient.METHOD_POST, "/api/matchmaking/create", {"players": players}, true)

func search_room(players: int) -> bool:
	return _request("search_room", HTTPClient.METHOD_POST, "/api/matchmaking/search", {"players": players}, true)

func get_room(room_id: int) -> bool:
	return _request("room", HTTPClient.METHOD_GET, "/api/matchmaking/room/%d" % room_id, {}, true)

func leave_room() -> bool:
	return _request("leave_room", HTTPClient.METHOD_POST, "/api/matchmaking/leave", {}, true)

func logout() -> void:
	token = ""
	account.clear()
	if FileAccess.file_exists(TOKEN_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(TOKEN_PATH))
	auth_changed.emit(account)

func _request(kind: String, method: HTTPClient.Method, path: String, body: Dictionary, authenticated: bool) -> bool:
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return false
	if base_url.is_empty():
		request_finished.emit(kind, {"ok": false, "error": "SERVER_NOT_CONFIGURED"})
		return false
	if authenticated and token.is_empty():
		request_finished.emit(kind, {"ok": false, "error": "AUTH_REQUIRED"})
		return false
	var headers := PackedStringArray(["Content-Type: application/json", "Accept: application/json"])
	if authenticated:
		headers.append("Authorization: Bearer %s" % token)
	var json_body := "" if method == HTTPClient.METHOD_GET else JSON.stringify(body)
	_pending_kind = kind
	var err := _http.request(base_url + path, headers, method, json_body)
	if err != OK:
		_pending_kind = ""
		request_finished.emit(kind, {"ok": false, "error": "REQUEST_START_FAILED", "code": err})
		return false
	return true

func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var kind := _pending_kind
	_pending_kind = ""
	var payload: Dictionary = {}
	if result != HTTPRequest.RESULT_SUCCESS:
		payload = {"ok": false, "error": "NETWORK_ERROR", "result": result, "http": response_code}
	else:
		var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
		if parsed is Dictionary:
			payload = parsed
		else:
			payload = {"ok": false, "error": "INVALID_SERVER_RESPONSE", "http": response_code}
	if response_code >= 400 and not payload.has("http"):
		payload["http"] = response_code

	if kind == "auth_google" and bool(payload.get("ok", false)):
		token = String(payload.get("token", ""))
		account = payload.get("account", {}) as Dictionary
		_save_token()
		auth_changed.emit(account)
	elif kind == "me":
		if bool(payload.get("ok", false)):
			account = payload.get("account", {}) as Dictionary
			auth_changed.emit(account)
		elif response_code == 401:
			logout()
	request_finished.emit(kind, payload)

func _save_token() -> void:
	if token.is_empty():
		return
	var f := FileAccess.open(TOKEN_PATH, FileAccess.WRITE)
	if f:
		f.store_string(token)

func _load_token() -> void:
	if not FileAccess.file_exists(TOKEN_PATH):
		return
	var f := FileAccess.open(TOKEN_PATH, FileAccess.READ)
	if f:
		token = f.get_as_text().strip_edges()
