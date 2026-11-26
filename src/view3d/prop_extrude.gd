class_name PropExtrude
extends RefCounted
## U2b: real thickness for solid outdoor props (rocks, posts, benches, fences, planters, lanterns,
## crates, stalls...) without repainting them.
##
## tools/extrude_u2b.py traces each sprite's outer contour and stores it in props.json "ext":
## {"d": depth, "p": [[x, hu, s, sx, sh], ...]} (map px from the foot, counter-clockwise). Every
## contour edge is pushed back by `d` behind the sprite plane. A point goes straight back on the
## ground (s = 0) or along the gameplay camera's view ray (s = 1); the tool picks s so that, from the
## gameplay camera, each back point still lands on the painting. The picture is unchanged; when the
## camera moves (walking, cutscenes, the screen edges) the sides and tops show, lit by the real sun,
## and the prop casts a solid shadow. Like the room prisms (FurnitureVolume) everything lies behind
## the sprite plane, so a character in front of a prop is never cut by it.
##
## One mesh per prop type, shared by all its instances through a MultiMesh in WorldView3D.

static var _meshes := {}                 # prop type -> ArrayMesh (built once per session)
static var _mats := {}                   # texture path -> material


static func has(ptype: String) -> bool:
	var d: Dictionary = Data.props.get(ptype, {})
	return d.has("ext") and (d.ext.get("p", []) as Array).size() >= 3


## The back offset of a contour point (metres, relative to its front point): `s` of the way from
## straight back on the ground to along the view ray, `depth` map px deep.
static func back(depth: float, s: float) -> Vector3:
	var p := WorldView3D.PITCH
	var flat := Vector3(0, 0, -depth * WorldView3D.S)
	var ray := Vector3(0, -sin(p), -cos(p)) * (depth * WorldView3D.S / cos(p))
	return flat.lerp(ray, clampf(s, 0.0, 1.0))


## A point on the leaning sprite plane, relative to the foot (metres).
static func front(x: float, hu: float) -> Vector3:
	var t := WorldView3D.TILT
	return Vector3(x * WorldView3D.S, cos(t) * hu * WorldView3D.S, sin(t) * hu * WorldView3D.S)


static func mesh_for(ptype: String, w: float, h: float) -> ArrayMesh:
	var key := "%s|%d|%d" % [ptype, int(w), int(h)]
	if _meshes.has(key):
		return _meshes[key]
	var ext: Dictionary = Data.props[ptype].ext
	var pts: Array = ext.p
	var depth := float(ext.d)
	var up := Vector3(0, cos(WorldView3D.TILT), sin(WorldView3D.TILT))
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := pts.size()
	var quads := 0
	for i in n:
		var a: Array = pts[i]
		var b: Array = pts[(i + 1) % n]
		if float(a[1]) < 1.0 and float(b[1]) < 1.0:
			continue                                   # the edge along the ground
		var fa := front(a[0], a[1]); var fb := front(b[0], b[1])
		var ba := fa + back(depth, a[2]); var bb := fb + back(depth, b[2])
		# outward in the sprite plane (counter-clockwise contour: outward is to the right of the edge)
		var dx := float(b[0]) - float(a[0]); var dh := float(b[1]) - float(a[1])
		var out := (Vector3.RIGHT * dh - up * dx).normalized()
		var nrm := (fb - fa).cross((ba + bb) * 0.5 - (fa + fb) * 0.5).normalized()
		if nrm.dot(out) < 0.0:
			nrm = -nrm
		var ua := Vector2(0.5 + float(a[3]) / w, 1.0 - float(a[4]) / h)
		var ub := Vector2(0.5 + float(b[3]) / w, 1.0 - float(b[4]) / h)
		_quad(st, [fa, fb, bb, ba], [ua, ub, ub, ua], nrm)
		quads += 1
	var m: ArrayMesh = st.commit() if quads > 0 else ArrayMesh.new()
	_meshes[key] = m
	return m


## Godot draws clockwise triangles as the front, and with culling off it flips a back face's normal:
## wind every face clockwise as seen from the side its normal points to.
static func _quad(st: SurfaceTool, q: Array, uv: Array, n: Vector3) -> void:
	var a: Vector3 = q[0]
	var cw: bool = ((q[1] as Vector3) - a).cross((q[2] as Vector3) - a).dot(n) < 0.0
	for i in ([0, 1, 2, 0, 2, 3] if cw else [0, 2, 1, 0, 3, 2]):
		st.set_normal(n)
		st.set_uv(uv[i])
		st.add_vertex(q[i])


static func material(tex: Texture2D) -> Material:
	var key := tex.resource_path
	if _mats.has(key):
		return _mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = 0.5
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS    # same as the sprites (K7 open)
	m.roughness = 0.92
	m.metallic_specular = 0.0
	# the sides sit behind the sprite plane only because sprites lean: keep them out of their own
	# front's shadow (same reason as FurnitureVolume)
	m.disable_receive_shadows = true
	_mats[key] = m
	return m


## Total triangles of one prop type's extrusion (QA / tests).
static func triangles(ptype: String, w: float, h: float) -> int:
	var m := mesh_for(ptype, w, h)
	if m.get_surface_count() == 0:
		return 0
	return (m.surface_get_arrays(0)[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
