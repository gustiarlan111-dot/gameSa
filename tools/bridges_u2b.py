#!/usr/bin/env python3
"""U2b: bridges with real height and rails.

The bridges of Taman Kota and the Plaza canal are painted flat on the ground, level with the water.
This patch (idempotent: it replaces only its own entries) gives each one

  * a height in assets/data/elevation.json: the Plaza bridges arch over the canal (up to the middle,
    down to the far bank), the Taman Kota plank bridge is a raised deck with a short ramp at each end.
    The height layer keeps every pixel where it was for the gameplay camera, so the picture does not
    change, but the couple walks up onto the bridge, the deck throws its shadow on the water and
    cutscene cameras see a real bridge;
  * standing rails or end posts in assets/data/maps.json, with 3D sides (tools/extrude_u2b.py):
    wooden fences along both edges of the Taman Kota deck, posts at the four corners of each Plaza
    bridge (wooden piles on the plank bridges, stone bollards on the stone one).

Run after regenerating either map (taman_kota_hd.py and plaza_hd.py call it on --apply):
    python3 tools/bridges_u2b.py [--check]
"""
import json
import sys
from pathlib import Path

A = Path(__file__).resolve().parents[1] / 'assets'
sys.path.insert(0, str(Path(__file__).resolve().parent / 'worldgen'))
from terrace import elev_dump  # noqa: E402  (the height layer's own one-primitive-per-line format)

# rect = deck (x, y, w, h) in map px; along = walking direction; e = height in picture px of face
BRIDGES = {
    'taman_kota': [dict(id='br_tk', rect=(1402, 1414, 96, 72), along='x', e=4, ramp=8, rails='hd_fence_h')],
    'plaza': [
        dict(id='br_pl0', rect=(436, 1324, 100, 98), along='y', e=6, posts='hd_pier_post'),
        dict(id='br_pl1', rect=(1136, 1324, 128, 98), along='y', e=8, posts='hd_bollard'),
        dict(id='br_pl2', rect=(1856, 1324, 100, 98), along='y', e=6, posts='hd_pier_post'),
    ],
}


def elevation_for(b):
    x, y, w, h = b['rect']
    e = b['e']
    if b['along'] == 'x':                 # raised deck, ramps at the west and east ends
        r = b['ramp']
        return [
            {'id': b['id'], 'kind': 'plateau', 'rect': [x + r, y, w - 2 * r, h], 'e': e},
            {'id': b['id'] + '_w', 'kind': 'slope', 'rect': [x, y, r, h], 'axis': 'x', 'from': 0, 'to': e},
            {'id': b['id'] + '_e', 'kind': 'slope', 'rect': [x + w - r, y, r, h], 'axis': 'x', 'from': e, 'to': 0},
        ]
    half = h // 2                          # an arch: up to the middle of the canal, then down
    return [
        {'id': b['id'] + '_n', 'kind': 'slope', 'rect': [x, y, w, half], 'axis': 'y', 'from': 0, 'to': e},
        {'id': b['id'] + '_s', 'kind': 'slope', 'rect': [x, y + half, w, h - half], 'axis': 'y', 'from': e, 'to': 0},
    ]


def props_for(b):
    x, y, w, h = b['rect']
    if b.get('rails'):                     # fences along the north and south edges (feet on the edge)
        return [{'type': b['rails'], 'x': x + w // 2, 'y': y + 8}, {'type': b['rails'], 'x': x + w // 2, 'y': y + h}]
    t = b['posts']
    return [{'type': t, 'x': px, 'y': py} for py in (y + 8, y + h - 2) for px in (x + 6, x + w - 6)]


def apply(areas=None, write=True):
    mp = A / 'data/maps.json'
    ep = A / 'data/elevation.json'
    M = json.loads(mp.read_text(encoding='utf-8'))
    E = json.loads(ep.read_text(encoding='utf-8'))
    changed = 0
    for area, bridges in BRIDGES.items():
        if areas and area not in areas:
            continue
        ids = set()
        for b in bridges:
            ids.update(p['id'] for p in elevation_for(b))
        prims = [p for p in E['areas'].get(area, []) if p.get('id') not in ids]
        mine = [p for b in bridges for p in elevation_for(b)]
        E['areas'][area] = prims + mine
        props = M['areas'][area]['props']
        add = [p for b in bridges for p in props_for(b)]
        keys = {(p['type'], p['x'], p['y']) for p in add}
        kept = [p for p in props if (p['type'], p['x'], p['y']) not in keys]
        M['areas'][area]['props'] = kept + add
        changed += len(add)
        print('%s: %d bridges, %d height primitives, %d rails/posts' % (area, len(bridges), len(mine), len(add)))
    if write:
        mp.write_text(json.dumps(M, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        ep.write_text(elev_dump(E), encoding='utf-8')
    return changed


if __name__ == '__main__':
    apply(write='--check' not in sys.argv)
