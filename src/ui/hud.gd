class_name Hud
extends Control
## Top bar: objective (left) and day, time, weather, coins and closeness (right).

var _objective: Label
var _obj_panel: PanelContainer
var _clock: Label
var _coins: Label
var _hearts: Label
var _right: PanelContainer
var _flash := 0.0

const WEATHER_ICON := {"cerah": "☀", "berawan": "☁", "hujan": "☂", "berangin": "≋"}


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_obj_panel = _pill()
	_obj_panel.position = Vector2(18, 16)
	_objective = UiTheme.label("", 19, UiTheme.TEXT, "bold")
	_obj_panel.add_child(_objective)
	_right = _pill()
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	_right.add_child(row)
	_clock = UiTheme.label("", 18, UiTheme.TEXT, "pixel")
	row.add_child(_clock)
	row.add_child(_sep())
	row.add_child(_icon("coin"))
	_coins = UiTheme.label("", 18, UiTheme.GILD, "pixel")
	row.add_child(_coins)
	row.add_child(_icon("heart"))
	_hearts = UiTheme.label("", 18, UiTheme.GEM, "pixel")
	row.add_child(_hearts)


func _pill() -> PanelContainer:
	var p := PanelContainer.new()
	var st: StyleBoxTexture = UiTheme.button_box("plain").duplicate()
	st.modulate_color = Color(1, 1, 1, 0.94)
	st.content_margin_left = 16; st.content_margin_right = 18; st.content_margin_top = 9; st.content_margin_bottom = 11
	p.add_theme_stylebox_override("panel", st)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(p)
	return p


func _icon(id: String) -> TextureRect:
	var t := TextureRect.new()
	t.texture = UiTheme.icon(id)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.custom_minimum_size = Vector2(24, 24)
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	return t


func _sep() -> ColorRect:
	var c := ColorRect.new()
	c.color = Color(UiTheme.WIN_LINE, 0.9)
	c.custom_minimum_size = Vector2(UiTheme.PX, 21)
	return c


func flash_objective() -> void:
	_flash = 1.6


func refresh(engine: QuestEngine, hidden: bool) -> void:
	visible = not hidden
	var p := engine.p
	_clock.text = "%s %d  ·  %s  %s" % [WorldClock.day_name(p.day), p.day, WorldClock.hhmm(p.minute), ("☾" if engine.weather_now() == "cerah" and WorldClock.is_night(p.minute) else WEATHER_ICON.get(engine.weather_now(), ""))]
	_coins.text = str(p.coins)
	_hearts.text = str(p.affection)
	_right.reset_size()
	_right.position = Vector2(size.x - _right.size.x - 172, 16)
	_fit_objective("✦  " + engine.objective_text())


## The objective pill never runs under the clock pill: long objectives end with an ellipsis.
func _fit_objective(t: String) -> void:
	if _objective.text == t and _obj_panel.size.x + 18 < _right.position.x:
		return
	_objective.text = t
	var maxw := maxf(160.0, _right.position.x - 18 - 14 - 36)
	var f := _objective.get_theme_font("font")
	var fs := _objective.get_theme_font_size("font_size")
	var natural := f.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 4
	_objective.clip_text = natural > maxw
	_objective.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_objective.custom_minimum_size = Vector2(minf(natural, maxw), 0)
	_objective.size = Vector2.ZERO
	_obj_panel.size = Vector2.ZERO
	_obj_panel.reset_size()


func bottom() -> float:
	return maxf(_obj_panel.position.y + _obj_panel.size.y, _right.position.y + _right.size.y)


func _process(delta: float) -> void:
	if _flash > 0:
		_flash -= delta
		var k := clampf(_flash, 0, 1)
		_obj_panel.scale = Vector2.ONE * (1.0 + 0.05 * sin(k * PI))
		_objective.add_theme_color_override("font_color", UiTheme.TEXT.lerp(UiTheme.GILD, k))
