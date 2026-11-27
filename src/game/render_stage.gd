class_name RenderStage
extends SubViewportContainer
## U1: draws the world at the design size on big screens.
##
## The game is designed for 1280x720 and stretches its 2D with "canvas_items", so the 3D view, the
## 2D overlay and the screen pass are drawn for every physical pixel. A 2.5K tablet (Redmi Pad 2:
## 2560x1600, Mali-G57 MC2) then fills 4.4x the pixels of the design for the same picture. When the
## screen holds at least twice the design on both axes, the world (World, its Atmosphere and the
## WorldView3D) moves into this SubViewport at the logical size (1280x800 there) and is enlarged
## with nearest filtering, so pixel art stays sharp; the UI stays on the screen at native sharpness.
## Logical units inside equal the UI's, so overlays that map world points to the UI still line up.
## Smaller screens (phones at 1.5x) keep drawing natively: a non-integer nearest enlargement would
## make pixel art uneven.

const BASE := Vector2(1280, 720)
const MIN_SCALE := 2.0

var viewport: SubViewport


## How many physical pixels one design pixel gets on this screen (the canvas_items scale).
static func scale_for(physical: Vector2) -> float:
	return minf(physical.x / BASE.x, physical.y / BASE.y)


## Whether to use the stage for a window of this physical size (env STAGE=0/1 forces it, for QA).
static func wanted(physical: Vector2) -> bool:
	var force := OS.get_environment("STAGE")
	if force != "":
		return force == "1"
	return scale_for(physical) >= MIN_SCALE


func _init() -> void:
	name = "RenderStage"
	stretch = true
	stretch_shrink = 1
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	focus_mode = Control.FOCUS_NONE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	viewport = SubViewport.new()
	viewport.name = "WorldViewport"
	viewport.handle_input_locally = false
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)


func _enter_tree() -> void:
	# the size must be right before the world enters (it frames its camera from it)
	viewport.size = Vector2i(get_tree().root.get_visible_rect().size.round())


## For the FPS counter: the size the world is drawn at, in pixels.
static func world_pixels(game) -> Vector2i:
	if game.stage:
		return game.stage.viewport.size
	return game.get_window().size
