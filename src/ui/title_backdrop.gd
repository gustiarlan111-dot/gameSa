class_name TitleBackdrop
extends Node
## Live 3D scene behind the title menu: Arland and Sofia stroll through the Plaza at dusk in the
## real HD-2D world (World + Atmosphere + WorldView3D), the camera following them slowly.
## Nothing here touches a save; the world is a throwaway copy.

const AREA := "plaza"
const MINUTE := 1120                 # 18:40, lamps on, warm dusk sky
const SPEED := 34.0

var world: World
var atmosphere: Atmosphere
var view: WorldView3D
var _dir := Vector2.RIGHT
var _turn := 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 7
	world = World.new()
	add_child(world)
	atmosphere = Atmosphere.new()
	atmosphere.world = world
	world.atmo = atmosphere
	world.add_child(atmosphere)
	var a := Data.area(AREA)
	var sp: Array = a.get("spawn", [1200, 700])
	world.start("sofia", AREA, Vector2(float(sp[0]), float(sp[1])), "right")
	world.player.position = world.nearest_open(world.player.position)
	world.locked = true
	world.partner_mode = 2
	world.place_partner_beside()
	atmosphere.indoor = false
	atmosphere.minute = MINUTE
	var l := WorldClock.light(MINUTE)
	atmosphere.light = Color(l[0], l[1], l[2], l[3])
	view = WorldView3D.new()
	view.world = world
	view.atmosphere = atmosphere
	add_child(view)


## Wander: keep walking, turn when the path ahead is blocked or now and then.
func _physics_process(delta: float) -> void:
	if world == null or world.player == null:
		return
	_turn -= delta
	var p := world.player.position
	var ahead := p + _dir * 70.0
	if _turn <= 0.0 or not Data.clear_segment(world.area, p.x, p.y, ahead.x, ahead.y, world.flags):
		_pick_dir(p)
	var step := _dir * SPEED * delta
	if Data.clear_segment(world.area, p.x, p.y, p.x + step.x, p.y + step.y, world.flags):
		world.player.position += step
		world.player.face(_dir.x, _dir.y)
		world.player.walking = true
		if world._trail.is_empty() or world._trail[-1].distance_to(world.player.position) > 6:
			world._trail.append(world.player.position)
			if world._trail.size() > 80:
				world._trail.pop_front()
	else:
		world.player.walking = false
		_turn = 0.0


func _pick_dir(p: Vector2) -> void:
	var best := _dir
	var best_score := -1.0
	for i in 8:
		var ang := _rng.randf() * TAU
		var d := Vector2.from_angle(ang)
		d = Vector2(d.x, d.y * 0.6).normalized()       # favour long sideways pans
		var reach := 0.0
		for k in range(1, 9):
			var q := p + d * 40.0 * k
			if not Data.clear_segment(Data.area(AREA), p.x, p.y, q.x, q.y, world.flags):
				break
			reach = k
		var score := reach + d.dot(_dir) * 1.5 + _rng.randf()
		if score > best_score:
			best_score = score
			best = d
	_dir = best
	_turn = _rng.randf_range(5.0, 9.0)
