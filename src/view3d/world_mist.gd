class_name WorldMist
extends Node3D
## U2b: ground mist that follows the clock and the weather.
##
## Three sheets of drifting mist lie a little above the ground (0.08, 0.3, 0.62 m) and follow the
## camera; the noise is sampled in world space, so the mist stays on the land and slides with the
## wind. It is thickest at dawn (05.00-07.00, gone by 09.00), a thin haze at dusk and at night, heavier
## in rain and thinner on windy days. Nature maps get it most (Hutan Bisik and Bukit Bintang too,
## though they use dream lighting) at 80%, town maps at 50%, dream maps and
## caves keep their own look (U2c). Raised terraces stand above it, so it gathers in the low ground.
## The distance fog of the 3D environment thickens with it (world_view_3d.gd _update_light).

const SHEETS := [[0.08, 0.42], [0.3, 0.26], [0.62, 0.14]]       # height (m), share of the strength
const NATURE := ["hutan_bisik", "taman_kota", "riverside", "dermaga", "bukit_bintang"]
const SIZE := 48.0                                                # metres, square

var view
var _mats: Array = []
var _sheets: Array = []
var _area := 1.0
var _nature := false
var strength := 0.0                                               # last value (QA / fog)


func setup(v) -> WorldMist:
	view = v
	name = "Mist"
	var id: String = v.world.current_id
	_nature = NATURE.has(id)
	_area = 0.8 if _nature else 0.5
	var shader := preload("res://src/fx/mist.gdshader")
	var plane := PlaneMesh.new()
	plane.size = Vector2(SIZE, SIZE)
	for i in SHEETS.size():
		var m := ShaderMaterial.new()
		m.shader = shader
		m.set_shader_parameter("layer_a", SHEETS[i][1])
		m.set_shader_parameter("seed", float(i) * 0.37)
		m.set_shader_parameter("wind", Vector2(0.12 + 0.05 * i, 0.03 - 0.02 * i))
		m.set_shader_parameter("pix", 2.0 * WorldView3D.S)
		m.set_shader_parameter("radius", SIZE * 0.5)
		m.render_priority = i
		var mi := MeshInstance3D.new()
		mi.mesh = plane
		mi.material_override = m
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_mats.append(m)
		_sheets.append(mi)
	return self


## Mist strength 0..1 for a time of day (minutes) and weather, before the area factor.
static func strength_at(minute: float, weather: String) -> float:
	var m := fposmod(minute, 1440.0)
	var dawn := smoothstep(270.0, 345.0, m) * (1.0 - smoothstep(420.0, 540.0, m))
	var dusk := smoothstep(1080.0, 1170.0, m) * (1.0 - smoothstep(1260.0, 1380.0, m)) * 0.3
	var night := 0.12 if (m >= 1320.0 or m < 270.0) else 0.0
	var s := maxf(dawn, maxf(dusk, night))
	match weather:
		"rain": s = maxf(s, 0.45)
		"berawan": s = minf(1.0, s * 1.2)
		"berangin": s *= 0.4
	return s


## The colour of the mist: warm white at dawn, rose at dusk, blue at night, grey in rain.
static func colour_at(minute: float, weather: String) -> Color:
	if weather == "rain":
		return Color(0.72, 0.76, 0.82)
	var m := fposmod(minute, 1440.0)
	if m >= 1260.0 or m < 300.0:
		return Color(0.6, 0.67, 0.86)
	if m >= 1080.0:
		return Color(0.96, 0.82, 0.78)
	return Color(0.93, 0.96, 1.0)


func _process(_delta: float) -> void:
	if view == null:
		return
	var at: Atmosphere = view.atmosphere
	# Hutan Bisik and Bukit Bintang play with dream lighting but are real places: they get mist too
	var off := at.indoor or (at.realm and not _nature) or at.dark_cave()
	var s := 0.0 if off else strength_at(float(at.minute), at.weather) * _area
	strength = s
	visible = s > 0.01
	if not visible:
		return
	var c := colour_at(float(at.minute), at.weather) * Color(at.tint_mod.r, at.tint_mod.g, at.tint_mod.b).lerp(Color.WHITE, 0.75)
	var focus: Vector3 = view._cam_target
	for i in _sheets.size():
		(_sheets[i] as MeshInstance3D).position = Vector3(focus.x, SHEETS[i][0], focus.z)    # over street level
		var m: ShaderMaterial = _mats[i]
		m.set_shader_parameter("strength", s)
		m.set_shader_parameter("col", Vector3(c.r, c.g, c.b))
		m.set_shader_parameter("centre", Vector2(focus.x, focus.z))
		var windy := at.weather == "berangin"
		m.set_shader_parameter("wind", Vector2((0.12 + 0.05 * i) * (3.0 if windy else 1.0), 0.03 - 0.02 * i))
