class_name TouchControls
extends Control
## Floating joystick (left half of the screen), action button and sprint button (port of TouchControls.java).
## Mouse drags work too, so it can be tested on desktop.

signal action_pressed
signal pause_pressed
signal book_pressed

var vec := Vector2.ZERO
var sprint := false
var enabled := true

var _base: TextureRect
var _knob: TextureRect
var _act: TextureButton
var _run: TextureButton
var _pause: Button
var _book: Button
var _origin := Vector2.ZERO
var _finger := -2           # -2 none, -1 mouse, >=0 touch index
const RADIUS := 78.0
var ui_scale := 1.0         # V8 settings: HUD size
var left_hand := false      # V8 settings: joystick on the right, buttons on the left


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_PASS
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_base = _img(UiTheme.disc(56, Color(0.1, 0.07, 0.18, 0.55), Color(UiTheme.GILD, 0.8), false), 168)
	_knob = _img(UiTheme.disc(24, Color("3a2d5c"), UiTheme.GILD), 74)
	_act = _btn(UiTheme.disc(38, UiTheme.ROSE, UiTheme.GILD), 112)
	_act.pressed.connect(func(): action_pressed.emit())
	var act_l := UiTheme.label("Aksi", 22, UiTheme.TEXT, "pixel")
	act_l.add_theme_color_override("font_outline_color", UiTheme.EDGE)
	act_l.add_theme_constant_override("outline_size", 6)
	act_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	act_l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	act_l.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	act_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_act.add_child(act_l)
	_run = _btn(UiTheme.disc(28, Color("2c2246"), Color("7b67a0")), 84)
	_run.toggle_mode = true
	_run.texture_pressed = UiTheme.disc(28, Color("4f3d7a"), UiTheme.GILD)
	_run.toggled.connect(func(on): sprint = on)
	var run_l := UiTheme.label("Lari", 18, UiTheme.TEXT, "pixel")
	run_l.add_theme_color_override("font_outline_color", UiTheme.EDGE)
	run_l.add_theme_constant_override("outline_size", 5)
	run_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	run_l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	run_l.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	run_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_run.add_child(run_l)
	_pause = UiTheme.button("II", 20)
	_pause.focus_mode = Control.FOCUS_NONE
	_pause.custom_minimum_size = Vector2(56, 52)
	_pause.pressed.connect(func(): pause_pressed.emit())
	add_child(_pause)
	_book = UiTheme.button("Buku", 18)
	_book.focus_mode = Control.FOCUS_NONE
	_book.custom_minimum_size = Vector2(72, 52)
	_book.pressed.connect(func(): book_pressed.emit())
	add_child(_book)
	resized.connect(_layout)
	GameSettings.listen(_from_settings)
	_from_settings()


func _from_settings() -> void:
	if not is_inside_tree():
		return
	apply_layout(float(GameSettings.value("hud_scale")), bool(GameSettings.value("left_hand")))


## Size and side of the touch controls (Settings: HUD size, left-handed layout).
func apply_layout(s: float, left: bool) -> void:
	ui_scale = s
	left_hand = left
	_base.size = Vector2.ONE * 168 * s
	_knob.size = Vector2.ONE * 74 * s
	_act.size = Vector2.ONE * 112 * s
	_run.size = Vector2.ONE * 84 * s
	_layout()


func _img(tex: Texture2D, s: float) -> TextureRect:
	var t := TextureRect.new()
	t.texture = tex
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.size = Vector2(s, s)
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	t.modulate.a = 0.55
	add_child(t)
	return t


func _btn(tex: Texture2D, s: float) -> TextureButton:
	var b := TextureButton.new()
	b.texture_normal = tex
	b.ignore_texture_size = true
	b.stretch_mode = TextureButton.STRETCH_SCALE
	b.size = Vector2(s, s)
	b.modulate.a = 0.85
	add_child(b)
	return b


func _rest() -> Vector2:
	var m := 130.0 * ui_scale
	return Vector2(size.x - m if left_hand else m, size.y - m)


func _layout() -> void:
	var s := ui_scale
	var ax := size.x - 150 * s if not left_hand else 150 * s - _act.size.x
	var rx := size.x - 240 * s if not left_hand else 240 * s - _run.size.x
	_act.position = Vector2(ax, size.y - 160 * s)
	_run.position = Vector2(rx, size.y - 104 * s)
	_pause.position = Vector2(size.x - 74, 16)
	_book.position = Vector2(size.x - 156, 16)
	if _finger == -2:
		_place(_rest(), Vector2.ZERO)


func _place(origin: Vector2, offset: Vector2) -> void:
	_base.position = origin - _base.size / 2
	_knob.position = origin + offset - _knob.size / 2


func _input(event: InputEvent) -> void:
	if not enabled or not visible:
		return
	var pos := Vector2.ZERO
	var idx := -3
	var pressed := false
	var moved := false
	if event is InputEventScreenTouch:
		pos = event.position; idx = event.index; pressed = event.pressed
	elif event is InputEventScreenDrag:
		pos = event.position; idx = event.index; moved = true
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and not DisplayServer.is_touchscreen_available():
		pos = event.position; idx = -1; pressed = event.pressed
	elif event is InputEventMouseMotion and _finger == -1:
		pos = event.position; idx = -1; moved = true
	else:
		return
	if moved:
		if idx == _finger:
			_drag(pos)
		return
	var stick_side := pos.x > size.x * 0.55 if left_hand else pos.x < size.x * 0.45
	if pressed and _finger == -2 and stick_side and pos.y > size.y * 0.25:
		_finger = idx
		_origin = pos
		_base.modulate.a = 0.8; _knob.modulate.a = 0.95
		_drag(pos)
		get_viewport().set_input_as_handled()
	elif not pressed and idx == _finger:
		_finger = -2
		vec = Vector2.ZERO
		_base.modulate.a = 0.55; _knob.modulate.a = 0.55
		_place(_rest(), Vector2.ZERO)


func _drag(pos: Vector2) -> void:
	var r := RADIUS * ui_scale
	var off := (pos - _origin).limit_length(r)
	vec = off / r
	if vec.length() < 0.18:
		vec = Vector2.ZERO
	_place(_origin, off)


## While a dialogue box is open only the pause/book buttons stay; the stick and round buttons
## would sit over the text.
func set_talking(on: bool) -> void:
	for n in [_base, _knob, _act, _run]:
		n.visible = not on


func reset() -> void:
	_finger = -2
	vec = Vector2.ZERO
	_place(_rest(), Vector2.ZERO)
