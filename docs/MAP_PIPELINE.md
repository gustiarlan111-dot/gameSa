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

## 3D view (HD-2D, Godot)

The game always draws in 3D; there is no graphics option.
- `src/world.gd` still runs the game in 2D map pixels (movement, collision, NPCs, doors, quests,
  cutscenes, save) but its 2D layers are hidden. Each prop holder carries metas `img`, `type`,
  `floor`, `alt` for the 3D builder.
- `src/view3d/world_view_3d.gd` (WorldView3D, child of Game) mirrors it: ground tiles as planes
  (1 map px = 1/32 m), props as quads standing on their foot point and leaning back (TILT), one
  MultiMesh per texture, box volumes behind shops/houses/library/cafe/cottages, actors and
  quest markers copied from their 2D sprites every frame (`flat` meta = lies on the ground,
  `skip3d` meta = not mirrored), omni lights + glow at lamps and crystals, sun by the clock
  (east in the morning, west at dusk, shadows), moonlight at night, soft top light indoors.
- Normal maps: `tools/normals.py` writes `assets/props/hd/n/<prop>_n.png`; the 3D materials use
  them. Run it after drawing or changing props, then `godot --headless --path . --import`.
- `src/game/atmosphere.gd` gives the day tint / night / lamp values, runs the screen pass
  `src/fx/post25d.gdshader` (depth blur, bloom, grade, vignette) on CanvasLayer 1 under the HUD
  (layer 2), and draws rain, petals, fireflies and butterflies in 2D. WorldView3D sets the
  viewport canvas transform to match the 3D ground, so 2D overlays and `World.view_rect()` line up.
