extends Node
## QA (not part of CI): load the saves the story autopilot wrote and resume each one in a Game.
func _ready() -> void:
	var bad := 0
	for r in ["sofia", "arland"]:
		var ld := SaveStore.load_slot(r, 1)
		var v = ld.value
		print("LOAD %s status=%s step=%s area=%s chapters=%d flags=%d" % [r, ld.get("status"), v.step if v else "-", v.area if v else "-", v.chapters.size() if v else 0, v.flags.size() if v else 0])
		if v == null:
			bad += 1
			continue
		var base := "user://saves/%s_slot_01.json" % r
		for suf in [".bak", ".bak2"]:
			var t = SaveStore._read(base + suf)
			var u = SaveStore.unwrap_payload(t) if t != null else null
			print("  backup %s -> %s" % [suf, (u.get("step", "?") if u is Dictionary else "unreadable")])
		var g := Game.new()
		g.p = v
		add_child(g)
		for i in 120:
			await get_tree().process_frame
		print("  resumed in %s at %s, step %s" % [g.p.area, g.world.player.position, g.p.step])
		g.queue_free()
		await get_tree().process_frame
	print("QA SAVES %s" % ("OK" if bad == 0 else "FAIL"))
	get_tree().quit()
