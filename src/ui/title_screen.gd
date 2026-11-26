class_name TitleScreen
extends Control
## Title -> route choice -> save slot. The live 3D Plaza at dusk plays behind the menus
## (TitleBackdrop); all frames are the pixel window kit from UiTheme.
## Emits start_game(progress, is_new).

signal start_game(progress: Progress, is_new: bool)

var _backdrop: TitleBackdrop
var _shade: TextureRect
var _page: Control
var _fx: Control
var _t := 0.0
var _intro := 0.0
var _stars: Array = []


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if get_parent() is CanvasLayer:
		get_parent().layer = 3             # above the 3D world's screen pass (layer 1)
	_backdrop = TitleBackdrop.new()
	get_parent().add_sibling.call_deferred(_backdrop)
	tree_exiting.connect(func():
		if is_instance_valid(_backdrop):
			_backdrop.queue_free())
	# soft left-to-right shade so the menu reads over the bright plaza
	_shade = TextureRect.new()
	var g := Gradient.new()
	g.set_color(0, Color(0.05, 0.03, 0.1, 0.78)); g.set_color(1, Color(0.05, 0.03, 0.1, 0.0))
	g.add_point(0.45, Color(0.05, 0.03, 0.1, 0.5))
	var gt := GradientTexture2D.new(); gt.gradient = g; gt.width = 256; gt.height = 4
	_shade.texture = gt
	_shade.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_shade.stretch_mode = TextureRect.STRETCH_SCALE
	_shade.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_shade)
	_fx = Control.new()
	_fx.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_fx.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fx.draw.connect(_draw_fx)
	add_child(_fx)
	_page = Control.new(); _page.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_page)
	var r := RandomNumberGenerator.new(); r.seed = 23
	for i in 26:
		_stars.append([r.randf(), r.randf() * 0.42, r.randf() * TAU, r.randi_range(1, 2)])
	Audio.music("menu_theme")
	show_title()


func _process(delta: float) -> void:
	_t += delta
	_intro = minf(1.0, _intro + delta * 1.6)
	_page.modulate.a = _intro
	_page.position.y = (1.0 - _intro) * 18.0
	_fx.queue_redraw()


## Twinkling pixel stars over the dusk sky.
func _draw_fx() -> void:
	var p := float(UiTheme.PX)
	for s in _stars:
		var a := 0.35 + 0.65 * maxf(0.0, sin(_t * 1.3 + s[2]))
		var pos := Vector2(s[0] * size.x, s[1] * size.y).snapped(Vector2(p, p))
		var c := Color(1, 0.95, 0.82, a * 0.9)
		_fx.draw_rect(Rect2(pos, Vector2(p, p)), c)
		if s[3] == 2 and a > 0.75:
			_fx.draw_rect(Rect2(pos - Vector2(p, 0), Vector2(p * 3, p)), Color(c, a * 0.45))
			_fx.draw_rect(Rect2(pos - Vector2(0, p), Vector2(p, p * 3)), Color(c, a * 0.45))


func _clear(left := false) -> VBoxContainer:
	for c in _page.get_children():
		c.queue_free()
	_intro = 0.0
	var box := VBoxContainer.new()
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override("separation", 14)
	if left:
		var m := MarginContainer.new()
		m.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		m.add_theme_constant_override("margin_left", 84)
		m.add_theme_constant_override("margin_top", 40)
		m.add_theme_constant_override("margin_bottom", 40)
		_page.add_child(m)
		box.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		m.add_child(box)
	else:
		var center := CenterContainer.new()
		center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_page.add_child(center)
		center.add_child(box)
	return box


func _heading(text: String, size: int, color := UiTheme.TEXT, kind := "title") -> Label:
	var l := UiTheme.label(text, size, color, kind)
	l.add_theme_color_override("font_outline_color", UiTheme.EDGE)
	l.add_theme_constant_override("outline_size", maxi(6, size / 6))
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.55))
	l.add_theme_constant_override("shadow_offset_x", UiTheme.PX)
	l.add_theme_constant_override("shadow_offset_y", UiTheme.PX)
	return l


func show_title() -> void:
	_shade.visible = true
	var box := _clear(true)
	var logo := HBoxContainer.new()
	logo.add_theme_constant_override("separation", 18)
	logo.add_child(_heading("Arland", 86, UiTheme.TEXT))
	logo.add_child(_heading("&", 86, UiTheme.GEM))
	logo.add_child(_heading("Sofia", 86, UiTheme.TEXT))
	box.add_child(logo)
	var sub := _heading("✦  Our Little Universe  ✦", 28, UiTheme.GILD, "pixel_soft")
	box.add_child(sub)
	var div := UiTheme.divider(300)
	div.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	box.add_child(div)
	var gap := Control.new(); gap.custom_minimum_size = Vector2(0, 14); box.add_child(gap)
	var menu := UiTheme.window_panel(Vector4(26, 24, 26, 26))
	menu.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	box.add_child(menu)
	var mv := VBoxContainer.new()
	mv.add_theme_constant_override("separation", 12)
	menu.add_child(mv)
	var play := UiTheme.button("Mulai Cerita", 28, true)
	play.custom_minimum_size = Vector2(380, 66)
	play.pressed.connect(show_routes)
	mv.add_child(play)
	var g := SaveStore.load_global()
	if g.get("lastRoute") != null and int(g.get("lastSlot", 0)) > 0:
		var r: String = g.lastRoute
		var s := int(g.lastSlot)
		var ld := SaveStore.load_slot(r, s)
		if ld.value != null:
			var cont := UiTheme.button("Lanjutkan  ·  %s, slot %d" % [Routes.display(r), s], 22)
			cont.custom_minimum_size = Vector2(380, 58)
			cont.pressed.connect(func(): start_game.emit(ld.value, false))
			mv.add_child(cont)
	var opt := UiTheme.button("Pengaturan", 22)
	opt.custom_minimum_size = Vector2(380, 58)
	opt.pressed.connect(func(): _settings().open())
	mv.add_child(opt)
	play.grab_focus.call_deferred()
	var ver := UiTheme.label("Versi HD-2D  ·  V8.0", 16, Color(UiTheme.TEXT_SOFT, 0.75), "pixel_soft")
	ver.add_theme_color_override("font_outline_color", Color(UiTheme.EDGE, 0.8))
	ver.add_theme_constant_override("outline_size", 4)
	box.add_child(ver)


var _settings_menu: SettingsMenu
func _settings() -> SettingsMenu:
	if _settings_menu == null:
		_settings_menu = SettingsMenu.new()
		add_child(_settings_menu)
	return _settings_menu


func show_routes() -> void:
	_shade.visible = false
	var box := _clear()
	var head := _heading("Pilih sudut pandang", 44)
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(head)
	var div := UiTheme.divider(320)
	div.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	box.add_child(div)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 40)
	box.add_child(row)
	var info := {Routes.ARLAND: ["Arland", "Jalani kisah ini\ndari mata Arland.", UiTheme.SKY],
			Routes.SOFIA: ["Sofia", "Jalani kisah ini\ndari mata Sofia.", UiTheme.GEM]}
	var first: Button = null
	for r in [Routes.ARLAND, Routes.SOFIA]:
		var card := UiTheme.window_panel(Vector4(22, 22, 22, 22))
		var col := VBoxContainer.new()
		col.add_theme_constant_override("separation", 10)
		card.add_child(col)
		var frame := PanelContainer.new()
		var fs: StyleBoxTexture = UiTheme.button_box("inset").duplicate()
		fs.content_margin_left = 6; fs.content_margin_right = 6; fs.content_margin_top = 6; fs.content_margin_bottom = 0
		frame.add_theme_stylebox_override("panel", fs)
		col.add_child(frame)
		var pic := TextureRect.new()
		pic.texture = Data.portrait(r, "senang")
		pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		pic.custom_minimum_size = Vector2(250, 230)
		pic.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		frame.add_child(pic)
		var name_l := _heading(info[r][0], 34, info[r][2])
		name_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		col.add_child(name_l)
		var tag := UiTheme.label(info[r][1], 17, UiTheme.TEXT_SOFT, "body")
		tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		col.add_child(tag)
		var b := UiTheme.button("Route " + Routes.display(r), 22, r == Routes.SOFIA)
		b.custom_minimum_size = Vector2(250, 56)
		b.pressed.connect(show_slots.bind(r))
		col.add_child(b)
		if first == null:
			first = b
		row.add_child(card)
	var back := UiTheme.button("◀  Kembali", 19)
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	back.custom_minimum_size = Vector2(180, 50)
	back.pressed.connect(show_title)
	box.add_child(back)
	first.grab_focus.call_deferred()


func show_slots(route: String) -> void:
	_shade.visible = false
	var box := _clear()
	var win := UiTheme.window_panel(Vector4(34, 26, 34, 28))
	box.add_child(win)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	win.add_child(v)
	var head := _heading("Route %s" % Routes.display(route), 38)
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(head)
	var sub := UiTheme.label("Pilih slot cerita", 18, UiTheme.GILD, "pixel_soft")
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(sub)
	var div := UiTheme.divider(360)
	div.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(div)
	var focus: Button = null
	for s in range(1, SaveStore.SLOTS + 1):
		var ld := SaveStore.load_slot(route, s)
		var panel := PanelContainer.new()
		var st: StyleBoxTexture = UiTheme.button_box("inset").duplicate()
		st.content_margin_left = 20; st.content_margin_right = 16; st.content_margin_top = 14; st.content_margin_bottom = 14
		panel.add_theme_stylebox_override("panel", st)
		panel.custom_minimum_size = Vector2(660, 0)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 14)
		panel.add_child(row)
		var num := _heading(str(s), 40, UiTheme.GILD)
		num.custom_minimum_size = Vector2(44, 0)
		num.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		num.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		row.add_child(num)
		var info := VBoxContainer.new()
		info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		info.alignment = BoxContainer.ALIGNMENT_CENTER
		row.add_child(info)
		var p: Progress = ld.value
		var title := "Slot kosong"
		var desc := "Mulai kisah baru dari awal."
		if p != null:
			title = Data.chapter_title(Data.step(p.step).get("chapter", ""))
			desc = "Hari %d, %s  ·  %d menit bermain" % [p.day, WorldClock.hhmm(p.minute), int(p.play_seconds / 60)]
			if ld.status == "RECOVERED":
				desc += "  ·  dipulihkan dari cadangan"
		elif ld.status == "CORRUPT":
			title = "Save rusak"; desc = str(ld.error)
		elif ld.status == "INCOMPATIBLE":
			title = "Save lama"; desc = str(ld.error)
		var tl := UiTheme.label(title, 22, UiTheme.TEXT if p != null else UiTheme.TEXT_SOFT, "pixel")
		tl.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		tl.clip_text = true
		info.add_child(tl)
		var dl := UiTheme.label(desc, 16, UiTheme.TEXT_SOFT, "body")
		dl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		info.add_child(dl)
		if p != null:
			var go := UiTheme.button("Lanjutkan", 20, true)
			go.custom_minimum_size = Vector2(150, 52)
			go.pressed.connect(func(): start_game.emit(p, false))
			row.add_child(go)
			var del := UiTheme.button("Hapus", 18)
			del.custom_minimum_size = Vector2(100, 52)
			del.pressed.connect(func():
				SaveStore.delete_slot(route, s)
				show_slots(route))
			row.add_child(del)
			if focus == null:
				focus = go
		elif ld.status != "INCOMPATIBLE":
			var nw := UiTheme.button("Cerita Baru", 20, true)
			nw.custom_minimum_size = Vector2(170, 52)
			nw.pressed.connect(func():
				start_game.emit(Progress.new_game(route, s, Data.first_step, Data.area(Routes.room(route))), true))
			row.add_child(nw)
			if focus == null:
				focus = nw
		v.add_child(panel)
	var back := UiTheme.button("◀  Kembali", 19)
	back.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	back.custom_minimum_size = Vector2(180, 50)
	back.pressed.connect(show_routes)
	v.add_child(back)
	if focus:
		focus.grab_focus.call_deferred()
