"""One-off: toko_bunga and arcade were laid out at twice the scale of the other rooms (1200x896,
furniture twice character size). Halve every coordinate that belongs to them so characters fit.
Saves are converted at load time (Progress, mapLayoutVersion < 6)."""
import json, pathlib
R = pathlib.Path(__file__).resolve().parents[1] / "assets/data"
T = {"toko_bunga", "arcade"}
H = lambda v: round(v / 2) if isinstance(v, int) else v / 2

def dump(name, obj):
    (R / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

maps = json.loads((R / "maps.json").read_text(encoding="utf-8"))
for k in T:
    a = maps["areas"][k]
    a["w"] //= 2; a["h"] //= 2
    a["spawn"] = [H(v) for v in a["spawn"]]
    for key in ("walls", "water", "gates", "elevationPlatforms"):
        a[key] = [[H(v) for v in r] if isinstance(r, list) else r for r in a.get(key, [])]
    for e in a.get("ellipses", []):
        raise SystemExit("ellipses not handled")
    for p in a["props"]:
        p["x"] = H(p["x"]); p["y"] = H(p["y"])
    for d in a["doors"]:
        d["rect"] = [H(v) for v in d["rect"]]
    for e in a.get("examine", []):
        for key in ("x", "y"):
            if key in e: e[key] = H(e[key])
    if a.get("bed"):
        a["bed"] = [H(v) for v in a["bed"]]
for k, a in maps["areas"].items():
    for d in a.get("doors", []):
        if d.get("to") in T:
            d["tx"] = H(d["tx"]); d["ty"] = H(d["ty"])
dump("maps.json", maps)

props = json.loads((R / "props.json").read_text(encoding="utf-8"))
for k in ("maps_v4_arcade_central_cabinets", "maps_v4_toko_bunga_flower_table"):
    props["props"][k]["scale"] = 0.5
dump("props.json", props)

n = [0]
def walk(o):
    if isinstance(o, dict):
        if o.get("area") in T:
            for key in ("x", "y", "wander"):      # r is reach distance: character scale, unchanged
                if isinstance(o.get(key), (int, float)) and not isinstance(o.get(key), bool):
                    o[key] = H(o[key]); n[0] += 1
            spr = o.get("sprite")
            if isinstance(spr, dict):
                for key in ("x", "y"):
                    if key in spr: spr[key] = H(spr[key]); n[0] += 1
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
quests = json.loads((R / "quests.json").read_text(encoding="utf-8"))
walk(quests)
dump("quests.json", quests)
print("quest values halved:", n[0])
