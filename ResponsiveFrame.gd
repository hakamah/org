class_name ResponsiveFrame
extends Control

const DESIGN_SIZE := Vector2(1600.0, 900.0)
const MIN_SCALE := 0.20

@onready var design_surface: Control = $DesignSurface

var _last_signature: String = ""

func _ready() -> void:
	resized.connect(_queue_layout)
	get_viewport().size_changed.connect(_queue_layout)
	call_deferred("_apply_layout")

func _queue_layout() -> void:
	call_deferred("_apply_layout")

func _apply_layout() -> void:
	if not is_instance_valid(design_surface):
		return
	var viewport_size: Vector2 = size
	if viewport_size.x <= 1.0 or viewport_size.y <= 1.0:
		viewport_size = get_viewport_rect().size
	if viewport_size.x <= 1.0 or viewport_size.y <= 1.0:
		return

	var safe_rect: Rect2 = _safe_rect_in_viewport(viewport_size)
	var scale_value: float = minf(safe_rect.size.x / DESIGN_SIZE.x, safe_rect.size.y / DESIGN_SIZE.y)
	scale_value = maxf(scale_value, MIN_SCALE)
	var rendered_size: Vector2 = DESIGN_SIZE * scale_value
	var centered_position: Vector2 = safe_rect.position + (safe_rect.size - rendered_size) * 0.5

	design_surface.position = centered_position
	design_surface.scale = Vector2(scale_value, scale_value)
	design_surface.size = DESIGN_SIZE
	design_surface.pivot_offset = Vector2.ZERO

	var signature := "%dx%d|%.3f|%.1f,%.1f|%.1f,%.1f,%.1f,%.1f" % [
		int(viewport_size.x), int(viewport_size.y), scale_value,
		centered_position.x, centered_position.y,
		safe_rect.position.x, safe_rect.position.y, safe_rect.size.x, safe_rect.size.y
	]
	if signature != _last_signature:
		_last_signature = signature
		print("RAMI_LAYOUT: viewport=", viewport_size, " safe=", safe_rect, " scale=", scale_value, " position=", centered_position)

func _safe_rect_in_viewport(viewport_size: Vector2) -> Rect2:
	var full_rect := Rect2(Vector2.ZERO, viewport_size)
	var safe_px: Rect2i = DisplayServer.get_display_safe_area()
	var window_px_i: Vector2i = DisplayServer.window_get_size()
	if safe_px.size.x <= 0 or safe_px.size.y <= 0 or window_px_i.x <= 0 or window_px_i.y <= 0:
		return full_rect

	var window_px := Vector2(float(window_px_i.x), float(window_px_i.y))
	var ratio := Vector2(viewport_size.x / window_px.x, viewport_size.y / window_px.y)
	var logical_safe := Rect2(
		Vector2(float(safe_px.position.x), float(safe_px.position.y)) * ratio,
		Vector2(float(safe_px.size.x), float(safe_px.size.y)) * ratio
	)
	var clipped: Rect2 = logical_safe.intersection(full_rect)
	if clipped.size.x < DESIGN_SIZE.x * MIN_SCALE or clipped.size.y < DESIGN_SIZE.y * MIN_SCALE:
		return full_rect
	return clipped
