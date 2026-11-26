class_name Elevation
extends RefCounted
## Height layer (V8 "Elevation 3.0"). The game logic stays 2D (movement, collision, NPCs, quests, save);
## this adds a height field e(x, y) on top of it, read from assets/data/elevation.json.
##
## The ground is painted in the oblique HD-2D view: a raised terrace is drawn as its top surface
## plus the retaining wall face below it (face height F map px on the picture). e(x, y) says how
## many picture pixels of "face" a point sits above the street: F on the terrace, falling from F to 0
## across the face strip and along stairs and ramps, 0 everywhere else.
##
## WorldView3D lifts every ground point, prop foot and character to
##     (x, e * tan(PITCH), y + e)        (map px; S scales to metres)
## For the default camera (pitch PITCH) that point projects exactly where the painted pixel was, so
## the gameplay view is unchanged while terraces, walls and stairs gain real height: the wall is a
## vertical surface that casts a shadow, people on the terrace stand up there, a character climbing
## stairs rises step by step, and cutscene cameras at other angles see real depth.
##
## Primitives (rects in map px):
##   {"kind": "plateau", "rect": [x, y, w, h], "e": F}
##   {"kind": "slope",   "rect": [x, y, w, h], "axis": "y"|"x", "from": e0, "to": e1, "stairs": bool}
##       e goes linearly from `from` at the rect's top/left edge to `to` at its bottom/right edge.
## Where primitives overlap the highest value wins.

const AXIS_X := 0
const AXIS_Y := 1


## Parse the JSON list into typed entries (done once per area by Data).
static func prepare(raw: Array) -> Array:
	var out: Array = []
	for p in raw:
		var r: Array = p.get("rect", [])
		if r.size() < 4:
			continue
		var e := {"rect": Rect2(r[0], r[1], r[2], r[3]), "slope": p.get("kind", "plateau") == "slope",
				"axis": AXIS_X if str(p.get("axis", "y")) == "x" else AXIS_Y,
				"from": float(p.get("from", p.get("e", 0.0))), "to": float(p.get("to", p.get("e", 0.0))),
				"stairs": bool(p.get("stairs", false)), "id": str(p.get("id", ""))}
		out.append(e)
	return out


static func _value(p: Dictionary, x: float, y: float) -> float:
	if not p.slope:
		return p.from
	var r: Rect2 = p.rect
	var t := (x - r.position.x) / maxf(r.size.x, 0.001) if p.axis == AXIS_X else (y - r.position.y) / maxf(r.size.y, 0.001)
	return lerpf(p.from, p.to, clampf(t, 0.0, 1.0))


static func _inside(r: Rect2, x: float, y: float) -> bool:
	return x >= r.position.x and x <= r.end.x and y >= r.position.y and y <= r.end.y


## Height of a map point in "face pixels" (0 = street level).
static func at(area: Dictionary, x: float, y: float) -> float:
	var prims: Array = area.get("_elev", [])
	if prims.is_empty():
		return 0.0
	var best := 0.0
	for p in prims:
		if _inside(p.rect, x, y):
			best = maxf(best, _value(p, x, y))
	return best


static func has_any(area: Dictionary) -> bool:
	return not area.get("_elev", []).is_empty()


## True on a stairs slope (walking there is a little slower and sounds like stone steps).
static func on_stairs(area: Dictionary, x: float, y: float) -> bool:
	for p in area.get("_elev", []):
		if p.stairs and _inside(p.rect, x, y):
			return true
	for s in area.get("stairs", []):
		var r: Array = s.get("rect", [])
		if r.size() >= 4 and _inside(Rect2(r[0], r[1], r[2], r[3]), x, y):
			return true
	return false


## Grid lines for a ground mesh over [a, b] on one axis: a regular step plus every primitive edge, each
## edge doubled a hair apart so a height jump becomes a vertical strip instead of a sloped smear.
static func breaks(area: Dictionary, a: float, b: float, axis: int, step: float) -> PackedFloat32Array:
	var vals := {}
	var v := a
	while v < b:
		vals[snappedf(v, 0.001)] = true
		v += step
	vals[b] = true
	for p in area.get("_elev", []):
		var r: Rect2 = p.rect
		var edges := [r.position.x, r.end.x] if axis == AXIS_X else [r.position.y, r.end.y]
		for ed in edges:
			for q in [ed - 0.02, ed, ed + 0.02]:
				if q > a and q < b:
					vals[snappedf(q, 0.001)] = true
	var out := PackedFloat32Array()
	for k in vals.keys():
		out.append(float(k))
	out.sort()
	return out


## True if any primitive touches the rect (so flat tiles keep their cheap single plane).
static func touches(area: Dictionary, r: Rect2) -> bool:
	for p in area.get("_elev", []):
		if p.rect.intersects(r, true):
			return true
	return false
