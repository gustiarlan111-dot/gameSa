extends Node
## U3b tool (not in the APK): renders Arland and Sofia TOGETHER from their GLBs, for the moments a
## pair of separate sprites cannot show with rigless models: walking hand in hand and a hug.
## Same camera, rig shader and scale as render_sheets.gd; Sofia is scaled so her height matches her
## single sprites (126 vs 134 px). Frames go to user://charframes/couple_<kind>_<dir>_<frame>.png;
## tools/char_sheets.py --couple packs them into assets/characters/couple/*@2x.png.
## Dirs: 0 down (toward the camera), 1 left, 2 right, 3 up.
## Run: xvfb-run godot --path . --rendering-driver opengl3 tests/charrender/render_couple.tscn
const FW := 640
const FH := 576
const PITCH := 10.0
const DIR_YAW := [0.0, -50.0, 50.0, 180.0]     # side walks at 50°: both stay visible
const HUG_YAW := [0.0, -38.0, 38.0, 180.0]      # the hug reads best close to front/back
const SOFIA_K := 0.9325            # (126 / 134) * (Arland raw height 475 / Sofia raw height 479)
var SEP := float(OS.get_environment("SEP")) if OS.get_environment("SEP") != "" else 0.31                  # half distance between the two in hand-holding (model units)
const WALK_N := 12

var vp: SubViewport
var holder: Node3D
var arland: Node3D
var sofia: Node3D
var ma: ShaderMaterial
var ms: ShaderMaterial


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://charframes"))
	vp = SubViewport.new()
	vp.size = Vector2i(FW, FH)
	vp.transparent_bg = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.msaa_3d = Viewport.MSAA_4X
	add_child(vp)
	var we := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	we.environment = env
	vp.add_child(we)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = 2.42
	var d := 10.0
	var p := deg_to_rad(PITCH)
	cam.position = Vector3(0, 1.0 + sin(p) * d, cos(p) * d)
	vp.add_child(cam)
	cam.look_at(Vector3(0, 1.0, 0), Vector3.UP)
	holder = Node3D.new()
	vp.add_child(holder)
	arland = _load("res://assets/characters/arland/model/Arland.glb")
	sofia = _load("res://assets/characters/sofia/model/Sofia.glb")
	sofia.scale = Vector3.ONE * SOFIA_K
	ma = _mat(arland); ms = _mat(sofia)
	var only := OS.get_environment("KIND_ONLY")
	for kind in ["hand_idle", "hand_walk", "hug"]:
		if only == "" or only == kind:
			await _render(kind)
	print("RENDER DONE")
	get_tree().quit()


func _load(path: String) -> Node3D:
	var pivot := Node3D.new()
	holder.add_child(pivot)
	pivot.add_child((load(path) as PackedScene).instantiate())
	return pivot


func _mat(who: Node3D) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = preload("res://tests/charrender/walk_rig.gdshader")
	for mi in who.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).material_override = m
	return m


func _reset(m: ShaderMaterial) -> void:
	for k in ["phase", "swing", "arm", "knee", "breathe", "l_fwd", "r_fwd", "l_up", "r_up", "bow", "sit"]:
		m.set_shader_parameter(k, 0.0)
	m.set_shader_parameter("arm_lk", 1.0); m.set_shader_parameter("arm_rk", 1.0)


func _render(kind: String) -> void:
	var n := WALK_N if kind == "hand_walk" else 2
	for dir in 4:
		holder.rotation_degrees.y = DIR_YAW[dir]
		for f in n:
			_reset(ma); _reset(ms)
			if kind == "hug":
				# facing each other, Sofia's head against Arland's shoulder; arms forward disappear
				# into the other's body, which reads as an embrace with these rigless models
				# Sofia faces Arland with her head against his chest, his arms go round her (hidden
				# behind her body): reads as an embrace even with arms fused to the body
				holder.rotation_degrees.y = HUG_YAW[dir]
				arland.position = Vector3(-0.12, 0, -0.1); arland.rotation_degrees.y = 14.0
				sofia.position = Vector3(0.26, 0, 0.13); sofia.rotation_degrees.y = 214.0
				for m in [ma, ms]:
					m.set_shader_parameter("l_fwd", deg_to_rad(22.0)); m.set_shader_parameter("r_fwd", deg_to_rad(22.0))
					m.set_shader_parameter("breathe", 1.0 if f == 0 else -1.0)
				ma.set_shader_parameter("bow", deg_to_rad(9.0)); ms.set_shader_parameter("bow", deg_to_rad(15.0))
			else:
				# side by side, Sofia on Arland's right; the inner hands reach out and meet
				arland.position = Vector3(SEP, 0, 0); arland.rotation_degrees.y = 0.0
				sofia.position = Vector3(-SEP, 0, 0.12); sofia.rotation_degrees.y = 0.0
				ma.set_shader_parameter("r_up", deg_to_rad(10.0)); ma.set_shader_parameter("r_fwd", deg_to_rad(16.0)); ma.set_shader_parameter("arm_rk", 0.0)
				ms.set_shader_parameter("l_up", deg_to_rad(10.0)); ms.set_shader_parameter("l_fwd", deg_to_rad(16.0)); ms.set_shader_parameter("arm_lk", 0.0)
				if kind == "hand_walk":
					for m in [ma, ms]:
						m.set_shader_parameter("phase", TAU * f / n)
						m.set_shader_parameter("swing", deg_to_rad(24.0))
						m.set_shader_parameter("arm", deg_to_rad(30.0))
						m.set_shader_parameter("knee", deg_to_rad(36.0))
				else:
					for m in [ma, ms]:
						m.set_shader_parameter("breathe", 1.0 if f == 0 else -1.0)
			await RenderingServer.frame_post_draw
			await RenderingServer.frame_post_draw
			vp.get_texture().get_image().save_png("user://charframes/couple_%s_%d_%02d.png" % [kind, dir, f])
		print(kind, " dir ", dir, " done")
