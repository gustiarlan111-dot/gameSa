class_name NpcLife
extends Node2D
## U3b: the town feels lived in.
##  * Neighbours chat: when two town NPCs stand close and the couple is nearby, they turn to each other
##    and talk in speech bubbles. Lines come from assets/data/npc_chatter.json, picked by weather, time
##    of day, chapter and what the couple has done (side quests, choices), pair talks first.
##  * Rain: everyone out in the open carries an umbrella, Arland and Sofia too (one big umbrella when
##    they walk hand in hand). NPCs who shelter from rain already do so through their schedules.
##  * Lightning: people in view flinch (a jolt and a "!") at each flash.
## Lives in the UI CanvasLayer and draws the bubbles in screen space (crisp text), positioned from the
## world's canvas transform, which the 3D view keeps in line with the 3D ground.

const NEAR_MIN := 26.0
const NEAR_MAX := 150.0
const HEAR := 420.0                 # the couple must be this close to the talkers (world px)
const LINE_T := 2.9                 # seconds per bubble
const FONT := 15

var game                            # Game
var data: Dictionary = {}
var _talk := {}                     # {a, b, lines, i, t, id}
var _cool := 8.0
var _recent: Array = []
var _scan := 0.0
var _flash_was := 0.0
var _rng := RandomNumberGenerator.new()


func setup(g) -> NpcLife:
	game = g
	data = Data._json("res://assets/data/npc_chatter.json") if ResourceLoader.exists("res://assets/data/npc_chatter.json") else {}
	_rng.randomize()
	return self


func _process(delta: float) -> void:
	if game == null or game.world == null:
		return
	var w: World = game.world
	_rain(w)
	_lightning(w)
	var quiet: bool = game.dialog.active or game.cine.active
	if quiet:
		if not _talk.is_empty():
			_end_talk(w)
		queue_redraw()
		return
	if _talk.is_empty():
		_cool -= delta
		_scan -= delta
		if _cool <= 0.0 and _scan <= 0.0:
			_scan = 1.0
			_try_start(w)
	else:
		_step_talk(w, delta)
	queue_redraw()


# ------------------------------------------------------------------ rain and lightning
func _rain(w: World) -> void:
	var a: Atmosphere = game.atmosphere
	var wet: bool = a.weather == "rain" and not a.indoor and not a.realm
	for id in w.npcs:
		var n: Actor = w.npcs[id]
		n.set_umbrella(wet and not n.character.begins_with("lumi"))
	w.player.set_umbrella(wet)
	w.partner.set_umbrella(wet and w.player.couple == "")


func _lightning(w: World) -> void:
	var f: float = game.atmosphere.flash
	if f > 0.55 and _flash_was <= 0.55:
		var view: Rect2 = w.view_rect().grow(40)
		for id in w.npcs:
			var n: Actor = w.npcs[id]
			if view.has_point(n.position) and n.pose == null and not n.walking:
				n.set_pose("surprised", 0.5, true); n.show_emote("exclaim", 1.0)
		for c in [w.player, w.partner]:
			if c.visible and c.pose == null and not c.walking and c.couple == "":
				c.set_pose("kaget", 0.7, true)
	_flash_was = f


# ------------------------------------------------------------------ chatter
static func pair_key(a: String, b: String) -> String:
	return "%s|%s" % [a, b] if a < b else "%s|%s" % [b, a]


## Talks this pair may have now (pair talks first), condition checked with the quest engine.
func talks_for(a_id: String, b_id: String) -> Array:
	var out: Array = []
	for t in data.get("pairs", {}).get(pair_key(a_id, b_id), []):
		if _ok(t):
			out.append(t)
	if out.is_empty() or _rng.randf() < 0.35:
		for t in data.get("generic", []):
			if _ok(t):
				out.append(t)
	return out


func _ok(t: Dictionary) -> bool:
	if _recent.has(t.get("id", "")):
		return false
	var when: Dictionary = (t.get("when", {}) as Dictionary).duplicate()
	var wx := str(when.get("weather", ""))
	when.erase("weather")
	if wx == "rain" and game.atmosphere.weather != "rain":
		return false
	if wx == "clear" and game.atmosphere.weather == "rain":
		return false
	return game.engine.check(when)


func _try_start(w: World) -> void:
	var ids: Array = w.npcs.keys()
	var me: Vector2 = w.player.position
	var best: Array = []
	for i in ids.size():
		var a: Actor = w.npcs[ids[i]]
		if a.walking or a.position.distance_to(me) > HEAR or _busy(w, ids[i]):
			continue
		for j in range(i + 1, ids.size()):
			var b: Actor = w.npcs[ids[j]]
			var d := a.position.distance_to(b.position)
			if d < NEAR_MIN or d > NEAR_MAX or b.walking or _busy(w, ids[j]):
				continue
			best.append([ids[i], ids[j], d])
	if best.is_empty():
		_cool = 3.0
		return
	var pick: Array = best[_rng.randi() % best.size()]
	var talks := talks_for(pick[0], pick[1])
	if talks.is_empty():
		_cool = 6.0
		return
	var t: Dictionary = talks[_rng.randi() % talks.size()]
	_talk = {"a": pick[0], "b": pick[1], "lines": t.get("lines", []), "i": -1, "t": 0.0, "id": t.get("id", "")}
	_recent.append(t.get("id", "")); if _recent.size() > 10: _recent.pop_front()
	for id in [pick[0], pick[1]]:
		var br: Dictionary = w.npc_brain[id]
		br.target = w.npcs[id].position; br.pause = 60.0
	w.npcs[pick[0]].face_to(w.npcs[pick[1]]); w.npcs[pick[1]].face_to(w.npcs[pick[0]])
	_next_line(w)


func _busy(w: World, id: String) -> bool:
	var br: Dictionary = w.npc_brain.get(id, {})
	return br.has("path") or br.has("leaving") or id.begins_with("lumi") or id == w.talking_to


func _step_talk(w: World, delta: float) -> void:
	if not (w.npcs.has(_talk.a) and w.npcs.has(_talk.b)):
		_end_talk(w)
		return
	_talk.t -= delta
	if _talk.t <= 0.0:
		_next_line(w)


func _next_line(w: World) -> void:
	_talk.i += 1
	if _talk.i >= _talk.lines.size():
		_end_talk(w)
		return
	_talk.t = LINE_T + str(_talk.lines[_talk.i][1]).length() * 0.02
	_talk.dur = _talk.t
	var who := speaker_id(_talk.lines[_talk.i][0], _talk.a, _talk.b)
	if w.npcs.has(who):
		w.npcs[who].set_pose("nod", 0.4, true)


## Which NPC says a line: 0/1 = first/second of the pair, or an NPC id (pair talks).
static func speaker_id(s, a: String, b: String) -> String:
	if s is String:
		return s if s == a or s == b else a
	return a if int(s) == 0 else b


func _end_talk(w: World) -> void:
	for id in [_talk.get("a", ""), _talk.get("b", "")]:
		if w.npc_brain.has(id):
			w.npc_brain[id].pause = _rng.randf_range(1.5, 4.0)
	_talk = {}
	_cool = _rng.randf_range(14.0, 30.0)


# ------------------------------------------------------------------ bubbles
func _draw() -> void:
	if _talk.is_empty() or int(_talk.i) < 0 or int(_talk.i) >= _talk.lines.size():
		return
	var w: World = game.world
	var line: Array = _talk.lines[_talk.i]
	var who := speaker_id(line[0], _talk.a, _talk.b)
	if not w.npcs.has(who):
		return
	var n: Actor = w.npcs[who]
	var xf: Transform2D = w.get_viewport().get_canvas_transform()
	var head: Vector2 = xf * (n.position + Vector2(0, -Actor.FH * n.style.scale - 10))
	var text := str(line[1])
	var f := UiTheme.font("body")
	var width := minf(300.0, f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, FONT).x + 4)
	var h := f.get_multiline_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, width, FONT).y
	var r := Rect2(head.x - width / 2.0 - 12, head.y - h - 22, width + 24, h + 14)
	var vs := get_viewport_rect().size
	r.position.x = clampf(r.position.x, 8, vs.x - r.size.x - 8)
	r.position.y = maxf(8, r.position.y)
	var age := float(_talk.get("dur", LINE_T)) - float(_talk.t)
	var a := clampf(age * 6.0, 0.0, 1.0) * clampf(float(_talk.t) * 4.0, 0.0, 1.0)
	var box := UiTheme.panel(Color(1.0, 0.98, 0.93, 0.95 * a), Color(0.78, 0.62, 0.36, a), 12, 2, 6)
	draw_style_box(box, r)
	var tip := PackedVector2Array([Vector2(head.x - 7, r.end.y - 1), Vector2(head.x + 7, r.end.y - 1), Vector2(head.x, r.end.y + 9)])
	draw_colored_polygon(tip, Color(1.0, 0.98, 0.93, 0.95 * a))
	UiTheme.draw_text(self, text, r.position.x + 12, r.position.y + 6, FONT, Color(0.24, 0.17, 0.28, a), "left", width)


## For QA and tests: the conversation currently shown ({} when none).
func current() -> Dictionary:
	return _talk
