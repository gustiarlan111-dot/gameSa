extends Node3D
## HD-2D style 3D prototype (for comparison with the 2.5D layer). Builds any area from maps.json in
## 3D: the HD ground tiles become a ground plane, every prop stands up as a lit, shadow-casting quad
## (tilted to face the camera like HD-2D sprites, with its generated normal map), shop/house fronts get
## a box volume behind them, the player is a billboard sprite. Perspective camera, real sun with
## shadows that follow the clock, lamp lights at night, fog, and the tilt-shift/bloom screen pass.
## Run:  godot --path . res://src/proto3d/proto3d.tscn -- --area jalan_kota --at 600,500 --minute 960
##       [--out shot.png --frames 90]   (WASD / arrows walk, Shift runs)

const S := 1.0 / 32.0            # world units -> metres
const PITCH := deg_to_rad(38.0)  # camera look-down angle; sprites tilt back the same way
const VOLUME := ["hd_shop_", "hd_house_", "hd_library", "hd_cafe", "hd_cottage"]

const AREAS := [["Jalan Kota", "jalan_kota", Vector2(600, 420)], ["Plaza", "plaza", Vector2(1150, 600)],
		["Perumahan", "perumahan", Vector2(678, 420)], ["Hutan", "hutan_bisik", Vector2(1470, 1520)]]
const TIMES := [["Pagi", 450], ["Siang", 720], ["Sore", 990], ["Malam", 1230]]
static var sel := {}             # area/minute picked in the in-game menu, kept across reloads

var area: Dictionary
var area_id := "jalan_kota"
var pos := Vector2(600, 500)
var minute := 960
var out := ""
var frames := 90
var _f := 0
var cam: Camera3D
var sun: DirectionalLight3D
var env: Environment
var player: Sprite3D
var _sheet: Texture2D
var _k := 2
var _anim := 0.0
var _dir := 0


func _ready() -> void:
	var a := OS.get_cmdline_user_args()
	for i in a.size():
		match a[i]:
			"--area": area_id = a[i + 1]
			"--at": pos = Vector2(float(a[i + 1].split(",")[0]), float(a[i + 1].split(",")[1]))
			"--minute": minute = int(a[i + 1])
			"--menu": sel = {}
			"--out": out = a[i + 1]
			"--frames": frames = int(a[i + 1])
	if out == "" and not sel.is_empty():
		area_id = sel.area; pos = sel.pos; minute = sel.minute
	area = Data.area(area_id)
	_build_env()
	_build_ground()
	_build_props()
	_build_player()
	_build_post()
	_place_camera(true)
	if out == "":
		_build_menu()


## Small menu for trying the prototype on a phone: area, time of day, back to the title. Drag
## anywhere else on the screen to walk.
func _build_menu() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 3
	add_child(layer)
	var bar := HBoxContainer.new()
	bar.position = Vector2(16, 12)
	bar.add_theme_constant_override("separation", 8)
	layer.add_child(bar)
	for a in AREAS:
		var b := UiTheme.button(a[0], 16, a[1] == area_id)
		b.pressed.connect(func(): sel = {"area": a[1], "pos": a[2], "minute": minute}; get_tree().reload_current_scene())
		bar.add_child(b)
	var sp := Control.new(); sp.custom_minimum_size = Vector2(18, 0); bar.add_child(sp)
	for t in TIMES:
		var b := UiTheme.button(t[0], 16, absi(int(t[1]) - minute) < 120)
		b.pressed.connect(func(): sel = {"area": area_id, "pos": pos, "minute": t[1]}; get_tree().reload_current_scene())
		bar.add_child(b)
	var back := UiTheme.button("Kembali", 16)
	back.position = Vector2(get_viewport().get_visible_rect().size.x - 130, 12)
	back.pressed.connect(func(): get_tree().change_scene_to_file("res://src/main.tscn"))
	layer.add_child(back)
	var note := UiTheme.label("Prototipe 3D (HD-2D) · geser layar untuk berjalan", 15, Color(1, 1, 1, 0.85), "body")
	note.position = Vector2(16, get_viewport().get_visible_rect().size.y - 34)
	layer.add_child(note)


var _touch_from := Vector2.ZERO
var _touch_vec := Vector2.ZERO
var _touching := false


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventScreenTouch:
		_touching = ev.pressed
		_touch_from = ev.position
		if not ev.pressed:
			_touch_vec = Vector2.ZERO
	elif ev is InputEventScreenDrag and _touching:
		var d: Vector2 = ev.position - _touch_from
		_touch_vec = d / 60.0 if d.length() < 60.0 else d.normalized()


func _w(x: float, y: float, h := 0.0) -> Vector3:
	return Vector3(x * S, h, y * S)


func _build_env() -> void:
	var we := WorldEnvironment.new()
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	var t := clampf((minute - 360.0) / 750.0, 0.0, 1.0)
	var e := sin(PI * t)
	var night := minute < 330 or minute > 1140
	env.background_color = Color(0.05, 0.07, 0.14) if night else Color(0.55, 0.72, 0.9).lerp(Color(0.95, 0.6, 0.45), clampf((1.0 - e) * 1.2, 0, 1))
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.25, 0.3, 0.5) if night else Color(0.62, 0.68, 0.8)
	env.ambient_light_energy = 0.45 if night else 0.5
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 0.88
	env.glow_enabled = true
	env.glow_intensity = 0.35
	env.glow_bloom = 0.08
	env.glow_hdr_threshold = 1.1
	env.fog_enabled = true
	env.fog_light_color = env.background_color.lerp(Color(0.8, 0.85, 0.95), 0.4)
	env.fog_density = 0.0035
	env.fog_sky_affect = 0.0
	we.environment = env
	add_child(we)
	sun = DirectionalLight3D.new()
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	sun.directional_shadow_max_distance = 60.0
	sun.shadow_blur = 1.5
	var az := lerpf(-70.0, 70.0, t)                      # east in the morning, west at dusk
	var el := 12.0 + 58.0 * e
	if night:
		az = 20.0; el = 50.0
		sun.light_color = Color(0.55, 0.65, 1.0); sun.light_energy = 0.25
	else:
		sun.light_color = Color(1.0, 0.95, 0.85).lerp(Color(1.0, 0.62, 0.38), clampf((1.0 - e) * 1.3, 0, 1))
		sun.light_energy = 0.95
	sun.rotation_degrees = Vector3(-el, az + 180.0, 0)
	add_child(sun)


func _build_ground() -> void:
	var tiles: Array = area.get("tiles", [])
	if tiles.is_empty():
		tiles = [{"image": area.image, "x": 0, "y": 0, "w": area.w, "h": area.h}]
	for t in tiles:
		var m := MeshInstance3D.new()
		var pm := PlaneMesh.new()
		pm.size = Vector2(t.w * S, t.h * S)
		m.mesh = pm
		var mat := StandardMaterial3D.new()
		mat.albedo_texture = load("res://assets/" + t.image)
		mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		mat.roughness = 0.95
		mat.albedo_color = Color(0.86, 0.86, 0.86)
		m.material_override = mat
		m.position = _w(t.x + t.w / 2.0, t.y + t.h / 2.0)
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(m)


func _prop_material(tex: Texture2D, img: String) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = tex
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.5
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	mat.roughness = 0.85
	var np_ := "res://assets/" + img.get_base_dir() + "/n/" + img.get_file().replace("@2x.png", "_n.png")
	if ResourceLoader.exists(np_):
		mat.normal_enabled = true
		mat.normal_texture = load(np_)
		mat.normal_scale = 0.8
	return mat


func _build_props() -> void:
	var mats := {}
	for p in area.get("props", []):
		var d: Dictionary = Data.props.get(p.type, {})
		if d.is_empty() or not ResourceLoader.exists("res://assets/" + d.image):
			continue
		var tex: Texture2D = load("res://assets/" + d.image)
		var k := Data.prop_scale(d)
		var w := tex.get_width() * k
		var h := tex.get_height() * k
		if not mats.has(d.image):
			mats[d.image] = _prop_material(tex, d.image)
		var floor_layer: bool = d.get("layer", "sort") == "floor"
		var q := MeshInstance3D.new()
		var qm := QuadMesh.new()
		q.mesh = qm
		q.material_override = mats[d.image]
		if floor_layer:                                    # bridges, rugs: lie flat on the ground
			qm.size = Vector2(w * S, h * S)
			q.rotation.x = -PI / 2.0
			q.position = _w(p.x, p.y - h / 2.0, 0.01)
			q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		else:
			# stand up, tilted back toward the camera so the drawn 3/4 view is not squashed
			var tall := h
			qm.size = Vector2(w * S, tall * S)
			qm.center_offset = Vector3(0, tall * S / 2.0, 0)
			var building := false
			for v in VOLUME:
				building = building or String(p.type).begins_with(v)
			q.rotation.x = 0.0 if building else -(PI / 2.0 - PITCH) * 0.55
			q.position = _w(p.x, p.y)
		add_child(q)
		for v in VOLUME:
			if String(p.type).begins_with(v):
				_add_volume(p, d, w, h)
				break
		if String(d.image).contains("lamp") or String(d.image).contains("lantern"):
			var l := OmniLight3D.new()
			l.light_color = Color(1.0, 0.78, 0.48)
			l.omni_range = 5.0
			l.light_energy = 2.2 if (minute < 330 or minute > 1080) else 0.0
			l.position = _w(p.x, p.y, h * S * 0.8)
			add_child(l)


## Shops and houses: a box behind the facade so the building has depth, side walls and a real shadow.
func _add_volume(p: Dictionary, d: Dictionary, w: float, h: float) -> void:
	var depth := w * 0.4
	var img: Image = (load("res://assets/" + d.image) as Texture2D).get_image()
	var wall := Color(0.72, 0.66, 0.6)
	var roof := Color(0.45, 0.35, 0.3)
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
	var top := MeshInstance3D.new()                     # roof slab in the roof colour
	var tm := BoxMesh.new()
	tm.size = Vector3(w * 0.96 * S, 0.25, depth * 1.04 * S)
	top.mesh = tm
	var rm := StandardMaterial3D.new()
	rm.albedo_color = roof
	top.material_override = rm
	top.position = Vector3(0, h * 0.31 * S, 0)
	b.add_child(top)
	b.position = _w(p.x, p.y - depth / 2.0 - 2.0, h * 0.31 * S)
	add_child(b)


func _build_player() -> void:
	player = Sprite3D.new()
	for n in ["walk_8dir_v53@2x", "walk_8dir_v53"]:
		var path := "res://assets/characters/sofia/%s.png" % n
		if ResourceLoader.exists(path):
			_sheet = load(path); _k = 2 if n.ends_with("@2x") else 1
			break
	player.texture = _sheet
	player.region_enabled = true
	player.pixel_size = S / _k
	player.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	player.shaded = true
	player.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	player.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	player.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	player.centered = true
	player.offset = Vector2(0, 72 * _k / 2.0)
	add_child(player)
	_set_frame()


func _set_frame() -> void:
	var col := int(_anim) % 6 if _anim > 0.0 else 0
	var row: int = [0, 2, 6, 4][_dir]
	player.region_rect = Rect2(col * 48 * _k, row * 72 * _k, 48 * _k, 72 * _k)
	player.position = _w(pos.x, pos.y)


func _build_post() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var r := ColorRect.new()
	r.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var m := ShaderMaterial.new()
	m.shader = preload("res://src/fx/post25d.gdshader")
	m.set_shader_parameter("bloom", 0.15)
	m.set_shader_parameter("vignette", 0.3)
	r.material = m
	layer.add_child(r)
	cam = Camera3D.new()
	cam.fov = 32.0
	add_child(cam)


func _place_camera(snap: bool) -> void:
	var target := _w(pos.x, pos.y, 0.8)
	var dist := 20.0
	var want := target + Vector3(0, sin(PITCH) * dist, cos(PITCH) * dist)
	cam.position = want if snap else cam.position.lerp(want, 0.12)
	cam.look_at(target, Vector3.UP)


func _process(delta: float) -> void:
	var v := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if _touch_vec.length() > 0.2:
		v = _touch_vec
	if v.length() > 0.1:
		var speed := 176.0 if Input.is_key_pressed(KEY_SHIFT) else 112.0
		var np_ := pos + v * speed * delta
		if not Data.blocked(area, np_.x, np_.y):
			pos = np_
		_dir = 1 if v.x < -0.5 else 2 if v.x > 0.5 else 3 if v.y < 0 else 0
		_anim += delta * 10.0
	else:
		_anim = 0.0
	_set_frame()
	_place_camera(false)
	_f += 1
	if out != "" and _f == frames:
		get_viewport().get_texture().get_image().save_png(out)
		get_tree().quit()
