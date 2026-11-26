class_name Cutscene
extends Node2D
## Data-driven cinematic player (port of game/CutscenePlayer.java). Commands run in order; timed
## commands (move, cam, wait, say, line, fade, caption) block unless "async": true.
## Commands ("c"): wait, move, place, face, pair, pose, emote, cam, shot, follow, bars, fade, flash, tint,
## shake, fx, say, line, caption, sfx, music, spawn, despawn, show, hide, alpha.
## Film lens (read by WorldView3D and the screen pass, 3D only): angle {pitch, yaw, t}, orbit {deg, t},
## crane {t, zoom}, dof {a, t}, mood {id: warm|cool|dream|memory|night|none, t}, key {on, color}.
## Without them every cutscene still gets the film look: a settle-in crane at the start, lower
## camera on close shots, slow drift and handheld breathing, a slow push-in while people talk,
## focus blur around the subject, filmic grade and grain, and a soft key light on the couple.
## This node lives inside the world (draws world effects); `overlay` draws bars/fade/captions on screen.
##
## Host (the Game node) provides: actor(who), spawn(id, sprite, x, y, dir), despawn(id), show_partner(on),
## say(scene, from, n, done), line(s, e, t, done), sfx(id), music(id), cam_center(), can_stand(x, y)

var host: Object
var overlay: CutsceneOverlay
var active := false
var fast := false

var _queue: Array = []
var _movers: Array = []
var _fxs: Array = []
var _done: Callable
var _waiting_cb := false
var _wait_t := 0.0
var _wait_mover = null
var _spawned: Array = []
var time := 0.0

var cam_active := false
var cam := Vector2.ZERO
var cam_zoom := 1.0
var _c0 := Vector2.ZERO
var _c1 := Vector2.ZERO
var _z0 := 1.0
var _z1 := 1.0
var _cam_t := 0.0
var _cam_dur := 0.0
var _async_cam := false
var _cam_follow: Node2D = null

var bars := 0.0
var _bars_target := 0.0
var _bars_speed := 2.0
var fade := 0.0
var _fade0 := 0.0
var _fade1 := 0.0
var _fade_t := 0.0
var _fade_dur := 0.0
var _async_fade := false
var fade_color := Color.BLACK
var flash := 0.0
var flash_dur := 0.0
var flash_color := Color.WHITE
var tint_a := 0.0
var _tint0 := 0.0
var _tint1 := 0.0
var _tint_t := 0.0
var _tint_dur := 0.0
var tint_color := Color("1b2350")
var _shake_t := 0.0
var _shake_amp := 0.0
var cap_title := ""
var cap_sub = null
var cap_art = null
var cap_t := 0.0
var cap_dur := 0.0
var _async_cap := false

# film lens (see header). Angles in degrees; 0 pitch = automatic (lower when the shot is closer).
const BASE_PITCH := 38.0
var film := 0.0                  # 0..1 how much of the film look is on (eases in/out)
var pitch := 0.0
var yaw := 0.0
var dof := 0.35
var mood := ""
var mood_a := 0.0
var key := 1.0
var key_color := Color(1.0, 0.86, 0.68)
var creep := 0.0                 # slow push-in while a line is on screen
var _tw := {}                    # property -> [from, to, t, dur]
var _settle := 0.0               # automatic crane at the start, 1 -> 0

var _sparkle: Texture2D
var _heart: Texture2D


func _ready() -> void:
	z_index = 50
	_sparkle = Data.tex("ui/sparkle.png")
	_heart = Data.tex("ui/emote_heart.png")


static func _ease(k: float) -> float:
	var t := clampf(k, 0, 1)
	return t * t * (3.0 - 2.0 * t)


static func safe_zoom(z: float) -> float:
	return clampf(z, 0.67, 1.5)


static func _preset_zoom(frame: String) -> float:
	return {"close": 1.42, "wide": 0.91, "intimate": 1.18}.get(frame, 1.0)


static func _pt(o):
	if o is Array and o.size() >= 2 and (o[0] is float or o[0] is int) and (o[1] is float or o[1] is int):
		return Vector2(o[0], o[1])
	return null


func start(cmds: Array, done: Callable) -> void:
	_queue = cmds.duplicate(); _movers.clear(); _fxs.clear(); _spawned.clear()
	_done = done; active = true; _waiting_cb = false; _wait_t = 0; _wait_mover = null; fast = false
	cam_active = true; cam = host.cam_center(); cam_zoom = 1.0; _cam_dur = 0; _cam_follow = null
	_bars_target = 1.0; tint_a = 0; _tint_dur = 0; fade = 0; _fade_dur = 0; cap_dur = 0; _shake_t = 0
	_tw.clear(); pitch = 0.0; yaw = 0.0; dof = 0.35; key = 1.0; key_color = Color(1.0, 0.86, 0.68); creep = 0.0
	if mood_a < 0.01:
		mood = ""
	var has_crane := cmds.any(func(c): return c is Dictionary and str(c.get("c", "")) == "crane")
	_settle = 0.0 if has_crane or cmds.size() < 3 else 1.0
	_pump()


func _tween(prop: String, to: float, t: float) -> void:
	if t <= 0.0:
		set(prop, to); _tw.erase(prop)
	else:
		_tw[prop] = [float(get(prop)), to, 0.0, t]


## Camera pitch the 3D view should use now (degrees above the ground).
func view_pitch() -> float:
	var auto := BASE_PITCH - clampf(cam_zoom + creep - 1.0, -0.4, 0.6) * 28.0
	var want := pitch if pitch > 0.0 else auto
	# the automatic opening is a cut to a higher angle that glides down into the scene
	return lerpf(BASE_PITCH, clampf(want, 18.0, 70.0), film) + _ease(_settle) * 22.0


func view_yaw() -> float:
	return (yaw + sin(time * 0.21) * 3.2) * film + _ease(_settle) * 9.0


## Small handheld breathing offset, in map pixels.
func handheld() -> Vector2:
	return Vector2(sin(time * 0.9) + 0.5 * sin(time * 2.3), cos(time * 0.7) * 0.8 + 0.4 * sin(time * 1.9)) * 1.4 * film


func view_zoom() -> float:
	return safe_zoom(cam_zoom + creep * film)


func _blocked() -> bool:
	return _waiting_cb or _wait_t > 0 or _wait_mover != null or (_cam_dur > 0 and not _async_cam) \
			or (_fade_dur > 0 and not _async_fade) or (cap_dur > 0 and not _async_cap)


func _pump() -> void:
	while active and not _blocked():
		if _queue.is_empty():
			_finish()
			return
		_exec(_queue.pop_front())


func _who(c: Dictionary) -> Node2D:
	return host.actor(str(c.get("who", "player")))


func _exec(c: Dictionary) -> void:
	var k := str(c.get("c", ""))
	var async := bool(c.get("async", false))
	match k:
		"wait":
			_wait_t = float(c.get("t", 0.5))
		"move":
			var a := _who(c)
			if a == null:
				return
			var pts: Array = []
			var to = _pt(c.get("to"))
			if to != null:
				pts.append(to)
			for o in c.get("path", []):
				var q = _pt(o)
				if q != null:
					pts.append(q)
			if pts.is_empty():
				return
			_movers = _movers.filter(func(m): return m.a != a)
			var run := bool(c.get("run", false))
			var total := 0.0
			var prev := a.position
			for q in pts:
				total += prev.distance_to(q); prev = q
			var m := {"a": a, "path": pts, "idx": 0, "run": run, "total": total, "done": 0.0, "speed": clampf(float(c.get("speed", 150.0 if run else 78.0)), 12, 350),
					"end_dir": Actor.dir_of(str(c.dir)) if c.get("dir") != null else -1}
			a.clear_pose()
			_movers.append(m)
			if not async:
				_wait_mover = m
		"place":
			var a := _who(c)
			if a == null:
				return
			a.position = Vector2(float(c.get("x", a.position.x)), float(c.get("y", a.position.y)))
			if c.get("dir") != null:
				a.dir = Actor.dir_of(str(c.dir)); a.facing8 = [0, 2, 6, 4][a.dir]
			a.visible = true
			if c.get("who") == "partner":
				host.show_partner(true)
		"face":
			var a := _who(c)
			if a == null:
				return
			if c.get("at") != null:
				a.face_to(host.actor(str(c.at)))
			else:
				a.dir = Actor.dir_of(str(c.get("dir", "down"))); a.facing8 = [0, 2, 6, 4][a.dir]
		"pair":
			var pl: Actor = host.actor("player")
			var other: Actor = host.actor("partner")
			if pl == null or other == null:
				return
			var kind := str(c.get("kind", "highfive"))
			var gap: float = {"hug": 21.0, "lean": 25.0, "photo": 24.0}.get(kind, 32.0)
			var t := Vector2(pl.position.x + gap, pl.position.y)
			if not host.can_stand(t.x, t.y):
				t.x = pl.position.x - gap
			if host.can_stand(t.x, t.y):
				other.position = t
			var left := other.position.x < pl.position.x
			if kind == "photo" or kind == "lean":
				pl.dir = Actor.DIR_DOWN; other.dir = Actor.DIR_DOWN
			else:
				pl.dir = Actor.DIR_LEFT if left else Actor.DIR_RIGHT
				other.dir = Actor.DIR_RIGHT if left else Actor.DIR_LEFT
			pl.facing8 = [0, 2, 6, 4][pl.dir]; other.facing8 = [0, 2, 6, 4][other.dir]
			var poses: Array = {"hug": ["hug", "hug"], "lean": ["sit", "lean"], "photo": ["photo", "cheer"], "dance": ["dance", "dance"],
					"handwalk": (["hold_l", "hold_r"] if left else ["hold_r", "hold_l"])}.get(kind, ["highfive", "highfive"])
			var dur := maxf(0.3, float(c.get("t", 1.8)))
			pl.set_pose(poses[0], dur); other.set_pose(poses[1], dur)
			if kind == "hug" and pl.character in Actor.COUPLE_X and other.character in Actor.COUPLE_X:
				# U3b: a real embrace drawn from the couple sheet (both GLBs rendered together); row 0 has
				# Arland on the left, row 3 Sofia on the left
				var arland_left: bool = (pl.character == "arland") != left
				pl.set_couple("hug", dur, (other.position.x - pl.position.x) / 2.0, 0 if arland_left else 3)
				other.hide_for(dur)
			pl.show_emote("heart", 1.4); other.show_emote("heart", 1.4)
			if bool(c.get("block", true)):
				_wait_t = dur
		"pose":
			var a := _who(c)
			if a == null:
				return
			var p = c.get("pose")
			if p == null or p == "none":
				a.clear_pose()
			else:
				a.set_pose(str(p), float(c.get("t", 0.0)))
			if bool(c.get("block", false)):
				_wait_t = float(c.get("t", 0.6))
		"emote":
			var a := _who(c)
			if a != null:
				a.show_emote(str(c.get("e", "heart")), float(c.get("t", 1.8)))
		"cam":
			cam_zoom = view_zoom(); creep = 0.0
			_c0 = cam; _z0 = cam_zoom; _cam_follow = null
			var on: Node2D = host.actor(str(c.on)) if c.get("on") != null else null
			_c1 = Vector2(on.position.x, on.position.y - 24) if on != null else Vector2(float(c.get("x", cam.x)), float(c.get("y", cam.y)))
			_z1 = safe_zoom(float(c.get("zoom", cam_zoom)))
			var t := clampf(float(c.get("t", 1.0)), 0, 8)
			if t <= 0:
				cam = _c1; cam_zoom = _z1; _cam_dur = 0; _async_cam = false
			else:
				_cam_t = 0; _cam_dur = t; _async_cam = async
		"shot":
			var pl: Node2D = host.actor("player")
			var partner: Node2D = host.actor("partner")
			var target := str(c.get("focus", "couple"))
			var single: Node2D = partner if target == "partner" else pl
			if target == "couple" and pl != null and partner != null and partner.visible:
				_c1 = (pl.position + partner.position) * 0.5 + Vector2(0, -30)
			elif single != null:
				_c1 = single.position + Vector2(0, -28)
			else:
				return
			cam_zoom = view_zoom(); creep = 0.0
			_c0 = cam; _z0 = cam_zoom; _cam_follow = null; cam_active = true
			_z1 = safe_zoom(float(c.get("zoom", _preset_zoom(str(c.get("frame", "intimate"))))))
			var d := clampf(float(c.get("t", 0.9)), 0, 5)
			if bool(c.get("bars", true)):
				_bars_target = 1.0
			if d <= 0:
				cam = _c1; cam_zoom = _z1; _cam_dur = 0; _async_cam = false
			else:
				_cam_t = 0; _cam_dur = d; _async_cam = async
		"angle":
			var t := clampf(float(c.get("t", 1.2)), 0, 10)
			if c.get("pitch") != null:
				_tween("pitch", clampf(float(c.pitch), 0, 70), t)
			if c.get("yaw") != null:
				_tween("yaw", clampf(float(c.yaw), -40, 40), t)
			if bool(c.get("block", false)):
				_wait_t = t
		"orbit":
			var t := clampf(float(c.get("t", 4.0)), 0.1, 16)
			_tween("yaw", clampf(yaw + float(c.get("deg", 14.0)), -40, 40), t)
			if bool(c.get("block", false)):
				_wait_t = t
		"crane":
			# establishing shot: start high and wide above the target, glide down into the scene
			var t := clampf(float(c.get("t", 3.2)), 0.3, 10)
			var z := safe_zoom(float(c.get("zoom", cam_zoom)))
			_settle = 0.0
			pitch = clampf(float(c.get("from", 66.0)), 20, 70); yaw = float(c.get("yaw", -14.0))
			_tween("pitch", clampf(float(c.get("pitch", 30.0)), 18, 70), t)
			_tween("yaw", 0.0, t)
			_c0 = cam; _c1 = cam; _z0 = safe_zoom(z - 0.22); _z1 = z; cam_zoom = _z0
			_cam_t = 0; _cam_dur = t; _async_cam = not bool(c.get("block", false))
		"dof":
			_tween("dof", clampf(float(c.get("a", 0.8)), 0, 1.5), float(c.get("t", 0.8)))
		"mood":
			var id := str(c.get("id", "none"))
			if id == "none" or id == "":
				_tween("mood_a", 0.0, float(c.get("t", 1.2)))
			else:
				if mood != id:
					mood_a = 0.0 if mood_a < 0.05 else mood_a
				mood = id
				_tween("mood_a", clampf(float(c.get("a", 1.0)), 0, 1), float(c.get("t", 1.2)))
		"key":
			_tween("key", 1.0 if bool(c.get("on", true)) else 0.0, float(c.get("t", 0.6)))
			if c.get("color") != null:
				key_color = Color(str(c.color))
		"follow":
			_cam_follow = host.actor(str(c.get("who", "player"))); _cam_dur = 0; _async_cam = false
		"bars":
			_bars_target = 1.0 if bool(c.get("on", true)) else 0.0
			_bars_speed = 1.0 / maxf(0.05, float(c.get("t", 0.5)))
		"fade":
			_fade0 = fade; _fade1 = clampf(float(c.get("to", 1.0)), 0, 1)
			_fade_t = 0; _fade_dur = clampf(float(c.get("t", 0.6)), 0.01, 6)
			fade_color = Color(str(c.get("color", "000000"))); _async_fade = async
		"flash":
			flash_dur = float(c.get("t", 0.5)); flash = flash_dur; flash_color = Color(str(c.get("color", "ffffff")))
		"tint":
			_tint0 = tint_a; _tint1 = float(c.get("a", 0.3)); _tint_t = 0; _tint_dur = maxf(0.01, float(c.get("t", 1.0)))
			if _tint0 <= 0.001 or c.get("color") != null:
				tint_color = Color(str(c.get("color", "1b2350")))
		"shake":
			_shake_t = float(c.get("t", 0.4)); _shake_amp = float(c.get("amp", 3.0))
		"fx":
			var on: Node2D = host.actor(str(c.on)) if c.get("on") != null else null
			var f := {"kind": str(c.get("kind", "sparkles")), "dur": clampf(float(c.get("t", 2.0)), 0.1, 16), "t": 0.0,
					"n": clampi(int(c.get("n", 24)), 1, 80), "seed": randf() * 100.0,
					"pos": Vector2(on.position.x, on.position.y - 30) if on != null else Vector2(float(c.get("x", cam.x)), float(c.get("y", cam.y)))}
			_fxs.append(f)
			match f.kind:
				"lanterns": host.sfx("lantern")
				"restore": host.sfx("quest_complete")
				"hearts": host.sfx("heart")
			if bool(c.get("block", false)):
				_wait_t = f.dur
		"say":
			_waiting_cb = true
			host.say(str(c.get("scene", "")), int(c.get("from", 0)), int(c.get("n", 0)), func(): _waiting_cb = false)
		"line":
			_waiting_cb = true
			host.line(str(c.get("s", "narrator")), str(c.get("e", "neutral")), str(c.get("t", "")), func(): _waiting_cb = false)
		"caption":
			cap_title = str(c.get("text", "")); cap_sub = c.get("sub")
			cap_art = caption_art(cap_title, cap_sub)
			cap_t = 0; cap_dur = clampf(float(c.get("t", 2.6)), 0.1, 12); _async_cap = async
		"sfx":
			host.sfx(str(c.get("id", "sparkle")))
		"music":
			host.music(str(c.get("id", "town")))
		"spawn":
			var id := str(c.get("id", "extra"))
			host.spawn(id, str(c.get("sprite", id)), float(c.get("x", 0)), float(c.get("y", 0)), Actor.dir_of(str(c.get("dir", "down"))))
			_spawned.append(id)
		"despawn":
			host.despawn(str(c.get("id", ""))); _spawned.erase(str(c.get("id", "")))
		"show":
			var a := _who(c)
			if a != null:
				a.visible = true; a.alpha = 1.0
			if c.get("who") == "partner":
				host.show_partner(true)
		"hide":
			var a := _who(c)
			if a != null:
				a.visible = false
			if c.get("who") == "partner":
				host.show_partner(false)
		"alpha":
			var a := _who(c)
			if a != null:
				a.alpha = float(c.get("a", 1.0)); a.visible = true


func _finish() -> void:
	active = false; _bars_target = 0.0; _tint_dur = 0
	cam_zoom = view_zoom(); creep = 0.0; _settle = 0.0
	_tween("mood_a", 0.0, 1.0)
	_cam_dur = 0; _async_cam = false; _wait_mover = null; _wait_t = 0; _waiting_cb = false
	for id in _spawned:
		host.despawn(id)
	_spawned.clear()
	for m in _movers:
		m.a.walking = false
	_movers.clear()
	var d := _done
	_done = Callable()
	if d.is_valid():
		d.call()


func _process(raw: float) -> void:
	var dt := clampf(raw, 0, 0.05) * (3.0 if fast and not _waiting_cb else 1.0)
	time += dt
	film = move_toward(film, 1.0 if active else 0.0, dt * (0.9 if active else 0.7))
	for prop in _tw.keys():
		var w: Array = _tw[prop]
		w[2] += dt
		var kk := clampf(w[2] / w[3], 0, 1)
		set(prop, lerpf(w[0], w[1], _ease(kk)))
		if kk >= 1.0:
			_tw.erase(prop)
	if _settle > 0.0:
		_settle = maxf(0.0, _settle - dt / 2.6)
	if active and (_waiting_cb or _wait_t > 0) and _cam_dur <= 0 and _cam_follow == null:
		creep = minf(0.1, creep + dt * 0.012)
	bars += signf(_bars_target - bars) * minf(absf(_bars_target - bars), dt * _bars_speed)
	if flash > 0:
		flash -= dt
	if _shake_t > 0:
		_shake_t -= dt
	_fxs = _fxs.filter(func(f): f.t += dt; return f.t <= f.dur)
	queue_redraw()
	if overlay:
		overlay.queue_redraw()
	if not active:
		if cam_active:     # ease the camera back to the player
			var pl: Node2D = host.actor("player")
			var tgt := pl.position + Vector2(0, -24)
			var s := 1.0 - exp(-5.0 * dt)
			cam += (tgt - cam) * s
			cam_zoom += (1.0 - cam_zoom) * s
			if cam.distance_to(tgt) < 1.0 and absf(cam_zoom - 1.0) < 0.01:
				cam_active = false
		if tint_a > 0:
			tint_a = maxf(0, tint_a - dt * 0.8)
		if fade > 0 and _fade_dur <= 0:
			fade = maxf(0, fade - dt * 2.0)
		return
	if _cam_dur > 0:
		_cam_t += dt
		var k := clampf(_cam_t / _cam_dur, 0, 1)
		var e := _ease(k)
		cam = _c0.lerp(_c1, e)
		cam_zoom = safe_zoom(lerpf(_z0, _z1, e))
		if k >= 1.0:
			_cam_dur = 0; _async_cam = false
	elif _cam_follow != null:
		var s := 1.0 - exp(-4.0 * dt)
		cam += (_cam_follow.position + Vector2(0, -24) - cam) * s
	if _fade_dur > 0:
		_fade_t += dt
		var k := clampf(_fade_t / _fade_dur, 0, 1)
		fade = lerpf(_fade0, _fade1, _ease(k))
		if k >= 1.0:
			_fade_dur = 0; _async_fade = false
	if _tint_dur > 0:
		_tint_t += dt
		var k := minf(1.0, _tint_t / _tint_dur)
		tint_a = lerpf(_tint0, _tint1, k)
		if k >= 1.0:
			_tint_dur = 0
	if cap_dur > 0:
		cap_t += dt
		if cap_t >= cap_dur:
			cap_dur = 0; _async_cap = false
	if _wait_t > 0:
		_wait_t -= dt
	for m in _movers.duplicate():
		var a: Actor = m.a
		var tgt: Vector2 = m.path[m.idx]
		var d := tgt - a.position
		# ease in and out: start and stop gently like a person, not a sliding cursor
		var edge := minf(float(m.done), float(m.total) - float(m.done))
		var step: float = m.speed * dt * clampf(0.35 + edge / 30.0, 0.35, 1.0)
		m.done += minf(step, d.length())
		if d.length() <= step:
			a.position = tgt
			m.idx += 1
			if m.idx >= m.path.size():
				a.walking = false; a.sprinting = false
				if m.end_dir >= 0:
					a.dir = m.end_dir; a.facing8 = [0, 2, 6, 4][a.dir]
				_movers.erase(m)
				if _wait_mover == m:
					_wait_mover = null
				continue
		else:
			a.position += d / d.length() * step
			a.face(d.x, d.y)
		a.walking = true; a.sprinting = m.run
	_pump()


func cam_point() -> Vector2:
	var s := Vector2.ZERO
	if _shake_t > 0:
		s = Vector2(sin(time * 70.0) * _shake_amp, cos(time * 53.0) * _shake_amp * 0.6)
	return cam + s + handheld()


## World-space effects. Same maths as the Java build, with y pointing down.
func _draw() -> void:
	var vr := get_viewport_rect()
	var view: Rect2 = host.world.view_rect() if host and host.get("world") else Rect2(Vector2.ZERO, vr.size)
	for f in _fxs:
		var k: float = f.t / f.dur
		var al := minf(minf(1.0, (f.dur - f.t) * 2.0), minf(1.0, f.t * 3.0))
		var g: Vector2 = f.pos
		match f.kind:
			"fireflies":
				for i in int(f.n):
					var ang: float = i * 2.39996 + f.seed
					var r := 22.0 + (i % 9) * 13.0
					var drift := sin(time * 0.65 + i * 0.93) * 12.0
					var p := g + Vector2(cos(ang) * r + drift, -(sin(ang) * r * 0.65 + cos(time * 0.88 + i) * 10.0))
					var pulse := 0.45 + 0.5 * maxf(0, sin(time * 2.0 + i * 1.4))
					_spr(p, 8, Color(1, 0.91, 0.57, al * pulse * 0.72))
			"sparkles":
				for i in int(f.n):
					var ang: float = i * 2.39996 + f.seed
					var r: float = 8 + k * (40 + (i % 5) * 12)
					_spr(g + Vector2(cos(ang) * r, -(sin(ang) * r * 0.8 + k * 18)), 8, Color(1, 0.92, 0.7, al * (0.5 + 0.5 * sin(time * 6 + i))))
			"hearts":
				if _heart:
					for i in mini(int(f.n), 8):
						var tt := fmod(f.t * 0.6 + i * 0.37, 1.0)
						var p := g + Vector2(sin(i * 1.7 + f.t * 2) * 18, -(50 + tt * 50))
						draw_texture_rect(_heart, Rect2(p - Vector2(7, 7), Vector2(14, 14)), false, Color(1, 1, 1, al * (1.0 - tt)))
			"petals":
				for i in 40:
					var px := fmod(i * 0.618 + f.t * (0.03 + (i % 4) * 0.01), 1.0) * view.size.x
					var py := fposmod(i * 0.382 - f.t * 0.08, 1.0) * view.size.y
					draw_rect(Rect2(view.position + Vector2(px, view.size.y - py), Vector2(3, 2)), Color(1, 0.76, 0.86, al * 0.9))
			"glow":
				var s := 50 + sin(time * 3) * 6
				_spr(g + Vector2(0, -20), s * 2, Color(1, 0.9, 0.65, al * 0.55))
			"portal":
				var rad := 6 + minf(1.0, k * 1.6) * 46
				_spr(g + Vector2(0, -30), rad * 2.8, Color(0.85, 0.75, 1, al * 0.45))
				for i in 36:
					var ang := i / 36.0 * TAU + time * 2.2
					var rr := rad * (0.75 + 0.25 * sin(time * 3 + i))
					_spr(g + Vector2(cos(ang) * rr, -30 - sin(ang) * rr * 1.2), 8, Color(1.0 if i % 2 == 0 else 0.8, 0.85, 1, al))
			"restore":
				var rr := k * 420
				for i in 64:
					var ang := i / 64.0 * TAU
					_spr(g + Vector2(cos(ang) * rr, sin(ang) * rr * 0.7), 10, Color(1, 0.9, 0.7, al * (1 - k)))
			"beam":
				draw_rect(Rect2(g.x - 14, view.position.y, 28, g.y - view.position.y), Color(1, 0.95, 0.8, al * 0.35))
				draw_rect(Rect2(g.x - 5, view.position.y, 10, g.y - view.position.y), Color(1, 1, 1, al * 0.5))
			"lanterns":
				var ln := Data.tex("items/lantern_paper.png")
				for i in int(f.n):
					var tt: float = f.t - fmod(i * 0.37, 2.5)
					if tt < 0:
						continue
					var p := g + Vector2((fmod(i * 0.618, 1.0) - 0.5) * 260 + sin(tt + i) * 6, -tt * 22 * (0.7 + (i % 3) * 0.2))
					_spr(p, 32, Color(1, 0.8, 0.5, al * 0.35))
					if ln:
						draw_texture_rect(ln, Rect2(p - Vector2(8, 8), Vector2(16, 16)), false, Color(1, 1, 1, al))
			"stars":
				for i in int(f.n):
					var p := view.position + Vector2(fmod(i * 0.618, 1.0) * view.size.x, (1.0 - fmod(i * 0.382 + 0.3, 1.0)) * view.size.y)
					_spr(p, 7, Color(1, 0.97, 0.85, al * (0.4 + 0.6 * maxf(0, sin(time * 2 + i)))))
			"rainlight":
				for i in mini(int(f.n), 65):
					var xx := view.position.x + fposmod(i * 0.61803 + f.t * 0.115, 1.0) * view.size.x
					var yy := view.position.y + (1.0 - fposmod(i * 0.37011 - f.t * 0.3, 1.0)) * view.size.y
					draw_rect(Rect2(xx, yy, 1.8, 14 + (i % 4) * 7), Color(0.72, 0.85, 1, al * 0.21))
			"mist":
				for i in mini(int(f.n), 24):
					var xx := view.position.x + fposmod(i * 0.61 + f.t * 0.013, 1.0) * view.size.x
					var yy := view.end.y - fmod(i * 0.42, 1.0) * view.size.y
					var w := 42.0 + (i % 4) * 35.0
					draw_rect(Rect2(xx - w * 0.5, yy, w, 2 + i % 3), Color(0.8, 0.84, 0.95, al * 0.1))
			"aurora":
				for i in mini(int(f.n), 32):
					var xx := view.position.x + fposmod(i * 0.0313 + f.t * 0.015, 1.0) * view.size.x
					var yy := view.position.y + view.size.y * 0.45 - sin(i * 0.31 + time * 0.38) * view.size.y * 0.12
					var hh := 18.0 + (i % 4) * 14.0
					draw_rect(Rect2(xx, yy - hh, maxf(4, view.size.x / 36.0), hh), Color(0.55 if i % 2 == 0 else 0.85, 0.75, 1, al * 0.065))
			"book":
				var bk := Data.tex("props/glowing_book.png")
				var lift := minf(1.0, k * 2) * 34 + sin(time * 2.5) * 3
				_spr(g + Vector2(0, -lift + 22 - 40), 80, Color(1, 0.9, 0.6, al * 0.6))
				if bk:
					draw_texture_rect(bk, Rect2(g + Vector2(-bk.get_width() / 2.0, -lift - bk.get_height()), bk.get_size()), false, Color(1, 1, 1, al))
	if tint_a > 0:
		draw_rect(view.grow(10), Color(tint_color, tint_a))


func _spr(center: Vector2, s: float, col: Color) -> void:
	if _sparkle:
		draw_texture_rect(_sparkle, Rect2(center - Vector2(s, s) / 2.0, Vector2(s, s)), false, col)


static func caption_art(title: String, sub):
	match title:
		"Sabtu pagi": return "sofia_morning" if sub != null and str(sub).contains("Sofia") else "arland_morning"
		"Plaza Kota": return "plaza_intro"
		"Memory Garden": return "garden_portal"
		"Perpustakaan Kota": return "library"
		"Arsip No. 7": return "archive"
		"Dermaga Danau": return "pier"
		"Setelah Hujan": return "reunion"
		"Satu Langit": return "sky"
		"The Quiet": return "quiet"
		"Festival Lentera": return "lantern"
	if title.begins_with("Halte"):
		return "rain"
	return null


func letterboxed() -> bool:
	return bars > 0.5
