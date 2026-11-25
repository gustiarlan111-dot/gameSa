class_name Critter
extends Node2D
## A small animal living on a map (cats, dogs, chickens, rabbits, squirrels, ducks, birds).
## Spawned by World from the area's "animals" list; WorldView3D mirrors it into the 3D scene.
## position = foot point in map pixels. Sheets in assets/animals face right, one row of frames.

# type -> [frame width, walk frames, idle frames, rest frame, speed, shy]
const KINDS := {
	"cat": [24, [0, 1], [2], 3, 34.0, false],
	"dog": [24, [0, 1], [2, 3], 4, 46.0, false],
	"chicken": [24, [0, 1], [2, 3], -1, 24.0, true],
	"rabbit": [24, [1, 2], [0], 3, 64.0, true],
	"squirrel": [18, [0, 1, 2], [3], -1, 78.0, true],
	"duck": [24, [0, 1, 2], [0], 3, 14.0, false],
	"bird": [16, [1, 2], [3, 0], -1, 150.0, true],
}

var world: World
var kind := "cat"
var region := Rect2()          # where it may walk / land
var water := Vector4.ZERO      # duck pond ellipse cx, cy, rx, ry
var night_only := false
var _sprite: Sprite2D
var _shadow: Sprite2D
var _cfg: Array
var _target := Vector2.ZERO
var _pause := 0.0
var _idle_t := 0.0             # how long it has been standing still (cats and dogs curl up)
var _anim := 0.0
var _moving := false
var _height := 0.0             # birds: height above the ground while flying
var _fly_from := Vector2.ZERO
var _fly_t := -1.0
var _fly_len := 1.0
var _dive := 0.0               # ducks: time left under water


func setup(w: World, type: String, spec: Dictionary, rng: RandomNumberGenerator) -> Critter:
	world = w
	kind = "cat" if type.begins_with("cat_") else type
	_cfg = KINDS.get(kind, KINDS.cat)
	night_only = spec.get("day", true) == false
	var tex: Texture2D = load("res://assets/animals/%s.png" % type)
	_shadow = Sprite2D.new()
	_shadow.texture = load("res://assets/fx/contact_shadow_v37.png") if ResourceLoader.exists("res://assets/fx/contact_shadow_v37.png") else null
	_shadow.set_meta("flat", true)
	_shadow.modulate = Color(1, 1, 1, 0.75)
	if _shadow.texture:
		var sw := 9.0 if kind == "bird" else 18.0
		_shadow.scale = Vector2(sw / _shadow.texture.get_width(), sw * 0.4 / _shadow.texture.get_height())
	add_child(_shadow)
	_sprite = Sprite2D.new()
	_sprite.texture = tex
	_sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_sprite.centered = false
	_sprite.region_enabled = true
	add_child(_sprite)
	if spec.has("water"):
		var wv: Array = spec.water
		water = Vector4(wv[0], wv[1], wv[2], wv[3])
		_shadow.visible = false
		position = _pond_point(rng)
	else:
		var r: Array = spec.get("region", [0, 0, world.area.get("w", 960), world.area.get("h", 640)])
		region = Rect2(r[0], r[1], r[2], r[3])
		position = _ground_point(rng, region)
	_target = position
	_pause = rng.randf_range(0.5, 4.0)
	_anim = rng.randf() * 4.0
	_sprite.flip_h = rng.randf() < 0.5
	_frame(_cfg[2][0])
	return self


func _pond_point(rng = null) -> Vector2:
	var a: float = (rng.randf() if rng else randf()) * TAU
	var d: float = sqrt(rng.randf() if rng else randf()) * 0.85
	return Vector2(water.x + cos(a) * water.z * d, water.y + sin(a) * water.w * d)


func _ground_point(rng, r: Rect2) -> Vector2:
	for _i in 24:
		var q := r.position + Vector2((rng.randf() if rng else randf()) * r.size.x, (rng.randf() if rng else randf()) * r.size.y)
		if world.can_stand(q.x, q.y):
			return q
	return r.get_center()


func _frame(i: int) -> void:
	var fw: int = _cfg[0]
	var fh := _sprite.texture.get_height()
	_sprite.region_rect = Rect2(i * fw, 0, fw, fh)
	_sprite.position = Vector2(-fw / 2.0, -fh - _height)


## Hidden while it is daytime for night animals, and everyone but ducks shelters from the rain.
func _awake() -> bool:
	var atm: Atmosphere = world.atmo
	if atm == null:
		return true
	if atm.weather == "rain" and kind != "duck":
		return false
	if night_only and atm.night < 0.35:
		return false
	return true


func _process(delta: float) -> void:
	if world == null or world.player == null:
		return
	visible = _awake()
	if not visible:
		return
	_anim += delta
	if kind == "duck":
		_duck(delta)
	elif kind == "bird":
		_bird(delta)
	else:
		_walker(delta)


func _scared() -> bool:
	if not _cfg[5]:
		return false
	for a in [world.player, world.partner]:
		if a and a.visible and a.position.distance_to(position) < (80.0 if kind == "bird" else 56.0):
			return true
	return false


func _walker(delta: float) -> void:
	var spd: float = _cfg[4]
	if _scared() and _pause > -1.0:
		var away := (position - world.player.position).normalized()
		_target = position + away.rotated(randf_range(-0.6, 0.6)) * randf_range(60.0, 110.0)
		_target = Vector2(clampf(_target.x, region.position.x, region.end.x), clampf(_target.y, region.position.y, region.end.y))
		_pause = -1.0                # fleeing: run at double speed until the target is reached
	var d := _target - position
	if d.length() > 1.5:
		var k := 2.0 if _pause <= -1.0 else 1.0
		# rabbits move in hops: only during the airborne part of each hop
		var hop := 1.0 if kind != "rabbit" else maxf(0.0, sin(_anim * 9.0))
		var n := position + d.normalized() * minf(d.length(), spd * k * hop * delta)
		if Data.clear_segment(world.area, position.x, position.y, n.x, n.y, world.flags):
			position = n
			if absf(d.x) > 0.5:
				_sprite.flip_h = d.x < 0
			_moving = true
			_idle_t = 0.0
		else:
			_target = position
		var fr: Array = _cfg[1]
		_frame(fr[int(_anim * (12.0 if k > 1.0 else 7.0)) % fr.size()])
		return
	if _moving:
		_moving = false
		_pause = randf_range(1.5, 6.0)
	_idle_t += delta
	_pause -= delta
	var rest: int = _cfg[3]
	if rest >= 0 and _idle_t > 9.0:
		_frame(rest)                  # curled up / lying down
	else:
		var idle: Array = _cfg[2]
		_frame(idle[int(_anim * 1.6) % idle.size()])
	if _pause <= 0.0:
		_pause = 0.0
		if rest >= 0 and _idle_t > 9.0 and randf() < 0.6:
			_pause = randf_range(6.0, 14.0)     # keep napping a while
			return
		var q := position + Vector2.from_angle(randf() * TAU) * randf_range(30.0, 120.0)
		q = Vector2(clampf(q.x, region.position.x, region.end.x), clampf(q.y, region.position.y, region.end.y))
		if world.can_stand(q.x, q.y):
			_target = q


func _duck(delta: float) -> void:
	if _dive > 0.0:
		_dive -= delta
		_frame(3)
		return
	var d := _target - position
	if d.length() > 1.0:
		position += d.normalized() * minf(d.length(), _cfg[4] * delta)
		if absf(d.x) > 0.3:
			_sprite.flip_h = d.x < 0
		_frame([0, 1, 2][int(_anim * 3.0) % 3])
	else:
		_frame(0)
		_pause -= delta
		if _pause <= 0.0:
			_pause = randf_range(2.0, 7.0)
			if randf() < 0.18:
				_dive = randf_range(1.2, 2.2)
			else:
				_target = _pond_point()
	# gentle bob on the water
	_sprite.position.y += sin(_anim * 2.2) * 0.6


func _bird(delta: float) -> void:
	if _fly_t >= 0.0:
		_fly_t += delta / _fly_len
		var t := minf(_fly_t, 1.0)
		position = _fly_from.lerp(_target, t)
		_height = sin(t * PI) * minf(70.0, 24.0 + _fly_from.distance_to(_target) * 0.25)
		_sprite.flip_h = _target.x < _fly_from.x
		_frame([1, 2][int(_anim * 14.0) % 2])
		_shadow.modulate.a = 0.75 - _height / 140.0
		if _fly_t >= 1.0:
			_fly_t = -1.0; _height = 0.0
			_pause = randf_range(2.0, 6.0)
		return
	_shadow.modulate.a = 0.75
	_pause -= delta
	if _scared() or _pause <= 0.0:
		var far := _scared()
		var q := _ground_point(null, region)
		if far or q.distance_to(position) < 20.0:
			q = position + Vector2.from_angle(randf() * TAU) * randf_range(140.0, 260.0)
			q = Vector2(clampf(q.x, region.position.x, region.end.x), clampf(q.y, region.position.y, region.end.y))
			if not world.can_stand(q.x, q.y):
				q = _ground_point(null, region)
		if far or randf() < 0.25:
			_fly_from = position; _target = q
			_fly_len = clampf(position.distance_to(q) / _cfg[4], 0.5, 2.5)
			_fly_t = 0.0
		else:
			_pause = randf_range(1.0, 3.5)
			if randf() < 0.5:
				_sprite.flip_h = not _sprite.flip_h
	# peck now and then
	_frame(0 if fmod(_anim, 2.4) < 0.5 else 3)
