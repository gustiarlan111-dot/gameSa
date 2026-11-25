class_name GfxSettings
extends RefCounted
## Graphics quality for the 2.5D layer, kept in user://settings.cfg (separate from the save files,
## so save schema 8 is untouched). 0 Rendah: plain 2D. 1 Sedang: sun shadows, cloud shadows, colour
## grade + vignette. 2 Tinggi: plus normal-mapped sun light, depth blur and bloom.

const PATH := "user://settings.cfg"
const NAMES := ["Rendah", "Sedang", "Tinggi"]


static func quality() -> int:
	var env := OS.get_environment("GFX_QUALITY")
	if env != "":
		return clampi(int(env), 0, 2)
	var c := ConfigFile.new()
	if c.load(PATH) != OK:
		return 1
	return clampi(int(c.get_value("gfx", "quality", 1)), 0, 2)


static func set_quality(q: int) -> void:
	var c := ConfigFile.new()
	c.load(PATH)
	c.set_value("gfx", "quality", clampi(q, 0, 2))
	c.save(PATH)
