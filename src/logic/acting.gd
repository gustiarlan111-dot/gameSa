class_name Acting
extends RefCounted
## U3b: characters act their lines. When someone speaks, their body takes the pose that matches the
## line's expression ("e" in story.json) for a moment: Arland and Sofia use the emotion rows of their
## pose sheets, other NPCs the small procedural gestures of Actor. Cutscene poses always win
## (Game._on_line only acts when the speaker has no pose and is standing still).

const EIGHT := {
	"senang": "senang", "tertawa": "senang", "lega": "senang", "tersenyum": "senang",
	"malu": "malu", "jatuh_cinta": "malu",
	"sedih": "sedih", "khawatir": "sedih",
	"kaget": "kaget",
	"marah": "marah", "kesal": "marah",
	"bingung": "", "penasaran": "", "serius": "", "senyum": "", "neutral": "",
}
const NPC := {
	"tertawa": "laugh", "senang": "nod", "lega": "nod", "malu": "shy", "jatuh_cinta": "shy",
	"kaget": "surprised", "bingung": "ponder", "penasaran": "ponder", "marah": "shake", "kesal": "shake",
}
const HOLD := 1.7          # seconds a reaction pose is held (the next line replaces it)


## Pose name for an expression, "" for none. eight = Arland/Sofia (they have the emotion sheet rows).
static func pose_for(expr: String, eight: bool) -> String:
	if eight:
		return str(EIGHT.get(expr, ""))
	return str(NPC.get(expr, ""))
