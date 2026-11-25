# Map pipeline (Godot)

Maps live in `assets/data/maps.json` (walls, props, doors, examine, gates, stairs, surface) and are
drawn as HD ground tiles `assets/maps/hd/<area>_<row>_<col>@2x.png` (2 texels per world unit).
Every sprite is drawn by code; nothing is pasted from old PNGs.

## Tools
| Tool | What it does |
|---|---|
| `tools/artkit/` | Art kit: `kit.py` (palette, shading, outlines), `nature.py` (trees, bushes, rocks), `built.py`, `landmarks.py` (houses, cafe, fountains, fences, signs), `forest.py` (cave, waterfall, tent, campfire, chests, bridge, light shafts) |
| `tools/kit_extra.py [ids] [--sheet out.png]` | Renders kit sprites to `assets/props/hd/<id>@2x.png` and registers them in `props.json` (collider `cw`/`ch`, layer) |
| `tools/worldgen/hdmap.py` | Map builder: ground painting helpers, prop placement, shadows, collision, surface grid for footsteps, validation, tile writing |
| `tools/worldgen/plaza_hd.py` | Plaza (done): landmarks, raised gardens and cafe terrace with stairs, fences, canal railings |
| `tools/worldgen/forest_hd.py` | Hutan Bisik (in progress): painted canopy for the deep woods, tree band along trails, cliffs + stairs, stream, hidden side trails to collectibles. `--reuse` skips the ~13 min ground pass |
| `tools/maptool.py check [area]` | Validators: missing assets, navigation, doors, collision on doors/stairs, stairs landings, pixel consistency, performance. Report in `build/map_check.md` |
| `tools/maptool.py catalog OUT.png` / `preview AREA OUT.png --colliders` | Asset catalog sheet, map preview with colliders and stairs |
| `tools/sfx_foliage.py` | Synthesises footstep/rustle sounds |

## Doing the next map
1. Draw any landmark the map needs in `tools/artkit/` and register it in `tools/kit_extra.py`.
2. Copy `plaza_hd.py` or `forest_hd.py` as `<area>_hd.py`; keep doors, examine points, quest points, gates and alt flags.
3. `python3 tools/worldgen/<area>_hd.py --preview out.png`, look at `out_hd.png`, revise.
4. `--apply`, then `godot --headless --path . --import`, `python3 tools/maptool.py check <area>` (0 errors),
   `godot --headless --path . tests/logic_test.tscn`, and an in-game screenshot:
   `godot --path . --rendering-driver opengl3 --resolution 1280x720 -- --shot sofia <area> X Y 90 out.png`.
5. Commit and push; CI builds the APK (release tag `latest`).

## Runtime features used by maps
- Props with `alt` + `altFlag` switch look when the story flag is set (chests, bridge, mural).
- `stairs` entries are checked by maptool; elevation is drawn (cliff/retaining wall faces) and blocked by wall rects except at stairs.
- `surface` (RLE rows, 8-unit cells: g grass, r gravel, s stone, w wood) picks the footstep sound.
- Grass, flowers, ferns, reeds and small bushes sway in the wind and rustle/shake when walked through.

## Status
- Done: Plaza.
- In progress: Hutan Bisik (`forest_hd.py` not applied yet).
- Next: other outdoor areas (jalan_kota, taman_kota, riverside, perumahan, dermaga, bukit_bintang, memory maps), then interiors.
- Known pre-existing validator errors: arland_room `a_frame`, jalan_kota 3 quest points, perpustakaan 2 quest points.

## 2.5D layer (Godot)

- `tools/normals.py` writes `assets/props/hd/n/<prop>_n.png` for every HD prop. Run it after
  drawing or changing props, then `godot --headless --path . --import`.
- `src/world.gd`: props use a CanvasTexture (diffuse + normal) on quality Tinggi; tall props get a
  long sun shadow on the `SunShadows` layer, sheared by `World.sun_dir` (`set_sun`). Actors mirror
  their frame into the same kind of shadow.
- `src/game/atmosphere.gd`: sun path over the day (shadow direction and length, DirectionalLight2D
  for normal-mapped light), drifting cloud shadows (`src/fx/clouds.gdshader`), screen pass
  `src/fx/post25d.gdshader` (depth blur at the top and bottom, bloom, grade, vignette) on CanvasLayer 1
  under the HUD (layer 2).
- Quality: pause menu "Grafik: Rendah / Sedang / Tinggi" (`src/logic/gfx_settings.gd`, stored in
  user://settings.cfg, default Sedang). Env `GFX_QUALITY=0..2` overrides it for screenshots.
  Software-rendered test machine, Hutan Bisik: Rendah 38-40 fps, Sedang 29-31, Tinggi 16-17.
