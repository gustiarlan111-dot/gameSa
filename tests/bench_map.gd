extends Node
## Map benchmark (V8 audit, Fase 0). One area per process, started like a loaded save:
##   godot --path . --rendering-driver opengl3 --resolution 1280x720 tests/bench_map.tscn -- --bench <area> [route]
## Prints one line "BENCH> {json}" with load time, frame time/fps, draw calls, objects, primitives,
## node count and memory, then quits. fps on a desktop software renderer is only a relative measure:
## the real target (mid-range Android) must be measured on the phone.

const WARMUP := 90
const SAMPLE := 180

var game: Game
var area := ""
var _t0 := 0
var _frame := 0
var _load_ms := 0.0
var _acc := {"ft": [], "dc": [], "obj": [], "prim": [], "gpu": [], "cpu": []}


func _ready() -> void:
	if OS.get_environment("SHOT_QUALITY") != "":
		GameSettings.get_all()["quality"] = OS.get_environment("SHOT_QUALITY")
	var args := OS.get_cmdline_user_args()
	var i := args.find("--bench")
	area = args[i + 1] if i >= 0 and args.size() > i + 1 else "plaza"
	var route: String = args[i + 2] if i >= 0 and args.size() > i + 2 else "sofia"
	var a: Dictionary = Data.area(area)
	_t0 = Time.get_ticks_usec()
	var p := Progress.new_game(route, 1, Data.first_step, a)
	p.area = area
	var sp: Array = a.get("spawn", [400, 400])
	p.x = float(sp[0]); p.y = float(sp[1]); p.companion = true
	game = Game.new().setup(p, false)
	add_child(game)
	game.resume_game()


func _process(delta: float) -> void:
	_frame += 1
	if _frame == 2:
		for vp in _vps():
			RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)
	if _frame > WARMUP:
		var g := 0.0
		var c := 0.0
		for vp in _vps():
			g += RenderingServer.viewport_get_measured_render_time_gpu(vp.get_viewport_rid())
			c += RenderingServer.viewport_get_measured_render_time_cpu(vp.get_viewport_rid())
		_acc.gpu.append(g); _acc.cpu.append(c)
	if _frame == 1:
		_load_ms = (Time.get_ticks_usec() - _t0) / 1000.0
	if _frame <= WARMUP:
		return
	_acc.ft.append(delta * 1000.0)
	_acc.dc.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	_acc.obj.append(Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME))
	_acc.prim.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
	if _frame >= WARMUP + SAMPLE:
		var ft: Array = _acc.ft.duplicate(); ft.sort()
		var avg := 0.0
		for v in ft:
			avg += v
		avg /= ft.size()
		var out := {
			"area": area, "load_ms": snappedf(_load_ms, 0.1),
			"ft_avg_ms": snappedf(avg, 0.01), "ft_p95_ms": snappedf(ft[int(ft.size() * 0.95)], 0.01),
			"fps_avg": snappedf(1000.0 / avg, 0.1),
			"draw_calls": int(_mean(_acc.dc)), "objects": int(_mean(_acc.obj)), "primitives": int(_mean(_acc.prim)),
			"nodes": int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),
			"mem_static_mb": snappedf(Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, 0.1),
			"vram_mb": snappedf(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0, 0.1),
			"tex_mb": snappedf(Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0, 0.1),
			"props": game.world.area.get("props", []).size(),
			"gpu_ms": snappedf(_mean(_acc.gpu), 0.01), "render_cpu_ms": snappedf(_mean(_acc.cpu), 0.01),
			"world_px": "%dx%d" % [RenderStage.world_pixels(game).x, RenderStage.world_pixels(game).y],
		}
		print("BENCH> ", JSON.stringify(out))
		get_tree().quit()


func _mean(a: Array) -> float:
	var s := 0.0
	for v in a:
		s += float(v)
	return s / maxf(1.0, a.size())


func _vps() -> Array:
	var out: Array = [get_tree().root]
	if game and game.stage:
		out.append(game.stage.viewport)
	return out
