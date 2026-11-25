"""Dermaga Danau, dense HD rebuild (2400x1360 world, 2 texels per unit). All drawn by code: lake with
depth ramp and foam, sandy shore, a long plank pier out to a wide fishing platform, a boat shed with
its own jetty and slipway in the east, a stone overlook north of the pier root, gravel shore path from
the Riverside gate, and a blossoming wood on the meadow. Same size, door, examine spots and quest
points as before.  Usage: python3 tools/worldgen/dermaga_hd.py [--preview OUT.png] [--apply]
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

AREA, W, H = 'dermaga', 2400, 1360
SEED = int(hashlib.sha256(b'dermaga_hd').hexdigest()[:8], 16)
PIER = (1166, 660, 68, 440)          # long pier from the sand to the platform
PLAT = (1016, 1088, 368, 128)        # fishing platform (quest scene, fishing spot)
SHED_JETTY = (1906, 690, 64, 120)
SLIP = (1700, 670, 90, 70)           # boat slipway (sand ramp)
OVERLOOK = (1204, 470, 92)           # stone circle north of the pier root (panorama point)
PATHS = [[(0, 531), (180, 540), (420, 548), (700, 560), (950, 566), (1204, 590), (1204, 650)],
         [(1204, 566), (1500, 578), (1760, 600), (2050, 612), (2400, 600)],
         [(1204, 590), (1204, 520)],
         [(700, 560), (620, 420), (520, 260), (480, 120)],
         [(2050, 612), (2200, 480), (2325, 380)],
         [(420, 548), (300, 625)]]
EDGE_WALLS = [[0, 0, 20, 475], [0, 587, 20, 773], [2380, 0, 20, 1360], [0, 0, 2400, 16]]


def shore(x):
    x = np.asarray(x, float)
    return 700 + 10 * np.sin(x / 150.0) + 6 * np.sin(x / 53.0 + 0.7)


def design(m):
    c = m.c
    c.put(np.ones((c.h, c.w), bool), c.grass(('#4f9157', '#57995d', '#5fa163', '#68a869', '#72b06f', '#7db876')), GRASS)
    n = noise(c.h, c.w, 150, SEED + 3)
    c.img[n > 0.62] = c.img[n > 0.62] * 0.9 + rgb('#3f7f4a') * 0.1
    c.img[n < 0.3] = c.img[n < 0.3] * 0.93 + rgb('#a6c86c') * 0.07
    X = c.xx / K
    Y = c.yy / K
    sh = shore(X[0])[None, :]
    water = Y > sh
    sand = (~water) & (Y > sh - 62 - 10 * np.sin(X / 47.0))
    c.put(sand, c.dirt(('#d8c08e', '#e0c999', '#e8d3a6', '#efdcb2')), SAND)
    c.put(m.rect(*SLIP) & ~water | (m.rect(SLIP[0] + 10, SLIP[1], SLIP[2] - 20, 40) & water),
          c.dirt(('#c9ae7c', '#d4b988', '#bea271')), SAND)
    gravel = c.dirt(('#b49b74', '#bfa77f', '#c9b28a', '#d4be97'))
    paths = np.zeros((c.h, c.w), bool)
    for i, p in enumerate(PATHS):
        paths |= m.path(p, 54 if i < 2 else 40, 3, i)
    paths &= ~water
    c.put(paths, gravel, PATH)
    ox, oy, orad = OVERLOOK
    ring = m.ellipse(ox, oy, orad, orad * 0.62)
    c.put(ring, c.tiles('#d9cdb8', '#cfc2ab', 24, grout='#a39278', salt=6), STONE)
    c.put(m.ellipse(ox, oy, orad * 0.3, orad * 0.19), c.tiles('#c6b79c', '#bcad92', 12, grout='#998a70', salt=7), STONE)
    # lake
    c.put(water, c.water(water, ('#1b4b70', '#225a82', '#2a6c94', '#3480a6', '#4896ba', '#66afcc')), WATER)
    dl = dist_from(~water, 8)
    for i, f in ((1, 0.55), (2, 0.35), (3, 0.15)):
        sel = water & (dl == i)
        c.img[sel] = c.img[sel] * (1 - f) + rgb('#e4f4f8') * f
    rng = np.random.default_rng(SEED + 4)
    for _ in range(1100):
        x, y = rng.uniform(20, W - 20), rng.uniform(720, H - 10)
        if y > shore(x) + 14:
            c.img[m.rect(x, y, rng.uniform(4, 14), 1)] = rgb('#cfeaf4')
    # pier, platform, shed jetty
    for (x, y, w, h), vert in ((PIER, True), (PLAT, False), (SHED_JETTY, True)):
        d = m.rect(x, y, w, h)
        c.put(d, c.planks(('#8b5d3c', '#996a46', '#a5754f', '#b07f57'), 16, salt=int(x), vertical=vert), DECK)
        m.walk_over |= d
        c.img[m.rect(x, y + h, w, 10) & water] *= 0.55
        if vert:
            for xx in (x, x + w - 6):
                c.img[m.rect(xx, y, 6, h)] = rgb('#5e3b27')
        else:
            for yy in (y, y + h - 6):
                c.img[m.rect(x, yy, w, 6)] = rgb('#5e3b27')
    m.water_mask = water & ~m.walk_over
    gm = c.mat == GRASS
    c.rim(c.mat == PATH, gm, dark='#86704f', ao=(0.9, 0.95))
    c.overhang(c.mat == PATH, gm, 0.25, 1)
    c.rim(np.isin(c.mat, [STONE, DECK]), gm | (c.mat == PATH) | (c.mat == SAND))
    wear(c, c.mat == STONE, 0.06, salt=2)
    moss(c, c.mat == STONE, gm, 0.4)
    ys, xs = np.nonzero(np.isin(c.mat, [PATH, SAND])[::8, ::8])
    for i in rng.integers(0, len(ys), 1000):
        y, x = ys[i] * 8, xs[i] * 8
        k = rng.random()
        if k < 0.3:
            c.img[y:y + 3, x:x + 4] = rgb(('#f3b8c8', '#f7d4de', '#e996ad')[rng.integers(0, 3)])
        elif c.mat[y, x] == SAND:
            c.img[y:y + 2, x:x + 3] = rgb(('#f4f0e6', '#c9b48a', '#e8e0d0')[rng.integers(0, 3)])
        else:
            c.img[y:y + 2, x:x + 2] = rgb('#8f877c')
    ys, xs = np.nonzero(gm[::6, ::6])
    for i in rng.integers(0, len(ys), 5600):
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
    return water


def furnish(m, P, water):
    pr = m.prop
    rng = np.random.default_rng(SEED + 9)
    c = m.c
    x, y, w, h = PIER
    for yy in range(y + 40, y + h, 60):                      # posts along both sides of the pier
        pr('hd_pier_post', x - 2, yy); pr('hd_pier_post', x + w + 2, yy)
    for yy in (y + 120, y + 300):
        pr('hd_lamp_gold', x - 4, yy)
    px, py, pw, ph = PLAT
    for xx in range(px + 10, px + pw, 62):
        pr('hd_pier_post', xx, py + ph + 4)
    pr('hd_lamp_gold', px + 8, py + 18); pr('hd_lamp_gold', px + pw - 8, py + 18)
    pr('hd_lifebuoy', px + 40, py + 14); pr('hd_crate', px + pw - 50, py + 24); pr('hd_barrel', px + pw - 80, py + 22)
    pr('hd_bench', px + 90, py + 18)
    pr('hd_rowboat', 1040, 1000); pr('hd_rowboat', 1330, 860); pr('hd_rowboat', 1985, 840)
    pr('hd_rowboat', 1745, 690)                                # pulled up on the slipway
    # boat shed + its jetty, nets and barrels
    pr('hd_fishing_hut', 1838, 598)
    jx, jy, jw, jh = SHED_JETTY
    pr('hd_pier_post', jx, jy + jh + 2); pr('hd_pier_post', jx + jw, jy + jh + 2)
    pr('hd_crate_stack', 1960, 600); pr('hd_barrel', 1990, 640); pr('hd_barrel', 2010, 652); pr('hd_sacks', 1680, 610)
    pr('hd_lantern_post', 1700, 560)
    # overlook: benches and the telescope facing the lake
    ox, oy, orad = OVERLOOK
    pr('hd_telescope', ox + 40, oy - 30); pr('hd_bench', ox - 60, oy - 36); pr('hd_bench', ox + 64, oy + 46)
    pr('hd_flowerbed', ox - 100, oy + 10); pr('hd_flowerbed', ox + 104, oy - 6)
    # shore path furniture
    pr('hd_notice_board', 760, 524)
    pr('hd_signpost_lake', 120, 500); pr('hd_signpost', 1250, 640)
    for xx in (330, 900, 1500, 2150):
        pr('hd_lamp', xx, 530 if xx < 1204 else 560)
    for xx, yy in ((520, 520), (1040, 540), (1640, 556), (2240, 570)):
        pr('hd_bench', xx, yy)
    pr('hd_picnic', 860, 420); pr('hd_bin', 1100, 548); pr('hd_bin', 1880, 660)
    pr('hd_campfire', 360, 690); pr('hd_log_bench', 360, 662)
    # reeds and lilies
    for _ in range(52):
        xx = rng.uniform(30, 2370)
        if 1150 < xx < 1250 or 1690 < xx < 1980:
            continue
        pr('hd_reeds', xx, shore(xx) + rng.uniform(8, 22))
    for _ in range(46):
        xx = rng.uniform(40, 2360); yy = rng.uniform(shore(xx) + 30, H - 20)
        if not (990 < xx < 1410 and yy < 1240) and not (1880 < xx < 2000 and yy < 830):
            pr(['hd_lily_a', 'hd_lily_b'][rng.integers(0, 2)], xx, yy)
    # blossoming wood on the meadow
    blocked = (c.mat != GRASS)
    trees = ['hd_tree_oak_a', 'hd_tree_oak_b', 'hd_tree_oak_c', 'hd_tree_cherry_a', 'hd_tree_cherry_b', 'hd_tree_blossom',
             'hd_tree_autumn_a', 'hd_tree_autumn_b', 'hd_tree_pine_a', 'hd_tree_pine_b', 'hd_tree_big_a', 'hd_tree_willow']
    wts = [3, 3, 2, 4, 4, 2, 2, 2, 2, 2, 2, 1]
    m.scatter(trees, wts, 80, (20, 20, 2360, 200), blocked, 22, P)
    m.scatter(trees, wts, 110, (20, 180, 2360, 300), blocked, 32, P)
    m.scatter(['hd_tree_willow', 'hd_tree_cherry_a', 'hd_tree_blossom'], [2, 1, 1], 10, (20, 480, 2360, 120), blocked, 30, P)
    m.scatter(['hd_bush_a', 'hd_bush_b', 'hd_bush_berry', 'hd_bush_rose', 'hd_bush_yellow'], [3, 3, 1, 1, 1], 150, (20, 30, 2360, 600), blocked, 14, P)
    m.scatter(['hd_flowers_pink', 'hd_flowers_yellow', 'hd_flowers_violet', 'hd_flowers_white'], [1, 1, 1, 1], 230, (20, 30, 2360, 620), blocked, 8, P)
    m.scatter(['hd_grass_tall', 'hd_grass_tall_b', 'hd_fern_a', 'hd_mushrooms'], [3, 2, 1, 1], 160, (20, 30, 2360, 600), blocked, 10, P)
    m.scatter(['hd_rock_a', 'hd_rock_b', 'hd_stump', 'hd_log'], [3, 2, 2, 1], 26, (20, 30, 2360, 600), blocked, 22, P)


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
    m.keep_out = [(x, y, 46) for x, y in pts] + [(40, 531, 80)]
    water = design(m)
    furnish(m, P, water)
    m.bake_shadows(P)
    water_walls = HDMap.collision(m, P)
    m.collision = lambda P_: EDGE_WALLS + water_walls
    extra = dict(ellipses=[], stairs=[], water=base.get('water', []), waterFlow=base.get('waterFlow', []),
                 animals=base.get('animals', []), visualStyle='godot_hd_dense', visualUpdate='godot_dermaga_dense',
                 v6Layout=dict(version=3, generator='tools/worldgen/dermaga_hd.py', hd=True))
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    m.write(base, extra, P, Q, apply='--apply' in sys.argv, preview=prev)


if __name__ == '__main__':
    main()
