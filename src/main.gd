extends Node
## Boot. Title, slots and settings menus come in phase 3; for now a new Sofia game starts directly.
## Capture modes for automated QA (never used by players):
##   -- --shot  <route> <area> <x> <y> <frames> <out.png> [x:y;x:y waypoints]   free exploration
##        (env SHOT_QUALITY=low|medium|high|ultra forces a graphics preset, SHOT_SETTINGS=1 opens the
##        settings window, SHOT_LEFT=1 the left-handed layout, SHOT_FLASH=1 a lightning flash,
##        SHOT_NOREFLECT=1 hides the V8.10 water reflections; U3b: SHOT_HAND=1, SHOT_POSE=<pose>,
##        SHOT_CINE=<json cmds>, SHOT_TALK=1 (see _process); none is saved)
##   -- --story <route> <out_prefix> <frame,frame,...>                           new game, the story runs
##        by itself (dialogue advances every 50 frames, first choice taken) and a screenshot is saved
##        at each listed frame. Env STORY_STEP/STORY_AREA[/STORY_FLAGS/STORY_COMPANION] start it at a
##        later step; STORY_ROTATE=1 rotates through choices instead of always taking the first.
##   -- --cine  <route> <step> [x:y]   jumps to a step, walks up to its first marker and plays its
##        cutscene with dialogue auto-advancing, then quits. Pair with --write-movie out.avi.

var game: Game
var _mode := ""
var _args := []
var _frame := 0
var _wp := 0
var _wps: Array = []
var _shots: Array = []
var _dlg := 0
var _idle := 0
var _rot := 0
var _last_step := ""
var _choice_seen := {}


func _ready() -> void:
	GameSettings.apply_global()          # V8: frame cap and volumes from user://settings.json
	if OS.get_environment("SHOT_QUALITY") != "":       # QA captures: force a graphics preset (not saved)
		GameSettings.get_all()["quality"] = OS.get_environment("SHOT_QUALITY")
	if OS.get_environment("SHOT_LEFT") == "1":
		GameSettings.get_all()["left_hand"] = true
	var args := OS.get_cmdline_user_args()
	var i := args.find("--shot")
	var j := args.find("--story")
	if i >= 0:
		_mode = "shot"
		_args = args.slice(i + 1)
		var p := Progress.new_game(_args[0], 1, Data.first_step, Data.area(_args[1]))
		p.area = _args[1]; p.x = float(_args[2]); p.y = float(_args[3]); p.companion = true
		if OS.get_environment("SHOT_MINUTE") != "":
			p.minute = int(OS.get_environment("SHOT_MINUTE"))
		if OS.get_environment("SHOT_DAY") != "":
			p.day = int(OS.get_environment("SHOT_DAY"))
		if OS.get_environment("SHOT_STEP") != "":
			p.step = OS.get_environment("SHOT_STEP")
		if _args.size() > 6:
			for pt in _args[6].split(";", false):
				var xy: PackedStringArray = pt.split(":")
				_wps.append(Vector2(float(xy[0]), float(xy[1])))
		_start(p, false)
	elif args.has("--cine"):
		_mode = "cine"
		_args = args.slice(args.find("--cine") + 1)
		var st := Data.step(_args[1])
		var it: Dictionary = {}
		for o in st.get("interactables", []):
			if o.get("route") == null or o.get("route") == _args[0]:
				it = o
				break
		var area: String = Routes.resolve(str(it.get("area", Routes.room(_args[0]))), _args[0])
		var p := Progress.new_game(_args[0], 1, _args[1], Data.area(area))
		p.step = _args[1]; p.area = area
		p.x = float(it.get("x", 400)) - 46; p.y = float(it.get("y", 400)) + 8
		if _args.size() > 2:
			p.x = float(_args[2].get_slice(":", 0)); p.y = float(_args[2].get_slice(":", 1))
		p.companion = st.get("chapter", "PRO") != "PRO"
		if OS.get_environment("SHOT_MINUTE") != "":
			p.minute = int(OS.get_environment("SHOT_MINUTE"))
		_start(p, false)
	elif args.has("--minigame"):
		_mode = "minigame"
		_args = args.slice(args.find("--minigame") + 1)   # id route out_prefix
		_start(Progress.new_game(_args[1], 1, Data.first_step, Data.area(Routes.room(_args[1]))), false)
	elif args.has("--title"):
		_mode = "title"
		_args = args.slice(args.find("--title") + 1)
		_title()
	elif j >= 0:
		_mode = "story"
		_args = args.slice(j + 1)
		for f in _args[2].split(",", false):
			_shots.append(int(f))
		var sp := OS.get_environment("STORY_STEP")       # QA: start the autopilot at a later step
		if sp == "":
			_start(Progress.new_game(_args[0], 1, Data.first_step, Data.area(Routes.room(_args[0]))), true)
		else:
			var area: String = Routes.resolve(OS.get_environment("STORY_AREA"), _args[0])
			var p := Progress.new_game(_args[0], 1, sp, Data.area(area))
			p.step = sp; p.area = area; p.companion = OS.get_environment("STORY_COMPANION") == "1"
			if OS.get_environment("SHOT_MINUTE") != "":
				p.minute = int(OS.get_environment("SHOT_MINUTE"))
			for f in OS.get_environment("STORY_FLAGS").split(",", false):
				p.add_flag(f)
			_start(p, false)
	else:
		_title()


var _title_node: TitleScreen


func _title() -> void:
	if game:
		game.queue_free()
		game = null
	var layer := CanvasLayer.new()
	add_child(layer)
	_title_node = TitleScreen.new()
	layer.add_child(_title_node)
	_title_node.start_game.connect(func(p: Progress, is_new: bool):
		layer.queue_free()
		_start(p, is_new))


func _start(p: Progress, new_game: bool, replay := false) -> void:
	if game:
		game.queue_free()
	game = Game.new().setup(p, replay)
	add_child(game)
	game.quit_to_title.connect(_title)
	game.replay_requested.connect(func(rp: Progress): _start.call_deferred(rp, false, true))
	if new_game:
		game.begin_new_game()
	else:
		game.resume_game()


func _process(_delta: float) -> void:
	if _mode == "":
		return
	_frame += 1
	if _mode == "title":
		match _frame:
			40: await _save_plain(_args[0] + "_judul.png"); _title_node.show_routes()
			80: await _save_plain(_args[0] + "_route.png"); _title_node.show_slots("sofia")
			120: await _save_plain(_args[0] + "_slot.png"); get_tree().quit()
		return
	if _mode == "minigame":
		var ov := game.minigame
		if _args[0].begins_with("romance:"):
			var tabs := ["gift", "date", "moment", "couple", "game"]
			match _frame:
				20:
					var p := game.p
					p.step = "C02_START" if Data.steps.has("C02_START") else p.step
					for st in Data.steps:
						if Data.step(st).get("chapter") == "C02":
							p.step = st
							break
					p.companion = true; p.coins = 40; p.affection = 22; p.minute = 9 * 60
					p.items.append_array(["kopi_senja", "tulip_kecil"])
					game.romance.open("taman_kota", func(acts, msg): print("ROMANCE ", msg, " acts=", acts.size()); game.world.partner_mode = 2; game.world.place_partner_beside(); game.runner.run(acts))
			if _frame >= 40 and _frame % 20 == 0 and _frame <= 120:
				var i := (_frame - 40) / 20
				await _save("%s_%s.png" % [_args[2], tabs[i]])
				if i < 4:
					game.romance.tab = tabs[i + 1]; game.romance._rebuild()
			if _frame == 140:
				await _save("%s_game.png" % _args[2])
				game.romance.tab = "date"; game.romance._rebuild()
			if _frame == 150:
				game.romance._choices[0].pressed.emit()
			if _frame == 200 or _frame == 320:
				await _save("%s_kencan_%d.png" % [_args[2], _frame])
				print("DIALOG ", game.dialog.active, " CINE ", game.cine.active, " RUNNER ", game.runner.busy())
			if _frame == 320:
				get_tree().quit()
			return
		if _args[0].begins_with("pause:"):           # UI capture: pause menu, history, confirm box, toast
			match _frame:
				20:
					game.p.coins = 42; game.p.affection = 18; process_mode = Node.PROCESS_MODE_ALWAYS
					game.open_pause()
				40: await _save(_args[2] + "_jeda.png"); game.pause.set_status("Progress tersimpan"); game.pause._lines = [{"speaker": "Sofia", "day": 1, "text": "Hari ini langitnya cantik sekali, ya."}, {"speaker": "Arland", "day": 1, "text": "Iya. Mau jalan ke dermaga nanti sore?"}]; game.pause._show_history()
				60: await _save(_args[2] + "_riwayat.png"); game.pause._history.visible = false; game.pause.visible = false; get_tree().paused = false; game.confirm.ask("Tidur sampai pagi?", "Hari akan berganti dan toko-toko buka lagi besok pagi.", "Tidur", func(): pass, "Nanti")
				80: await _save(_args[2] + "_konfirmasi.png"); get_tree().quit()
			return
		if _args[0].begins_with("book:"):
			match _frame:
				20:
					var p := game.p
					p.add_flag("V26_C03_FINISHED"); p.items.append_array(["kopi_senja", "denah_dito", "kartu_klub_baca"])
					p.chapters["PRO"] = true; p.chapters["C01"] = true; p.snapshot("PRO"); p.snapshot("C01")
					p.add_flag("SQ_BUNGA_START"); p.play_seconds = 200
					game.save_now(); game.open_book()
				40: await _save(_args[2] + "_kenangan.png"); game.book.tab = 1; game.book._rebuild()
				60: await _save(_args[2] + "_tas.png"); game.book.tab = 2; game.book._rebuild()
				80: await _save(_args[2] + "_bab.png"); game.book.tab = 4; game.book._rebuild()
				100: await _save(_args[2] + "_prestasi.png"); game.book.tab = 5; game.book._rebuild()
				120: await _save(_args[2] + "_jelajah.png"); game.book._ask_replay("C01")
				140: await _save(_args[2] + "_konfirmasi.png"); game.book._confirm_ch = "C01"; game.book.replay_requested.emit("C01")
				200: print("REPLAY ", game.replay, " step=", game.p.step, " chapters=", game.p.chapters.keys()); await _save(_args[2] + "_replay.png"); get_tree().quit()
			return
		if _args[0].begins_with("puzzle:") or _args[0].begins_with("shop:"):
			var id: String = _args[0].get_slice(":", 1)
			match _frame:
				20:
					if _args[0].begins_with("shop:"):
						game.p.coins = 30
						game.open_shop(id, func(): print("SHOP CLOSED"))
					else:
						game.p.add_flag("C01_HINT_" + _args[1].to_upper())
						game.open_puzzle(id, func(ok): print("PUZZLE ", ok))
				60: await _save(_args[2] + "_a.png")
				61:
					if game.shop.visible:
						game.shop._buy[0].pressed.emit()
					else:
						var sy: Array = game.puzzle._pz.symbols
						var o: Array = game.puzzle._order
						game.puzzle._press(o[1]); game.puzzle._press(o[2]); game.puzzle._press(o[0])
				100: await _save(_args[2] + "_b.png"); get_tree().quit()
			return
		match _frame:
			20: game.open_minigame(_args[0], func(sc): print("MINIGAME SCORE ", sc))
			70: await _save(_args[2] + "_main.png")
			71:
				for k in 6:
					ov.game.key(k % 4); ov.game.tap(ov.game.x + ov.game.w * (0.2 + 0.15 * k), ov.game.y + ov.game.h * 0.45)
			110: await _save(_args[2] + "_main2.png")
			111: ov.game.finished = true; ov.game.result_text = ov.game.result_text if ov.game.result_text != "" else "(hasil uji otomatis)"
			140: await _save(_args[2] + "_hasil.png"); get_tree().quit()
		return
	if _mode == "cine":
		if _frame == 20:
			game._find_target()
			game.interact()
		elif _frame > 20:
			if game.dialog.active:
				_dlg += 1
				if _dlg % 75 == 0:
					if game.dialog.choosing():
						game.dialog.choose(0)
					else:
						game.dialog.advance(); game.dialog.advance()
			else:
				_dlg = 0
			if game.cine.active or game.dialog.active or game.runner.busy():
				_idle = 0
			else:
				_idle += 1
			if _idle > 45 or _frame > 9000:
				print("CINE DONE frame=", _frame, " step=", game.p.step)
				get_tree().quit()
		return
	if _mode == "shot":
		if game == null:                  # QA capture only: the game node is not there yet
			return
		var w := game.world
		if _frame == 2 and OS.get_environment("SHOT_SETTINGS") == "1":
			game.settings.open()          # QA: capture the V8 settings window over the scene
		if OS.get_environment("SHOT_FLASH") == "1" and _frame == int(_args[4]) - 3:
			game.atmosphere.flash = 1.0   # QA: capture a lightning flash
		# U3b QA: SHOT_HAND=1 walks hand in hand, SHOT_POSE=<pose> holds a pose on both, SHOT_CINE=<json
		# cutscene commands> plays them at frame 20, SHOT_TALK=1 lets neighbours start chatting at once
		if _frame == 3 and OS.get_environment("SHOT_HAND") == "1":
			game.p.holding_hands = true
		if _frame == 10 and OS.get_environment("SHOT_POSE") != "":
			for a in [w.player, w.partner]:
				a.set_pose(OS.get_environment("SHOT_POSE"), 99.0)
		if _frame == 20 and OS.get_environment("SHOT_CINE") != "":
			game.runner.run([{"do": "cine", "cmds": JSON.parse_string(OS.get_environment("SHOT_CINE"))}])
		if _frame == 4 and OS.get_environment("SHOT_TALK") == "1":
			game.npc_life._cool = 0.0
		if _frame == int(_args[4]) - 1 and game.npc_life.current().size() > 0:
			print("TALK ", game.npc_life.current().get("id"), " ", game.npc_life.current().get("a"), "+", game.npc_life.current().get("b"))
		if _wp < _wps.size():
			var d: Vector2 = _wps[_wp] - w.player.position
			if d.length() < 8:
				_wp += 1
				game.controls.vec = Vector2.ZERO
			else:
				game.controls.vec = d.normalized()
				game.controls.sprint = OS.get_environment("SHOT_SPRINT") == "1"
		else:
			game.controls.vec = Vector2.ZERO
		if _frame == int(_args[4]):
			await _save(_args[5])
			get_tree().quit()
	else:
		_autoplay()
		if game.p.step != _last_step:        # QA log: every story step reached, to spot a softlock
			_last_step = game.p.step
			print("STEP> %s %s frame=%d" % [_last_step, game.p.area, _frame])
		if _frame % 50 == 0 and _qa_overlay():
			pass
		elif _frame % 50 == 0:
			if game.dialog.choosing():
				# first choice, or rotate through them so a wrong answer is retried with the next one
				# first choice; when the same question comes back (a wrong answer in an echo or quiz),
				# try the next option, as a player would (STORY_ROTATE=1 rotates every choice)
				var ck := str(game.dialog._choices)
				var seen := int(_choice_seen.get(ck, 0))
				_choice_seen[ck] = seen + 1
				var n: int = maxi(1, game.dialog._choices.size())
				game.dialog.choose(seen % n if OS.get_environment("STORY_ROTATE") != "1" else _rot % n)
				if seen > 0:
					print("QA> retry choice #%d at %s" % [seen % n, game.p.step])
				_rot += 1
			elif game.dialog.active:
				game.dialog.advance()
				game.dialog.advance()
			elif game._card.visible:
				game._finish_card()
		if _shots.has(_frame):
			await _save("%s_%04d.png" % [_args[1], _frame])
		if _frame >= _shots.max():
			print("STEP ", game.p.step, " AREA ", game.p.area, " FLAGS ", game.p.flags.size())
			get_tree().quit()


## V8 QA: the autopilot also plays through the overlays that used to stop it (puzzle, minigame,
## confirm, shop, romance), so a whole route can run to the ending. Each one is logged as "QA>".
func _qa_overlay() -> bool:
	var pz = game.puzzle
	if pz.visible:
		if pz._solved_t < 0 and pz._entered.size() < pz._order.size():
			print("QA> puzzle %s: %s" % [game.p.step, pz._order[pz._entered.size()]])
			pz._press(pz._order[pz._entered.size()])
		return true
	if game.minigame.visible:
		print("QA> minigame %s auto-finished (score 3)" % game.p.step)
		game.minigame._finish(3)
		return true
	if game.confirm.visible:
		print("QA> confirm '%s' -> yes" % game.confirm._title.text)
		game.confirm._close(game.confirm._on_yes)
		return true
	if game.shop.visible:
		print("QA> shop closed"); game.shop.close()
		return true
	if game.romance.visible:
		print("QA> romance closed"); game.romance.close()
		return true
	return false


## Story autopilot for captures: walk to the active step's marker (crossing doors when it is in
## another area) and use it.
func _autoplay() -> void:
	var w := game.world
	game.controls.vec = Vector2.ZERO
	if w.locked:
		return
	var its := game.engine.interactables(game.p.area)
	if not its.is_empty():
		var it: Dictionary = its[0]
		var t := Vector2(float(it.get("x", 0)), float(it.get("y", 0)))
		var d := t - w.player.position
		if d.length() <= float(it.get("r", 64)) * 0.7:
			game._find_target()
			game.interact()
		else:
			game.controls.vec = _steer(t, float(it.get("r", 64)) * 0.6)
		return
	var goal := _goal_area()
	if goal == "" or goal == game.p.area:
		return
	var door := _next_door(game.p.area, goal)
	if door.is_empty():
		return
	var r: Array = door.rect
	var c := Vector2(r[0] + r[2] / 2.0, r[1] + r[3] / 2.0)
	game.controls.vec = _steer(c, maxf(r[2], r[3]) * 0.5 + 14.0, Rect2(r[0], r[1], r[2], r[3]).grow(10))


## V8 QA: the autopilot used to walk in a straight line and got stuck on trees (both routes stalled
## at PRO_SHARDS in memory_garden). It now follows a breadth-first path over the real collision
## (Data.blocked, 8 px cells), replanned when the target changes or the player stops moving.
const NAV_CELL := 8.0
var _nav_key := ""
var _nav_pts: Array = []
var _nav_last := Vector2.ZERO
var _nav_still := 0


func _steer(target: Vector2, radius: float, goal_rect := Rect2()) -> Vector2:
	var w := game.world
	var pos := w.player.position
	var key := "%s|%d|%d" % [game.p.area, int(target.x), int(target.y)]
	_nav_still = _nav_still + 1 if pos.distance_to(_nav_last) < 0.5 else 0
	_nav_last = pos
	if key != _nav_key or _nav_still > 40:
		if key == _nav_key and not _nav_pts.is_empty():
			# stuck on a collider the cell centres missed (ellipse edges are tested at 5 foot points):
			# close the cell in front and route around it, as a player would
			var g := _grid()
			g.set_point_solid(_cell(g, _nav_pts[0]))
		_nav_key = key
		_nav_still = 0
		_nav_pts = _plan(pos, target, radius, goal_rect)
	if OS.get_environment("NAV_DEBUG") == "1" and _frame % 120 == 0:
		print("NAV ", game.p.area, " pos=", pos, " target=", target, " pts=", _nav_pts.size(), " still=", _nav_still)
	while not _nav_pts.is_empty() and pos.distance_to(_nav_pts[0]) < 6.0:
		_nav_pts.pop_front()
	var to: Vector2 = _nav_pts[0] if not _nav_pts.is_empty() else target
	return (to - pos).normalized()


var _nav_grid: AStarGrid2D
var _nav_grid_key := ""


## Walkable grid of the current area (native AStarGrid2D), rebuilt when the area or its open gates change.
func _grid() -> AStarGrid2D:
	var a: Dictionary = game.world.area
	var flags: Dictionary = game.world.flags
	var key := "%s|%d" % [a.get("id", ""), flags.size()]
	if _nav_grid != null and key == _nav_grid_key:
		return _nav_grid
	var g := AStarGrid2D.new()
	g.region = Rect2i(0, 0, int(ceil(float(a.get("w", 960)) / NAV_CELL)), int(ceil(float(a.get("h", 640)) / NAV_CELL)))
	g.cell_size = Vector2(NAV_CELL, NAV_CELL)
	g.offset = Vector2(NAV_CELL, NAV_CELL) * 0.5
	g.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	g.update()
	for y in g.region.size.y:
		for x in g.region.size.x:
			if Data.blocked(a, (x + 0.5) * NAV_CELL, (y + 0.5) * NAV_CELL, flags):
				g.set_point_solid(Vector2i(x, y))
	_nav_grid = g
	_nav_grid_key = key
	return g


func _cell(g: AStarGrid2D, p: Vector2) -> Vector2i:
	return Vector2i(clampi(int(p.x / NAV_CELL), 0, g.region.size.x - 1), clampi(int(p.y / NAV_CELL), 0, g.region.size.y - 1))


## Nearest open cell to a point (targets often sit on an NPC, a table or a door at the map edge).
func _open_near(g: AStarGrid2D, p: Vector2, rect := Rect2()) -> Vector2i:
	var c := _cell(g, p)
	for r in range(0, 40):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var n := c + Vector2i(dx, dy)
				if g.is_in_boundsv(n) and not g.is_point_solid(n):
					return n
	return c


func _plan(from: Vector2, target: Vector2, _radius: float, goal_rect: Rect2) -> Array:
	var g := _grid()
	var start := _open_near(g, from)
	var goal := _open_near(g, goal_rect.get_center() if goal_rect.size != Vector2.ZERO else target)
	var path: PackedVector2Array = g.get_point_path(start, goal)
	var pts: Array = []
	for i in range(1, path.size()):
		pts.append(path[i])
	return pts


func _goal_area() -> String:
	var st := game.engine.step()
	var first := ""
	for it in st.get("interactables", []):
		if it.get("route") == null or it.get("route") == game.p.route:
			var ar: String = Routes.resolve(it.get("area", ""), game.p.route)
			if first == "":
				first = ar
			# V8 QA: go where something can still be done (free days spread their activities over areas)
			if ar != game.p.area and not game.engine.interactables(ar).is_empty():
				return ar
	if first != "":
		return first
	var ea: Dictionary = st.get("enterArea", {})
	return Routes.resolve(ea.get("area", ""), game.p.route) if ea.get("area") != null else ""


func _next_door(from: String, goal: String) -> Dictionary:
	var prev := {from: null}
	var q := [from]
	while not q.is_empty():
		var a: String = q.pop_front()
		if a == goal:
			break
		for d in Data.area(a).get("doors", []):
			var to := str(d.get("to", ""))
			if not prev.has(to) and Data.maps.has(to) and game.engine.door_lock(d) == "":
				prev[to] = [a, d]
				q.append(to)
	if not prev.has(goal):
		return {}
	var cur := goal
	while prev[cur] != null and prev[cur][0] != from:
		cur = prev[cur][0]
	return prev[cur][1] if prev[cur] != null else {}


func _save_plain(path: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
	print("SHOT ", path)


func _save(path: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(path)
	print("SHOT ", path, " step=", game.p.step, " area=", game.p.area, " at ", game.world.player.position, " day=", game.p.day, " minute=", game.p.minute, " music=", Audio.current_music(), " amb=", Audio.current_ambience())
