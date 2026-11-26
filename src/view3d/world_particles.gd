class_name WorldParticles
extends Node3D
## U2b: particles that live in the 3D world instead of on the screen.
##
## Leaves: they fall from the crowns of the trees around the camera (emission points are refreshed
## as the camera moves). The colour follows the tree, so cherry and blossom trees drop pink petals,
## autumn trees orange leaves and the rest green ones. They drift with the wind (more on windy days),
## spin, and stop in rain. Dream maps keep their own particles (U2c); Hutan Bisik and Bukit Bintang,
## which play with dream lighting, are real places and get them.
## Fireflies: glowing motes near the ground from dusk to dawn on nature maps and wherever the area
## asked for fireflies; dream maps with fireflies keep them all the time. They replace the flat 2D
## fireflies of Atmosphere (which also showed in daylight).
##
## CPU particles, small counts (12-40 leaves, 50 fireflies): safe for GL Compatibility on phones.

const NATURE := ["hutan_bisik", "taman_kota", "riverside", "dermaga", "bukit_bintang"]
const REACH := Vector2(560.0, 340.0)          # map px around the camera focus that drops leaves
const PINK := [Color(1.0, 0.78, 0.86), Color(0.98, 0.66, 0.78), Color(1.0, 0.88, 0.92)]
const ORANGE := [Color(0.95, 0.58, 0.25), Color(0.86, 0.42, 0.2), Color(0.98, 0.76, 0.32)]
const GREEN := [Color(0.45, 0.68, 0.32), Color(0.58, 0.76, 0.36), Color(0.36, 0.56, 0.28)]
const DARK := [Color(0.3, 0.46, 0.3), Color(0.24, 0.4, 0.3)]

var view
var leaves: CPUParticles3D
var fireflies: CPUParticles3D
var _crowns: Array = []                       # [Vector2 foot, Vector3 crown centre, float radius, Array palette]
var _last_focus := Vector2(INF, INF)
var _leaf_mat: StandardMaterial3D
var _rng := RandomNumberGenerator.new()
var _nature := false


static func palette_for(ptype: String) -> Array:
	if ptype.contains("cherry") or ptype.contains("blossom"):
		return PINK
	if ptype.contains("autumn"):
		return ORANGE
	if ptype.contains("dark") or ptype.contains("pine"):
		return DARK
	return GREEN


## Leaves per area from its tree density (trees per million map px), 0 when there are too few trees.
static func leaf_amount(trees: int, w: float, h: float) -> int:
	var dens := float(trees) / maxf(1.0, w * h / 1.0e6)
	return 0 if dens < 8.0 else clampi(int(round(dens * 0.9)), 12, 40)


func setup(v) -> WorldParticles:
	view = v
	name = "Particles"
	_rng.seed = hash(str(v.world.current_id))
	var world: World = v.world
	var trees := 0
	for holder in world._prop_nodes:
		if not is_instance_valid(holder) or holder.get_child_count() == 0:
			continue
		var t := str(holder.get_meta("type", ""))
		if not t.contains("tree") or t.contains("planter") or t.contains("dream") or t.contains("lantern"):
			continue
		var s := holder.get_child(0) as Sprite2D
		if s == null or s.texture == null:
			continue
		var w: float = s.texture.get_width() * s.scale.x
		var h: float = s.texture.get_height() * s.scale.y
		trees += 1
		_crowns.append([holder.position, v.stand(holder.position.x, holder.position.y, h * 0.62), w * 0.28 * WorldView3D.S, palette_for(t)])
	var n := leaf_amount(trees, float(world.area.get("w", 960)), float(world.area.get("h", 640)))
	if n > 0:
		leaves = _make_leaves(n)
		add_child(leaves)
	var id: String = world.current_id
	_nature = NATURE.has(id)
	if _nature or str(world.area.get("ambient", "")) == "fireflies":
		fireflies = _make_fireflies()
		add_child(fireflies)
	print_verbose("particles: %d trees, %d leaves, fireflies %s" % [trees, n, fireflies != null])
	return self


func _make_leaves(n: int) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.name = "Leaves"
	p.amount = n
	p.lifetime = 7.0
	p.preprocess = 7.0                               # some leaves already on their way down
	p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_POINTS
	p.direction = Vector3(1.0, -0.4, 0.25)
	p.spread = 35.0
	p.initial_velocity_min = 0.15
	p.initial_velocity_max = 0.4
	p.gravity = Vector3(0, -0.12, 0)
	p.damping_min = 0.02
	p.damping_max = 0.06
	p.angular_velocity_min = -200.0
	p.angular_velocity_max = 200.0
	p.angle_max = 360.0
	p.scale_amount_min = 0.7
	p.scale_amount_max = 1.25
	var ramp := Gradient.new()                       # fade in at the crown, out near the ground
	ramp.set_color(0, Color(1, 1, 1, 0)); ramp.set_color(1, Color(1, 1, 1, 0))
	ramp.add_point(0.1, Color(1, 1, 1, 1)); ramp.add_point(0.85, Color(1, 1, 1, 1))
	p.color_ramp = ramp
	var q := QuadMesh.new()
	q.size = Vector2(0.16, 0.1)                      # about 5 x 3 map px
	_leaf_mat = StandardMaterial3D.new()
	_leaf_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_leaf_mat.vertex_color_use_as_albedo = true
	_leaf_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_leaf_mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	_leaf_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	q.material = _leaf_mat
	p.mesh = q
	p.emitting = false
	return p


func _make_fireflies() -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.name = "Fireflies"
	p.amount = 50
	p.lifetime = 5.0
	p.preprocess = 5.0                               # already all out when the night (or the area) begins
	p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(14.0, 0.9, 9.0)                # 0.2-2.0 m: over the bushes too
	p.direction = Vector3(0, 0.3, 0)
	p.spread = 180.0
	p.initial_velocity_min = 0.04
	p.initial_velocity_max = 0.16
	p.gravity = Vector3.ZERO
	p.damping_min = 0.0
	p.damping_max = 0.03
	p.scale_amount_min = 0.7
	p.scale_amount_max = 1.2
	var ramp := Gradient.new()                       # two slow blinks per life
	ramp.set_color(0, Color(1, 0.95, 0.5, 0)); ramp.set_color(1, Color(1, 0.95, 0.5, 0))
	ramp.add_point(0.2, Color(1, 0.96, 0.52, 1)); ramp.add_point(0.45, Color(0.82, 1.0, 0.42, 0.25))
	ramp.add_point(0.7, Color(1, 0.96, 0.52, 1))
	p.color_ramp = ramp
	var q := QuadMesh.new()
	q.size = Vector2(0.38, 0.38)                      # the glow; its bright core is a few pixels
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = view._glow_tex
	m.albedo_color = Color(1.6, 1.5, 0.9)            # over 1: the night glow pass blooms them
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.no_depth_test = false
	m.disable_receive_shadows = true
	q.material = m
	p.mesh = q
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	p.emitting = false
	return p


## Crowns near the camera become the leaves' emission points (with their colours).
func _refresh_points(focus: Vector2) -> void:
	_last_focus = focus
	var pts := PackedVector3Array()
	var cols := PackedColorArray()
	for c in _crowns:
		var f: Vector2 = c[0]
		if absf(f.x - focus.x) > REACH.x or absf(f.y - focus.y) > REACH.y:
			continue
		var pal: Array = c[3]
		for k in 3:
			var o := Vector3(_rng.randf_range(-1, 1), _rng.randf_range(-0.6, 0.6), _rng.randf_range(-0.3, 0.3)) * float(c[2])
			pts.append((c[1] as Vector3) + o)
			cols.append(pal[_rng.randi() % pal.size()])
		if pts.size() >= 150:
			break
	leaves.emission_points = pts
	leaves.emission_colors = cols
	print_verbose("leaves: %d crown points near %s" % [pts.size(), focus])


func _process(_delta: float) -> void:
	if view == null:
		return
	var at: Atmosphere = view.atmosphere
	var focus3: Vector3 = view._cam_target
	var focus := Vector2(focus3.x / WorldView3D.S, focus3.z / WorldView3D.S)
	var rain := at.weather == "rain"
	var outside := not at.indoor and not at.dark_cave()
	if leaves:
		if focus.distance_to(_last_focus) > 64.0:
			_refresh_points(focus)
		var windy := at.weather == "berangin"
		leaves.initial_velocity_min = 1.1 if windy else 0.15
		leaves.initial_velocity_max = 1.7 if windy else 0.4
		_switch(leaves, outside and not rain and (_nature or not at.realm) and leaves.emission_points.size() > 0)
		var t := at.tint_mod
		_leaf_mat.albedo_color = Color(t.r, t.g, t.b).lerp(Color.WHITE, 0.25)
	if fireflies:
		fireflies.position = Vector3(focus3.x, 1.1, focus3.z)
		_switch(fireflies, outside and not rain and (at.night > 0.45 or at.realm))
	at.fireflies3d = fireflies != null


## Turning on restarts the system so `preprocess` fills it at once instead of growing for a lifetime.
func _switch(p: CPUParticles3D, on: bool) -> void:
	if on and not p.emitting:
		p.restart()
	p.emitting = on


## For QA and tests.
func leaf_points() -> int:
	return leaves.emission_points.size() if leaves else 0
