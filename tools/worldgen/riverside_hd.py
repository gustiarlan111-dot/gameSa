"""Riverside (Danau), dense HD rebuild (2400x1360 world, 2 texels per unit). All drawn by code:
lake with depth ramp, foam and lilies, stone promenade with iron railings, wooden viewing deck and
fishing pier, sandy west beach with a pulled-up boat, islet, fishing hut on the east shore, meadow
paths to the plaza and dermaga through a dense mixed wood. Same size, doors, examine spot and quest
points as before.

V8.9: the wood and meadow sit on a terrace (e=34, assets/data/elevation.json) behind a stone retaining
wall along the north edge of the promenade: a grand staircase down to the viewing deck, a west stair
where the beach path comes down, an east stair by the benches; railing along the top.
Usage: python3 tools/worldgen/riverside_hd.py [--preview OUT.png] [--apply]
"""
import sys, json, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hdmap import HDMap, K, GRASS, PATH, STONE, WATER, DECK, SAND, A   # noqa: E402
from paint import rgb, wear, moss                                     # noqa: E402
from ground import dist_from, noise                                   # noqa: E402
import common                                                         # noqa: E402
from terrace import Terrace, write_elevation                          # noqa: E402

AREA, W, H = 'riverside', 2400, 1360
SEED = int(hashlib.sha256(b'riverside_hd').hexdigest()[:8], 16)
PROM_TOP = 786
FACE_Y, FACE_H, FACE_X1 = 752, 34, 2260       # terrace wall along the promenade (x 0..FACE_X1)
STAIRS_X = [(276, 60), (1000, 312), (1872, 60)]   # beach path, grand stair to the deck, east stair
TER = Terrace()
ELEVATION = [
    {'id': 'wood_terrace', 'kind': 'plateau', 'rect': [0, 0, FACE_X1, FACE_Y], 'e': FACE_H},
    {'id': 'prom_wall', 'kind': 'slope', 'rect': [0, FACE_Y, FACE_X1, FACE_H], 'axis': 'y', 'from': FACE_H, 'to': 0},
    {'id': 'east_ramp', 'kind': 'slope', 'rect': [FACE_X1, 0, 120, FACE_Y + FACE_H], 'axis': 'x', 'from': FACE_H, 'to': 0},
] + [{'id': 'st%d' % i, 'kind': 'slope', 'rect': [x, FACE_Y, w, FACE_H], 'axis': 'y', 'from': FACE_H, 'to': 0, 'stairs': True}
     for i, (x, w) in enumerate(STAIRS_X)]
DECK_R = (1184, 880, 544, 120)
PIER = (1490, 1000, 70, 110)
HUT_JETTY = (2196, 890, 64, 96)
PATHS = [[(1200, 0), (1200, 120), (1150, 300), (1180, 500), (1200, 700), (1200, 800)],
         [(1150, 300), (800, 380), (450, 420), (375, 380)],
         [(450, 420), (380, 600), (300, 790), (260, 870)],
         [(380, 600), (150, 700)],
         [(1180, 500), (1600, 560), (2000, 522), (2300, 600), (2340, 762), (2400, 762)],
         [(2000, 522), (2200, 380), (2325, 245)]]
EDGE_WALLS = [[0, 0, 20, 1360], [2380, 0, 20, 700], [2380, 825, 20, 535], [0, 0, 1131, 16], [1269, 0, 1131, 16]]


def shore(x):
    """Lake edge y for every world x: promenade shore in the middle/east, a beach bay in the west."""
    x = np.asarray(x, float)
    s = 912 + 8 * np.sin(x / 170.0) + 5 * np.sin(x / 61.0 + 1.3)
    bay = 1010 + 10 * np.sin(x / 90.0)
    t = np.clip((x - 430) / 160.0, 0, 1)
    t = t * t * (3 - 2 * t)
    return bay * (1 - t) + s * t


def design(m):
    c = m.c
    c.put(np.ones((c.h, c.w), bool), c.grass(('#4f9157', '#57995d', '#5fa163', '#68a869', '#72b06f', '#7db876')), GRASS)
    n = noise(c.h, c.w, 140, SEED + 3)
    c.img[n > 0.62] = c.img[n > 0.62] * 0.9 + rgb('#3f7f4a') * 0.1
    c.img[n < 0.3] = c.img[n < 0.3] * 0.93 + rgb('#9cc46a') * 0.07
    X = c.xx / K
    Y = c.yy / K
    sh = shore(X[0])[None, :]
    water = Y > sh
    # beach (west bay) and promenade (rest)
    beach = (~water) & (Y > 850 + 20 * np.sin(X / 70.0)) & (X < 560)
    c.put(beach, c.dirt(('#d8c08e', '#e0c999', '#e8d3a6', '#efdcb2')), SAND)
    prom = (~water) & (Y > PROM_TOP) & (X > 520) & (X < 2300) & ~beach
    c.put(prom, c.tiles('#d9cdb8', '#cfc2ab', 26, grout='#a39278', salt=4), STONE)
    lip = (~water) & (Y > sh - 10) & (X > 470)
    c.put(lip, c.bricks(('#9c958a', '#a8a196', '#b4ada1', '#c0b9ad'), 30, 10, '#6f695f', salt=5), STONE)
    # paths
    gravel = c.dirt(('#b49b74', '#bfa77f', '#c9b28a', '#d4be97'))
    paths = np.zeros((c.h, c.w), bool)
    for i, p in enumerate(PATHS):
        paths |= m.path(p, 50 if i in (0, 4) else 42, 3, i)
    paths &= ~water & ~prom
    c.put(paths, gravel, PATH)
    # lake
    c.put(water, c.water(water, ('#1d4f74', '#245f86', '#2c7198', '#3784aa', '#4b9abd', '#68b2cf')), WATER)
    dl = dist_from(~water, 8)
    for i, f in ((1, 0.55), (2, 0.35), (3, 0.15)):
        sel = water & (dl == i)
        c.img[sel] = c.img[sel] * (1 - f) + rgb('#e4f4f8') * f
    c.img[water & (Y < sh + 8) & (X > 470)] *= 0.62                  # embankment shadow
    # sparkle streaks
    rng = np.random.default_rng(SEED + 4)
    for _ in range(900):
        x, y = rng.uniform(20, W - 20), rng.uniform(930, H - 10)
        if y > shore(x) + 14:
            c.img[m.rect(x, y, rng.uniform(4, 14), 1)] = rgb('#cfeaf4')
    # islet
    isl = m.ellipse(600, 1200, 115, 46, 4, 3)
    c.put(isl, c.dirt(('#d8c08e', '#e0c999', '#e8d3a6')), SAND)
    c.put(m.ellipse(600, 1194, 88, 32, 3, 4), c.grass(), GRASS)
    # viewing deck, pier, hut jetty
    for (x, y, w, h), vert in ((DECK_R, False), (PIER, True), (HUT_JETTY, True)):
        d = m.rect(x, y, w, h)
        c.put(d, c.planks(('#8b5d3c', '#996a46', '#a5754f', '#b07f57'), 16, salt=int(x), vertical=vert), DECK)
        m.walk_over |= d
        c.img[m.rect(x, y + h, w, 8) & water] *= 0.6
        for xx in (x, x + w - 6):
            c.img[m.rect(xx, y, 6, h)] = rgb('#5e3b27')
    m.water_mask = water & ~m.walk_over
    # edges and clutter
    gm = c.mat == GRASS
    c.rim(c.mat == PATH, gm, dark='#86704f', ao=(0.9, 0.95))
    c.overhang(c.mat == PATH, gm, 0.25, 1)
    c.rim(np.isin(c.mat, [STONE, DECK]), gm | (c.mat == PATH) | (c.mat == SAND))
    wear(c, c.mat == STONE, 0.06, salt=2)
    moss(c, c.mat == STONE, gm, 0.4)
    ys, xs = np.nonzero(np.isin(c.mat, [STONE, PATH, SAND])[::8, ::8])
    for i in rng.integers(0, len(ys), 900):
        y, x = ys[i] * 8, xs[i] * 8
        k = rng.random()
        if k < 0.35:
            c.img[y:y + 3, x:x + 4] = rgb(('#f3b8c8', '#f7d4de', '#e996ad')[rng.integers(0, 3)])
        elif k < 0.7:
            c.img[y:y + 3, x:x + 3] = rgb(('#c98b4a', '#a3693a', '#d9a35c')[rng.integers(0, 3)])
        elif c.mat[y, x] == SAND:
            c.img[y:y + 2, x:x + 3] = rgb(('#f4f0e6', '#c9b48a')[rng.integers(0, 2)])   # shells
        else:
            c.img[y:y + 2, x:x + 2] = rgb('#8f877c')
    ys, xs = np.nonzero(gm[::6, ::6])
    for i in rng.integers(0, len(ys), 5200):
        y, x = ys[i] * 6, xs[i] * 6
        if rng.random() < 0.78:
            for d in range(-2, 3):
                h_ = rng.integers(3, 7)
                if x + d * 2 < c.w:
                    c.img[max(0, y - h_):y, x + d * 2] = c.img[y, x] * (1.18 if d % 2 else 0.85)
        else:
            c.img[y:y + 2, x:x + 2] = rgb(('#fbf6ec', '#f7c9d9', '#f4d870', '#c4b2f2')[rng.integers(0, 4)])
    edge = np.minimum.reduce([c.xx, c.yy, c.w - 1 - c.xx, c.h - 1 - c.yy])
    c.img[edge < 10] *= 0.86
    TER.__init__()
    TER.run(m, c, 0, FACE_X1, FACE_Y, FACE_H, STAIRS_X, 60)
    # east end of the wall: a short return so the wall does not just stop in the grass
    c.put(m.rect(FACE_X1 - 6, FACE_Y - 7, 8, FACE_H + 7), c.bricks(('#8d877b', '#999285'), 20, 14, '#5f5a51', salt=61), STONE)
    return water


def furnish(m, P, water):
    pr = m.prop
    rng = np.random.default_rng(SEED + 9)
    c = m.c
    # deck + pier furniture
    pr('hd_telescope', 1470, 896); pr('hd_lifebuoy', 1196, 900); pr('hd_lifebuoy', 1716, 996)
    for y in range(1016, 1110, 30):
        pr('hd_pier_post', 1492, y); pr('hd_pier_post', 1558, y)
    for x in range(1200, 1728, 66):
        if not 1480 < x < 1570:
            pr('hd_pier_post', x, 1004)
    pr('hd_rowboat', 1630, 1090); pr('hd_rowboat', 2300, 1010); pr('hd_rowboat', 250, 1000)
    # east shore: fishing hut + jetty
    pr('hd_fishing_hut', 2230, 884); pr('hd_crate', 2150, 880); pr('hd_barrel', 2306, 870); pr('hd_pier_post', 2198, 984); pr('hd_pier_post', 2258, 984)
    # promenade: benches facing the lake, lamps, railings at the water edge
    for x, y in ((700, 812), (900, 812), (1420, 812), (1660, 812), (2040, 812)):
        pr('hd_bench', x, y)
    # top of the terrace wall: iron railing with stone urn piers at the grand staircase
    xa = 20
    for sx, sw in STAIRS_X + [(FACE_X1 + 14, 0)]:
        xb = sx - 12
        n = max(1, int(round((xb - xa) / 96)))
        for k in range(n):
            pr('hd_railing_iron', xa + (xb - xa) * (k + 0.5) / n, FACE_Y)
        xa = sx + sw + 12
    for x in (STAIRS_X[1][0] - 14, STAIRS_X[1][0] + STAIRS_X[1][1] + 14):
        pr('hd_balustrade_post', x, FACE_Y + 1)
    for x in (STAIRS_X[1][0] + 30, STAIRS_X[1][0] + STAIRS_X[1][1] - 30):
        pr('hd_stair_planter', x, FACE_Y + FACE_H + 40)
    for x in range(600, 2300, 230):
        pr('hd_lamp_gold', x, 800)
    for x in list(range(570, 1080, 100)) + list(range(1782, 2140, 100)):
        pr('hd_railing_iron', x, int(shore(x)) + 6)
    pr('hd_signpost_lake', 1260, 150); pr('hd_signpost', 2290, 700)
    pr('hd_picnic', 260, 330); pr('hd_bin', 1340, 812); pr('hd_bin', 2090, 812)
    pr('hd_flowerbed', 800, 806); pr('hd_flowerbed', 1540, 806); pr('hd_flowerbed', 1780, 806)
    # islet
    pr('hd_tree_willow', 580, 1196); pr('hd_tree_pine_a', 640, 1186); pr('hd_bush_berry', 545, 1212); pr('hd_reeds', 690, 1214)
    # shoreline reeds and lilies
    for _ in range(46):
        x = rng.uniform(30, 2370)
        if 1170 < x < 1740 or 2180 < x < 2280:
            continue
        pr('hd_reeds', x, shore(x) + rng.uniform(8, 22))
    for _ in range(40):
        x = rng.uniform(40, 2360); y = rng.uniform(shore(x) + 30, H - 20)
        if not (1170 < x < 1740 and y < 1130):
            pr(['hd_lily_a', 'hd_lily_b'][rng.integers(0, 2)], x, y)
    # dense mixed wood around the meadow paths
    blocked = (c.mat != GRASS)
    trees = ['hd_tree_oak_a', 'hd_tree_oak_b', 'hd_tree_oak_c', 'hd_tree_cherry_a', 'hd_tree_cherry_b', 'hd_tree_autumn_a',
             'hd_tree_autumn_b', 'hd_tree_pine_a', 'hd_tree_pine_b', 'hd_tree_big_a', 'hd_tree_big_b', 'hd_tree_willow']
    m.scatter(trees, [4, 4, 3, 3, 3, 2, 2, 2, 2, 2, 2, 1], 70, (20, 20, 2360, 200), blocked, 22, P)
    m.scatter(trees, [4, 4, 3, 3, 3, 2, 2, 2, 2, 2, 2, 1], 130, (20, 180, 2360, 560), blocked, 30, P)
    m.scatter(['hd_tree_willow', 'hd_tree_cherry_a', 'hd_tree_cherry_b'], [2, 1, 1], 14, (20, 700, 520, 140), blocked, 26, P)
    m.scatter(['hd_bush_a', 'hd_bush_b', 'hd_bush_berry', 'hd_bush_rose', 'hd_bush_yellow'], [3, 3, 1, 1, 1], 150, (20, 30, 2360, 760), blocked, 14, P)
    m.scatter(['hd_flowers_pink', 'hd_flowers_yellow', 'hd_flowers_violet', 'hd_flowers_white'], [1, 1, 1, 1], 200, (20, 30, 2360, 760), blocked, 8, P)
    m.scatter(['hd_grass_tall', 'hd_grass_tall_b', 'hd_fern_a', 'hd_mushrooms'], [3, 2, 1, 1], 160, (20, 30, 2360, 760), blocked, 10, P)
    m.scatter(['hd_rock_a', 'hd_rock_b', 'hd_stump', 'hd_log'], [3, 2, 2, 1], 26, (20, 30, 2360, 760), blocked, 22, P)


def main():
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = M['areas'][AREA]
    m = HDMap(AREA, W, H, SEED)
    pts = [(p[3], p[4]) for p in common.migrate_quests(json.loads(json.dumps(Q)), AREA, lambda x, y: (x, y)) if p[3] is not None]
    pts += [(e['x'], e['y']) for e in base.get('examine', [])]
    pts += [(d['tx'], d['ty']) for b in M['areas'].values() for d in b.get('doors', []) if d.get('to') == AREA]
    pts += [(base['spawn'][0], base['spawn'][1])]
    m.keep_out = [(x, y, 46) for x, y in pts] + [(1200, 40, 80), (2360, 762, 70)]
    water = design(m)
    furnish(m, P, water)
    keep = {'hd_railing_iron', 'hd_balustrade_post'}
    dropped = [p for p in m.props if p['type'] not in keep and TER.hits(p, P)]
    m.props = [p for p in m.props if p['type'] in keep or not TER.hits(p, P)]
    print('terrace walls', len(TER.walls), 'stairs', len(TER.stairs), 'props dropped', len(dropped))
    m.bake_shadows(P)
    water_walls = HDMap.collision(m, P)
    m.collision = lambda P_: EDGE_WALLS + water_walls + TER.walls
    extra = dict(ellipses=[], stairs=TER.stairs, water=base.get('water', []), animals=base.get('animals', []),
                 visualStyle='godot_hd_dense', visualUpdate='godot_riverside_dense',
                 v6Layout=dict(version=3, generator='tools/worldgen/riverside_hd.py', hd=True))
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    bad = m.write(base, extra, P, Q, apply='--apply' in sys.argv, preview=prev)
    if '--apply' in sys.argv and not bad:
        write_elevation(A, AREA, ELEVATION)


if __name__ == '__main__':
    main()
