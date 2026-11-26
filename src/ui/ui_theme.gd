class_name UiTheme
extends RefCounted
## Shared colours, fonts and the pixel-art window kit of the interface.
## Every frame, button and plate is drawn here in code at art resolution (one art pixel = PX
## screen pixels) and scaled up with nearest filtering, so the menus share the crisp HD-2D pixel
## look of the 3D world. No image files are used for the UI frames.

# legacy palette (cream cards: minigame boards still use it)
const INK := Color("3b3049")
const INK_SOFT := Color("6a5a80")
const CREAM := Color("fbf3ee")
const PINK := Color("e89cb4")
const PINK_DEEP := Color("c4567e")
const LAVENDER := Color("9b8ab8")
const GOLD := Color("ffd678")
const BG := Color("2c2240")
const NPC_TAG := Color(0.36, 0.58, 0.5)

# HD-2D window palette (night-blue velvet, gilt frame, rose gems)
const PX := 3                          # screen pixels per art pixel
const EDGE := Color("0d0918")          # outline
const WIN_TOP := Color("30264c")
const WIN_BOTTOM := Color("181227")
const WIN_LINE := Color("5d4a80")      # inner bevel line
const GILD := Color("e8c27a")
const GILD_DARK := Color("9c7444")
const GEM := Color("f08fb2")
const TEXT := Color("fbf3ee")          # text on windows
const TEXT_SOFT := Color("c9b9de")
const TEXT_DIM := Color("8f7fa8")
const ROSE := Color("c4567e")
const SKY := Color("8fb8e8")

static var _fonts := {}
static var _boxes := {}


static func font(kind := "body") -> Font:
	if _fonts.has(kind):
		return _fonts[kind]
	var path: String = {"body": "res://fonts/Inter-Medium.otf", "bold": "res://fonts/Inter-Bold.otf",
			"title": "res://fonts/PixelifySans-Bold.ttf", "pixel": "res://fonts/PixelifySans-Bold.ttf",
			"pixel_soft": "res://fonts/PixelifySans-Medium.ttf"}.get(kind, "res://fonts/Inter-Medium.otf")
	var f: Font = load(path)
	if path.contains("Pixelify"):
		# no "fi" ligature (it turned "Sofia" into "Soña"); Inter covers the symbols it lacks
		var v := FontVariation.new()
		v.base_font = f
		var ts := TextServerManager.get_primary_interface()
		v.opentype_features = {ts.name_to_tag("liga"): 0, ts.name_to_tag("clig"): 0}
		v.fallbacks = [load("res://fonts/Inter-Bold.otf")]
		f = v
	_fonts[kind] = f
	return f


# ------------------------------------------------------------------ pixel kit
static func _tex(img: Image) -> ImageTexture:
	img.resize(img.get_width() * PX, img.get_height() * PX, Image.INTERPOLATE_NEAREST)
	return ImageTexture.create_from_image(img)


static func _box(tex: Texture2D, m: Vector4, content: Vector4) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = tex
	s.texture_margin_left = m.x * PX; s.texture_margin_top = m.y * PX
	s.texture_margin_right = m.z * PX; s.texture_margin_bottom = m.w * PX
	s.content_margin_left = content.x; s.content_margin_top = content.y
	s.content_margin_right = content.z; s.content_margin_bottom = content.w
	return s


## Ring distance from the edge, with the four corners cut round.
static func _ring(x: int, y: int, w: int, h: int, cut: int) -> int:
	var cx := mini(x, w - 1 - x)
	var cy := mini(y, h - 1 - y)
	if cx + cy < cut:
		return -1
	return mini(cx, cy) if cx + cy >= cut + 1 or cut == 0 else -2


## Big ornate window: outline, gilt frame, dark gap, bevel line, velvet gradient, rose gem corners
## and a one-pixel drop shadow. `tone` tints the velvet (Color.WHITE = default).
static func window(tone := Color.WHITE, alpha := 0.94, gems := true) -> StyleBoxTexture:
	var key := "win%s%s%s" % [tone.to_html(), alpha, gems]
	if _boxes.has(key):
		return _boxes[key]
	var n := 26
	var img := Image.create(n, n + 1, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for y in n:
		for x in n:
			var r := _ring(x, y, n, n, 2)
			if r == -1:
				continue
			var c: Color
			if r == -2 or r == 0:
				c = EDGE
			elif r == 1:
				c = GILD if y < n / 2 else GILD.lerp(GILD_DARK, 0.55)
				if y == 1 or x == 1:
					c = c.lightened(0.25)
			elif r == 2:
				c = EDGE.lerp(WIN_BOTTOM, 0.4)
			elif r == 3:
				c = WIN_LINE
			else:
				var t := clampf((y - 4.0) / (n - 9.0), 0.0, 1.0)
				c = WIN_TOP.lerp(WIN_BOTTOM, t) * tone
				c.a = alpha
			img.set_pixel(x, y, c)
	if gems:
		for o in [Vector2i(4, 4), Vector2i(n - 5, 4), Vector2i(4, n - 5), Vector2i(n - 5, n - 5)]:
			for d in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]:
				img.set_pixelv(o + d, GILD)
			img.set_pixelv(o, GEM)
	for x in range(2, n - 2):                       # drop shadow row
		img.set_pixel(x, n, Color(0, 0, 0, 0.35))
	var s := _box(_tex(img), Vector4(7, 7, 7, 8), Vector4(28, 24, 28, 24))
	_boxes[key] = s
	return s


## Small bevelled box for buttons, pills and plates. kind: "plain", "accent", "plate:<rrggbb>", "inset".
## state: normal / hover / pressed / focus / disabled.
static func button_box(kind := "plain", state := "normal") -> StyleBoxTexture:
	var key := "btn%s%s" % [kind, state]
	if _boxes.has(key):
		return _boxes[key]
	var fill := Color("2c2246")
	var border := Color("7b67a0")
	if kind == "accent":
		fill = ROSE; border = GILD
	elif kind.begins_with("plate:"):
		fill = Color(kind.substr(6)); border = GILD
	elif kind == "inset":
		fill = Color(0.07, 0.05, 0.12, 0.55); border = Color(WIN_LINE, 0.8)
	if state == "hover" or state == "focus":
		fill = fill.lightened(0.12); border = Color("ffe3a3")
	elif state == "pressed":
		fill = fill.darkened(0.18)
	elif state == "disabled":
		fill = fill.lerp(Color("1d1728"), 0.6); border = border.lerp(Color("3a3248"), 0.7)
	var n := 14
	var img := Image.create(n, n + 1, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for y in n:
		for x in n:
			var r := _ring(x, y, n, n, 1)
			if r == -1:
				continue
			var c := fill
			if r == -2 or r == 0:
				c = EDGE
			elif r == 1:
				c = border
			elif kind == "inset":
				c = fill if y > 2 else fill.darkened(0.3)
			elif y == 2 and state != "pressed" or y == n - 3 and state == "pressed":
				c = fill.lightened(0.28)              # bevel highlight
			elif y == n - 3 or y == 2:
				c = fill.darkened(0.28)
			elif y < n / 2:
				c = fill.lightened(0.05)
			img.set_pixel(x, y, c)
	if (state == "focus" or state == "hover") and kind != "inset":
		for p in [Vector2i(2, 2), Vector2i(n - 3, 2), Vector2i(2, n - 3), Vector2i(n - 3, n - 3)]:
			img.set_pixelv(p, Color("fff3cf"))
	if kind != "inset" and state != "pressed":
		for x in range(1, n - 1):
			img.set_pixel(x, n, Color(0, 0, 0, 0.4))
	var cm := Vector4(18, 9, 18, 11) if kind != "inset" else Vector4(14, 10, 14, 10)
	var s := _box(_tex(img), Vector4(4, 4, 4, 5), cm)
	_boxes[key] = s
	return s


## A PanelContainer framed as a window.
static func window_panel(margin := Vector4(30, 24, 30, 24), tone := Color.WHITE, alpha := 0.94) -> PanelContainer:
	var pc := PanelContainer.new()
	var st: StyleBoxTexture = window(tone, alpha).duplicate()
	st.content_margin_left = margin.x; st.content_margin_top = margin.y
	st.content_margin_right = margin.z; st.content_margin_bottom = margin.w
	pc.add_theme_stylebox_override("panel", st)
	pc.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return pc


## Gilt rule with a rose diamond in the middle (pixel art, drawn with rects).
static func draw_divider(ci: CanvasItem, cx: float, y: float, w: float, a := 1.0) -> void:
	var p := float(PX)
	ci.draw_rect(Rect2(cx - w / 2, y, w, p), Color(GILD, 0.75 * a))
	ci.draw_rect(Rect2(cx - w / 2, y + p, w, p), Color(EDGE, 0.5 * a))
	ci.draw_rect(Rect2(cx - p * 1.5, y - p, p * 3, p * 3), Color(GILD, a))
	ci.draw_rect(Rect2(cx - p / 2, y - p * 2, p, p * 5), Color(GILD, a))
	ci.draw_rect(Rect2(cx - p * 2.5, y, p * 5, p), Color(GILD, a))
	ci.draw_rect(Rect2(cx - p / 2, y, p, p), Color(GEM, a))
	for sx in [-1, 1]:
		ci.draw_rect(Rect2(cx + sx * (w / 2 + p * 2) - p / 2, y, p, p), Color(GILD, 0.75 * a))


## Pixel triangle pointing down (dialog "next") or right (cursor).
static func draw_arrow(ci: CanvasItem, pos: Vector2, c: Color, down := true, s := 4) -> void:
	var p := float(PX)
	for i in s:
		var len := (s - i) * 2 - 1
		if down:
			ci.draw_rect(Rect2(pos.x + i * p, pos.y + i * p, len * p, p), c)
		else:
			ci.draw_rect(Rect2(pos.x + i * p, pos.y + i * p, p, len * p), c)


## Control that draws a divider; for use in containers.
static func divider(w := 260.0) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(w + PX * 6, PX * 6)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.draw.connect(func(): draw_divider(c, c.size.x / 2, c.size.y / 2 - PX / 2.0, w))
	return c


## Round pixel disc (touch buttons, joystick). ring = border colour, fill can be translucent.
static func disc(d: int, fill: Color, ring: Color, hi := true) -> ImageTexture:
	var key := "disc%d%s%s%s" % [d, fill.to_html(), ring.to_html(), hi]
	if _boxes.has(key):
		return _boxes[key]
	var img := Image.create(d, d, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var r := d / 2.0
	for y in d:
		for x in d:
			var dist := Vector2(x + 0.5 - r, y + 0.5 - r).length()
			if dist > r:
				continue
			var c := fill
			if dist > r - 1:
				c = EDGE
			elif dist > r - 2:
				c = ring
			elif hi and y < r * 0.55 and dist < r - 3:
				c = fill.lightened(0.18)
			img.set_pixel(x, y, c)
	var t := _tex(img)
	_boxes[key] = t
	return t


static func panel(bg := CREAM, border := Color(0.84, 0.74, 0.86), radius := 18, border_w := 3, shadow := 14) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(border_w)
	s.set_corner_radius_all(radius)
	s.shadow_color = Color(0.1, 0.05, 0.15, 0.35)
	s.shadow_size = shadow
	s.shadow_offset = Vector2(0, 5)
	s.anti_aliasing = true
	return s


static func label(text: String, size: int, color: Color, kind := "body") -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font(kind))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l


static func button(text: String, size := 22, accent := false) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_ALL
	b.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	b.add_theme_font_override("font", font("pixel"))
	b.add_theme_font_size_override("font_size", size)
	style_button(b, accent)
	return b


## (Re)applies the pixel button look; accent = the rose "main action" variant.
static func style_button(b: Button, accent := false) -> void:
	var fg := TEXT
	b.add_theme_color_override("font_color", fg)
	b.add_theme_color_override("font_hover_color", Color("fff6dc"))
	b.add_theme_color_override("font_pressed_color", fg.darkened(0.1))
	b.add_theme_color_override("font_focus_color", Color("fff6dc"))
	b.add_theme_color_override("font_disabled_color", Color(TEXT_SOFT, 0.45))
	b.add_theme_color_override("font_outline_color", Color(EDGE, 0.85))
	b.add_theme_constant_override("outline_size", 4)
	var k := "accent" if accent else "plain"
	for st in ["normal", "hover", "pressed", "focus", "disabled"]:
		b.add_theme_stylebox_override(st, button_box(k, st))


## Draws text whose top edge is at y (y-down), wrapping when width > 0. outline > 0 adds a dark
## pixel outline (for titles over pictures).
static func draw_text(ci: CanvasItem, s: String, x: float, y: float, size: int, c: Color, align := "left", width := 0.0, kind := "body", outline := 0) -> void:
	var f := font(kind)
	var ha := HORIZONTAL_ALIGNMENT_LEFT
	if align == "center":
		ha = HORIZONTAL_ALIGNMENT_CENTER
	elif align == "right":
		ha = HORIZONTAL_ALIGNMENT_RIGHT
	var base := y + f.get_ascent(size) * 0.82 + size * 0.1
	if width > 0:
		if outline > 0:
			ci.draw_multiline_string_outline(f, Vector2(x, base), s, ha, width, size, -1, outline, Color(EDGE, c.a))
		ci.draw_multiline_string(f, Vector2(x, base), s, ha, width, size, -1, c)
	else:
		if outline > 0:
			ci.draw_string_outline(f, Vector2(x, base), s, ha, -1.0, size, outline, Color(EDGE, c.a))
		ci.draw_string(f, Vector2(x, base), s, ha, -1.0, size, c)


## Loads a texture outside _draw (a texture first loaded during _draw renders white on GL compatibility).
static func icon_button(text: String, tex: Texture2D, size := 22) -> Button:
	var b := button(text, size)
	b.icon = tex
	b.expand_icon = true
	b.add_theme_constant_override("icon_max_width", 48)
	return b


const _ICONS := {
	"coin": ["..####..", ".#oooo#.", "#oyyyyo#", "#oy##yo#", "#oy##yo#", "#oyyyyo#", ".#oooo#.", "..####.."],
	"heart": [".##..##.", "#pp##pp#", "#pwpppp#", "#pppppp#", ".#pppp#.", "..#pp#..", "...##...", "........"],
}


## Tiny pixel icons drawn from the patterns above (# outline, o/y gold, p rose, w shine).
static func icon(id: String) -> ImageTexture:
	var key := "icon" + id
	if _boxes.has(key):
		return _boxes[key]
	var rows: Array = _ICONS.get(id, _ICONS.coin)
	var img := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var pal := {"#": EDGE, "o": Color("c98a2c"), "y": Color("ffd24a"), "p": Color("ef6f98"), "w": Color("ffe1ec")}
	for y in rows.size():
		for x in rows[y].length():
			var ch: String = rows[y][x]
			if pal.has(ch):
				img.set_pixel(x, y, pal[ch])
	var t := _tex(img)
	_boxes[key] = t
	return t
