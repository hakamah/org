extends Node

signal auth_changed(account: Dictionary)
signal auth_progress(message: String)
signal auth_failed(message: String)
signal request_finished(kind: String, payload: Dictionary)

var base_url: String = ""
var google_auth_url: String = ""
var token: String = ""
var account: Dictionary = {}
var _http: HTTPRequest
var _pending_kind: String = ""
var _google_busy: bool = false
var _cm_bridge = null

const TOKEN_PATH := "user://rami_auth_token.txt"
const CM_BRIDGE_CLASS := "com.hakamah.rami.auth.RamiCredentialBridge"

func _ready() -> void:
	base_url = String(ProjectSettings.get_setting("rami/server_url", "")).strip_edges().trim_suffix("/")
	google_auth_url = String(ProjectSettings.get_setting("rami/google_auth_url", "")).strip_edges().trim_suffix("/")
	_http = HTTPRequest.new()
	_http.timeout = 12.0
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)
	_load_token()
	if not token.is_empty() and not base_url.is_empty():
		request_me()

func is_server_configured() -> bool:
	return not base_url.is_empty() and not google_auth_url.is_empty()

func is_authenticated() -> bool:
	return not token.is_empty() and not account.is_empty()

func is_google_busy() -> bool:
	return _google_busy

func begin_google_login() -> void:
	if _google_busy:
		auth_progress.emit("Connexion Google déjà en cours…")
		return
	if google_auth_url.is_empty():
		auth_failed.emit("Serveur Google RAMI non configuré.")
		return
	if OS.get_name() != "Android":
		auth_failed.emit("La connexion Google native est disponible sur Android.")
		return
	_google_busy = true
	auth_progress.emit("Préparation de Google…")
	call_deferred("_begin_google_login_async")

func cancel_google_login() -> void:
	_google_busy = false
	if _cm_bridge != null:
		_cm_bridge.cancel()
		JavaClassWrapper.get_exception()
		_cm_bridge.reset()
		JavaClassWrapper.get_exception()
	auth_progress.emit("Connexion Google annulée.")

func _begin_google_login_async() -> void:
	var start := await _request_json_once(HTTPClient.METHOD_POST, google_auth_url + "/start", {}, false)
	if not _google_busy:
		return
	if not bool(start.get("ok", false)):
		_google_busy = false
		var code := String(start.get("error", "NETWORK_ERROR"))
		if code == "GOOGLE_NOT_CONFIGURED":
			auth_failed.emit("Google RAMI n'est pas encore configuré côté serveur.")
		else:
			auth_failed.emit("Impossible de préparer la connexion Google : %s" % code)
		return

	var nonce := String(start.get("nonce", ""))
	var client_id := String(start.get("google_client_id", ""))
	if nonce.is_empty() or client_id.is_empty():
		_google_busy = false
		auth_failed.emit("Configuration Google RAMI incomplète.")
		return

	JavaClassWrapper.get_exception()
	var bridge = JavaClassWrapper.wrap(CM_BRIDGE_CLASS)
	var java_err = JavaClassWrapper.get_exception()
	if java_err != null or bridge == null:
		_google_busy = false
		auth_failed.emit("Le module Google natif RAMI n'est pas chargé dans cette APK.")
		return
	_cm_bridge = bridge

	var runtime = Engine.get_singleton("AndroidRuntime")
	var activity = null
	if runtime != null:
		activity = runtime.getActivity()
	java_err = JavaClassWrapper.get_exception()
	if java_err != null or activity == null:
		_google_busy = false
		auth_failed.emit("Impossible d'ouvrir l'interface Google Android.")
		return

	_cm_bridge.reset()
	java_err = JavaClassWrapper.get_exception()
	if java_err != null:
		_google_busy = false
		auth_failed.emit("Le module Google natif RAMI n'a pas pu être initialisé.")
		return

	auth_progress.emit("Ouverture de la fenêtre Google…")
	var started = _cm_bridge.start(activity, client_id, nonce)
	java_err = JavaClassWrapper.get_exception()
	if java_err != null or not bool(started):
		_google_busy = false
		var early_code := ""
		if java_err == null:
			early_code = String(_cm_bridge.getErrorCode())
			JavaClassWrapper.get_exception()
		auth_failed.emit(_friendly_google_error(early_code))
		return

	var started_at := Time.get_ticks_msec()
	var final_state := 1
	while _google_busy:
		final_state = int(_cm_bridge.getState())
		java_err = JavaClassWrapper.get_exception()
		if java_err != null:
			final_state = 4
			break
		if final_state != 1:
			break
		var stage := String(_cm_bridge.getStage())
		JavaClassWrapper.get_exception()
		if stage == "native_sheet_requested":
			auth_progress.emit("Choisissez votre compte Google…")
		elif stage == "native_explicit_google_requested":
			auth_progress.emit("Se connecter avec Google…")
		if Time.get_ticks_msec() - started_at > 120000:
			_cm_bridge.cancel()
			JavaClassWrapper.get_exception()
			final_state = 4
			break
		await get_tree().create_timer(0.10).timeout

	if not _google_busy:
		return
	if final_state == 3:
		_google_busy = false
		_cm_bridge.reset()
		JavaClassWrapper.get_exception()
		auth_failed.emit("Connexion Google annulée.")
		return
	if final_state != 2:
		var cm_code := String(_cm_bridge.getErrorCode())
		JavaClassWrapper.get_exception()
		_google_busy = false
		_cm_bridge.reset()
		JavaClassWrapper.get_exception()
		auth_failed.emit(_friendly_google_error(cm_code))
		return

	var google_id_token := String(_cm_bridge.takeIdToken())
	java_err = JavaClassWrapper.get_exception()
	if java_err != null or google_id_token.is_empty():
		_google_busy = false
		_cm_bridge.reset()
		JavaClassWrapper.get_exception()
		auth_failed.emit("Google n'a pas fourni de jeton d'identité.")
		return

	auth_progress.emit("Validation du compte RAMI…")
	var exchange := await _request_json_once(
		HTTPClient.METHOD_POST,
		google_auth_url + "/exchange",
		{"id_token": google_id_token, "nonce": nonce},
		false
	)
	google_id_token = ""
	_cm_bridge.reset()
	JavaClassWrapper.get_exception()
	_google_busy = false
	if not bool(exchange.get("ok", false)):
		auth_failed.emit("Le serveur RAMI a refusé la connexion Google : %s" % String(exchange.get("error", "AUTH_FAILED")))
		return

	token = String(exchange.get("token", ""))
	account = exchange.get("account", {}) as Dictionary
	if token.is_empty() or account.is_empty():
		auth_failed.emit("Session RAMI incomplète après Google.")
		return
	_save_token()
	auth_changed.emit(account)
	auth_progress.emit("Connexion Google réussie.")

func _friendly_google_error(code: String) -> String:
	match code:
		"provider_configuration": return "Google est présent, mais la configuration OAuth RAMI (package/SHA-1) est invalide."
		"unsupported": return "Google Credential Manager n'est pas pris en charge sur cet appareil."
		"no_credential": return "Aucun compte Google utilisable n'a été trouvé sur cet appareil."
		"user_cancelled", "cancelled_by_app": return "Connexion Google annulée."
		"client_id_missing": return "Client Google RAMI manquant."
		_: return "Connexion Google native impossible%s" % (" : " + code if not code.is_empty() else ".")

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
	cancel_google_login()
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

func _request_json_once(method: HTTPClient.Method, url: String, body: Dictionary, authenticated: bool) -> Dictionary:
	var req := HTTPRequest.new()
	req.timeout = 15.0
	add_child(req)
	var headers := PackedStringArray(["Content-Type: application/json", "Accept: application/json"])
	if authenticated and not token.is_empty():
		headers.append("Authorization: Bearer %s" % token)
	var json_body := "" if method == HTTPClient.METHOD_GET else JSON.stringify(body)
	var err := req.request(url, headers, method, json_body)
	if err != OK:
		req.queue_free()
		return {"ok": false, "error": "REQUEST_START_FAILED", "code": err}
	var completed: Array = await req.request_completed
	req.queue_free()
	var result := int(completed[0])
	var response_code := int(completed[1])
	var raw: PackedByteArray = completed[3]
	if result != HTTPRequest.RESULT_SUCCESS:
		return {"ok": false, "error": "NETWORK_ERROR", "result": result, "http": response_code}
	var parsed: Variant = JSON.parse_string(raw.get_string_from_utf8())
	if parsed is Dictionary:
		var payload := parsed as Dictionary
		if response_code >= 400 and not payload.has("http"):
			payload["http"] = response_code
		return payload
	return {"ok": false, "error": "INVALID_SERVER_RESPONSE", "http": response_code}

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

	if kind == "me":
		if bool(payload.get("ok", false)):
			account = payload.get("account", {}) as Dictionary
			auth_changed.emit(account)
		elif response_code == 401:
			token = ""
			account.clear()
			if FileAccess.file_exists(TOKEN_PATH):
				DirAccess.remove_absolute(ProjectSettings.globalize_path(TOKEN_PATH))
			auth_changed.emit(account)
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
