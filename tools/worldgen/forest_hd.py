"""Hutan Bisik, dense HD forest (3200x2400 world, 2 texels per unit).

Same trail network, doors, quest points and gates as before (trails are traced from the
previous ground), but the woods are now a real forest:
  * deep woods: a continuous canopy painted from leaf clusters, solid (you walk the trails)
  * forest edge: overlapping HD trees, bushes, ferns, logs and mushrooms along every trail
  * hidden side trails lead to every off-path collectible (stars, planks, chests)
  * rocky cliffs with stone stairs on the two terraces, a stream with rocky banks,
    a waterfall and a plank bridge that is broken until the story fixes it
  * clearings: the mushroom ring, the camp (tent, fire, log benches) and the chest glade
Usage: python3 tools/worldgen/forest_hd.py [--preview OUT.png] [--apply]
"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'artkit'))
from hdmap import HDMap, K, GRASS, PATH, STONE, WATER, DECK, SOIL, A   # noqa: E402
from paint import rgb, wear, moss                                     # noqa: E402
from ground import dist_from, noise                                   # noqa: E402
import common                                                         # noqa: E402

AREA, W, H = 'hutan_bisik', 3200, 2400
SEED = int(hashlib.sha256(b'hutan_bisik_dense').hexdigest()[:8], 16)
CANOPY = 12                       # material id: solid canopy
CLEARINGS = [(1600, 600, 150, 120), (1470, 1440, 210, 160), (2075, 270, 130, 100), (640, 1060, 140, 70)]
CLIFFS = [(120, 584, 580, 664), (680, 584, 1140, 664), (2600, 760, 2820, 840), (2900, 776, 3200, 840)]
STAIRS = [(580, 584, 100, 80), (2820, 760, 80, 80)]
BRIDGE = (2300, 962, 160, 76)
OLD_TO_NEW = {'v41_cave_entrance_cave': 'hd_cave_mouth', 'v41_waterfall_hb_waterfall': 'hd_waterfall',
              'tent': 'hd_tent', 'campfire': 'hd_campfire', 'log_bench': 'hd_log_bench', 'log_bench_b': 'hd_log_bench_b',
              'stone_lantern': 'hd_stone_lantern', 'stone_lantern_e': 'hd_stone_lantern', 'carving_moon': 'hd_carving_moon',
              'carving_star': 'hd_carving_star', 'chest': 'hd_chest', 'chest_hs': 'hd_chest', 'chest_open': 'hd_chest_open',
              'bridge_broken_hb': 'hd_bridge_broken', 'bridge_fixed_hb': 'hd_bridge_fixed', 'signpost_e2': 'hd_signpost_hill',
              'signpost_s2': 'hd_signpost_park', 'signpost_hx': 'hd_signpost_camp', 'v51_cliff_moss': 'hd_rock_ledge',
              'hd_bench': 'hd_log_bench_b'}
DROP = ('hd_signpost',)               # duplicate of the camp signpost
TREES = ['hd_tree_oak_a', 'hd_tree_oak_b', 'hd_tree_oak_c', 'hd_tree_pine_a', 'hd_tree_pine_b', 'hd_tree_dark_a',
         'hd_tree_dark_b', 'hd_tree_big_a', 'hd_tree_big_b', 'hd_tree_willow', 'hd_tree_autumn_a']
TREE_W = [5, 4, 3, 5, 5, 4, 4, 3, 3, 1, 1]


def old_masks():
    im = np.asarray(Image.open(A / 'maps/hutan_bisik.png').convert('RGB')).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    path = (r > 150) & (r - b > 35) & (g > 130)
    path = ndimage.binary_closing(ndimage.binary_opening(path, iterations=2), iterations=4)
    water = (b > r + 40) & (b > 120)
    water = ndimage.binary_opening(water, iterations=2)
    wl, wn = ndimage.label(water)
    wsz = ndimage.sum(water, wl, range(1, wn + 1))
    water = np.isin(wl, [i + 1 for i, s in enumerate(wsz) if s > 20000])          # the stream only
    water = ndimage.binary_closing(water, iterations=3)
    yy, xx = np.mgrid[0:H, 0:W]
    stream_band = (xx > 2270) & (xx < 2500)
    path &= ~(stream_band & ~((yy > BRIDGE[1]) & (yy < BRIDGE[1] + BRIDGE[3])))
    lab, n = ndimage.label(path)
    sz = ndimage.sum(path, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s > 5000])
    return keep, water


def up(mask):
    return np.repeat(np.repeat(mask, K, 0), K, 1)


def canopy_tile(seed, size=512):
    """Seamless-ish tile of overlapping crowns seen from above (dark, lit top-left)."""
    import kit, nature
    sp = kit.Sprite(size, size)
    rng = np.random.default_rng(seed)
    cl = []
    for i in range(150):
        x, y = rng.uniform(-30, size + 30), rng.uniform(-30, size + 30)
        r = rng.uniform(30, 62)
        cl.append((x, y, r, rng.uniform(0.2, 0.7)))
        for dx in (-size, 0, size):              # wrap in x and y so tiles join without seams
            for dy in (-size, 0, size):
                if (dx or dy) and abs(x + dx - size / 2) < size / 2 + 70 and abs(y + dy - size / 2) < size / 2 + 70:
                    cl.append((x + dx, y + dy, r, 0.4))
    R = kit.LEAF_DARK
    nature._leafy_cluster_field(sp, cl, R, seed)
    img = sp.rgb.copy()
    img[sp.a < 0.5] = R[0]
    return img * 0.86


def design(m, P, path_w, water_w):
    c = m.c
    # forest floor: deep green with moss and leaf litter
    floor = c.grass(('#2f5a39', '#35633e', '#3c6c43', '#447549', '#4c7f4f', '#558955'))
    c.put(np.ones((c.h, c.w), bool), floor, GRASS)
    lit = noise(c.h, c.w, 160, SEED + 2)
    c.img[lit > 0.66] = c.img[lit > 0.66] * 1.08
    rng0 = np.random.default_rng(SEED + 5)                # fallen leaves: tiny warm flecks
    for _ in range(c.h * c.w // 900):
        y, x = rng0.integers(0, c.h - 2), rng0.integers(0, c.w - 3)
        c.img[y:y + 2, x:x + 3] = rgb(('#8a6a3a', '#a7743a', '#6f5a2e', '#b98a4a')[rng0.integers(0, 4)])
    # trails (+ hidden side trails to collectibles)
    trails = up(path_w)
    for x, y in m.side_points:
        best = np.argwhere(path_w[::8, ::8])
        if not len(best):
            continue
        d = (best[:, 1] * 8 - x) ** 2 + (best[:, 0] * 8 - y) ** 2
        ty, tx = best[d.argmin()] * 8
        trails |= m.path([(x, y), ((x + tx) / 2 + 20, (y + ty) / 2), (tx, ty)], 30, 3, int(x))
    for x0, y0, w, h in STAIRS:                            # connect trails through the stair gaps
        trails |= m.path([(x0 + w / 2, y0 - 60), (x0 + w / 2, y0 + h + 60)], 54, 2, int(x0))
    for cx, cy, rx, ry in CLEARINGS:
        trails |= m.ellipse(cx, cy, rx * 0.55, ry * 0.5, 8, int(cx))
    dirt = c.dirt(('#7d6043', '#8a6a4a', '#957553', '#a0805c'))
    c.put(trails, dirt, PATH)
    m.trails = trails
    # clearings: lighter grass and flowers
    for cx, cy, rx, ry in CLEARINGS:
        cl = m.ellipse(cx, cy, rx, ry, 10, int(cy)) & ~trails
        c.img[cl] = c.img[cl] * 1.18
    # stream with rocky banks
    water = up(water_w)
    c.put(water, c.water(water, ('#1d4a63', '#235770', '#2b6680', '#357792', '#468aa4')), WATER)
    bank = (dist_from(water, 14 * K) > 0) & (dist_from(water, 14 * K) < 9 * K) & ~water
    c.put(bank, c.dirt(('#6b6a62', '#7a786e', '#89867b', '#979488')), STONE)
    rng = np.random.default_rng(SEED + 9)
    ys, xs = np.nonzero(bank[::10, ::10])
    for i in rng.integers(0, len(ys), 900):
        y, x = ys[i] * 10, xs[i] * 10
        r = rng.integers(4, 11)
        b = c.ellipse(x, y, r, r * 0.75)
        c.img[b] = rgb(('#7f8590', '#9aa0a8', '#666b78')[rng.integers(0, 3)])
        c.img[b & (c.yy < y - r * 0.2)] *= 1.15
    dl = dist_from(~water, 6)
    for i, f in ((1, 0.5), (2, 0.25)):
        s = water & (dl == i)
        c.img[s] = c.img[s] * (1 - f) + rgb('#dcf0f6') * f
    m.water_mask = water
    # cliffs: rock faces under the terrace edges, stone stairs in the gaps
    for x0, y0, x1, y1 in CLIFFS:
        face = m.rect(x0, y0, x1 - x0, y1 - y0)
        rock = c.bricks(('#4f5361', '#5c616e', '#6a6f7c', '#777c88'), 52, 26, '#2e313a', salt=int(x0))
        c.put(face, rock, STONE)
        t = np.clip((c.yy / K - y0) / (y1 - y0), 0, 1)
        c.img[face] *= (1.05 - 0.45 * t[face])[:, None]
        strata = face & (np.sin(c.yy * 0.09 + noise(c.h, c.w, 40, int(x0)) * 5) > 0.9)
        c.img[strata] *= 0.75
        top = m.rect(x0, y0 - 8, x1 - x0, 9)
        c.img[top] = c.img[top] * 0.5 + rgb('#4f7e40') * 0.5
        mossy = face & (noise(c.h, c.w, 30, int(y0)) > 0.66) & (t < 0.45)
        c.img[mossy] = c.img[mossy] * 0.4 + rgb('#3a6637') * 0.6
        sh = m.rect(x0, y1, x1 - x0, 16)
        tt = np.clip((c.yy / K - y1) / 16, 0, 1)
        c.img[sh] *= (0.5 + 0.5 * tt[sh])[:, None]
    for x0, y0, w, h in STAIRS:
        n = int(h / 10)
        tex = c.bricks(('#9a9eaa', '#a8acb6', '#b6bac2'), 60, 20, '#5e626c', salt=int(x0) + 3)
        for i in range(n):
            a = y0 + i * h / n
            c.put(m.rect(x0 + 6, a, w - 12, h / n * 0.6), tex, STONE)
            c.put(m.rect(x0 + 6, a + h / n * 0.6, w - 12, h / n * 0.4 + 0.5), tex * 0.62, STONE)
    # deep woods canopy (solid): everything far enough from trails, clearings and water
    free = trails | water | bank | up(np.zeros_like(path_w))
    for x0, y0, x1, y1 in CLIFFS:
        free |= m.rect(x0, y0 - 30, x1 - x0, y1 - y0 + 60)
    small = free[::K * 4, ::K * 4]
    d = ndimage.distance_transform_edt(~small) * 4                   # world units to nearest open ground
    deep = d > 150
    deep = ndimage.binary_opening(deep, iterations=2)
    m.deep_small = deep
    deep_k = np.repeat(np.repeat(deep, K * 4, 0), K * 4, 1)[:c.h, :c.w]
    deep_k = c.wobble(deep_k, 10 * K, 30 * K, 77)
    tiles = [canopy_tile(s) for s in (1, 2, 3)]
    T = 512
    canopy = np.zeros_like(c.img)
    rng = np.random.default_rng(SEED + 21)
    for ty in range(0, c.h, T):
        for tx in range(0, c.w, T):
            t = tiles[rng.integers(0, 3)]
            hh, ww = min(T, c.h - ty), min(T, c.w - tx)
            canopy[ty:ty + hh, tx:tx + ww] = t[:hh, :ww]
    tint = noise(c.h, c.w, 300, SEED + 44)                   # large hue drift hides the tile repeat
    canopy = canopy * (0.88 + 0.24 * tint)[..., None]
    shade = np.clip(dist_from(~deep_k, 60 * K) / (60 * K), 0, 1)
    canopy *= (1.0 - 0.35 * shade)[..., None]
    c.put(deep_k, canopy, CANOPY)
    m.canopy_mask = deep_k
    # edges, wear
    gm = c.mat == GRASS
    c.rim(c.mat == PATH, gm, dark='#3d2f20', ao=(0.82, 0.9))
    c.overhang(c.mat == PATH, gm, 0.35, 1)
    # roots and fallen leaves across trails
    ys, xs = np.nonzero((c.mat == PATH)[::8, ::8])
    for i in rng.integers(0, len(ys), 1500):
        y, x = ys[i] * 8, xs[i] * 8
        k = rng.random()
        if k < 0.5:
            c.img[y:y + 3, x:x + 4] = rgb(('#c98b4a', '#a3693a', '#d9a35c', '#8a6a3a')[rng.integers(0, 4)])
        elif k < 0.6:
            for t in range(rng.integers(10, 26)):
                yy, xx = y + int(np.sin(t * 0.4) * 3), x + t
                if 0 <= yy < c.h - 2 and 0 <= xx < c.w:
                    c.img[yy:yy + 2, xx] = rgb('#5a4030')
        else:
            c.img[y:y + 2, x:x + 2] = rgb('#6b5a48')


def furnish(m, P, old):
    pr = m.prop
    rng = np.random.default_rng(SEED + 31)
    for p in old:
        t = p['type']
        if any(s in t for s in ('tree', 'bush', 'mushroom', 'rock_a', 'rock_b')) or t in DROP:
            continue
        q = dict(p)
        q['type'] = OLD_TO_NEW.get(t, t)
        if 'alt' in q:
            q['alt'] = OLD_TO_NEW.get(q['alt'], q['alt'])
        m.props.append(q)
    # mushroom ring
    for k in range(14):
        a = k / 14 * 2 * np.pi
        pr('hd_mushrooms_glow' if k % 3 == 0 else 'hd_mushrooms', 1600 + np.cos(a) * 70, 600 + np.sin(a) * 44)
    pr('hd_light_shaft', 1640, 700)
    pr('hd_light_shaft', 2120, 380)
    pr('hd_light_shaft', 1420, 1560)
    for x, y in ((1330, 1520), (1610, 1360)):
        pr('hd_log', x, y)
    # forest edge: trees in a band along trails; deep woods behind are painted canopy
    small_open = ~m.deep_small
    trails_s = m.trails[::K * 4, ::K * 4]
    dt = ndimage.distance_transform_edt(~trails_s) * 4
    canopy_s = m.deep_small
    dc = ndimage.distance_transform_edt(~canopy_s) * 4
    water_s = m.water_mask[::K * 4, ::K * 4]
    dw = ndimage.distance_transform_edt(~water_s) * 4
    pts = [(x, y, r) for x, y, r in m.keep_out]

    def ok(x, y, near_tr):
        j, i = int(y / 4), int(x / 4)
        if not (0 <= j < dt.shape[0] and 0 <= i < dt.shape[1]):
            return False
        if dt[j, i] < near_tr or dw[j, i] < 40:
            return False
        for x0, y0, x1, y1 in CLIFFS:
            if x0 - 20 < x < x1 + 20 and y0 - 30 < y < y1 + 50:
                return False
        for px, py, r in pts:
            if (x - px) ** 2 + (y - py) ** 2 < r * r:
                return False
        for cx, cy, rx, ry in CLEARINGS:
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1:
                return False
        return True
    step = 58
    for y in np.arange(60, H - 20, step * 0.8):
        for x in np.arange(30, W - 20, step):
            xx = x + rng.uniform(-22, 22) + (step / 2 if int(y / (step * 0.8)) % 2 else 0)
            yy = y + rng.uniform(-16, 16)
            j, i = int(yy / 4), int(xx / 4)
            if not (0 <= j < dt.shape[0] and 0 <= i < dt.shape[1]):
                continue
            if dc[j, i] > 0 and dc[j, i] < 170 and ok(xx, yy, 46):
                pr(TREES[rng.choice(len(TREES), p=np.array(TREE_W) / sum(TREE_W))], xx, yy)
            elif dc[j, i] == 0 and rng.random() < 0.08 and dt[j, i] > 80:
                pr(TREES[rng.integers(0, 4)], xx, yy)          # a few crowns poking out of the canopy
    # undergrowth along the trail edges and under the trees
    blocked = (m.c.mat == PATH) | (m.c.mat == WATER) | (m.c.mat == STONE) | m.canopy_mask
    m.scatter(['hd_fern_a', 'hd_fern_b', 'hd_grass_tall', 'hd_grass_tall_b', 'hd_bush_a', 'hd_bush_b', 'hd_bush_berry',
               'hd_mushrooms', 'hd_mushrooms_glow', 'hd_flowers_white', 'hd_flowers_violet'],
              [6, 6, 4, 4, 4, 4, 2, 3, 1, 2, 2], 900, (30, 80, W - 60, H - 120), blocked, 6, P)
    m.scatter(['hd_log', 'hd_stump', 'hd_rock_a', 'hd_rock_b', 'hd_rock_ledge_b'], [3, 3, 3, 3, 1], 60,
              (30, 80, W - 60, H - 120), blocked | (dist_from(m.c.mat == PATH, 50 * K) < 26 * K), 30, P)
    m.props = [p for p in m.props if p is not None]


def main():
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = M['areas'][AREA]
    old = [p for p in base['props'] if not any(s in p['type'] for s in ('tree', 'bush', 'mushroom', 'hd_rock'))]
    m = HDMap(AREA, W, H, SEED)
    qp = [(p[3], p[4]) for p in common.migrate_quests(json.loads(json.dumps(Q)), AREA, lambda x, y: (x, y))]
    pts = qp + [(e['x'], e['y']) for e in base.get('examine', [])]
    pts += [(d['tx'], d['ty']) for b in M['areas'].values() for d in b.get('doors', []) if d.get('to') == AREA]
    m.points = [(x, y, 46) for x, y in pts]
    for d in base['doors']:
        x, y, w, h = d['rect']; m.points.append((x + w / 2, y + h / 2, max(w, h) / 2 + 40))
    path_w, water_w = old_masks()
    # off-trail points get a hidden side trail and a cleared spot
    m.side_points = []
    for x, y in pts:
        if 2280 < x < 2500 and 900 < y < 1100:
            continue
        j, i = int(y), int(x)
        win = path_w[max(0, j - 40):j + 40, max(0, i - 40):i + 40]
        if not win.any() and not water_w[min(H - 1, j), min(W - 1, i)]:
            m.side_points.append((x, y))
    m.keep_out = [(x, y, 60) for x, y in pts]
    cache = Path('/tmp/claude-0/forest_design.npz')
    if '--reuse' in sys.argv and cache.exists():
        z = np.load(cache)
        m.c.img, m.c.mat = z['img'], z['mat']
        m.trails, m.water_mask, m.canopy_mask, m.deep_small = z['trails'], z['water'], z['canopy'], z['deep']
    else:
        design(m, P, path_w, water_w)
        np.savez(cache, img=m.c.img, mat=m.c.mat, trails=m.trails, water=m.water_mask, canopy=m.canopy_mask, deep=m.deep_small)
    furnish(m, P, old)
    m.bake_shadows(P)
    base_walls = [w for w in base['walls']]
    solid = ndimage.binary_erosion(m.canopy_mask[::K * 8, ::K * 8], iterations=1)   # 8-unit cells, 8 units inside the edge
    canopy_walls = [[x * 8, y * 8, w * 8, h * 8] for x, y, w, h in common.mask_to_walls(solid, step=1)]
    gates = [dict(g, rect=[BRIDGE[0] + 8, BRIDGE[1], BRIDGE[2] - 16, BRIDGE[3]]) if g.get('openFlag') == 'JEMBATAN_FIXED' else g
             for g in base.get('gates', [])]
    m.collision = lambda P_: base_walls + canopy_walls
    extra = dict(ellipses=[], water=base.get('water', []), animals=base.get('animals', []), gates=gates,
                 waterFlow=base.get('waterFlow'), stairs=[dict(id='cliff%d' % i, rect=list(s), dir='down') for i, s in enumerate(STAIRS)],
                 visualStyle='godot_hd_dense', visualUpdate='godot_forest_dense',
                 v6Layout=dict(version=3, generator='tools/worldgen/forest_hd.py', hd=True))
    print('props', len(m.props), 'canopy walls', len(canopy_walls), 'side trails', len(m.side_points))
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    m.write(base, extra, P, Q, apply='--apply' in sys.argv, preview=prev)


if __name__ == '__main__':
    main()
