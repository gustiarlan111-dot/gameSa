class_name AreaSound
extends Node
## Layered soundscape for the current area (child of the Audio autoload).
##
## Driven by assets/audio/area_sound.json (built by tools/audio/make_soundscape.py):
##  - layers: looping beds that fade in/out with the hour and weather ("when" tokens),
##  - spots: random one-shots (gulls, tokek, owl, cup clinks...) with random pitch and side,
##    sent through a reverb sized for the place (room, forest, cave...),
##  - emitters: positional loops (fountain, waterfall, campfire, river, sea, lake) whose volume
##    and pan follow the player's distance to the prop / water.
## Layers shared by two areas (wind, crickets...) keep playing across a door, so walking from one
## map to the next never cuts the sound.

const DATA := "res://assets/audio/area_sound.json"
const FADE := 0.35            # layer fade speed (full swing in ~3 s)
const SPOT_BUSES := ["AmbSpotL", "AmbSpotC", "AmbSpotR"]
const SPOT_PAN := [-0.65, 0.0, 0.65]
const EMIT_BUSES := 4
const MAX_SPOTS := 6

var level := 1.0              # set by Audio every frame (ambience volume x dialogue ducking)
var listener := Vector2.ZERO  # player position on the 2D map
var area_id := ""
var tokens := {}              # active "when" tokens

var _data := {}
var _layers := {}             # id -> {player, target, level}
var _emit := {}               # id -> {player, bus, points, rects, paths, ellipses, r, vol, level}
var _spots: Array = []        # [{def, t}]
var _cache := {}
var _verb: AudioEffectReverb
var _ready_buses := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_process(false)        # wakes up on the first sync()
	if FileAccess.file_exists(DATA):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		if parsed is Dictionary:
			_data = parsed
	_make_buses()


func has_area(id: String) -> bool:
	return _data.get("areas", {}).has(id)


func profile(id: String) -> Dictionary:
	return _data.get("areas", {}).get(id, {})


## Active "when" tokens for a weather and minute (also used by tests).
static func tokens_for(weather: String, minute: int) -> Dictionary:
	var h := WorldClock.hour(minute)
	var night := WorldClock.is_night(minute)
	var rain := weather == "hujan" or weather == "rain"
	var t := {"day": not night, "night": night, "dawn": h >= 5 and h < 9, "dusk": h >= 16 and h < 19,
		"rain": rain, "dry": not rain, "wind": weather == "berangin"}
	return t


static func matches(when: String, t: Dictionary) -> bool:
	if when == "":
		return true
	for w in when.split(","):
		if not t.get(w.strip_edges(), false):
			return false
	return true


## Target volume of every layer of an area for the given tokens (id -> volume; same id = loudest).
static func layer_targets(prof: Dictionary, t: Dictionary) -> Dictionary:
	var out := {}
	for l in prof.get("layers", []):
		if matches(str(l.get("when", "")), t):
			out[l.id] = maxf(float(out.get(l.id, 0.0)), float(l.vol))
	return out


## Called on area enter and every ~1 s by the game. area = the maps.json area dictionary.
func sync(id: String, area: Dictionary, weather: String, minute: int) -> void:
	tokens = tokens_for(weather, minute)
	set_process(true)
	var prof := profile(id)
	if id != area_id:
		area_id = id
		_setup_spots(prof)
		_setup_emitters(prof, area)
		_set_reverb(str(prof.get("reverb", "open")))
	var want := layer_targets(prof, tokens)
	for lid in want:
		if not _layers.has(lid):
			var s := _stream("res://assets/audio/amb/%s.ogg" % lid)
			if s == null:
				continue
			var pl := AudioStreamPlayer.new()
			pl.stream = s
			pl.bus = "Ambience"
			pl.volume_db = -80
			add_child(pl)
			# start each bed at a random point so two areas sharing a layer don't phase
			pl.play(randf() * maxf(0.0, s.get_length() - 1.0))
			_layers[lid] = {"player": pl, "target": 0.0, "level": 0.0}
		_layers[lid].target = want[lid]
	for lid in _layers:
		if not want.has(lid):
			_layers[lid].target = 0.0


func stop_all() -> void:
	area_id = ""
	for lid in _layers:
		_layers[lid].target = 0.0
	for eid in _emit:
		_emit[eid].vol = 0.0
	_spots.clear()


func current() -> String:
	var ids := []
	for lid in _layers:
		if _layers[lid].target > 0:
			ids.append(lid)
	return ",".join(ids)


func _process(dt: float) -> void:
	var gone := []
	for lid in _layers:
		var l: Dictionary = _layers[lid]
		l.level = move_toward(l.level, l.target, dt * FADE)
		var pl: AudioStreamPlayer = l.player
		pl.volume_db = linear_to_db(maxf(0.0001, l.level * level))
		if l.level <= 0.0 and l.target <= 0.0:
			pl.stop()
			pl.queue_free()
			gone.append(lid)
	for lid in gone:
		_layers.erase(lid)
	_process_emitters(dt)
	_process_spots(dt)


# ------------------------------------------------------------------ spots
func _setup_spots(prof: Dictionary) -> void:
	_spots.clear()
	for s in prof.get("spots", []):
		var every: Array = s.get("every", [10, 20])
		# first one comes soon-ish but not all at once on entering
		_spots.append({"def": s, "t": randf_range(0.25, 0.8) * float(every[0]) + randf() * 3.0})


func _process_spots(dt: float) -> void:
	for sp in _spots:
		sp.t -= dt
		if sp.t > 0:
			continue
		var d: Dictionary = sp.def
		var every: Array = d.get("every", [10, 20])
		sp.t = randf_range(float(every[0]), float(every[1]))
		if matches(str(d.get("when", "")), tokens) and level > 0.001:
			play_spot(str(d.id), float(d.get("vol", 0.5)) * (0.55 if d.get("far", false) else 1.0))


func play_spot(id: String, vol: float) -> void:
	if get_child_count() > 40:
		return
	var n := int(_data.get("spot_variants", 3))
	var s := _stream("res://assets/audio/spots/%s_%d.ogg" % [id, randi_range(1, n)])
	if s == null:
		return
	var busy := 0
	for c in get_children():
		if c.has_meta("spot"):
			busy += 1
	if busy >= MAX_SPOTS:
		return
	var p := AudioStreamPlayer.new()
	p.stream = s
	p.bus = SPOT_BUSES[randi() % SPOT_BUSES.size()] if _ready_buses else "Master"
	p.pitch_scale = randf_range(0.92, 1.08)
	p.volume_db = linear_to_db(clampf(vol * level * randf_range(0.75, 1.0), 0.0001, 1.0))
	p.set_meta("spot", true)
	add_child(p)
	p.finished.connect(p.queue_free)
	p.play()


# ------------------------------------------------------------------ emitters
func _setup_emitters(prof: Dictionary, area: Dictionary) -> void:
	for eid in _emit:
		_emit[eid].vol = 0.0          # fade the old ones out, reuse if the new area has them too
	var table: Dictionary = _data.get("emitters", {})
	for pr in area.get("props", []):
		var e = table.get(str(pr.get("type", "")))
		if e == null:
			continue
		var em := _emitter(str(e.id))
		em.points.append([Vector2(float(pr.x), float(pr.y)), float(e.get("r", 400)), float(e.get("vol", 1.0))])
	var flow = prof.get("flow")
	var flows = area.get("waterFlow")
	if flow != null and flows is Array:
		var em := _emitter(str(flow.id))
		for f in flows:
			if f.has("path"):
				em.paths.append([f.path, float(f.get("width", 60)), float(flow.r), float(flow.vol)])
			else:
				em.rects.append([Rect2(f.x, f.y, f.w, f.h), float(flow.r), float(flow.vol)])
	var lake = prof.get("lake")
	if lake != null:
		var em := _emitter(str(lake.id))
		for w in area.get("water", []):
			em.ellipses.append([Vector4(w.cx, w.cy, w.rx, w.ry), float(lake.r), float(lake.vol)])
	for eid in _emit:
		var em: Dictionary = _emit[eid]
		em.vol = 0.0 if em.points.is_empty() and em.rects.is_empty() and em.paths.is_empty() and em.ellipses.is_empty() else 1.0


func _emitter(id: String) -> Dictionary:
	if not _emit.has(id):
		var bus_name := ""
		for i in EMIT_BUSES:
			var b := "AmbEmit%d" % i
			var used := false
			for k in _emit:
				used = used or _emit[k].bus == b
			if not used:
				bus_name = b
				break
		var pl: AudioStreamPlayer = null
		var s := _stream("res://assets/audio/amb/%s.ogg" % id)
		if s != null and bus_name != "":
			pl = AudioStreamPlayer.new()
			pl.stream = s
			pl.bus = bus_name if _ready_buses else "Master"
			pl.volume_db = -80
			add_child(pl)
			pl.play(randf() * maxf(0.0, s.get_length() - 1.0))
		_emit[id] = {"player": pl, "bus": bus_name, "level": 0.0, "pan": 0.0, "vol": 0.0}
	var em: Dictionary = _emit[id]
	if em.vol <= 0.0:
		em.points = []; em.rects = []; em.paths = []; em.ellipses = []
	em.vol = 1.0
	return em


## Loudness 0..1 and the direction (x offset) of the nearest source of an emitter.
static func emitter_gain(em: Dictionary, at: Vector2) -> Vector2:
	var best := 0.0
	var dx := 0.0
	var cands := []
	for p in em.get("points", []):
		cands.append([p[0].distance_to(at), p[1], p[2], p[0].x - at.x])
	for r in em.get("rects", []):
		var rc: Rect2 = r[0]
		var q := Vector2(clampf(at.x, rc.position.x, rc.end.x), clampf(at.y, rc.position.y, rc.end.y))
		cands.append([q.distance_to(at), r[1], r[2], (q.x - at.x) * 0.5])
	for pa in em.get("paths", []):
		var pts: Array = pa[0]
		var bd := INF
		var bq := at
		for i in range(pts.size() - 1):
			var a := Vector2(pts[i][0], pts[i][1])
			var b := Vector2(pts[i + 1][0], pts[i + 1][1])
			var q := Geometry2D.get_closest_point_to_segment(at, a, b)
			var d := q.distance_to(at)
			if d < bd:
				bd = d; bq = q
		cands.append([maxf(0.0, bd - pa[1] * 0.5), pa[2], pa[3], bq.x - at.x])
	for e in em.get("ellipses", []):
		var v: Vector4 = e[0]
		var rel := at - Vector2(v.x, v.y)
		var k := sqrt(pow(rel.x / maxf(v.z, 1.0), 2) + pow(rel.y / maxf(v.w, 1.0), 2))
		var d := 0.0 if k <= 1.0 else rel.length() * (1.0 - 1.0 / k)
		cands.append([d, e[1], e[2], -rel.x * 0.3])
	for c in cands:
		var g := clampf(1.0 - c[0] / maxf(c[1], 1.0), 0.0, 1.0)
		g = g * g * c[2]
		if g > best:
			best = g
			dx = c[3]
	return Vector2(best, dx)


func _process_emitters(dt: float) -> void:
	var gone := []
	for eid in _emit:
		var em: Dictionary = _emit[eid]
		var g := emitter_gain(em, listener) if em.vol > 0 else Vector2.ZERO
		em.level = move_toward(em.level, g.x, dt * 0.8)
		var pl = em.player
		if pl == null:
			if em.vol <= 0:
				gone.append(eid)
			continue
		pl.volume_db = linear_to_db(maxf(0.0001, em.level * level))
		if _ready_buses and em.bus != "":
			em.pan = lerpf(em.pan, clampf(g.y / 420.0, -0.8, 0.8), minf(1.0, dt * 3.0))
			var idx := AudioServer.get_bus_index(em.bus)
			if idx >= 0:
				var fx = AudioServer.get_bus_effect(idx, 0)
				if fx is AudioEffectPanner:
					fx.pan = em.pan
		if em.vol <= 0 and em.level <= 0.0:
			pl.stop()
			pl.queue_free()
			gone.append(eid)
	for eid in gone:
		_emit.erase(eid)


# ------------------------------------------------------------------ buses
func _make_buses() -> void:
	if AudioServer.get_bus_index("Ambience") >= 0:
		_ready_buses = true
		_verb = AudioServer.get_bus_effect(AudioServer.get_bus_index("AmbVerb"), 0)
		return
	_add_bus("Ambience", "Master")
	_add_bus("AmbVerb", "Master")
	_verb = AudioEffectReverb.new()
	_verb.dry = 1.0
	_verb.wet = 0.1
	AudioServer.add_bus_effect(AudioServer.get_bus_index("AmbVerb"), _verb)
	for i in SPOT_BUSES.size():
		_add_bus(SPOT_BUSES[i], "AmbVerb")
		var pan := AudioEffectPanner.new()
		pan.pan = SPOT_PAN[i]
		AudioServer.add_bus_effect(AudioServer.get_bus_index(SPOT_BUSES[i]), pan)
	for i in EMIT_BUSES:
		var b := "AmbEmit%d" % i
		_add_bus(b, "Master")
		AudioServer.add_bus_effect(AudioServer.get_bus_index(b), AudioEffectPanner.new())
	_ready_buses = true


func _add_bus(name: String, send: String) -> void:
	var i := AudioServer.bus_count
	AudioServer.add_bus(i)
	AudioServer.set_bus_name(i, name)
	AudioServer.set_bus_send(i, send)


func _set_reverb(kind: String) -> void:
	if _verb == null:
		return
	var r: Array = _data.get("reverb", {}).get(kind, [0.3, 0.5, 0.08, 20])
	_verb.room_size = float(r[0])
	_verb.damping = float(r[1])
	_verb.wet = float(r[2])
	_verb.predelay_msec = float(r[3])


func _stream(path: String) -> AudioStream:
	if _cache.has(path):
		return _cache[path]
	if not ResourceLoader.exists(path):
		return null
	var s: AudioStream = load(path)
	if s is AudioStreamOggVorbis and path.contains("/amb/"):
		s.loop = true
	_cache[path] = s
	return s
