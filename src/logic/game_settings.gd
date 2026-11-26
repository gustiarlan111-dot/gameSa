class_name GameSettings
extends RefCounted
## V8 player settings: graphics preset, frame rate, volumes, HUD size, joystick side.
## Stored apart from the story saves in user://settings.json (written to .tmp, then renamed), so a
## settings change never touches a save slot and a broken settings file just falls back to defaults.

const PATH := "user://settings.json"
const QUALITIES := ["low", "medium", "high", "ultra"]
const QUALITY_NAMES := {"low": "Rendah", "medium": "Sedang", "high": "Tinggi", "ultra": "Ultra"}
const HUD_SCALES := [0.85, 1.0, 1.15, 1.3]
const DEFAULTS := {
	"version": 1,
	"quality": "high",       # the look the game shipped with before V8
	"fps": 60,               # 30 saves battery on weaker phones
	"music": 0.7,
	"ambience": 0.8,
	"sfx": 0.9,
	"hud_scale": 1.0,
	"left_hand": false,      # joystick on the right, buttons on the left
	"lightning": true,       # thunderstorm flashes (off for light-sensitive players; thunder stays)
}

static var current: Dictionary = {}
static var _loaded := false


static func get_all() -> Dictionary:
	if not _loaded:
		load_file()
	return current


static func value(key: String):
	return get_all().get(key, DEFAULTS.get(key))


## Read the file; anything missing, mistyped or out of range is replaced by its default.
static func load_file() -> void:
	_loaded = true
	current = DEFAULTS.duplicate()
	if not FileAccess.file_exists(PATH):
		return
	var f := FileAccess.open(PATH, FileAccess.READ)
	if f == null:
		return
	var parsed = JSON.parse_string(f.get_as_text())
	if parsed is Dictionary:
		current = sanitize(parsed)


static func sanitize(d: Dictionary) -> Dictionary:
	var out := DEFAULTS.duplicate()
	if str(d.get("quality", "")) in QUALITIES:
		out.quality = str(d.quality)
	if int(d.get("fps", 0)) in [30, 60]:
		out.fps = int(d.fps)
	for k in ["music", "ambience", "sfx"]:
		if d.get(k) is float or d.get(k) is int:
			out[k] = clampf(float(d[k]), 0.0, 1.0)
	if d.get("hud_scale") is float or d.get("hud_scale") is int:
		out.hud_scale = clampf(float(d.hud_scale), 0.7, 1.5)
	if d.get("left_hand") is bool:
		out.left_hand = d.left_hand
	if d.get("lightning") is bool:
		out.lightning = d.lightning
	return out


static func set_value(key: String, v) -> void:
	var d := get_all().duplicate()
	d[key] = v
	current = sanitize(d)
	save_file()
	apply_global()


static func save_file() -> bool:
	var f := FileAccess.open(PATH + ".tmp", FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(current, "  "))
	f.close()
	return DirAccess.rename_absolute(PATH + ".tmp", PATH) == OK


## Things that live outside a scene: frame cap, volumes. Scenes read the rest (quality, HUD) through
## `quality()` / `value()` when they build, and listen to `changed` via GameSettings.notify.
static func apply_global() -> void:
	var d := get_all()
	Engine.max_fps = int(d.fps)
	var au = Engine.get_main_loop().root.get_node_or_null("Audio") if Engine.get_main_loop() else null
	if au:
		au.music_volume = float(d.music)
		au.ambience_volume = float(d.ambience)
		au.sfx_volume = float(d.sfx)
	for cb in _listeners:
		if cb.is_valid():
			cb.call()


static var _listeners: Array[Callable] = []


static func listen(cb: Callable) -> void:
	_listeners = _listeners.filter(func(c): return c.is_valid())
	_listeners.append(cb)


## Per-preset render values (one place, so the 3D view, the screen pass and QA agree).
##   shadows: sun shadows on;  shadow_size: directional shadow atlas;  glow: bloom in the 3D view;
##   post: the screen pass (grade, vignette, bloom);  taps: its blur/bloom taps (off = grade only);
##   lamps: real lamp lights (off = glow sprites only);  msaa: 3D anti-aliasing.
static func quality() -> Dictionary:
	match str(value("quality")):
		"low":
			return {"shadows": false, "shadow_size": 1024, "glow": false, "post": false, "taps": false, "lamps": false, "msaa": 0}
		"medium":
			return {"shadows": true, "shadow_size": 2048, "glow": true, "post": true, "taps": false, "lamps": true, "msaa": 0}
		"ultra":
			return {"shadows": true, "shadow_size": 4096, "glow": true, "post": true, "taps": true, "lamps": true, "msaa": 2}
	# high = the look the game shipped with: project default shadow atlas (0 = leave it)
	return {"shadows": true, "shadow_size": 0, "glow": true, "post": true, "taps": true, "lamps": true, "msaa": 0}
