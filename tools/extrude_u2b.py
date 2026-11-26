#!/usr/bin/env python3
"""U2b: silhouettes for the 3D sides of outdoor props (src/view3d/prop_extrude.gd).

Every solid standing prop used outdoors (rocks, posts, benches, fences, planters, lanterns, crates,
stalls...) gets its outer contour traced from the sprite's alpha, simplified, and written to
assets/data/props.json as

    "ext": {"d": depth, "p": [[x, hu, s, sx, sh], ...]}

in map px from the sprite's foot (x right, hu up the sprite), counter-clockwise. The game extrudes
each contour edge backwards by `d`: a point moves straight back on the ground (s = 0) or along the
gameplay camera's view ray (s = 1); s is chosen per point so that from the gameplay camera every
back point still lands inside the painted silhouette, i.e. the picture never changes, while a moving
camera sees sides and tops. (sx, sh) is where the side samples its colour: 1.5 px inside the outline.

Depth comes from the prop's foot box (props.json ch): ch x 1.6 (x 0.8 for fences and rails),
clamped to 4..48 px. Trees, bushes, grass, flowers, open structures and buildings (which get boxes in
world_view_3d.gd) are skipped.

    python3 tools/extrude_u2b.py            # writes props.json
    python3 tools/extrude_u2b.py --check    # prints what would change
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import propsjson  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'assets'

SKIP = ('tree', 'bush', 'grass', 'fern', 'reed', 'mushroom', 'flower', 'gazebo', 'bicycle', 'arch', 'campfire',
        'bunting', 'banner', 'light_shaft', 'garden_plot', 'lantern_string', 'paper_pile', 'swing', 'clothesline')
VOLUME = ('hd_shop_', 'hd_house_', 'hd_library', 'hd_cafe', 'hd_cottage')      # world_view_3d.gd VOLUME
PITCH = math.radians(38.0)
TILT = -(math.pi / 2.0 - PITCH) * 0.55
# how far up the sprite (map px) a point appears per map px it moves straight back on the ground,
# seen from the gameplay camera: (u . back) / (u . sprite_up) with u the camera's up vector
UP_PER_BACK = math.sin(PITCH) / (math.cos(TILT) * math.cos(PITCH) - math.sin(TILT) * math.sin(PITCH))
TOL = 0.6            # contour simplification, map px
# props that carry plants (pots, urns on balustrade posts, topiary): leaves and the flowers among them
# are not extruded, only the pot or post under them (an extruded bush reads as a green barrel)
PLANTED = ('planter', 'balustrade_post')
MAX_PTS = 72


def thin(pid):
    return 'fence' in pid or 'railing' in pid or 'bike_rack' in pid or ('balustrade' in pid and 'post' not in pid)


def candidates(P, M):
    used = set()
    for a in M.values():
        if a.get('indoor') or a.get('room3d'):
            continue
        for p in a['props']:
            used.add(p['type'])
            if p.get('alt'):
                used.add(p['alt'])
    out = []
    for pid in sorted(used):
        d = P.get(pid)
        if not d or d.get('layer', 'sort') != 'sort' or not d.get('cw') or not d.get('ch'):
            continue
        if any(s in pid for s in SKIP) or pid.startswith(VOLUME):
            continue
        out.append(pid)
    return out


def trace(mask):
    """Outer boundary of the largest blob, as (row, col) pixel centres, clockwise in image space."""
    h, w = mask.shape
    m = np.zeros((h + 2, w + 2), bool)
    m[1:-1, 1:-1] = mask
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        return []
    # start: bottom-most row, left-most pixel in it (its left neighbour is empty)
    r0 = ys.max()
    c0 = xs[ys == r0].min()
    nb = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]    # N NE E SE S SW W NW
    pts = [(r0, c0)]
    cur = (r0, c0)
    back = 6                                                   # came from the west
    for _ in range(8 * (h + 2) * (w + 2)):
        found = False
        for k in range(8):
            d = (back + 1 + k) % 8
            nr, nc = cur[0] + nb[d][0], cur[1] + nb[d][1]
            if m[nr, nc]:
                back = (d + 4) % 8
                cur = (nr, nc)
                found = True
                break
        if not found:
            break
        if cur == (r0, c0):
            break
        pts.append(cur)
    return [(r - 1, c - 1) for r, c in pts]


def rdp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = np.asarray(pts[0], float), np.asarray(pts[-1], float)
    ab = b - a
    n = np.hypot(*ab)
    best, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        p = np.asarray(pts[i], float) - a
        dist = abs(ab[0] * p[1] - ab[1] * p[0]) / n if n > 1e-9 else np.hypot(*p)
        if dist > best:
            best, idx = dist, i
    if best <= tol:
        return [pts[0], pts[-1]]
    return rdp(pts[:idx + 1], tol)[:-1] + rdp(pts[idx:], tol)


def inside(mask, k, wmap, hmap, x, hu, grow=0.75):
    """Is map point (x, hu) on the sprite (within `grow` map px of an opaque pixel)?"""
    c = (x + wmap / 2.0) / k
    r = (hmap - hu) / k
    g = grow / k
    # pixels whose centres (index + 0.5) lie within `grow` of the point on both axes
    r0, r1 = int(math.ceil(r - g - 0.5)), int(math.floor(r + g - 0.5))
    c0, c1 = int(math.ceil(c - g - 0.5)), int(math.floor(c + g - 0.5))
    H, W = mask.shape
    r0, c0 = max(0, r0), max(0, c0)
    r1, c1 = min(H - 1, r1), min(W - 1, c1)
    if r0 > r1 or c0 > c1:
        return False
    return bool(mask[r0:r1 + 1, c0:c1 + 1].any())


def foliage(rgba):
    """Leaves (green-dominant, saturated) grown by 3 px so the flowers among them go too."""
    from scipy import ndimage
    c = rgba[..., :3].astype(np.float32)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    mx, mn = c.max(-1), c.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1.0)
    leaf = (g > r * 1.08) & (g > b * 1.02) & (sat > 0.18) & (rgba[..., 3] > 127)
    return ndimage.binary_dilation(leaf, iterations=3)


def profile(pid, d):
    img = Image.open(A / d['image']).convert('RGBA')
    k = 0.5 if '@2x' in d['image'] else 1.0
    if 'scale' in d:
        k = float(d['scale'])
    rgba = np.asarray(img)
    alpha = rgba[..., 3] > 127
    hmap, wmap = alpha.shape[0] * k, alpha.shape[1] * k
    body = alpha & ~foliage(rgba) if any(f in pid for f in PLANTED) else alpha
    pix = trace(body)
    if len(pix) < 8:
        return None
    # image (row, col) -> map (x, hu); counter-clockwise with hu up
    pts = [((c + 0.5) * k - wmap / 2.0, hmap - (r + 0.5) * k) for r, c in pix]
    tol = TOL
    while True:
        # simplify as two open chains so the start point does not force a vertex
        half = len(pts) // 2
        s = rdp(pts[:half + 1], tol)[:-1] + rdp(pts[half:] + [pts[0]], tol)[:-1]
        if len(s) <= MAX_PTS or tol > 4:
            break
        tol *= 1.4
    area = 0.0
    for i in range(len(s)):
        x0, y0 = s[i]; x1, y1 = s[(i + 1) % len(s)]
        area += x0 * y1 - x1 * y0
    if area < 0:
        s = s[::-1]
    depth = float(np.clip(d['ch'] * (0.8 if thin(pid) else 1.6), 4.0, 48.0))
    htop = max(p[1] for p in s)
    out = []
    n = len(s)
    for i, (x, hu) in enumerate(s):
        # ray share: like the room prisms (straight back at the foot, along the ray at the top), raised
        # until the back point's screen position stays on the painting
        sv = min(1.0, max(0.0, hu / max(1.0, htop)))
        while sv < 1.0 and not inside(alpha, k, wmap, hmap, x, hu + (1.0 - sv) * UP_PER_BACK * depth):
            sv = min(1.0, sv + 0.05)
        # colour sample: 1.5 px inside, along the inward normal of the two neighbouring edges
        px, ph = s[i - 1]; nx_, nh_ = s[(i + 1) % n]
        tx, th = nx_ - px, nh_ - ph
        ln = math.hypot(tx, th) or 1.0
        ix, ih = -th / ln, tx / ln                              # CCW: inward is to the left
        sx, sh = x + ix * 1.5, hu + ih * 1.5
        if not inside(alpha, k, wmap, hmap, sx, sh, grow=0.0):
            sx, sh = x, hu
        out.append([round(float(x), 1), round(float(hu), 1), round(float(sv), 2), round(float(sx), 1), round(float(sh), 1)])
    return {"d": round(depth, 1), "p": out}


def refresh(data):
    """Recompute "ext" for every candidate in props.json data (kit tools call this after redrawing)."""
    P = data['props']
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))['areas']
    ids = candidates(P, M)
    made = 0
    for pid in P:
        if pid not in ids:
            P[pid].pop('ext', None)
    for pid in ids:
        e = profile(pid, P[pid])
        if e is None:
            P[pid].pop('ext', None)
            continue
        P[pid]['ext'] = e
        made += 1
    print('extruded %d of %d candidates; points: %d' % (made, len(ids), sum(len(P[i]['ext']['p']) for i in ids if 'ext' in P[i])))
    return made


def main():
    pj = A / 'data/props.json'
    data = json.loads(pj.read_text(encoding='utf-8'))
    refresh(data)
    if '--check' in sys.argv:
        return
    pj.write_text(propsjson.dumps(data), encoding='utf-8')


if __name__ == '__main__':
    main()
