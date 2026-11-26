extends Node
## V8.3 tool (not in the APK): renders Arland/Sofia GLBs into the game's 8-direction sheets.
## Writes raw frames to user://charframes/<char>_<kind>_<row>_<frame>.png (4x supersampled);
## tools/char_sheets.py downsamples, outlines and packs them into assets/characters/<char>/*@2x.png.
## Rows follow Actor.facing8: 0 down, 1 down-left, 2 left, 3 up-left, 4 up, 5 up-right, 6 right, 7 down-right.
## Run: xvfb-run godot --path . --rendering-driver opengl3 tests/charrender/render_sheets.tscn
const CHARS := {"arland": "res://assets/characters/arland/model/Arland.glb", "sofia": "res://assets/characters/sofia/model/Sofia.glb"}
const FW := 384
const FH := 576
const PITCH := 10.0
const KINDS := {"idle": 12, "walk": 24}
# Actor.POSES order; each: [frame0, frame1] of {param: degrees}. Columns: dir (down, left, right, up) * 2 + frame.
# Arms are fused to the body in these rigless models, so arm gestures stay small (<= 22°, the
# range that reads cleanly in the walk); overhead gestures become body language instead.
const POSES := [
	["sit", {"sit": 1.0}, {"sit": 1.0, "breathe": 1.0}],
	["wave", {"r_fwd": 16, "breathe": 1.0}, {"r_fwd": 22, "breathe": -1.0}],
	["give", {"l_fwd": 22, "r_fwd": 22, "bow": 6}, {"l_fwd": 22, "r_fwd": 22, "bow": 8}],
	["reach", {"r_fwd": 22, "bow": 8}, {"r_fwd": 22, "bow": 10}],
	["bow", {"bow": 18}, {"bow": 18}],                     # chibi head: more would leave the frame
	["hold_l", {"l_fwd": 12}, {"l_fwd": 16}],
	["hold_r", {"r_fwd": 12}, {"r_fwd": 16}],
	["cheer", {"breathe": 1.0, "l_fwd": 14, "r_fwd": 14}, {"breathe": -1.0}],
	["hug", {"l_fwd": 22, "r_fwd": 22, "bow": 8}, {"l_fwd": 22, "r_fwd": 22, "bow": 10}],
	["lean", {"bow": 12}, {"bow": 14}],
	["photo", {"l_fwd": 22, "r_fwd": 22, "bow": -4}, {"l_fwd": 20, "r_fwd": 20, "bow": -4}],
	["highfive", {"r_fwd": 22, "breathe": 1.0}, {"r_fwd": 18}],
	["dance", {"l_fwd": 18, "bow": 4, "breathe": 1.0}, {"r_fwd": 18, "bow": -4, "breathe": -1.0}],
	["read", {"l_fwd": 22, "r_fwd": 22, "bow": 12}, {"l_fwd": 20, "r_fwd": 22, "bow": 13}],
	["water", {"r_fwd": 22, "bow": 15}, {"r_fwd": 14, "bow": 15}],
	["sweep", {"l_fwd": 20, "r_fwd": 20, "bow": 16}, {"l_fwd": 10, "r_fwd": 10, "bow": 16}],
]
const POSE_YAW := [0.0, -72.0, 72.0, 180.0]
const POSE_PARAMS := ["l_fwd", "r_fwd", "l_up", "r_up", "bow", "sit", "breathe"]
const YAW := [0.0, -40.0, -72.0, -140.0, 180.0, 140.0, 72.0, 40.0]   # sides at 72° so the face still reads

var vp: SubViewport
var cam: Camera3D
var holder: Node3D


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
	cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = 2.42
	var d := 10.0
	var p := deg_to_rad(PITCH)
	cam.position = Vector3(0, 1.0 + sin(p) * d, cos(p) * d)
	vp.add_child(cam)
	cam.look_at(Vector3(0, 1.0, 0), Vector3.UP)
	holder = Node3D.new()
	vp.add_child(holder)
	var only := OS.get_environment("CHAR_ONLY")
	for c in CHARS:
		if only != "" and only != c:
			continue
		await _render(c)
	print("RENDER DONE")
	get_tree().quit()


func _render(c: String) -> void:
	for ch in holder.get_children():
		ch.queue_free()
	var scene: PackedScene = load(CHARS[c])
	var inst := scene.instantiate()
	holder.add_child(inst)
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://tests/charrender/walk_rig.gdshader")
	for mi in inst.find_children("*", "MeshInstance3D", true, false):
		(mi as MeshInstance3D).material_override = mat
	for kind in KINDS:
		var n: int = KINDS[kind]
		for row in 8:
			holder.rotation_degrees.y = YAW[row]
			for f in n:
				if kind == "walk":
					mat.set_shader_parameter("phase", TAU * f / n)
					mat.set_shader_parameter("swing", deg_to_rad(24.0))
					mat.set_shader_parameter("arm", deg_to_rad(20.0))
					mat.set_shader_parameter("breathe", 0.0)
				else:
					mat.set_shader_parameter("phase", 0.0)
					mat.set_shader_parameter("swing", 0.0)
					mat.set_shader_parameter("arm", 0.0)
					mat.set_shader_parameter("breathe", sin(TAU * f / n))
				await RenderingServer.frame_post_draw
				await RenderingServer.frame_post_draw
				var img := vp.get_texture().get_image()
				img.save_png("user://charframes/%s_%s_%d_%02d.png" % [c, kind, row, f])
		print(c, " ", kind, " done")
	mat.set_shader_parameter("swing", 0.0); mat.set_shader_parameter("arm", 0.0); mat.set_shader_parameter("phase", 0.0)
	for pi in POSES.size():
		for d in 4:
			holder.rotation_degrees.y = POSE_YAW[d]
			for f in 2:
				var spec: Dictionary = POSES[pi][1 + f]
				for k in POSE_PARAMS:
					var v: float = float(spec.get(k, 0.0))
					mat.set_shader_parameter(k, v if k in ["sit", "breathe"] else deg_to_rad(v))
				await RenderingServer.frame_post_draw
				await RenderingServer.frame_post_draw
				vp.get_texture().get_image().save_png("user://charframes/%s_pose_%02d_%d_%d.png" % [c, pi, d, f])
	for k in POSE_PARAMS:
		mat.set_shader_parameter(k, 0.0)
	print(c, " poses done")
