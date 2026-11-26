class_name Atmosphere
extends Node2D
## Time of day, weather and light (port of WorldRenderer.drawAmbient, upgraded for the 3D view).
## Works out the day tint, night amount and lamp state that WorldView3D lights the 3D world with,
## runs the screen pass (tilt-shift depth blur, bloom, grade, vignette) under the HUD, and draws the
## 2D overlay effects: rain, wind, petals, fireflies, butterflies and the sun/moon halo.

var world: World
var time := 0.0
var light := Color(1, 1, 1, 0)   # rgb tint, a = strength (WorldClock.light or the step tint)
var weather := "cerah"           # cerah / berawan / rain / berangin
var indoor := false
var realm := false
var ambient := ""
var minute := 720
var tint_mod := Color.WHITE       # day tint for the 3D ambient light
var lamp_on := 0.0                # 0..1, street lamps and lanterns
var night := 0.0                  # 0 day .. 1 full night (outdoors)
var storm := false                # V8: thunderstorm on this rainy day (set by Game)
var flash := 0.0                  # V8: lightning, 0..1 (WorldView3D lights the 3D world with it)
var fireflies3d := false          # U2b: WorldParticles draws the fireflies in 3D, so the flat ones stay off
var _next_bolt := 6.0
var _thunder_in := -1.0
var _bolt_rng := RandomNumberGenerator.new()
var _post: ColorRect
## Cutscene colour moods: [tint, desaturation]
const MOODS := {"": [Color(1, 1, 1), 0.0], "warm": [Color(1.1, 0.98, 0.84), 0.05], "cool": [Color(0.86, 0.96, 1.1), 0.1],
		"dream": [Color(1.04, 0.92, 1.12), 0.0], "memory": [Color(1.1, 0.98, 0.82), 0.55], "night": [Color(0.8, 0.88, 1.12), 0.2]}
var _post_mat: ShaderMaterial
var _glow_tex: Texture2D
var _sparkle: Texture2D
var _rain: Array = []


func _ready() -> void:
	z_index = 40
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.35, Color(1, 1, 1, 0.55))
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.5)
	gt.fill_to = Vector2(1.0, 0.5)
	gt.width = 256; gt.height = 256
	_glow_tex = gt
	_sparkle = Data.tex("ui/sparkle.png")
	var layer := CanvasLayer.new()
	layer.layer = 1
	add_child(layer)
	_post = ColorRect.new()
	_post.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_post.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_post_mat = ShaderMaterial.new()
	_post_mat.shader = preload("res://src/fx/post25d.gdshader")
	_post.material = _post_mat
	layer.add_child(_post)
	var r := RandomNumberGenerator.new(); r.seed = 11
	for i in 220:
		_rain.append(Vector2(r.randf(), r.randf()))


func dark_cave() -> bool:
	return ambient == "dark"


func _process(delta: float) -> void:
	time += delta
	var rain := weather == "rain" and not indoor
	var tc := Color(light.r, light.g, light.b)
	var a := light.a
	if weather == "rain":
		tc = Color(0.25, 0.3, 0.42); a = 0.12 if indoor else 0.28
	elif indoor:
		a *= 0.45
	var mod := Color.WHITE.lerp(tc, clampf(a * 2.7, 0.0, 0.9))
	if weather == "berawan" and not indoor and not realm:
		mod = mod * Color(0.93, 0.94, 0.97)
	if dark_cave():
		mod = Color(0.16, 0.15, 0.24)
	tint_mod = tint_mod.lerp(mod, minf(1.0, delta * 3.0))
	night = clampf((light.a - 0.12) / 0.2, 0.0, 1.0) if not indoor else 0.0
	lamp_on = 1.0 if (realm or dark_cave()) else maxf(pow(night, 1.6), 0.5 if rain else 0.0)
	if indoor and not dark_cave():
		lamp_on = clampf(light.a * 2.0, 0.0, 0.6)
	_update_storm(delta)
	# screen pass
	var t := (minute - 360.0) / 750.0
	var outdoors := not indoor and not realm and not dark_cave()
	var q := GameSettings.quality()
	_post.visible = bool(q.post)
	_post_mat.set_shader_parameter("blur_amt", 1.0)
	_post_mat.set_shader_parameter("taps", bool(q.taps))
	_post_mat.set_shader_parameter("bloom", 0.3 if night > 0.3 else 0.18)
	_post_mat.set_shader_parameter("warmth", (clampf((t - 0.75) * 4.0, 0.0, 1.0) * 0.45 if outdoors else 0.0))
	_post_mat.set_shader_parameter("vignette", 0.42 if (night > 0.3 or dark_cave()) else 0.3)
	var c: Cutscene = world.cine if world else null
	var f := c.film if c != null else 0.0
	_post_mat.set_shader_parameter("film", f)
	_post_mat.set_shader_parameter("t", time)
	if c != null and f > 0.001:
		var m: Array = MOODS.get(c.mood, MOODS[""])
		_post_mat.set_shader_parameter("dof", c.dof)
		_post_mat.set_shader_parameter("mood_col", m[0])
		_post_mat.set_shader_parameter("mood_desat", m[1])
		_post_mat.set_shader_parameter("mood_a", c.mood_a)
		_post_mat.set_shader_parameter("focus_y", 0.52)
	queue_redraw()


## Lightning: a soft double flicker every 9-26 s, thunder 0.5-2.5 s later (farther = later and
## quieter). Flash strength stays gentle and never strobes; Settings > "Kilat petir" turns the flash
## off (thunder stays).
func _update_storm(delta: float) -> void:
	flash = maxf(0.0, flash - delta * 3.2)
	var active := storm and weather == "rain" and not indoor and not realm and not dark_cave()
	if not active:
		_thunder_in = -1.0
		return
	_next_bolt -= delta
	if _next_bolt <= 0.0:
		_next_bolt = _bolt_rng.randf_range(9.0, 26.0)
		var dist := _bolt_rng.randf()
		if bool(GameSettings.value("lightning")):
			flash = lerpf(1.0, 0.45, dist)
			get_tree().create_timer(0.11).timeout.connect(func(): flash = maxf(flash, lerpf(0.7, 0.3, dist)))
		_thunder_in = lerpf(0.5, 2.5, dist)
		set_meta("thunder_gain", lerpf(0.9, 0.4, dist))
	if _thunder_in > 0.0:
		_thunder_in -= delta
		if _thunder_in <= 0.0:
			Audio.sfx("thunder", float(get_meta("thunder_gain", 0.7)))


func _view() -> Rect2:
	return world.view_rect()


func _draw() -> void:
	if world == null:
		return
	var v := _view()
	var L := v.position.x
	var T := v.position.y
	var W := v.size.x
	var H := v.size.y
	var rain := weather == "rain" and not indoor
	var is_night := light.a >= 0.2 and not rain and not indoor
	# sun or moon halo
	if not indoor and not realm and not dark_cave():
		var halo := 230.0 if is_night else 260.0
		var hp := Vector2(L + W * (0.82 if is_night else 0.18), T + H * 0.2)
		var hc := Color(0.72, 0.78, 1, 0.12 if rain else 0.18) if is_night else Color(1, 0.78, 0.54, 0.14 if rain else 0.22)
		draw_texture_rect(_glow_tex, Rect2(hp - Vector2(halo, halo) / 2, Vector2(halo, halo)), false, hc)
	# area ambience particles
	if ambient != "" and ambient != "dark" and not rain:
		var n := 28
		for i in n:
			var fx := fmod(i * 0.6180339 + time * (0.012 + (i % 5) * 0.004), 1.0) * W
			var fy := fposmod(i * 0.3819 + (time * 0.03 if ambient == "petals" else -sin(time * 0.3 + i) * 0.02), 1.0) * H
			var pt := Vector2(L + fx, T + fy)
			if ambient == "petals":
				draw_rect(Rect2(pt, Vector2(4, 3)), Color(1, 0.78, 0.86, 0.85))
			elif ambient == "fireflies" and fireflies3d:
				continue
			elif ambient == "fireflies":
				var al := 0.3 + 0.7 * maxf(0, sin(time * 2 + i))
				draw_texture_rect(_glow_tex, Rect2(pt - Vector2(9, 9), Vector2(18, 18)), false, Color(1, 0.95, 0.55, al * 0.8))
				draw_rect(Rect2(pt - Vector2(1, 1), Vector2(2.5, 2.5)), Color(1, 1, 0.7, al))
			elif _sparkle:
				var al := 0.3 + 0.6 * maxf(0, sin(time * 1.5 + i * 2))
				draw_texture_rect(_sparkle, Rect2(pt - Vector2(3, 3), Vector2(7, 7)), false, Color(1, 0.96, 0.85, al))
	# U2c: shooting stars over the starry maps, one every few seconds, high in the view
	if ambient == "stars" and not rain:
		var period := 4.5
		var k := int(time / period)
		var ph := fmod(time, period) / 0.7
		if ph < 1.0:
			var sx := L + W * (0.15 + 0.7 * fposmod(k * 0.618, 1.0))
			var sy := T + H * (0.05 + 0.22 * fposmod(k * 0.382, 1.0))
			var dirv := Vector2(-1.0 if k % 2 == 0 else 1.0, 0.45).normalized()
			var head := Vector2(sx, sy) + dirv * 260.0 * ph
			var fade := sin(ph * PI)
			for j in 6:
				var a := head - dirv * (j * 9.0)
				draw_rect(Rect2(a - Vector2(1, 1), Vector2(3 - j * 0.35, 2)), Color(0.9, 0.95, 1.0, fade * (1.0 - j / 6.0)))
	# rain: slanted streaks and splash rings near the bottom of the view
	if rain:
		draw_rect(v, Color(0.2, 0.26, 0.38, 0.16 if storm else 0.1))
		if storm:                        # heavier, wind-driven sheets of rain
			for i in _rain.size():
				var r2: Vector2 = _rain[i]
				var gx := fmod(r2.y * 1.7 + time * 0.12, 1.0) * (W + 120) - 60
				var gy := fposmod(r2.x * 1.3 + time * 1.45, 1.0) * (H + 40) - 20
				var q0 := Vector2(L + gx, T + gy)
				draw_line(q0, q0 + Vector2(-7, 15), Color(0.85, 0.9, 1, 0.42), 1.2)
		for i in _rain.size():
			var r: Vector2 = _rain[i]
			var fx := fmod(r.x + time * 0.05, 1.0) * (W + 60) - 30
			var fy := fposmod(r.y + time * (1.1 + (i % 4) * 0.15), 1.0) * (H + 40) - 20
			var p0 := Vector2(L + fx, T + fy)
			var near := i % 3 == 0
			draw_line(p0, p0 + (Vector2(-3.5, 17) if near else Vector2(-2.2, 11)), Color(0.88, 0.93, 1, 0.75 if near else 0.5), 1.6 if near else 1.1)
		for i in 18:
			var k := fmod(time * 1.7 + i * 0.37, 1.0)
			var c := Vector2(L + fmod(i * 0.618 + floor(time * 1.7 + i * 0.37) * 0.29, 1.0) * W, T + H * (0.35 + fmod(i * 0.41, 0.6)))
			draw_arc(c, 2 + k * 7, 0, TAU, 12, Color(0.85, 0.92, 1, 0.35 * (1 - k)), 1.0)
	# butterflies on sunny outdoor days
	if not indoor and not rain and not is_night and not realm and not dark_cave():
		for i in 7:
			var bx := fposmod(i * 0.618 + sin(time * 0.11 + i) * 0.18, 1.0) * W
			var by := fposmod(i * 0.37 + cos(time * 0.09 + i * 2) * 0.15, 1.0) * H
			var flap := absf(sin(time * 14.0 + i)) * 2.6 + 0.8
			var bc := Color(1, 0.85, 0.4, 0.95) if i % 2 == 0 else Color(0.95, 0.75, 0.95, 0.95)
			draw_rect(Rect2(L + bx - flap - 0.5, T + by, flap, 2.4), bc)
			draw_rect(Rect2(L + bx + 0.5, T + by, flap, 2.4), bc)
	# windy days: leaves and petals carried sideways
	if weather == "berangin" and not indoor and not realm:
		for i in 35:
			var fx := fmod(i * 0.618 + time * (0.09 + (i % 4) * 0.02), 1.0) * (W + 40) - 20
			var fy := fposmod(i * 0.37 + sin(time * 1.3 + i) * 0.03, 1.0) * H
			var lc := Color(1, 0.78, 0.86, 0.9) if i % 3 == 0 else Color(0.55, 0.75, 0.4, 0.9)
			draw_set_transform(Vector2(L + fx, T + fy), sin(time * 4 + i) * 0.8)
			draw_rect(Rect2(-2, -1, 4, 2.4), lc)
			draw_set_transform(Vector2.ZERO)

	if flash > 0.01:                     # lightning lights the whole view for a moment
		draw_rect(v, Color(0.86, 0.9, 1.0, 0.26 * flash))
