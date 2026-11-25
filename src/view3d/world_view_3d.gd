class_name WorldView3D
extends Node3D
## The game's 3D (HD-2D) picture. The 2D World keeps running the game exactly as before (movement,
## collision, NPCs, quests, doors, cutscenes, save) but no longer draws itself; this node mirrors it
## in 3D every frame:
##   ground tiles  -> textured planes;  props -> standing quads tilted back like HD-2D sprites (one
##   MultiMesh per texture), with box volumes behind shops and houses;  characters, quest items and
##   markers -> lit sprites copied from their 2D sprites;  lamps -> real point lights;  the clock ->
##   a sun that moves and casts shadows, moonlight at night, ambient from the day tint.
## The 2D effect layers (rain, petals, fireflies, cutscene effects) still draw in 2D: the viewport's
## canvas transform is set to match the 3D ground, so they land in the right place.

const S := 1.0 / 32.0                   # map pixels -> metres
const PITCH := deg_to_rad(38.0)         # camera looks down this much
const TILT := -(PI / 2.0 - PITCH) * 0.55  # standing sprites lean back toward the camera's view
const FOV := 32.0
const VOLUME := ["hd_shop_", "hd_house_", "hd_library", "hd_cafe", "hd_cottage"]

var world: World
var atmosphere: Atmosphere
var cam: Camera3D
var sun: DirectionalLight3D
var env: Environment
var _static: Node3D                     # rebuilt on every area change
var _dyn: Node3D                        # mirrored actors / extras
var _mirrors := {}                      # 2D root instance id -> {root, pivot, base, sprites{}}
var _rustle := {}                       # 2D prop holder -> [MultiMesh, index, Transform3D]
var _alts: Array = []                   # [{sprite2d, mesh, tex}]
var _lamps: Array = []                  # [{light, glow, crystal}]
var _player_light: OmniLight3D
var _occ: Array = []                   # standing props that could hide the couple: [pos2d, w, h]
var _occ_pitch := 0.0
var _key_light: OmniLight3D             # cutscenes: warm key light on the couple
var _rim_light: OmniLight3D             # cutscenes: cool light from behind for a rim
var _cam_target := Vector3.ZERO
var _snap := true
var _glow_tex: Texture2D
var _quad: QuadMesh
var _mats := {}
const SWAY3D := preload("res://src/fx/sway3d.gdshader")


func _ready() -> void:
	_quad = QuadMesh.new()
	_quad.size = Vector2.ONE
	_quad.center_offset = Vector3(0, 0.5, 0)       # quad's bottom edge sits on its foot point
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1)); g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.3, Color(1, 1, 1, 0.5))
	var gt := GradientTexture2D.new()
	gt.gradient = g; gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.5); gt.fill_to = Vector2(1.0, 0.5)
	gt.width = 128; gt.height = 128
	_glow_tex = gt
	var we := WorldEnvironment.new()
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 0.82
	env.glow_enabled = true
	env.glow_intensity = 0.4
	env.glow_bloom = 0.0
	env.glow_hdr_threshold = 1.05
	env.fog_enabled = true
	env.fog_density = 0.003
	env.fog_sky_affect = 0.0
	we.environment = env
	add_child(we)
	sun = DirectionalLight3D.new()
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	sun.directional_shadow_max_distance = 55.0
	sun.shadow_blur = 1.5
	sun.shadow_bias = 0.04
	add_child(sun)
	cam = Camera3D.new()
	cam.fov = FOV
	cam.near = 0.5
	cam.far = 200.0
	add_child(cam)
	cam.make_current()
	_player_light = OmniLight3D.new()
	_player_light.light_color = Color(1, 0.92, 0.8)
	_player_light.omni_range = 5.0
	add_child(_player_light)
	_key_light = OmniLight3D.new()
	_key_light.omni_range = 5.5
	_key_light.omni_attenuation = 1.4
	_key_light.visible = false
	add_child(_key_light)
	_rim_light = OmniLight3D.new()
	_rim_light.omni_range = 4.5
	_rim_light.light_color = Color(0.62, 0.74, 1.0)
	_rim_light.visible = false
	add_child(_rim_light)
	_dyn = Node3D.new(); _dyn.name = "Dynamic"; add_child(_dyn)
	world.area_entered.connect(func(_id): rebuild.call_deferred())
	world.camera.enabled = false
	for n in [world._ground, world._floor, world._sorted]:
		n.visible = false
	rebuild()


static func at(x: float, y: float, h := 0.0) -> Vector3:
	return Vector3(x * S, h, y * S)


## A point `h` map pixels up a standing (tilted) sprite whose foot is at (x, y).
func stand(x: float, y: float, h: float) -> Vector3:
	return Vector3(x * S, cos(_tilt) * h * S + _lift(y), y * S + sin(_tilt) * h * S)


## Rooms are painted as one picture in the classic 3/4 view, walls included. Indoors the camera
## looks straight down on that picture and everything lies flat on it, so the room keeps its painted
## look; small height steps by map y keep the old front-to-back order. Outdoors sprites stand up.
var _indoor := false
var _tilt := TILT
func _lift(y: float) -> float:
	return 0.02 + y / 4000.0 if _indoor else 0.0


# ------------------------------------------------------------------ static scene
func rebuild() -> void:
	if _static:
		_static.queue_free()
	_static = Node3D.new(); _static.name = "Area"; add_child(_static)
	for k in _mirrors.keys():
		_mirrors[k].pivot.queue_free(); _mirrors[k].base.queue_free()
	_mirrors.clear()
	_rustle.clear(); _alts.clear(); _lamps.clear()
	_indoor = bool(world.area.get("indoor", false))
	_tilt = -PI / 2.0 if _indoor else TILT
	_build_ground()
	_build_props()
	_build_lamps()
	if not _indoor:
		var wf := WaterFx.new().setup(world)
		if wf.active():
			_static.add_child(wf)
		else:
			wf.free()
	_snap = true


func _build_ground() -> void:
	var edge := Color(0.3, 0.42, 0.3)
	var first := true
	for s in world._ground.get_children():
		if not (s is Sprite2D) or s.texture == null or s.is_queued_for_deletion():
			continue
		var w: float = s.texture.get_width() * s.scale.x
		var h: float = s.texture.get_height() * s.scale.y
		var m := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(w * S, h * S)
		m.mesh = pm
		var mat := StandardMaterial3D.new()
		mat.albedo_texture = s.texture
		mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		mat.roughness = 0.95
		mat.albedo_color = Color(0.84, 0.84, 0.84)
		m.material_override = mat
		m.position = at(s.position.x + w / 2.0, s.position.y + h / 2.0)
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_static.add_child(m)
		if first:
			first = false
			var img: Image = s.texture.get_image()
			if img:
				img = img.duplicate()
				if img.is_compressed():
					img.decompress()
				img.resize(4, 4, Image.INTERPOLATE_BILINEAR)
				edge = img.get_pixel(0, 0).lerp(img.get_pixel(3, 3), 0.5)
	# everything beyond the map edge: a wide plane in the map's own ground colour
	var w := float(world.area.get("w", 960))
	var h := float(world.area.get("h", 640))
	var out := MeshInstance3D.new()
	var om := PlaneMesh.new()
	om.size = Vector2(w * S + 200, h * S + 200)
	out.mesh = om
	var omat := StandardMaterial3D.new()
	omat.albedo_color = edge * 0.8 if not world.area.get("indoor", false) else Color(0.08, 0.06, 0.08)
	omat.roughness = 1.0
	out.material_override = omat
	out.position = at(w / 2.0, h / 2.0, -0.03)
	out.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	out.visible = not world.area.get("indoor", false)
	_static.add_child(out)


func _material(tex: Texture2D, img: String, standing: bool) -> Material:
	var key := "%s|%s" % [img, standing]
	if _mats.has(key):
		return _mats[key]
	var sway: Material = world._sway_for(img) if standing and not _indoor else null
	if sway:
		var sm := ShaderMaterial.new()
		sm.shader = SWAY3D
		sm.set_shader_parameter("albedo_tex", tex)
		sm.set_shader_parameter("amp", float(sway.get_shader_parameter("amp")) * 1.4 * S)
		sm.set_shader_parameter("speed", sway.get_shader_parameter("speed"))
		var nm := "res://assets/" + img.get_base_dir() + "/n/" + img.get_file().replace("@2x.png", "_n.png")
		if ResourceLoader.exists(nm):
			sm.set_shader_parameter("normal_tex", load(nm))
			sm.set_shader_parameter("use_normal", true)
		_mats[key] = sm
		return sm
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = tex
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.5
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	mat.roughness = 0.88
	var np_ := "res://assets/" + img.get_base_dir() + "/n/" + img.get_file().replace("@2x.png", "_n.png")
	if standing and ResourceLoader.exists(np_):
		mat.normal_enabled = true
		mat.normal_texture = load(np_)
		mat.normal_scale = 0.7
	_mats[key] = mat
	return mat


func _prop_basis(w: float, h: float, standing: bool, skew := 0.0) -> Basis:
	var rot := Basis(Vector3.RIGHT, _tilt if standing else -PI / 2.0)
	var shear := Basis(Vector3(1, 0, 0), Vector3(-tan(skew), 1, 0), Vector3(0, 0, 1))
	return rot * shear * Basis.from_scale(Vector3(w * S, h * S, 1.0))


func _build_props() -> void:
	_occ.clear()
	var groups := {}                     # key -> {tex, img, standing, items: [[holder, xf]]}
	for holder in world._prop_nodes:
		if not is_instance_valid(holder) or holder.is_queued_for_deletion() or holder.get_child_count() == 0:
			continue
		var s := holder.get_child(0) as Sprite2D
		if s == null or s.texture == null:
			continue
		var img: String = holder.get_meta("img", s.texture.resource_path.trim_prefix("res://assets/"))
		var standing := not bool(holder.get_meta("floor", false))
		var ptype: String = holder.get_meta("type", "")
		var w: float = s.texture.get_width() * s.scale.x
		var h: float = s.texture.get_height() * s.scale.y
		var building := false
		for v in VOLUME:
			building = (building or ptype.begins_with(v)) and not _indoor
		var foot := at(holder.position.x, holder.position.y, _lift(holder.position.y) if standing else 0.012)
		if holder.has_meta("alt"):
			var mi := MeshInstance3D.new()
			mi.mesh = _quad
			mi.material_override = _material(s.texture, img, standing)
			mi.transform = Transform3D(_prop_basis(w, h, standing), foot)
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if standing else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_static.add_child(mi)
			_alts.append({"sprite": s, "mesh": mi, "tex": s.texture, "standing": standing, "foot": foot})
			continue
		if standing and not building and h > 36.0:
			_occ.append([holder.position, w, h])
		var b := Basis(Vector3.RIGHT, 0.0) * Basis.from_scale(Vector3(w * S, h * S, 1.0)) if building else _prop_basis(w, h, standing)
		var key := "%s|%s|%s" % [img, standing, building]
		if not groups.has(key):
			groups[key] = {"tex": s.texture, "img": img, "standing": standing, "items": []}
		groups[key].items.append([holder, Transform3D(b, foot)])
		if building:
			_add_volume(holder.position, s.texture, w, h)
	for key in groups:
		var gr: Dictionary = groups[key]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = _quad
		mm.instance_count = gr.items.size()
		var i := 0
		for it in gr.items:
			mm.set_instance_transform(i, it[1])
			_rustle[it[0]] = [mm, i, it[1]]
			i += 1
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.material_override = _material(gr.tex, gr.img, gr.standing)
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if gr.standing else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_static.add_child(mmi)
	# only foliage needs per-frame transforms
	var keep := {}
	for f in world.foliage:
		if _rustle.has(f.node):
			keep[f.node] = _rustle[f.node]
	_rustle = keep


## Shops and houses: a box behind the facade so the building has depth, side walls and a real shadow.
func _add_volume(foot2d: Vector2, tex: Texture2D, w: float, h: float) -> void:
	var depth := w * 0.4
	var wall := Color(0.72, 0.66, 0.6)
	var roof := Color(0.45, 0.35, 0.3)
	var img: Image = tex.get_image()
	if img:
		img = img.duplicate()
		if img.is_compressed():
			img.decompress()
		wall = img.get_pixel(int(img.get_width() * 0.2), int(img.get_height() * 0.75))
		roof = img.get_pixel(int(img.get_width() * 0.5), int(img.get_height() * 0.12))
	var b := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(w * 0.92 * S, h * 0.62 * S, depth * S)
	b.mesh = bm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = wall
	mat.roughness = 0.9
	b.material_override = mat
	var top := MeshInstance3D.new()
	var tm := BoxMesh.new()
	tm.size = Vector3(w * 0.96 * S, 0.25, depth * 1.04 * S)
	top.mesh = tm
	var rm := StandardMaterial3D.new()
	rm.albedo_color = roof
	top.material_override = rm
	top.position = Vector3(0, h * 0.31 * S, 0)
	b.add_child(top)
	b.position = at(foot2d.x, foot2d.y - depth / 2.0 - 2.0, h * 0.31 * S)
	_static.add_child(b)


func _build_lamps() -> void:
	for spot in world.light_spots:
		var crystal: bool = spot.kind == "crystal"
		var foot: Vector2 = spot.foot + Vector2(0, 8)
		var hh: float = foot.y - spot.pos.y
		var p := stand(foot.x, foot.y, hh)
		# a real light only where no other light is close: crowded crystals share one, which keeps
		# the per-object light limit free for the player's light and saves GPU time on phones
		var l := OmniLight3D.new()
		l.light_color = Color(0.62, 0.8, 1.0) if crystal else Color(1.0, 0.76, 0.46)
		l.omni_range = 4.0 if crystal else 5.5
		l.omni_attenuation = 1.2
		l.position = p + Vector3(0, 0, 0.35)
		var crowded := false
		for o in _lamps:
			if o.light.position.distance_to(l.position) < (6.0 if crystal else 3.0):
				crowded = true
				break
		if crowded:
			l.light_energy = 0.0
			l.visible = false
			l.set_meta("off", true)
		_static.add_child(l)
		var gl := Sprite3D.new()
		gl.texture = _glow_tex
		gl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		gl.shaded = false
		gl.no_depth_test = false
		gl.transparent = true
		gl.pixel_size = 1.6 / 128.0
		gl.position = p + Vector3(0, 0, 0.1)
		gl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var gm := StandardMaterial3D.new()
		gm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		gm.albedo_texture = _glow_tex
		gm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		gl.material_override = gm
		_static.add_child(gl)
		_lamps.append({"light": l, "glow": gl, "mat": gm, "crystal": crystal, "x": foot.x})


# ------------------------------------------------------------------ per frame
func _process(delta: float) -> void:
	if world == null or world.player == null:
		return
	_update_alts()
	_update_rustle()
	_update_mirrors()
	_update_light(delta)
	_update_camera(delta)


func _update_alts() -> void:
	for e in _alts:
		var s: Sprite2D = e.sprite
		if not is_instance_valid(s) or s.texture == e.tex:
			continue
		e.tex = s.texture
		var w: float = s.texture.get_width() * s.scale.x
		var h: float = s.texture.get_height() * s.scale.y
		e.mesh.material_override = _material(s.texture, s.texture.resource_path.trim_prefix("res://assets/"), e.standing)
		e.mesh.transform = Transform3D(_prop_basis(w, h, e.standing), e.foot)


func _update_rustle() -> void:
	for holder in _rustle:
		if not is_instance_valid(holder):
			continue
		var r: Array = _rustle[holder]
		var sk: float = holder.skew
		var moving := absf(sk) >= 0.0005
		if not moving and r.size() == 3:
			continue
		var base: Transform3D = r[2]
		if not moving:
			r[0].set_instance_transform(r[1], base)
			r.resize(3)
			continue
		var b := base.basis * Basis(Vector3(1, 0, 0), Vector3(-tan(sk) * 0.5, 1, 0), Vector3(0, 0, 1))
		r[0].set_instance_transform(r[1], Transform3D(b, base.origin))
		if r.size() == 3:
			r.append(true)


## Characters and quest items: copy each visible 2D sprite into a 3D sprite at the same place.
func _update_mirrors() -> void:
	var roots: Array = []
	for c in world._sorted.get_children():
		if c is Actor or c is Critter:
			roots.append(c)
	for c in world.extras.get_children():
		roots.append(c)
	var seen := {}
	for r in roots:
		if r.is_queued_for_deletion():
			continue
		var id: int = r.get_instance_id()
		seen[id] = true
		if not _mirrors.has(id):
			var pivot := Node3D.new(); pivot.rotation.x = _tilt
			var base := Node3D.new()
			_dyn.add_child(base); _dyn.add_child(pivot)
			_mirrors[id] = {"pivot": pivot, "base": base, "sprites": {}}
		var m: Dictionary = _mirrors[id]
		var foot := at(r.position.x, r.position.y)
		m.pivot.rotation.x = _tilt
		m.pivot.position = foot + Vector3(0, _lift(r.position.y) + 0.004, 0)
		m.base.position = foot + Vector3(0, _lift(r.position.y), 0)
		m.pivot.visible = r.visible
		m.base.visible = r.visible
		if r.visible:
			_mirror_sprites(r, r, Transform2D.IDENTITY, r.modulate, m)
	for id in _mirrors.keys():
		if not seen.has(id):
			_mirrors[id].pivot.queue_free(); _mirrors[id].base.queue_free()
			_mirrors.erase(id)


func _mirror_sprites(root: Node2D, node: Node, xf: Transform2D, mod: Color, m: Dictionary) -> void:
	for c in node.get_children():
		if not (c is Node2D):
			continue
		var n := c as Node2D
		var sid := n.get_instance_id()
		var vis := n.visible and not n.has_meta("skip3d")
		var cx := xf * n.transform
		var cm := mod * n.modulate
		if n is Sprite2D:
			var s := n as Sprite2D
			var sp: Sprite3D = m.sprites.get(sid)
			var flat := s.has_meta("flat")
			if sp == null:
				sp = Sprite3D.new()
				sp.centered = true
				sp.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD if not flat else SpriteBase3D.ALPHA_CUT_DISABLED
				sp.shaded = not flat
				sp.double_sided = true
				if flat:
					sp.rotation.x = -PI / 2.0
					sp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
					m.base.add_child(sp)
				else:
					sp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
					m.pivot.add_child(sp)
				m.sprites[sid] = sp
			sp.visible = vis and s.texture != null
			if sp.visible:
				sp.texture = s.texture
				sp.region_enabled = s.region_enabled
				sp.region_rect = s.region_rect
				sp.flip_h = s.flip_h
				sp.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST if s.texture_filter == CanvasItem.TEXTURE_FILTER_NEAREST else BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
				var r := s.get_rect()
				var ctr := cx * r.get_center()
				var sc := cx.get_scale()
				sp.pixel_size = S * absf(sc.x)
				sp.scale = Vector3(1.0, absf(sc.y) / maxf(0.0001, absf(sc.x)), 1.0)
				sp.modulate = cm * s.self_modulate
				if flat:
					sp.position = Vector3(ctr.x * S, 0.02, ctr.y * S)
				else:
					sp.position = Vector3(ctr.x * S, -ctr.y * S, 0.0)
					sp.rotation.z = -cx.get_rotation()
		if vis and n.get_child_count() > 0:
			_mirror_sprites(root, n, cx, cm, m)
		elif not vis:
			_hide_under(n, m)


func _hide_under(n: Node, m: Dictionary) -> void:
	for c in n.get_children():
		var sp: Sprite3D = m.sprites.get(c.get_instance_id())
		if sp:
			sp.visible = false
		_hide_under(c, m)


# ------------------------------------------------------------------ light and camera
func _starry() -> bool:
	return str(world.area.get("music", "")) == "star"


func _update_light(delta: float) -> void:
	var a := atmosphere
	var minute := float(a.minute)
	var t := clampf((minute - 360.0) / 750.0, 0.0, 1.0)
	var e := sin(PI * t)
	var rain := a.weather == "rain" and not a.indoor
	var cave := a.dark_cave()
	var day := not a.indoor and not a.realm and not cave and minute > 345 and minute < 1125
	var tint: Color = a.tint_mod
	var k := minf(1.0, delta * 3.0)
	# ambient follows the day tint (night blue, dusk warm); indoors stays brighter
	var amb := tint * Color(0.74, 0.77, 0.88)
	var amb_e := 0.8 if a.indoor else (0.5 if cave else (0.48 if day else 0.6))
	env.ambient_light_color = env.ambient_light_color.lerp(amb, k)
	env.ambient_light_energy = lerpf(env.ambient_light_energy, amb_e, k)
	var sky := Color(0.55, 0.72, 0.9).lerp(Color(0.95, 0.62, 0.48), clampf((1.0 - e) * 1.2, 0, 1)) * tint
	if a.realm and not a.indoor and not cave:
		amb = Color(0.5, 0.52, 0.86) if _starry() else Color(0.86, 0.74, 0.84)
		env.ambient_light_color = env.ambient_light_color.lerp(amb, k)
		env.ambient_light_energy = lerpf(env.ambient_light_energy, 0.36 if _starry() else 0.55, k)
		sky = Color(0.03, 0.04, 0.12) if _starry() else Color(0.6, 0.42, 0.5)
	if a.indoor or cave:
		sky = Color(0.008, 0.006, 0.012)
	env.background_color = sky
	env.fog_light_color = sky.lerp(Color(0.8, 0.85, 0.95) * tint, 0.4)
	env.fog_density = 0.006 if rain else 0.002
	env.fog_enabled = not _indoor
	env.glow_enabled = not day or rain or e < 0.35
	# sun by day (east in the morning, west at dusk), moon at night, a soft top light indoors
	var az := lerpf(-70.0, 70.0, t)
	var el := 14.0 + 56.0 * e
	var energy := 0.0
	var col := Color(1, 1, 1)
	if day:
		energy = (0.78 - 0.3 * e) * clampf(e * 3.0, 0.0, 1.0)
		col = Color(1.0, 0.95, 0.86).lerp(Color(1.0, 0.64, 0.4), clampf((1.0 - e) * 1.3, 0, 1))
		if rain:
			energy *= 0.15
		elif a.weather == "berawan":
			energy *= 0.55
	elif a.indoor:
		az = 15.0; el = 62.0; energy = 0.35; col = Color(1.0, 0.92, 0.82)
	elif a.realm and not a.indoor:
		# dream places keep their own light: starry evening on the star maps, a golden dusk elsewhere
		if _starry():
			az = -30.0; el = 48.0; energy = 0.4; col = Color(0.66, 0.74, 1.0)
		else:
			az = -55.0; el = 24.0; energy = 0.7; col = Color(1.0, 0.8, 0.62)
	elif not cave:
		az = 15.0; el = 66.0; energy = 0.22; col = Color(0.58, 0.68, 1.0)
	sun.rotation_degrees = Vector3(-el, az + 180.0, 0)
	sun.light_color = col
	sun.light_energy = lerpf(sun.light_energy, energy, k)
	sun.shadow_enabled = sun.light_energy > 0.08 and not _indoor
	var lamp_on: float = a.lamp_on
	for l in _lamps:
		var flick := 1.0 + 0.06 * sin(a.time * 2.0 + float(l.x))
		var on := (1.0 if l.crystal and cave else lamp_on) * flick
		l.light.light_energy = (1.6 if l.crystal else 2.4) * on
		l.light.visible = on > 0.02 and not l.light.has_meta("off")
		l.glow.visible = on > 0.02
		l.mat.albedo_color = (Color(0.62, 0.82, 1.0) if l.crystal else Color(1.0, 0.82, 0.55)) * Color(1, 1, 1, 0.55 * minf(1.0, on))
	var pl := world.player
	_player_light.position = stand(pl.position.x, pl.position.y, 40) + Vector3(0, 0, 0.6)
	_player_light.light_energy = 1.8 if cave else 0.6 * float(a.night)
	_player_light.omni_range = 7.0 if cave else 4.0
	_player_light.visible = _player_light.light_energy > 0.02
	_update_key_light()


## Cutscene lighting: a warm key from the camera side and a cool rim from behind the subject,
## stronger at night so faces stay readable, fading in and out with the film look.
func _update_key_light() -> void:
	var c := world.cine
	var f: float = c.film * c.key if c != null else 0.0
	_key_light.visible = f > 0.02 and not _indoor
	_rim_light.visible = _key_light.visible
	if not _key_light.visible:
		return
	var a := atmosphere
	var dim := clampf(0.55 + 0.9 * float(a.night) + (0.6 if a.dark_cave() else 0.0), 0.0, 1.6)
	var foc := world.player.position
	if world.partner.visible:
		foc = (foc + world.partner.position) * 0.5
	var yaw := deg_to_rad(c.view_yaw())
	var side := Vector3(sin(yaw), 0, cos(yaw))
	_key_light.position = stand(foc.x, foc.y, 52) + side * 1.6 + Vector3(-0.9, 0.4, 0)
	_key_light.light_color = c.key_color
	_key_light.light_energy = 0.9 * dim * f
	_rim_light.position = stand(foc.x, foc.y, 60) - side * 1.3 + Vector3(0.7, 0.3, 0)
	_rim_light.light_energy = 0.75 * dim * f


func _clear_pitch() -> float:
	var foc := world.player.position
	if world.partner.visible:
		foc = (foc + world.partner.position) * 0.5
	var need := 0.0
	for o in _occ:
		var dy: float = o[0].y - foc.y
		if dy < 6.0 or dy > 420.0 or absf(o[0].x - foc.x) > o[1] * 0.5 + 26.0:
			continue
		var top: float = o[2] * S * cos(TILT) - 0.6      # metres above the couple's shoulders
		if top > 0.0:
			need = maxf(need, atan2(top, dy * S) + deg_to_rad(10.0))
	return minf(need, deg_to_rad(68.0))


func _update_camera(delta: float) -> void:
	var vp := get_viewport().get_visible_rect().size
	var c2 := world.camera
	var view_h: float = vp.y / maxf(0.01, c2.zoom.y)
	var view_w: float = view_h * vp.x / vp.y
	var aw := float(world.area.get("w", 960))
	var ah := float(world.area.get("h", 640))
	var tgt: Vector2 = c2.position
	tgt.x = aw / 2.0 if aw <= view_w else clampf(tgt.x, view_w / 2.0, aw - view_w / 2.0)
	tgt.y = ah / 2.0 if ah <= view_h else clampf(tgt.y, view_h * (0.5 if _indoor else 0.42), ah - view_h * 0.5)
	var dist := 1.3 * view_h * S * sin(PITCH) / (2.0 * tan(deg_to_rad(FOV) / 2.0))
	var cine := world.cine
	var film: float = cine.film if cine != null else 0.0
	var pitch := deg_to_rad(cine.view_pitch()) if cine != null else PITCH
	if film > 0.001 and not _indoor:
		# a low film camera must not put a bush or tree between the lens and the couple's faces:
		# raise the angle just enough to look over anything standing in front of them
		var need := _clear_pitch()
		_occ_pitch = lerpf(_occ_pitch, need, 1.0 - exp(-delta * 4.0)) if not _snap else need
		pitch = maxf(pitch, _occ_pitch)
	var yaw := deg_to_rad(cine.view_yaw()) if cine != null else 0.0
	# film shots look at the characters' chest rather than their feet
	var want := at(tgt.x, tgt.y, 0.6) + Vector3(0, 0.55 * film, 0)
	var cine_cam := cine != null and cine.cam_active
	if _snap or cine_cam:
		_cam_target = want
		_snap = false
	else:
		_cam_target = _cam_target.lerp(want, 1.0 - exp(-delta * 7.0))
	if _indoor:
		cam.projection = Camera3D.PROJECTION_ORTHOGONAL
		cam.size = view_h * S
		cam.position = _cam_target + Vector3(0, 40.0, 0)
		cam.look_at(_cam_target, Vector3(0, 0, -1))
	else:
		cam.projection = Camera3D.PROJECTION_PERSPECTIVE
		var hz := cos(pitch) * dist
		cam.position = _cam_target + Vector3(sin(yaw) * hz, sin(pitch) * dist, cos(yaw) * hz)
		cam.fov = lerpf(FOV, FOV - 4.0, film)       # a slightly longer lens in cutscenes
		cam.look_at(_cam_target, Vector3.UP)
	# 2D overlay alignment: an affine map from map pixels to the screen, fitted around the view centre
	var c := Vector2(_cam_target.x / S, _cam_target.z / S)
	var p0 := cam.unproject_position(at(c.x, c.y))
	var px := cam.unproject_position(at(c.x + 100.0, c.y))
	var py := cam.unproject_position(stand(c.x, c.y + 100.0, 0.0)).lerp(cam.unproject_position(stand(c.x, c.y, -100.0)), 0.5)
	var ax := (px - p0) / 100.0
	var ay := (py - p0) / 100.0
	var xf := Transform2D(ax, ay, Vector2.ZERO)
	xf.origin = p0 - xf.basis_xform(c)
	get_viewport().canvas_transform = xf
