#!/usr/bin/env python3
"""U2c: an HD unlit lantern for Lantern Field's story lanterns.

The six lanterns the couple lights in chapter 4 (types lantern_off and v41_lantern_off_lantern, lit
look `lantern_post`) were the last 1x sprites in an HD map. This draws the unlit twin of
hd_lantern_post (same post, the paper shade dull and without its glow) and points the three
definitions at HD images; the old 1x files stay, the lantern minigame still uses them.
The new name avoids "lantern_post" on purpose: world.gd gives a light to images with that name.

    python3 tools/lantern_unlit_u2c.py
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'assets'
SRC = A / 'props/hd/hd_lantern_post@2x.png'
OUT = A / 'props/hd/hd_lantern_unlit@2x.png'
SHADE = (34, 40, 62, 84)                 # x0, y0, x1, y1 of the paper shade in the @2x image


def unlit():
    a = np.asarray(Image.open(SRC).convert('RGBA')).astype(np.float32)
    x0, y0, x1, y1 = SHADE
    reg = a[y0:y1, x0:x1]
    al = reg[..., 3]
    reg[al < 230, 3] = 0                                  # the glow halo goes
    r, g, b = reg[..., 0], reg[..., 1], reg[..., 2]
    solid = reg[..., 3] > 0
    stripe = solid & (r > 190) & (g < 165) & (g > 70)     # the shade's orange ribs
    paper = solid & ~stripe & (r > 150) & (r - b > 40)
    lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255.0
    lo, hi = np.array([104, 92, 74], np.float32), np.array([196, 180, 148], np.float32)
    t = np.clip((lum - 0.55) / 0.45, 0, 1)[..., None]
    reg[..., :3] = np.where(paper[..., None], lo + (hi - lo) * t, reg[..., :3])
    reg[..., :3] = np.where(stripe[..., None], np.array([132, 86, 52], np.float32), reg[..., :3])
    # anything left outside the shade that still glows (spill beyond the box) fades too
    rest = a.copy()
    rest[y0:y1, x0:x1] = reg
    halo = (rest[..., 3] > 0) & (rest[..., 3] < 200)
    rest[halo, 3] = 0
    Image.fromarray(rest.clip(0, 255).astype(np.uint8)).save(OUT)


def main():
    unlit()
    sys.path.insert(0, str(ROOT / 'tools'))
    import propsjson
    import extrude_u2b
    pj = A / 'data/props.json'
    data = json.loads(pj.read_text(encoding='utf-8'))
    P = data['props']
    for pid in ('lantern_off', 'v41_lantern_off_lantern'):
        P[pid]['image'] = 'props/hd/hd_lantern_unlit@2x.png'
    P['lantern_post']['image'] = 'props/hd/hd_lantern_post@2x.png'
    extrude_u2b.refresh(data)
    pj.write_text(propsjson.dumps(data), encoding='utf-8')
    subprocess.run([sys.executable, str(ROOT / 'tools/normals.py'), 'hd_lantern_unlit'], check=True)
    print('wrote', OUT.relative_to(ROOT))


if __name__ == '__main__':
    main()
