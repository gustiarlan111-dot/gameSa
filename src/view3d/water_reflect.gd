class_name WaterReflect
extends Node3D
## V8.10 water reflections for the 3D view (works on GL Compatibility, no second camera).
## Every standing prop whose foot is near open water, and every character walking by the water, gets
## a copy of its sprite lying upside down on the water plane below the foot (src/fx/water_reflect.gdshader).
## The copy is masked to open water by a low-resolution mask of the area (built once from WaterFx), so
## it never shows on banks, decks or piers; it wobbles with the surface and fades with distance.
## Off on the "low" graphics preset (GameSettings quality "reflect").

const SHADER := preload("res://src/fx/water_reflect.gdshader")
const S := 1.0 / 32.0
const CELL := 8                       # mask resolution in map px
const REACH := 0.92                   # reflection length = sprite height * REACH
const MAX_STATIC := 400               # cap per area (performance on low-end phones)

var view: WorldView3D
var fx: WaterFx
var _mask_tex: ImageTexture
var _mats: Array = []                 # every ShaderMaterial, for the per-frame tint
var _actors := {}                     # Sprite3D instance id -> {mi, mat}
var _quad: QuadMesh
var count_static := 0
var _qa_off := OS.get_environment("SHOT_NOREFLECT") == "1"
var _near_cache := {}                 # 16 px cell -> water within reach (characters)


func setup(v: WorldView3D, water: WaterFx) -> WaterReflect:
	view = v
	fx = water
	_quad = QuadMesh.new()
	_quad.size = Vector2(1, 1)
	_build_mask()
	_build_static()
	return self


func _build_mask() -> void:
	var a: Dictionary = view.world.area
	var w := int(ceil(float(a.get("w", 1200)) / CELL))
	var h := int(ceil(float(a.get("h", 900)) / CELL))
	var img := Image.create(w, h, false, Image.FORMAT_L8)
	for y in h:
		for x in w:
			if fx.is_water(Vector2((x + 0.5) * CELL, (y + 0.5) * CELL)):
				img.set_pixel(x, y, Color(1, 1, 1))
	_mask_tex = ImageTexture.create_from_image(img)


func _material(tex: Texture2D) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = SHADER
	m.set_shader_parameter("albedo_tex", tex)
	m.set_shader_parameter("mask_tex", _mask_tex)
	m.set_shader_parameter("map_size", Vector2(float(view.world.area.get("w", 1200)), float(view.world.area.get("h", 900))))
	_mats.append(m)
	return m


## True when open water lies within the reflection's reach below a foot point.
func near_water(p: Vector2, w: float, reach: float) -> bool:
	var dy := 6.0
	while dy < reach:
		for dx in [-w * 0.3, 0.0, w * 0.3]:
			if fx.is_water(p + Vector2(dx, dy)):
				return true
		dy += 14.0
	return false


func _flat_basis(w: float, h: float) -> Basis:
	# flat on the water, texture top toward the camera (south): an upside-down copy below the foot
	return Basis(Vector3.RIGHT, -PI / 2.0) * Basis.from_scale(Vector3(w * S, -h * S, 1.0))


func _build_static() -> void:
	var groups := {}                  # texture path -> {tex, xfs}
	for holder in view._inst.keys():
		if not is_instance_valid(holder) or count_static >= MAX_STATIC:
			continue
		var s := holder.get_child(0) as Sprite2D
		if s == null or s.texture == null:
			continue
		var p: Vector2 = holder.position
		if Elevation.at(view.world.area, p.x, p.y) > 2.0:
			continue                  # only things standing at water level
		var w: float = s.texture.get_width() * s.scale.x
		var h: float = s.texture.get_height() * s.scale.y
		var reach := h * REACH
		if not near_water(p, w, minf(reach, 220.0)):
			continue
		var key := s.texture.resource_path
		if not groups.has(key):
			groups[key] = {"tex": s.texture, "xfs": []}
		var ctr := Vector3(p.x * S, 0.014, (p.y + reach * 0.5) * S)
		groups[key].xfs.append(Transform3D(_flat_basis(w, reach), ctr))
		count_static += 1
	for key in groups:
		var g: Dictionary = groups[key]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = _quad
		mm.instance_count = g.xfs.size()
		for i in g.xfs.size():
			mm.set_instance_transform(i, g.xfs[i])
		var mi := MultiMeshInstance3D.new()
		mi.multimesh = mm
		mi.material_override = _material(g.tex)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)


func _process(_delta: float) -> void:
	if view == null or view.env == null:
		return
	visible = bool(view._q.get("reflect", true)) and not _qa_off   # SHOT_NOREFLECT=1: QA before/after shots
	if not visible:
		return
	var e := view.env
	var tint := e.ambient_light_color * e.ambient_light_energy * 1.15 + view.sun.light_color * view.sun.light_energy * 0.75
	var t := Vector3(minf(tint.r, 1.25), minf(tint.g, 1.25), minf(tint.b, 1.25))
	for m in _mats:
		m.set_shader_parameter("tint", t)
	_update_actors()


## Characters: one reflection quad per standing (non-flat) character sprite, shown while the
## character is close to open water.
func _update_actors() -> void:
	var seen := {}
	for id in view._mirrors:
		var mr: Dictionary = view._mirrors[id]
		var root := instance_from_id(id) as Node2D
		if root == null or not mr.pivot.visible:
			continue
		var p := root.position
		var cell := Vector2i(int(p.x / 16.0), int(p.y / 16.0))
		if not _near_cache.has(cell):
			_near_cache[cell] = Elevation.at(view.world.area, p.x, p.y) <= 2.0 and near_water(p, 24.0, 96.0)
		var near: bool = _near_cache[cell]
		for sid in mr.sprites:
			var sp: Sprite3D = mr.sprites[sid]
			if sp.get_parent() != mr.pivot:
				continue              # flat sprites (contact shadow, rings) are not reflected
			seen[sid] = true
			var r: Dictionary = _actors.get(sid, {})
			if r.is_empty():
				var mi := MeshInstance3D.new()
				mi.mesh = _quad
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				add_child(mi)
				r = {"mi": mi, "mat": null, "tex": null}
				_actors[sid] = r
			var show := near and sp.visible and sp.texture != null
			r.mi.visible = show
			if not show:
				continue
			if r.tex != sp.texture:
				r.mat = _material(sp.texture)
				r.mi.material_override = r.mat
				r.tex = sp.texture
			var ts := Vector2(sp.texture.get_size())
			var reg: Rect2 = sp.region_rect if sp.region_enabled else Rect2(Vector2.ZERO, ts)
			var u := Vector4(reg.position.x / ts.x, reg.position.y / ts.y, reg.size.x / ts.x, reg.size.y / ts.y)
			if sp.flip_h:
				u = Vector4(u.x + u.z, u.y, -u.z, u.w)
			r.mat.set_shader_parameter("uv_rect", u)
			var w := reg.size.x * sp.pixel_size * sp.scale.x / S
			var h := reg.size.y * sp.pixel_size * sp.scale.y / S
			var up := sp.position.y / S - h * 0.5       # sprite bottom above the foot (map px)
			var reach := h * REACH
			r.mi.transform = Transform3D(_flat_basis(w, reach),
					Vector3((p.x + sp.position.x / S) * S, 0.016, (p.y + maxf(up, 0.0) + reach * 0.5) * S))
	for sid in _actors.keys():
		if not seen.has(sid):
			_actors[sid].mi.queue_free()
			_actors.erase(sid)
