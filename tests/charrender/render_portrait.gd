extends Node
## V8.4 tool: close-up bust renders of the GLB characters for dialogue portraits (not in the APK).
const CHARS := {"arland": "res://assets/characters/arland/model/Arland.glb", "sofia": "res://assets/characters/sofia/model/Sofia.glb"}

func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://portraitframes"))
	var vp := SubViewport.new()
	vp.size = Vector2i(704, 880)
	vp.transparent_bg = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var we := WorldEnvironment.new(); var env := Environment.new(); env.background_mode = Environment.BG_CLEAR_COLOR; we.environment = env
	vp.add_child(we)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = float(OS.get_environment("P_SIZE")) if OS.get_environment("P_SIZE") != "" else 1.25
	vp.add_child(cam)
	var cy := float(OS.get_environment("P_Y")) if OS.get_environment("P_Y") != "" else 1.42
	cam.position = Vector3(0, cy + 0.6, 6.0)
	cam.look_at(Vector3(0, cy, 0), Vector3.UP)
	var holder := Node3D.new(); vp.add_child(holder)
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://tests/charrender/walk_rig.gdshader")
	mat.set_shader_parameter("leg_gap", 0.0)
	for c in CHARS:
		for ch in holder.get_children(): ch.queue_free()
		var inst: Node3D = (load(CHARS[c]) as PackedScene).instantiate()
		holder.add_child(inst)
		for mi in inst.find_children("*", "MeshInstance3D", true, false):
			(mi as MeshInstance3D).material_override = mat
		for yaw in [0.0, 10.0]:
			holder.rotation_degrees.y = yaw if c == "arland" else -yaw
			await RenderingServer.frame_post_draw
			await RenderingServer.frame_post_draw
			vp.get_texture().get_image().save_png("user://portraitframes/%s_%d.png" % [c, int(yaw)])
	print("PORTRAIT DONE")
	get_tree().quit()
