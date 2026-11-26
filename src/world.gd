class_name World
extends Node2D
## Explorable area: HD ground tiles, y-sorted props and characters, foot collision, camera,
## partner following the player's trail, doors between areas. Port of GameScreen/WorldRenderer/
## PlayerController/CompanionController (exploration part).

signal area_entered(area_id: String)
signal door_touched(door: Dictionary, old_pos: Vector2)

const WALK_SPEED := 112.0
const SPRINT_SPEED := 176.0
const STAIRS_SPEED := 0.72      # V8: walking speed factor on stairs (Elevation 3.0)
const VIEW_H := 428.0          # world units visible vertically at framing 1.0 (same as Java ExtendViewport)

var area: Dictionary = {}
var route := "sofia"
var flags := {}
var player: Actor
var partner: Actor
var camera: Camera2D
var framing := 1.2
var input_vec := Vector2.ZERO     # set by the touch joystick (HUD); keyboard is read here
var sprint_held := false
var door_cooldown := 0.0
var locked := false               # dialogue / cutscene / menus own the input
var partner_mode := 2             # 0 hidden, 1 placed by the story step, 2 walking with the player
var cine: Cutscene                # set by Game; overrides the camera while active
var npcs := {}                    # town NPC id -> Actor
var npc_brain := {}               # id -> {home, radius, target, pause}
var extras: Node2D                # quest item sprites and markers
var light_spots: Array = []       # [{pos, kind: "lamp"|"crystal"}] for the atmosphere lights
var _floor: Node2D
var _sorted: Node2D
var _ground: Node2D
var _trail: Array[Vector2] = []
var _surface := PackedByteArray()  # footstep surface letters per cell (see tools/worldgen/hdmap.py)
var _surf_cell := 8
var _surf_w := 0
var _alts: Array = []             # props with an alternate look once a story flag is set (chest opened, bridge fixed)
var _alt_t := 0.0
var _prop_nodes: Array[Node2D] = []   # prop holders; WorldView3D builds the 3D scene from them
var atmo: Atmosphere               # set by Game; animals read night / rain from it
var foliage: Array = []           # [{node, pos, r, kind: "grass"|"bush", t}] rustle when walked through
# V8 Living NPC: walk grid for NPCs going to / coming from doors. Built a few rows per physics frame
# after entering an area (no hitch on phones), 16 px cells over the real collision.
const NAV_CELL := 16.0
const NAV_ROWS_PER_FRAME := 3
var _nav: AStarGrid2D
var _nav_row := 0


func _ready() -> void:
	_ground = Node2D.new(); _ground.name = "Ground"; add_child(_ground)
	_floor = Node2D.new(); _floor.name = "Floor"; add_child(_floor)
	_sorted = Node2D.new(); _sorted.name = "Sorted"; _sorted.y_sort_enabled = true; add_child(_sorted)
	extras = Node2D.new(); extras.name = "Extras"; extras.y_sort_enabled = true
	_sorted.add_child(extras)
	camera = Camera2D.new(); camera.position_smoothing_enabled = true; camera.position_smoothing_speed = 7.0
	add_child(camera)


func start(route_id: String, area_id: String, pos: Vector2, facing := "down") -> void:
	route = route_id
	var me := "arland" if route == "arland" else "sofia"
	var other := "sofia" if route == "arland" else "arland"
	player = Actor.new().setup(me)
	partner = Actor.new().setup(other)
	enter_area(area_id, pos, facing)


func enter_area(area_id: String, pos: Vector2, facing := "down") -> void:
	area = Data.area(area_id)
	for n in [_ground, _floor]:
		for c in n.get_children():
			c.queue_free()
	for c in _sorted.get_children():
		if c != player and c != partner and c != extras:
			c.queue_free()
	for c in extras.get_children():
		c.queue_free()
	npcs.clear()
	npc_brain.clear()
	_build_ground()
	_build_props()
	_load_surface()
	_nav = AStarGrid2D.new()
	_nav.region = Rect2i(0, 0, int(ceil(float(area.get("w", 960)) / NAV_CELL)), int(ceil(float(area.get("h", 640)) / NAV_CELL)))
	_nav.cell_size = Vector2(NAV_CELL, NAV_CELL)
	_nav.offset = Vector2(NAV_CELL, NAV_CELL) * 0.5
	_nav.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	_nav.update()
	_nav_row = 0
	_spawn_animals(area_id)
	if player.get_parent() == null:
		_sorted.add_child(player); _sorted.add_child(partner)
	player.position = nearest_open(pos)
	player.dir = Actor.dir_of(facing)
	partner.position = nearest_open(player.position + Vector2(-26, 10))
	_trail.clear()
	camera.limit_left = 0; camera.limit_top = 0
	camera.limit_right = int(area.get("w", 960)); camera.limit_bottom = int(area.get("h", 640))
	camera.position = player.position + Vector2(0, -24)
	camera.reset_smoothing()
	door_cooldown = 0.6
	area_entered.emit(area_id)


func _spawn_animals(area_id: String) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(area_id)
	for spec in area.get("animals", []):
		var type := str(spec.get("type", ""))
		if not ResourceLoader.exists("res://assets/animals/%s.png" % type):
			continue
		for i in int(spec.get("n", 1)):
			_sorted.add_child(Critter.new().setup(self, type, spec, rng))


func _build_ground() -> void:
	var tiles: Array = area.get("tiles", [])
	if tiles.is_empty():
		var s := Sprite2D.new()
		s.texture = load("res://assets/" + area.get("image", ""))
		s.centered = false
		s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		if s.texture:
			s.scale = Vector2(area.w / s.texture.get_width(), area.h / s.texture.get_height())
		_ground.add_child(s)
		return
	for t in tiles:
		var s := Sprite2D.new()
		s.texture = load("res://assets/" + t.image)
		s.centered = false
		s.position = Vector2(t.x, t.y)
		s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		if s.texture:
			s.scale = Vector2(t.w / s.texture.get_width(), t.h / s.texture.get_height())
		_ground.add_child(s)


func _build_props() -> void:
	_prop_nodes.clear()
	light_spots.clear()
	foliage.clear()
	_alts.clear()
	for p in area.get("props", []):
		var ptype: String = p.get("type", "")
		if p.has("alt") and p.has("altFlag") and flags.has(p.altFlag):
			ptype = p.alt
		var d: Dictionary = Data.props.get(ptype, {})
		if d.is_empty():
			continue
		var tex: Texture2D = load("res://assets/" + d.image) if ResourceLoader.exists("res://assets/" + d.image) else null
		if tex == null:
			continue
		var holder := Node2D.new()
		holder.position = Vector2(p.x, p.y)
		holder.set_meta("img", d.image)
		holder.set_meta("type", ptype)
		if d.get("layer", "sort") == "floor":
			holder.set_meta("floor", true)
		if p.has("alt") and p.has("altFlag"):
			holder.set_meta("alt", true)
		var s := Sprite2D.new()
		var k := Data.prop_scale(d)
		s.texture = tex
		s.centered = false
		s.scale = Vector2(k, k)
		s.position = Vector2(-tex.get_width() * k / 2.0, -tex.get_height() * k)
		s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS if k < 1.0 else CanvasItem.TEXTURE_FILTER_NEAREST
		holder.add_child(s)
		if p.has("alt") and p.has("altFlag"):
			_alts.append({"sprite": s, "p": p, "on": flags.has(p.altFlag)})
		var img: String = d.image
		var sway := _sway_for(img)
		if sway:
			s.material = sway
		var fk := _foliage_kind(img)
		if fk != "":
			var r := tex.get_width() * k * (0.42 if fk == "grass" else 0.55)
			foliage.append({"node": holder, "pos": holder.position, "r": r, "kind": fk, "t": 0.0})
		if img.contains("lamp") or img.contains("lantern_post") or img.contains("lantern_on") or img.contains("crystal"):
			var kind := "crystal" if img.contains("crystal") else "lamp"
			var hgt := tex.get_height() * k
			light_spots.append({"pos": Vector2(p.x, p.y - hgt * (0.82 if kind == "lamp" else 0.5)), "foot": Vector2(p.x, p.y - 8), "kind": kind})
		_prop_nodes.append(holder)
		if d.get("layer", "sort") == "floor":
			_floor.add_child(holder)
		else:
			_sorted.add_child(holder)


## Swap a prop to its alternate texture when its flag changes while the player is in the area.
func _refresh_alts() -> void:
	for e in _alts:
		var p: Dictionary = e.p
		var on: bool = flags.has(p.altFlag)
		if on == e.on:
			continue
		e.on = on
		var d: Dictionary = Data.props.get(p.alt if on else p.type, {})
		if d.is_empty() or not ResourceLoader.exists("res://assets/" + d.image):
			continue
		var s: Sprite2D = e.sprite
		var tex: Texture2D = load("res://assets/" + d.image)
		var k := Data.prop_scale(d)
		s.texture = tex
		s.scale = Vector2(k, k)
		s.position = Vector2(-tex.get_width() * k / 2.0, -tex.get_height() * k)


func _foliage_kind(img: String) -> String:
	if img.contains("grass") or img.contains("reeds") or img.contains("fern") or img.contains("flowers") or img.contains("wildflowers"):
		return "grass"
	if img.contains("bush") or img.contains("hedge"):
		return "bush"
	return ""


func _load_surface() -> void:
	_surface = PackedByteArray()
	_surf_w = 0
	var sf: Dictionary = area.get("surface", {})
	if sf.is_empty():
		return
	_surf_cell = int(sf.get("cell", 8))
	var rows: Array = sf.get("rows", [])
	var re := RegEx.new()
	re.compile("([a-z])(\\d+)")
	for row in rows:
		for m in re.search_all(String(row)):
			var ch := m.get_string(1).unicode_at(0)
			for i in int(m.get_string(2)):
				_surface.append(ch)
		if _surf_w == 0:
			_surf_w = _surface.size()


## Footstep sound for the ground under a point, or "" when the area has no surface map.
func step_sound(p: Vector2) -> String:
	if _surface.is_empty():
		return ""
	var i := int(p.x / _surf_cell)
	var j := int(p.y / _surf_cell)
	var idx := j * _surf_w + i
	if i < 0 or i >= _surf_w or idx < 0 or idx >= _surface.size():
		return ""
	match char(_surface[idx]):
		"g": return "step_grass"
		"r": return "step_gravel"
		"w": return "step_wood"
	return "step_stone"


## V8: true while standing on stairs (elevation.json slopes marked stairs, or maps.json stairs).
func on_stairs(p: Vector2) -> bool:
	return Elevation.on_stairs(area, p.x, p.y)


## Height of a point above street level in picture pixels (0 indoors and on flat maps).
func height_at(p: Vector2) -> float:
	return Elevation.at(area, p.x, p.y)


## Walking into tall grass, flowers or against a bush rustles it: a sound and a little shake.
func rustle(p: Vector2, delta: float) -> String:
	var hit := ""
	for f in foliage:
		f.t = maxf(0.0, float(f.t) - delta)
		var d: Vector2 = p - f.pos
		var rr: float = f.r
		var inside: bool = absf(d.x) < rr and d.y > -rr * 0.5 and d.y < 14.0
		if inside and f.t <= 0.0:
			f.t = 0.7
			hit = f.kind
			var n: Node2D = f.node
			if is_instance_valid(n):
				var tw := n.create_tween()
				var base := n.skew
				tw.tween_property(n, "skew", base + (0.12 if d.x < 0 else -0.12), 0.08)
				tw.tween_property(n, "skew", base - 0.06, 0.12)
				tw.tween_property(n, "skew", base, 0.18)
	return hit


const SWAY_SHADER := preload("res://src/fx/sway.gdshader")
var _sway_mats := {}


## Foliage gets a gentle wind sway (one shared material per strength, cheap on mobile).
func _sway_for(img: String) -> Material:
	var amp := 0.0
	if img.contains("tree") or img.contains("willow"):
		amp = 3.0
	elif img.contains("grass") or img.contains("reeds") or img.contains("fern"):
		amp = 4.0
	elif img.contains("bush") or img.contains("flowers"):
		amp = 1.2
	if amp == 0.0 or img.contains("planter") or img.contains("stump") or img.contains("log"):
		return null
	if not _sway_mats.has(amp):
		var m := ShaderMaterial.new()
		m.shader = SWAY_SHADER
		m.set_shader_parameter("amp", amp)
		m.set_shader_parameter("speed", 1.1 if amp < 4.0 else 1.6)
		_sway_mats[amp] = m
	return _sway_mats[amp]


## World rectangle on screen, from the viewport's canvas transform (works for the 2D camera and for
## the 3D view, which sets the canvas transform itself so 2D effects line up with the 3D ground).
func view_rect() -> Rect2:
	var inv := get_viewport().get_canvas_transform().affine_inverse()
	var vs := get_viewport_rect().size
	var a := inv * Vector2.ZERO
	var b := inv * vs
	return Rect2(a, b - a).abs()


func nearest_open(p: Vector2) -> Vector2:
	if not Data.blocked(area, p.x, p.y, flags):
		return p
	for r in range(4, 400, 4):
		for i in 16:
			var q := p + Vector2.from_angle(i * TAU / 16.0) * r
			if not Data.blocked(area, q.x, q.y, flags):
				return q
	return Vector2(area.spawn[0], area.spawn[1])


func can_stand(x: float, y: float) -> bool:
	return not Data.blocked(area, x, y, flags)


func add_npc(id: String, sprite: String, pos: Vector2, facing: String, wander: float) -> Actor:
	var a := Actor.new().setup(sprite)
	a.position = nearest_open(pos)
	a.dir = Actor.dir_of(facing)
	a.facing8 = [0, 2, 6, 4][a.dir]
	_sorted.add_child(a)
	npcs[id] = a
	npc_brain[id] = {"home": a.position, "radius": wander, "target": a.position, "pause": randf_range(1.0, 4.0)}
	return a


## V8 Living NPC: a walkable point just inside the door that leads to `to_area` (or the door nearest
## to `near` when no door goes there), or null in a map without doors.
func door_point(to_area: String, near: Vector2):
	var hop := first_hop(str(area.get("id", "")), to_area)
	var best = null
	var best_d := INF
	for d in area.get("doors", []):
		var r: Array = d.get("rect", [])
		if r.size() < 4:
			continue
		var c := Vector2(r[0] + r[2] / 2.0, r[1] + r[3] / 2.0)
		var inside := Vector2(clampf(c.x, 24.0, float(area.get("w", 960)) - 24.0), clampf(c.y, 24.0, float(area.get("h", 640)) - 24.0))
		var dd := inside.distance_to(near) - (100000.0 if hop != "" and str(d.get("to", "")) == hop else 0.0)
		if dd < best_d:
			best_d = dd
			best = nearest_open(inside)
	return best


## The neighbouring area on the shortest door route from `from` to `to` ("" when none).
static func first_hop(from: String, to: String) -> String:
	if to == "" or from == to or not Data.maps.has(to):
		return ""
	var prev := {from: ""}
	var q: Array = [from]
	while not q.is_empty():
		var cur: String = q.pop_front()
		if cur == to:
			break
		for d in Data.area(cur).get("doors", []):
			var nx := str(d.get("to", ""))
			if Data.maps.has(nx) and not prev.has(nx):
				prev[nx] = cur
				q.append(nx)
	if not prev.has(to):
		return ""
	var step := to
	while prev[step] != from:
		step = prev[step]
	return step


## True when an NPC can get from a to b: a straight line, or a grid path once the grid is built.
func clear_path(a: Vector2, b: Vector2) -> bool:
	return Data.clear_segment(area, a.x, a.y, b.x, b.y, flags) or not nav_path(a, b).is_empty()


func nav_ready() -> bool:
	return _nav != null and _nav_row >= _nav.region.size.y


func _nav_build_step() -> void:
	if _nav == null or nav_ready():
		return
	var end := mini(_nav_row + NAV_ROWS_PER_FRAME, _nav.region.size.y)
	for y in range(_nav_row, end):
		for x in _nav.region.size.x:
			if Data.blocked(area, (x + 0.5) * NAV_CELL, (y + 0.5) * NAV_CELL, flags):
				_nav.set_point_solid(Vector2i(x, y))
	_nav_row = end


func _nav_open(p: Vector2) -> Vector2i:
	var c := Vector2i(clampi(int(p.x / NAV_CELL), 0, _nav.region.size.x - 1), clampi(int(p.y / NAV_CELL), 0, _nav.region.size.y - 1))
	for r in 4:
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				var n := c + Vector2i(dx, dy)
				if _nav.is_in_boundsv(n) and not _nav.is_point_solid(n):
					return n
	return c


## Waypoints from a to b over the NPC grid ([] when the grid is not ready or there is no way).
func nav_path(a: Vector2, b: Vector2) -> Array:
	if not nav_ready():
		return []
	var pts: PackedVector2Array = _nav.get_point_path(_nav_open(a), _nav_open(b))
	var out: Array = []
	for i in range(1, pts.size()):
		out.append(pts[i])
	if not out.is_empty():
		out[-1] = b
	return out


## Give an NPC a route (used when walking in from a door).
func npc_route(id: String, to: Vector2) -> void:
	if npc_brain.has(id):
		var b: Dictionary = npc_brain[id]
		var a: Actor = npcs[id]
		if not Data.clear_segment(area, a.position.x, a.position.y, to.x, to.y, flags):
			var path := nav_path(a.position, to)
			if not path.is_empty():
				b.path = path


## Send a town NPC out through the door toward `to_area`. False when there is no clear way out.
func npc_leave(id: String, to_area: String) -> bool:
	if not npcs.has(id):
		return false
	var a: Actor = npcs[id]
	var out = door_point(to_area, a.position)
	if out == null or not clear_path(a.position, out):
		return false
	var b: Dictionary = npc_brain[id]
	b.target = out; b.home = out; b.radius = 0.0; b.pause = 0.0
	var dist := a.position.distance_to(out)
	if not Data.clear_segment(area, a.position.x, a.position.y, out.x, out.y, flags):
		b.path = nav_path(a.position, out)
		dist = 0.0
		var prev := a.position
		for q in b.path:
			dist += prev.distance_to(q); prev = q
	b.leaving = dist / 46.0 + 5.0      # walk time + slack, then give up (someone stands in the way)
	return true


func remove_npc(id: String) -> void:
	if npcs.has(id):
		npcs[id].queue_free()
		npcs.erase(id)
		npc_brain.erase(id)


## Town NPCs stroll slowly around their scheduled spot and never walk through walls or people.
func _update_npcs(delta: float, talking_to: String) -> void:
	for id in npcs:
		var a: Actor = npcs[id]
		var b: Dictionary = npc_brain[id]
		if locked and (id == talking_to or (cine and cine.active)):
			a.walking = false
			continue
		if b.has("path"):
			var path: Array = b.path
			while not path.is_empty() and a.position.distance_to(path[0]) < 4.0:
				path.pop_front()
			if path.is_empty():
				b.erase("path")
			else:
				b.target = path[0]; b.pause = 0.0
		if b.has("leaving"):
			b.leaving = float(b.leaving) - delta
			if b.leaving <= 0.0 or (not b.has("path") and a.position.distance_to(b.target) <= 3.0):
				remove_npc.call_deferred(id)    # through the door
				continue
		var d: Vector2 = b.target - a.position
		if d.length() > 2.0:
			var n := a.position + d.normalized() * minf(d.length(), 46.0 * delta)
			var near_player := absf(n.x - player.position.x) < 22 and absf(n.y - player.position.y) < 16
			if Data.clear_segment(area, a.position.x, a.position.y, n.x, n.y, flags) and not near_player:
				a.position = n; a.face(d.x, d.y); a.walking = true
			else:
				if not b.has("leaving"):
					b.target = a.position
				b.pause = 0.55; a.walking = false
		else:
			a.walking = false
			b.pause -= delta
			if b.pause <= 0:
				b.pause = randf_range(2.0, 6.0)
				if b.radius > 0:
					for _i in 8:
						var q: Vector2 = b.home + Vector2.from_angle(randf() * TAU) * randf() * b.radius
						if can_stand(q.x, q.y):
							b.target = q
							break
				elif randf() < 0.3:
					a.dir = randi() % 4; a.facing8 = [0, 2, 6, 4][a.dir]


var talking_to := ""


func _physics_process(delta: float) -> void:
	_alt_t -= delta
	if _alt_t <= 0.0:
		_alt_t = 0.4
		_refresh_alts()
	if player == null:
		return
	door_cooldown = maxf(0.0, door_cooldown - delta)
	_nav_build_step()
	_update_npcs(delta, talking_to)
	var v := Vector2.ZERO if locked else Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if v == Vector2.ZERO and not locked:
		v = input_vec
	var sprint := sprint_held or Input.is_key_pressed(KEY_SHIFT)
	var len := v.length()
	if cine and cine.active:
		pass                       # cutscene moves the actors
	elif len < 0.01:
		player.walking = false
	else:
		var dirv := v / len
		var spd := (SPRINT_SPEED if sprint else WALK_SPEED) * maxf(0.45, minf(1.0, len)) * delta
		if on_stairs(player.position):
			spd *= STAIRS_SPEED          # climbing or going down steps takes a little longer
		var o := player.position
		var nx := o.x + dirv.x * spd
		if Data.clear_segment(area, o.x, o.y, nx, o.y, flags):
			player.position.x = nx
		var ny := player.position.y + dirv.y * spd
		if Data.clear_segment(area, player.position.x, o.y, player.position.x, ny, flags):
			player.position.y = ny
		player.face(dirv.x, dirv.y)
		player.sprinting = sprint
		player.walking = (player.position - o).length() > 0.01
		if player.walking and (_trail.is_empty() or _trail[-1].distance_to(player.position) > 6):
			_trail.append(player.position)
			if _trail.size() > 80:
				_trail.pop_front()
		_check_doors(o)
	if partner_mode == 2 and not (cine and cine.active):
		_follow(delta)
	var vp := get_viewport_rect().size
	if cine and cine.cam_active:
		camera.position_smoothing_enabled = false
		camera.position = cine.cam_point()
		var zc := vp.y / VIEW_H * cine.view_zoom()
		camera.zoom = Vector2(zc, zc)
		_fit_limits(vp / zc)
		return
	camera.position_smoothing_enabled = true
	camera.position = player.position + Vector2(0, -24)
	var z := vp.y / (VIEW_H * framing * (1.045 if area.get("indoor", false) else 1.0))
	camera.zoom = Vector2(z, z)
	_fit_limits(vp / z)


## Maps smaller than the view (small rooms) are centred instead of pinned to the top-left.
func _fit_limits(view: Vector2) -> void:
	var w := float(area.get("w", 960))
	var h := float(area.get("h", 640))
	camera.limit_left = int(minf(0.0, (w - view.x) / 2.0)); camera.limit_right = int(maxf(w, (w + view.x) / 2.0))
	camera.limit_top = int(minf(0.0, (h - view.y) / 2.0)); camera.limit_bottom = int(maxf(h, (h + view.y) / 2.0))


## Partner walks along the player's trail and stops at a comfortable distance.
func _follow(delta: float) -> void:
	var target := partner.position
	while _trail.size() > 0 and _trail[0].distance_to(player.position) > 34:
		target = _trail[0]
		if partner.position.distance_to(_trail[0]) < 6:
			_trail.pop_front()
		else:
			break
	var d := target - partner.position
	var dist_player := partner.position.distance_to(player.position)
	if d.length() > 2 and dist_player > 30:
		var spd := (SPRINT_SPEED if player.sprinting else WALK_SPEED) * (1.08 if dist_player > 70 else 0.96) * delta
		var step := d.normalized() * minf(spd, d.length())
		partner.position += step
		partner.face(step.x, step.y)
		partner.walking = true
		partner.sprinting = player.sprinting
	else:
		partner.walking = false
		if dist_player < 80:
			partner.face(player.position.x - partner.position.x, player.position.y - partner.position.y)
	if dist_player > 240:      # fell far behind (e.g. after a scene): catch up next to the player
		place_partner_beside()


func place_partner_beside() -> void:
	partner.position = nearest_open(player.position + Vector2(-24, 8))
	_trail.clear()


func _check_doors(old: Vector2) -> void:
	if door_cooldown > 0:
		return
	var x0 := player.position.x - Data.FOOT_W / 2.0
	var foot := Rect2(x0, player.position.y - Data.FOOT_TOP, Data.FOOT_W, Data.FOOT_TOP + Data.FOOT_BOTTOM)
	for d in area.get("doors", []):
		var r: Array = d.get("rect", [])
		if r.size() >= 4 and foot.intersects(Rect2(r[0], r[1], r[2], r[3])):
			door_cooldown = 1.0
			door_touched.emit(d, old)
			return
