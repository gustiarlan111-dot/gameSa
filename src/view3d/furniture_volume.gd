class_name FurnitureVolume
extends RefCounted
## U2a: real depth for room furniture without repainting it.
##
## Room pieces stay the painted 3/4-view sprites that lean back like every standing sprite, so the
## couple (who lean the same way) never sinks into a cabinet front. Behind each box-shaped piece a
## prism is added: two side faces and a top, all lying behind the sprite plane and cut along the
## camera's own view ray. From the gameplay camera the silhouette is pixel for pixel the painting;
## when the camera moves, perspective shows the side that faces the screen centre and, low on the
## screen, a sliver of the top, so the room reads as a diorama. The prism also casts a solid shadow.
##
## The block comes from the generator: props.json "vol" = [left, top, width, top depth, front height]
## in map pixels from the piece's foot (tools/worldgen/rooms_hd.py stand_up).

const SIDE_L := 0.8          # painted light comes from the top-left: the left side is the brighter one
const SIDE_R := 0.64
const TOP := 1.0
const MIN_DEPTH := 6.0
const MAX_DEPTH := 40.0
const INSET := 1.25          # map px inside the painted outline, where the front's own colours are
## Side normals lean up like the sprites' own (world_view_3d.gd _up_normal): the painting carries the
## shading, so a side takes the room's light like the front does and the vertex colour darkens it.
const SIDE_N_UP := 0.88


## Depth of the block in map px: what the painted top face implies (1.6 x its picture height, see
## docs/WORLD3D.md), at least a third of the width, and no deeper than the floor in front of the wall.
static func depth_for(vol: Array, room_space: float) -> float:
	var d := maxf(1.6 * float(vol[3]), 0.3 * float(vol[2]))
	var tall := float(vol[3]) + float(vol[4])
	return clampf(minf(d, minf(tall, room_space)), 0.0, MAX_DEPTH)


## The four corners of one side face (x in map px) and of the top: [F0, F1, B1, B0], where F lies on
## the sprite plane and B is `depth` behind it. Pure geometry so tests can check it.
static func side_quad(view, x: float, foot: Vector2, hb0: float, hb1: float, depth: float) -> Array:
	var p: float = WorldView3D.PITCH
	var s: float = WorldView3D.S
	var f0: Vector3 = view.stand(x, foot.y, hb0)
	var f1: Vector3 = view.stand(x, foot.y, hb1)
	var ray := Vector3(0, -sin(p), -cos(p)) * (depth * s / cos(p))
	return [f0, f1, f1 + ray, f0 + Vector3(0, 0, -depth * s)]


## Builds the prism for one standing room piece, or null when it has no block or too little room.
static func build(view, holder: Node2D, spr: Sprite2D, w: float, h: float, wall_y: float, mats: Dictionary) -> MeshInstance3D:
	var d: Dictionary = Data.props.get(str(holder.get_meta("type", "")), {})
	var vol: Array = d.get("vol", [])
	if vol.size() < 5 or spr.flip_h or w <= 0.0 or h <= 0.0:
		return null
	var foot := holder.position
	var depth := depth_for(vol, foot.y - wall_y - 2.0)
	if depth < MIN_DEPTH:
		return null
	var ox := float(vol[0])
	var bw := float(vol[2])
	var hb1 := -float(vol[1])                                  # block top, up the sprite from the foot
	var hb0 := hb1 - float(vol[3]) - float(vol[4])             # block bottom
	var hft := hb0 + float(vol[4])                             # where the front meets the painted top
	if hb0 < -0.5 or hb1 > h + 0.5 or bw < 8.0:
		return null
	var u := func(xm: float) -> float: return clampf(0.5 + xm / w, 0.0, 1.0)
	var v := func(hu: float) -> float: return clampf(1.0 - hu / h, 0.0, 1.0)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var xl := foot.x + ox
	var xr := xl + bw
	var ql := side_quad(view, xl, foot, hb0, hb1, depth)
	var qr := side_quad(view, xr, foot, hb0, hb1, depth)
	var vb: float = v.call(hb0 + 0.25)
	var vt: float = v.call(maxf(hb0 + 0.5, hft - INSET))
	_face(st, ql, Vector3(-sqrt(1.0 - SIDE_N_UP * SIDE_N_UP), SIDE_N_UP, 0), Color(SIDE_L, SIDE_L, SIDE_L),
		[Vector2(u.call(ox + INSET), vb), Vector2(u.call(ox + INSET), vt), Vector2(u.call(ox + INSET), vt), Vector2(u.call(ox + INSET), vb)])
	_face(st, qr, Vector3(sqrt(1.0 - SIDE_N_UP * SIDE_N_UP), SIDE_N_UP, 0), Color(SIDE_R, SIDE_R, SIDE_R),
		[Vector2(u.call(ox + bw - INSET), vb), Vector2(u.call(ox + bw - INSET), vt), Vector2(u.call(ox + bw - INSET), vt), Vector2(u.call(ox + bw - INSET), vb)])
	# the top only shows as a thin band low on the screen: one texel of the painted top (its inner
	# corner, clear of whatever stands on it) reads as the board's edge instead of stretched clutter
	var p: float = WorldView3D.PITCH
	var tt := Vector2(u.call(ox + INSET + 1.0), v.call(hb1 - minf(2.0, float(vol[3]) * 0.5)))
	_face(st, [ql[1], qr[1], qr[2], ql[2]], Vector3(0, cos(p), -sin(p)), Color(TOP, TOP, TOP), [tt, tt, tt, tt])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = material(spr.texture, mats)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	mi.name = "Vol_" + str(holder.get_meta("type", ""))
	return mi


## Godot draws clockwise triangles as the front, and with culling off it flips the normal of a back
## face, so each face is wound to be clockwise seen from the side its normal points to.
static func _face(st: SurfaceTool, q: Array, n: Vector3, c: Color, uv: Array) -> void:
	var a: Vector3 = q[0]
	var cw: bool = ((q[1] as Vector3) - a).cross((q[2] as Vector3) - a).dot(n) < 0.0
	for i in ([0, 1, 2, 0, 2, 3] if cw else [0, 2, 1, 0, 3, 2]):
		st.set_normal(n)
		st.set_color(c)
		st.set_uv(uv[i])
		st.add_vertex(q[i])


static func material(tex: Texture2D, mats: Dictionary) -> Material:
	var key := "vol|" + tex.resource_path
	if mats.has(key):
		return mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.vertex_color_use_as_albedo = true
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = 0.5
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS    # same as the sprite (K7 open)
	m.roughness = 0.9
	m.metallic_specular = 0.0
	# the sides sit behind the sprite plane only because the sprite leans: let them keep the room's light
	# instead of lying in their own front's shadow
	m.disable_receive_shadows = true
	mats[key] = m
	return m
