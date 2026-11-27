class_name SettingsMenu
extends Control
## V8 settings window (from the pause menu and the title screen): graphics preset, frame rate,
## music / ambience / effects volume, HUD size and left-handed layout. Every change is saved at once
## (GameSettings) and applied live, so the player sees the effect behind the window.

signal closed

var _rows: VBoxContainer
var _groups := {}            # key -> [[button, value], ...] for the choice rows


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var dim := ColorRect.new(); dim.color = Color(0.05, 0.03, 0.1, 0.55); dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var center := CenterContainer.new(); center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel := UiTheme.window_panel(Vector4(34, 24, 34, 26))
	center.add_child(panel)
	_rows = VBoxContainer.new()
	_rows.add_theme_constant_override("separation", 10)
	panel.add_child(_rows)
	var head := UiTheme.label("Pengaturan", 36, UiTheme.GILD, "title")
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	head.add_theme_color_override("font_outline_color", UiTheme.EDGE)
	head.add_theme_constant_override("outline_size", 7)
	_rows.add_child(head)
	var div := UiTheme.divider(260)
	div.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_rows.add_child(div)
	var qs: Array = []
	for q in GameSettings.QUALITIES:
		qs.append([GameSettings.QUALITY_NAMES[q], q])
	_choice("Kualitas grafis", "quality", qs)
	_choice("Frame rate", "fps", [["30 FPS", 30], ["60 FPS", 60]])
	_slider("Musik", "music")
	_slider("Suasana", "ambience")
	_slider("Efek suara", "sfx")
	_choice("Ukuran kontrol", "hud_scale", [["Kecil", 0.85], ["Normal", 1.0], ["Besar", 1.15], ["Sangat besar", 1.3]])
	_choice("Joystick", "left_hand", [["Kiri", false], ["Kanan", true]])
	_choice("Kilat petir", "lightning", [["Nyala", true], ["Mati", false]])
	_choice("Penghitung FPS", "show_fps", [["Nyala", true], ["Mati", false]])
	var note := UiTheme.label("Rendah: tanpa bayangan dan efek layar, untuk ponsel lama. 30 FPS menghemat baterai.", 15, UiTheme.TEXT_DIM, "body")
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note.custom_minimum_size = Vector2(560, 0)
	_rows.add_child(note)
	var close := UiTheme.button("Tutup", 22, true)
	close.custom_minimum_size = Vector2(200, 54)
	close.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	close.pressed.connect(func(): visible = false; closed.emit())
	_rows.add_child(close)


func open() -> void:
	_refresh()
	visible = true


func _row(title: String) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	var l := UiTheme.label(title, 19, UiTheme.TEXT_SOFT, "body")
	l.custom_minimum_size = Vector2(170, 0)
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	h.add_child(l)
	_rows.add_child(h)
	return h


func _choice(title: String, key: String, options: Array) -> void:
	var h := _row(title)
	var list: Array = []
	for o in options:
		var b := UiTheme.button(str(o[0]), 17)
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_ALL
		b.custom_minimum_size = Vector2(98, 44)
		var v = o[1]
		b.pressed.connect(func(): GameSettings.set_value(key, v); _refresh())
		h.add_child(b)
		list.append([b, v])
	_groups[key] = list


func _slider(title: String, key: String) -> void:
	var h := _row(title)
	var s := HSlider.new()
	s.min_value = 0; s.max_value = 100; s.step = 5
	s.custom_minimum_size = Vector2(330, 40)
	s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var pct := UiTheme.label("", 17, UiTheme.TEXT, "pixel")
	pct.custom_minimum_size = Vector2(56, 0)
	s.value_changed.connect(func(v): pct.text = "%d%%" % int(v); GameSettings.set_value(key, v / 100.0))
	s.set_meta("key", key)
	h.add_child(s)
	h.add_child(pct)
	_groups[key] = s


func _refresh() -> void:
	var d := GameSettings.get_all()
	for key in _groups:
		var g = _groups[key]
		if g is HSlider:
			g.set_value_no_signal(roundf(float(d[key]) * 100.0))
			(g.get_parent().get_child(2) as Label).text = "%d%%" % int(g.value)
		else:
			for pair in g:
				var cur = d[key]
				var on: bool = (absf(float(cur) - float(pair[1])) < 0.01) if (cur is float or cur is int) and not (cur is bool) else cur == pair[1]
				(pair[0] as Button).set_pressed_no_signal(on)
				UiTheme.style_button(pair[0], on)
