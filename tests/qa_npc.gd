extends Node
## QA (not in CI): Living NPC transitions. Env QA_NPC=<id>, QA_AT=<minute>, QA_SIDE=east|west.
## The NPC's schedule moves it out of the plaza: it must walk out through the door on the route to
## its next area (World.first_hop) instead of vanishing on the spot.
func _ready() -> void:
	var id := OS.get_environment("QA_NPC")
	var side := OS.get_environment("QA_SIDE")
	var p := Progress.new_game("sofia", 1, "C03_PICNIC", Data.area("plaza"))
	p.step = "C03_PICNIC"; p.area = "plaza"; p.x = 1200; p.y = 820; p.minute = int(OS.get_environment("QA_AT"))
	var g := Game.new(); g.p = p
	add_child(g)
	await get_tree().process_frame
	var w: World = g.world
	var start = w.npcs[id].position if w.npcs.has(id) else null
	print(id, " at start: ", start, " minute ", g.p.minute)
	var last = start
	var leaving := false
	for i in (60 * 90 if OS.get_environment("QA_MODE") != "arrive" else 0):
		await get_tree().physics_frame
		if w.npcs.has(id):
			if w.npc_brain[id].has("leaving") and not leaving:
				leaving = true
				print("minute ", g.p.minute, ": leaving toward ", w.npc_brain[id].target)
			if w.npcs[id].position.distance_to(last) > 0.1 and i % 300 == 0:
				print("  walking ", w.npcs[id].position)
			last = w.npcs[id].position
		elif leaving:
			print("went out at ", last, " minute ", g.p.minute)
			break
	if OS.get_environment("QA_MODE") == "arrive":
		var first = null
		for i in 60 * 40:
			await get_tree().physics_frame
			if w.npcs.has(id):
				if first == null:
					first = w.npcs[id].position
					print("minute ", g.p.minute, ": appeared at ", first, " heading to ", w.npc_brain[id].home)
				last = w.npcs[id].position
				if last.distance_to(w.npc_brain[id].home) < 6.0 and not w.npc_brain[id].has("path"):
					print("reached spot ", last, " minute ", g.p.minute)
					break
		var ok2: bool = first != null and first.distance_to(w.npc_brain[id].home) > 200 and last.distance_to(w.npc_brain[id].home) < 6.0
		print("QA NPC ARRIVE %s %s" % [id, "OK" if ok2 else "FAIL"])
		get_tree().quit()
		return
	var at_door: bool = last != null and ((last.x > 2300) if side == "east" else (last.x < 100))
	print("QA NPC %s %s" % [id, "OK" if start != null and leaving and not w.npcs.has(id) and at_door else "FAIL"])
	get_tree().quit()
