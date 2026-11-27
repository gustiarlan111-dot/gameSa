class_name RenderStage
extends TextureRect
## U1: where the world is drawn on big screens, and at what size.
##
## The game is designed for 1280x720 and stretches its 2D with "canvas_items", so the 3D view, the
## 2D overlay and the screen pass are drawn for every physical pixel. A 2.5K tablet (Redmi Pad 2:
## 2560x1600, Mali-G57 MC2) fills 4.4x the pixels of the design for the same picture.
##
## On screens with at least twice the design on both axes the world (World, its Atmosphere and the
## WorldView3D) lives in this SubViewport, whose 2D coordinates are always the logical UI size
## (size_2d_override), so overlays that map world points to the UI line up in both modes:
##   * HD (graphics "Tinggi"/"Ultra", the default): drawn at the full screen size, shown 1:1;
##   * light ("Sedang"/"Rendah"): drawn at the logical size (1280x800 on the Redmi Pad 2) and enlarged
##     2x with nearest filtering. About a third of the pixel work, at the price of coarser edges,
##     which is why it is never the default (the owner wants the game HD).
## The mode follows the setting live. Smaller screens (phones at 1.5x) keep drawing natively.

const BASE := Vector2(1280, 720)
const MIN_SCALE := 2.0
const LIGHT := ["low", "medium"]

var viewport: SubViewport


## How many physical pixels one design pixel gets on this screen (the canvas_items scale).
static func scale_for(physical: Vector2) -> float:
	return minf(physical.x / BASE.x, physical.y / BASE.y)


## Whether the screen is big enough for the stage at all (env STAGE=0/1 forces it, for QA).
static func wanted(physical: Vector2) -> bool:
	var force := OS.get_environment("STAGE")
	if force != "":
		return force == "1"
	return scale_for(physical) >= MIN_SCALE


## Light mode: the world drawn at the logical size. Only on the lighter graphics presets.
static func light_for(quality: String) -> bool:
	return LIGHT.has(quality)


func _init() -> void:
	name = "RenderStage"
	expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	stretch_mode = TextureRect.STRETCH_SCALE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	focus_mode = Control.FOCUS_NONE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	viewport = SubViewport.new()
	viewport.name = "WorldViewport"
	viewport.handle_input_locally = false
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.size_2d_override_stretch = true
	add_child(viewport)
	texture = viewport.get_texture()


func _enter_tree() -> void:
	# the size must be right before the world enters (it frames its camera from it)
	refit()
	if not get_tree().root.size_changed.is_connected(refit):
		get_tree().root.size_changed.connect(refit)
	GameSettings.listen(refit)


## Size the render target for the screen and the current graphics preset.
func refit() -> void:
	if not is_inside_tree():
		return
	var logical := Vector2i(get_tree().root.get_visible_rect().size.round())
	var physical := get_window().size
	viewport.size_2d_override = logical
	viewport.size = logical if light_for(str(GameSettings.value("quality"))) else physical


## For the FPS counter: the size the world is drawn at, in pixels.
static func world_pixels(game) -> Vector2i:
	if game.stage:
		return game.stage.viewport.size
	return game.get_window().size
