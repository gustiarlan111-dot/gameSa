class_name ConfirmBox
extends Control
## Small yes/no card (port of ui/ConfirmBox.java).

var _title: Label
var _text: Label
var _yes: Button
var _no: Button
var _on_yes: Callable
var _on_no: Callable


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	visible = false
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var dim := ColorRect.new(); dim.color = Color(UiTheme.BG, 0.55); dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var center := CenterContainer.new(); center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var pc := UiTheme.window_panel(Vector4(34, 28, 34, 28))
	center.add_child(pc)
	var v := VBoxContainer.new(); v.add_theme_constant_override("separation", 14)
	pc.add_child(v)
	_title = UiTheme.label("", 30, UiTheme.GILD, "title")
	_title.add_theme_color_override("font_outline_color", UiTheme.EDGE)
	_title.add_theme_constant_override("outline_size", 6)
	v.add_child(_title)
	_text = UiTheme.label("", 19, UiTheme.TEXT)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size = Vector2(500, 0)
	v.add_child(_text)
	var row := HBoxContainer.new(); row.alignment = BoxContainer.ALIGNMENT_END; row.add_theme_constant_override("separation", 12)
	v.add_child(row)
	_no = UiTheme.button("", 20)
	_no.custom_minimum_size = Vector2(140, 52)
	_no.pressed.connect(func(): _close(_on_no))
	row.add_child(_no)
	_yes = UiTheme.button("", 20, true)
	_yes.custom_minimum_size = Vector2(140, 52)
	_yes.pressed.connect(func(): _close(_on_yes))
	row.add_child(_yes)


func ask(title: String, text: String, yes: String, on_yes: Callable, no := "", on_no := Callable()) -> void:
	_title.text = title; _text.text = text
	_yes.text = yes; _on_yes = on_yes
	_no.text = no; _no.visible = no != ""; _on_no = on_no
	visible = true
	_yes.grab_focus.call_deferred()


func _close(cb: Callable) -> void:
	visible = false
	if cb.is_valid():
		cb.call()


func _unhandled_key_input(e: InputEvent) -> void:
	if visible and e.pressed and e.keycode == KEY_ESCAPE:
		_close(_on_no)
		get_viewport().set_input_as_handled()
