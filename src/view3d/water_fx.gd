class_name WaterFx
extends Node3D
## Living water for the 3D view: expanding ripple rings and drifting light glints on the painted
## water of the current area, plus a ring behind every swimming duck. Water is found from the area's
## "water" ellipses, "waterFlow" bands/river paths, and only where the map blocks walking (so piers
## and banks inside a zone stay dry). Two MultiMeshes, so it stays one draw call each.

const S := 1.0 / 32.0
const RINGS := 40
const GLINTS := 60

var world: World
var atmosphere: Atmosphere
var _zones: Array = []           # [kind, data]
var _flow_dx := 1.0
var _flow_speed := 10.0
var _rings: MultiMesh
var _glints: MultiMesh
var _ring_state: Array = []      # [pos2d, age, life, size]
var _glint_state: Array = []     # [pos2d, age, life, len]
var _spawn_acc := 0.0
var _duck_acc := {}


func setup(w: World) -> WaterFx:
	world = w
	for e in w.area.get("water", []):
		_zones.append(["ellipse", Vector4(e.cx, e.cy, e.rx, e.ry)])
	var flows = w.area.get("waterFlow")
	if flows is Array:
		for f in flows:
			if f.has("path"):
				_zones.append(["path", f])
			else:
				_zones.append(["rect", Rect2(f.x, f.y, f.w, f.h)])
				_flow_dx = float(f.get("dx", 1))
			_flow_speed = float(f.get("speed", 10))
	_rings = _make_mm(RINGS, _ring_tex(), 1.0)
	_glints = _make_mm(GLINTS, _glint_tex(), 0.0)
	for i in RINGS:
		_ring_state.append([Vector2.ZERO, 1.0, 0.0, 0.0])
	for i in GLINTS:
		_glint_state.append([Vector2.ZERO, 1.0, 0.0, 0.0])
	return self


func active() -> bool:
	return not _zones.is_empty()


func _make_mm(n: int, tex: Texture2D, _k: float) -> MultiMesh:
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = q
	mm.instance_count = n
	for i in n:
		mm.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ZERO), Vector3.ZERO))
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = tex
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.vertex_color_use_as_albedo = true
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mm


## A 1-pixel ellipse outline (pixel-art ring), squashed later to sit on the water.
func _ring_tex() -> Texture2D:
	var n := 32
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for y in n:
		for x in n:
			var d := Vector2(x + 0.5 - n / 2.0, y + 0.5 - n / 2.0).length()
			if absf(d - 14.0) < 0.75:
				img.set_pixel(x, y, Color(1, 1, 1, 1))
			elif absf(d - 12.5) < 0.6:
				img.set_pixel(x, y, Color(1, 1, 1, 0.35))
	return ImageTexture.create_from_image(img)


func _glint_tex() -> Texture2D:
	var img := Image.create(8, 2, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for x in range(1, 7):
		img.set_pixel(x, 0, Color(1, 1, 1, 1.0 if x > 1 and x < 6 else 0.5))
	img.set_pixel(3, 1, Color(1, 1, 1, 0.4)); img.set_pixel(4, 1, Color(1, 1, 1, 0.4))
	return ImageTexture.create_from_image(img)


func is_water(p: Vector2) -> bool:
	var inside := false
	for z in _zones:
		match z[0]:
			"ellipse":
				var e: Vector4 = z[1]
				inside = pow((p.x - e.x) / e.z, 2) + pow((p.y - e.y) / e.w, 2) <= 1.0
			"rect":
				inside = (z[1] as Rect2).has_point(p)
			"path":
				var pts: Array = z[1].path
				var hw: float = float(z[1].get("width", 60)) * 0.5
				for i in pts.size() - 1:
					var a := Vector2(pts[i][0], pts[i][1]); var b := Vector2(pts[i + 1][0], pts[i + 1][1])
					if Geometry2D.get_closest_point_to_segment(p, a, b).distance_to(p) < hw:
						inside = true
						break
		if inside:
			break
	return inside and not world.can_stand(p.x, p.y)


func _random_water(view: Rect2) -> Vector2:
	for _i in 6:
		var p := view.position + Vector2(randf() * view.size.x, randf() * view.size.y)
		if is_water(p):
			return p
	return Vector2.INF


func ripple(p: Vector2, size := 1.0) -> void:
	for st in _ring_state:
		if st[1] >= st[2]:
			st[0] = p; st[1] = 0.0; st[2] = randf_range(1.3, 2.0) * size; st[3] = size
			return


func _process(delta: float) -> void:
	if world == null or _zones.is_empty():
		return
	var view := world.view_rect().grow(40)
	_spawn_acc += delta
	while _spawn_acc > 0.09:
		_spawn_acc -= 0.09
		var p := _random_water(view)
		if p != Vector2.INF:
			if randf() < 0.35:
				ripple(p, randf_range(0.6, 1.0))
			else:
				for st in _glint_state:
					if st[1] >= st[2]:
						st[0] = p; st[1] = 0.0; st[2] = randf_range(0.8, 1.8); st[3] = randf_range(0.7, 1.4)
						break
	# swimming ducks leave rings
	for c in world._sorted.get_children():
		if c is Critter and c.kind == "duck" and c.visible:
			var t: float = _duck_acc.get(c.get_instance_id(), randf()) - delta
			if t <= 0.0:
				t = 0.7
				ripple(c.position + Vector2(0, -1), 0.8)
			_duck_acc[c.get_instance_id()] = t
	atmosphere = world.atmo
	var tint: Color = atmosphere.tint_mod if atmosphere else Color.WHITE
	var night: float = atmosphere.night if atmosphere else 0.0
	var base := Color(0.8, 0.92, 1.0) * tint * (0.8 + 0.3 * night)
	for i in RINGS:
		var st: Array = _ring_state[i]
		st[1] += delta
		if st[1] >= st[2]:
			_rings.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ZERO), Vector3.ZERO))
			continue
		var k: float = st[1] / st[2]
		var r: float = lerpf(5.0, 26.0, sqrt(k)) * st[3]
		var basis := Basis(Vector3.RIGHT, -PI / 2.0) * Basis.from_scale(Vector3(r * S, r * 0.42 * S, 1))
		_rings.set_instance_transform(i, Transform3D(basis, Vector3(st[0].x * S, 0.03, st[0].y * S)))
		var c := base * (1.0 - k) * 1.2
		c.a = 1.0
		_rings.set_instance_color(i, c)
	var drift := _flow_dx * _flow_speed * 0.6
	for i in GLINTS:
		var st: Array = _glint_state[i]
		st[1] += delta
		if st[1] >= st[2]:
			_glints.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ZERO), Vector3.ZERO))
			continue
		st[0].x += drift * delta
		var k: float = st[1] / st[2]
		var a := sin(k * PI)
		var len: float = 8.0 * st[3] * (0.6 + 0.4 * a)
		var basis := Basis(Vector3.RIGHT, -PI / 2.0) * Basis.from_scale(Vector3(len * S, 2.0 * S, 1))
		_glints.set_instance_transform(i, Transform3D(basis, Vector3(st[0].x * S, 0.03, st[0].y * S)))
		var c := base * a * 1.1
		c.a = 1.0
		_glints.set_instance_color(i, c)
