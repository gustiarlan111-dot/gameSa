class_name RoomLight
extends Node3D
## U2a: windows of 3D rooms follow the clock and the weather.
##  * The glass shows the live sky (src/fx/window_sky.gdshader): dawn, day with drifting clouds, golden
##    hour, sunset, dusk, night with stars and moon; grey with rain running down the glass in the rain.
##  * Sunlight comes in through each window: a slanted patch of light on the floor, a soft beam with
##    dust motes floating in it, and a spotlight that really lights the floor and furniture. Its colour
##    and strength follow the hour (warm by day, orange at golden hour, faint blue moonlight on clear
##    nights, almost none in the rain). The patch slants right in the morning and left in the afternoon.
## Window rects come from the room generator (maps.json "windows", tools/worldgen/rooms_hd.py).

const SKY := preload("res://src/fx/window_sky.gdshader")
const S := 1.0 / 32.0
# minute -> [sky top, sky bottom, land, stars, light colour, light strength]
const KEYS := [
	[0, "0b1030", "1c2550", "141a30", 1.0, "9fb4ff", 0.10],
	[300, "1c2346", "4a4f7a", "202638", 0.7, "9fb4ff", 0.08],
	[370, "6f8fd0", "f5b9a0", "6a7a6a", 0.0, "ffc6a6", 0.45],
	[450, "6fb2ea", "cfe8f6", "8fb58a", 0.0, "fff3d0", 1.0],
	[930, "6fb2ea", "d2eaf6", "8fb58a", 0.0, "fff3d0", 1.0],
	[1010, "7aa0d6", "f6c98a", "8a9a6a", 0.0, "ffc98a", 0.85],
	[1070, "3a3f78", "f08a6a", "4a4050", 0.1, "ff9a6a", 0.5],
	[1130, "1e2450", "6a4f7a", "252232", 0.5, "c0a0ff", 0.12],
	[1260, "0b1030", "1c2550", "141a30", 1.0, "9fb4ff", 0.10],
	[1440, "0b1030", "1c2550", "141a30", 1.0, "9fb4ff", 0.10],
]

var view: WorldView3D
const SPOT_MIN := 0.2              # window power below which the spotlight is off (moonlight 0.10)
var _wins: Array = []             # [{mat, spot, patch, beam, dust, rect}]
var _patch_mat: StandardMaterial3D
var _beam_mat: StandardMaterial3D


func setup(v: WorldView3D) -> RoomLight:
	view = v
	var a: Dictionary = v.world.area
	var wall = null
	for h in v.world._prop_nodes:
		if is_instance_valid(h) and str(h.get_meta("type", "")).ends_with("_wall"):
			wall = h
			break
	if wall == null:
		return self
	var foot: Vector2 = wall.position
	_patch_mat = _additive()
	_beam_mat = _additive()
	var i := 0
	for r in a.get("windows", []):
		_add_window(r, foot, i)
		i += 1
	return self


func _additive() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.vertex_color_use_as_albedo = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.no_depth_test = false
	m.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	return m


func _add_window(r: Array, foot: Vector2, i: int) -> void:
	var wx := float(r[0]); var wy := float(r[1]); var ww := float(r[2]); var wh := float(r[3])
	# glass, on the tilted back wall picture exactly over the painted glass
	var glass := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	q.center_offset = Vector3(0, 0.5, 0)
	glass.mesh = q
	var b: Basis = view._prop_basis(ww, wh, true)
	glass.transform = Transform3D(b, view.stand(wx + ww / 2.0, foot.y, foot.y - (wy + wh)) + b.z.normalized() * 0.012)
	var mat := ShaderMaterial.new()
	mat.shader = SKY
	mat.set_shader_parameter("size", Vector2(ww, wh))
	mat.set_shader_parameter("seed", float(i) * 3.7 + float(view.world.area.get("w", 600)) * 0.01)
	glass.material_override = mat
	glass.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(glass)
	# sunlight on the floor: a slanted patch below the window (skew set per frame)
	var patch := MeshInstance3D.new()
	patch.material_override = _patch_mat
	patch.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(patch)
	# beam: a soft sheet from the window down to the patch, dust floating in it
	var beam := MeshInstance3D.new()
	beam.material_override = _beam_mat
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(beam)
	var dust := CPUParticles3D.new()
	dust.amount = 18
	dust.lifetime = 6.0
	dust.preprocess = 6.0
	dust.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	dust.direction = Vector3(0.3, -0.2, 0.2)
	dust.spread = 180.0
	dust.initial_velocity_min = 0.02; dust.initial_velocity_max = 0.06
	dust.gravity = Vector3(0, -0.01, 0)
	var dq := QuadMesh.new()
	dq.size = Vector2(0.035, 0.035)
	var dm := StandardMaterial3D.new()
	dm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	dm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	dm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	dm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	dm.vertex_color_use_as_albedo = true
	dq.material = dm
	dust.mesh = dq
	add_child(dust)
	var spot := SpotLight3D.new()
	spot.shadow_enabled = false
	spot.spot_angle = 38.0
	spot.light_specular = 0.1
	spot.light_cull_mask = 0xFFFFF & ~WorldView3D.WALL_LAYER     # sunlight through the glass never lights its own wall
	spot.spot_attenuation = 0.3                # near flat falloff: a pale case under the glass lights much like the floor
	add_child(spot)
	_wins.append({"mat": mat, "patch": patch, "beam": beam, "dust": dust, "spot": spot, "rect": [wx, wy, ww, wh], "foot": foot, "skew": -999.0})


static func hexc(h: String) -> Color:
	return Color.html("#" + h)


## Sky and light for a minute of the day (0..1440) and weather; also used by tests.
## How far (map px) the sunlit patch slants sideways on its way down: morning light leans right,
## afternoon light leans left. world_view_3d.gd turns the room's sun the same way.
static func skew_at(minute: float) -> float:
	return lerpf(36.0, -36.0, clampf((minute - 480.0) / 600.0, 0.0, 1.0))


static func sky_at(minute: float, rain: bool) -> Dictionary:
	var m := fposmod(minute, 1440.0)
	var k := 0
	while k < KEYS.size() - 2 and m >= float(KEYS[k + 1][0]):
		k += 1
	var a: Array = KEYS[k]
	var b: Array = KEYS[k + 1]
	var t := clampf((m - float(a[0])) / maxf(1.0, float(b[0]) - float(a[0])), 0.0, 1.0)
	var out := {
		"top": hexc(a[1]).lerp(hexc(b[1]), t), "bot": hexc(a[2]).lerp(hexc(b[2]), t),
		"land": hexc(a[3]).lerp(hexc(b[3]), t), "stars": lerpf(a[4], b[4], t),
		"light": hexc(a[5]).lerp(hexc(b[5]), t), "power": lerpf(a[6], b[6], t), "clouds": 0.45,
	}
	if rain:
		var grey := Color(0.48, 0.52, 0.58)
		out.top = out.top.lerp(grey * 0.9, 0.75); out.bot = out.bot.lerp(grey * 1.25, 0.75)
		out.land = out.land.lerp(grey * 0.6, 0.6)
		out.stars = 0.0; out.clouds = 1.0; out.power *= 0.22
		out.light = out.light.lerp(Color(0.75, 0.8, 0.9), 0.7)
	return out


func _process(_delta: float) -> void:
	if view == null or _wins.is_empty():
		return
	var at: Atmosphere = view.atmosphere
	var rain: bool = at.weather == "rain"
	var sk := sky_at(float(at.minute), rain)
	var q: Dictionary = view._q
	var lamps_ok := bool(q.get("lamps", true))
	var skew := skew_at(float(at.minute))
	for w in _wins:
		var m: ShaderMaterial = w.mat
		m.set_shader_parameter("top", Vector3(sk.top.r, sk.top.g, sk.top.b))
		m.set_shader_parameter("bot", Vector3(sk.bot.r, sk.bot.g, sk.bot.b))
		m.set_shader_parameter("land", Vector3(sk.land.r, sk.land.g, sk.land.b))
		m.set_shader_parameter("cloud_col", Vector3(1, 1, 1) * (0.55 + 0.45 * sk.power) if not rain else Vector3(0.62, 0.66, 0.72))
		m.set_shader_parameter("clouds", sk.clouds)
		m.set_shader_parameter("stars", sk.stars)
		m.set_shader_parameter("moon", 1.0 if sk.stars > 0.6 and not rain else 0.0)
		m.set_shader_parameter("rain", 1.0 if rain else 0.0)
		m.set_shader_parameter("flash", at.flash)
		if absf(skew - float(w.skew)) > 0.5:
			_shape(w, skew)
		var col: Color = sk.light
		var p: float = sk.power
		_patch_mat.albedo_color = Color(col.r, col.g, col.b, 0.32 * p)
		_beam_mat.albedo_color = Color(col.r, col.g, col.b, 0.10 * p)
		(w.dust as CPUParticles3D).emitting = p > 0.3
		(w.dust as CPUParticles3D).color = Color(col.r, col.g, col.b, 0.7 * p)
		var sp: SpotLight3D = w.spot
		sp.visible = lamps_ok and p > SPOT_MIN       # moonlight stays a patch and a beam: at night the room lamps need the light slots
		sp.light_color = col
		sp.light_energy = 0.65 * p               # floor as bright as with 1.3 at falloff 1 (it lies ~2.9 m away)


## Rebuild the floor patch, the beam and the dust box for a slant (map px of sideways shift).
func _shape(w: Dictionary, skew: float) -> void:
	w.skew = skew
	var r: Array = w.rect
	var foot: Vector2 = w.foot
	var x0: float = r[0] - 4.0
	var x1: float = r[0] + r[2] + 4.0
	var y0: float = foot.y + 3.0
	var ym: float = foot.y + 17.0              # light through the glass lands a sill's height out from the wall
	var y1: float = foot.y + 92.0
	var k0 := 14.0 / 89.0
	var top_l := view.ground(x0, y0, 0.012); var top_r := view.ground(x1, y0, 0.012)
	var mid_pl := view.ground(x0 + skew * k0, ym, 0.012); var mid_pr := view.ground(x1 + skew * k0, ym, 0.012)
	var bot_l := view.ground(x0 + skew, y1, 0.012); var bot_r := view.ground(x1 + skew, y1, 0.012)
	var bright := Color(1, 1, 1, 1); var dim := Color(1, 1, 1, 0)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for v in [[top_l, dim], [top_r, dim], [mid_pr, bright], [top_l, dim], [mid_pr, bright], [mid_pl, bright],
			[mid_pl, bright], [mid_pr, bright], [bot_r, dim], [mid_pl, bright], [bot_r, dim], [bot_l, dim]]:
		st.set_color(v[1]); st.add_vertex(v[0])
	(w.patch as MeshInstance3D).mesh = st.commit()
	# beam: from the window's bottom edge on the wall down to the far edge of the patch
	var wy_bottom: float = foot.y - (r[1] + r[3])
	var win_l := view.stand(x0 + 4.0, foot.y, wy_bottom + r[3] * 0.5)
	var win_r := view.stand(x1 - 4.0, foot.y, wy_bottom + r[3] * 0.5)
	var mid_l := view.ground(x0 + skew * 0.55, foot.y + 55.0, 0.02)
	var mid_r := view.ground(x1 + skew * 0.55, foot.y + 55.0, 0.02)
	var sb := SurfaceTool.new()
	sb.begin(Mesh.PRIMITIVE_TRIANGLES)
	for v in [[win_l, bright], [win_r, bright], [mid_r, dim], [win_l, bright], [mid_r, dim], [mid_l, dim]]:
		sb.set_color(v[1]); sb.add_vertex(v[0])
	(w.beam as MeshInstance3D).mesh = sb.commit()
	var d: CPUParticles3D = w.dust
	var c := (win_l + win_r + mid_l + mid_r) / 4.0
	d.position = c
	d.emission_box_extents = Vector3(absf(win_r.x - win_l.x) * 0.5, absf(win_l.y - mid_l.y) * 0.45, absf(win_l.z - mid_l.z) * 0.45)
	var sp: SpotLight3D = w.spot
	# out in the room and above the window: the wall under the glass falls outside the 38 degree cone
	# (it sat 0.25 m away and blew out the cafe shelves), the floor is as far as before
	sp.position = (win_l + win_r) / 2.0 + Vector3(0, 0.8, 1.2)
	var tgt := view.ground((x0 + x1) / 2.0 + skew * 0.7, foot.y + 70.0)
	sp.look_at_from_position(sp.position, tgt, Vector3.UP)
	sp.spot_range = sp.position.distance_to(tgt) * 1.6
