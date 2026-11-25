"""Bukit Bintang, dense HD rebuild (2400x1600 world, 2 texels per unit). All drawn by code: a cool
hilltop meadow under the stars, a gravel ridge path from the forest gate up to the observatory
terrace and on to the stargazing lookout in the east, a fenced cliff edge in the south with rock
ledges dropping to a dark pine valley, star stones and stone lanterns along the way, a hidden
clearing with the treasure chest in the north-west. Same size, door, examine spots and quest points
as before.  Usage: python3 tools/worldgen/bukit_bintang_hd.py [--preview OUT.png] [--apply]
"""
import sys, json, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hdmap import HDMap, K, GRASS, PATH, STONE, A   # noqa: E402
from paint import rgb, wear, moss                   # noqa: E402
from ground import noise                            # noqa: E402
import common                                       # noqa: E402

AREA, W, H = 'bukit_bintang', 2400, 1600
SEED = int(hashlib.sha256(b'bukit_bintang_hd').hexdigest()[:8], 16)
EDGE_Y = 1240                         # cliff edge: nothing south of it is walkable
OBS = (1375, 706)                     # observatory foot
LOOKOUT = (1930, 920, 230, 130)       # stone terrace with the big telescope (ellipse cx, cy, rx, ry)
TERRACE = (1375, 800, 210, 70)        # stone forecourt in front of the observatory
PATHS = [[(0, 775), (220, 790), (480, 800), (760, 830), (1000, 860), (1200, 850), (1375, 830)],
         [(1375, 830), (1560, 860), (1760, 900), (1930, 920)],
         [(1375, 830), (1375, 760)],
         [(760, 830), (620, 640), (480, 480), (340, 400)],
         [(1000, 860), (1060, 1000), (1125, 1170)],
         [(1930, 920), (2100, 700), (2200, 420)],
         [(220, 790), (275, 860)]]
WALLS = [[0, 0, 20, 700], [0, 850, 20, 750], [2380, 0, 20, 1600], [20, 0, 2360, 20], [0, EDGE_Y, 2400, H - EDGE_Y]]


def edge_y(x):
    x = np.asarray(x, float)
    return EDGE_Y + 14 + 8 * np.sin(x / 120.0) + 5 * np.sin(x / 41.0 + 2.0)


def design(m):
    c = m.c
    c.put(np.ones((c.h, c.w), bool), c.grass(('#3f7f5c', '#478864', '#4f916b', '#589a72', '#62a479', '#6fb083')), GRASS)
    n = noise(c.h, c.w, 160, SEED + 3)
    c.img[n > 0.62] = c.img[n > 0.62] * 0.9 + rgb('#2f6a52') * 0.1
    c.img[n < 0.3] = c.img[n < 0.3] * 0.92 + rgb('#9fd09a') * 0.08
    X = c.xx / K
    Y = c.yy / K
    ey = edge_y(X[0])[None, :]
    below = Y > ey
    # cliff face then the dark valley far below
    face = below & (Y < ey + 70)
    c.put(face, c.bricks(('#4a4652', '#57525f', '#645f6c', '#726c7a'), 34, 16, '#2e2b36', salt=8), STONE)
    c.img[face] *= (0.95 - 0.35 * np.clip((Y - ey) / 70.0, 0, 1))[face][..., None]
    valley = below & ~face
    c.put(valley, c.grass(('#1f3f38', '#24473f', '#2a5046', '#30584c')), GRASS)
    c.img[valley] *= 0.8
    gravel = c.dirt(('#b0a08a', '#bcab94', '#c7b79f', '#d2c3ab'))
    paths = np.zeros((c.h, c.w), bool)
    for i, p in enumerate(PATHS):
        paths |= m.path(p, 56 if i < 2 else 40, 3, i)
    # ridge walk along the fence
    paths |= (Y > ey - 46) & (Y < ey - 4) & (X > 40) & (X < 2360)
    paths &= ~below
    c.put(paths, gravel, PATH)
    tx, ty, trx, tr_y = TERRACE
    c.put(m.ellipse(tx, ty, trx, tr_y), c.tiles('#d4ccbf', '#c9c0b2', 24, grout='#9c917f', salt=6), STONE)
    lx, ly, lrx, lry = LOOKOUT
    c.put(m.ellipse(lx, ly, lrx, lry), c.tiles('#d4ccbf', '#c9c0b2', 24, grout='#9c917f', salt=7), STONE)
    ring = m.ellipse(lx, ly, lrx * 0.42, lry * 0.42) & ~m.ellipse(lx, ly, lrx * 0.36, lry * 0.36)
    c.put(ring, c.tiles('#e8c97a', '#d9b866', 8, grout='#a8893f', salt=9), STONE)        # brass compass ring
    for k in range(8):                                                                    # star rays
        a = k * np.pi / 4
        c.img[m.path([(lx, ly), (lx + np.cos(a) * lrx * 0.33, ly + np.sin(a) * lry * 0.33)], 4)] = rgb('#e8c97a')
    # NW clearing with the chest: soft moss ring
    c.put(m.ellipse(330, 400, 120, 70, 6, 3), c.dirt(('#7a9a62', '#86a66c', '#92b276')), PATH)
    gm = c.mat == GRASS
    c.rim(c.mat == PATH, gm, dark='#7d6f5c', ao=(0.9, 0.95))
    c.overhang(c.mat == PATH, gm, 0.25, 1)
    c.rim(c.mat == STONE, gm | (c.mat == PATH))
    wear(c, c.mat == STONE, 0.05, salt=2)
    moss(c, c.mat == STONE, gm, 0.35)
    rng = np.random.default_rng(SEED + 4)
    ys, xs = np.nonzero((c.mat == PATH)[::8, ::8])
    for i in rng.integers(0, len(ys), 800):
        y, x = ys[i] * 8, xs[i] * 8
        c.img[y:y + 2, x:x + 2] = rgb(('#8f877c', '#e6dccb', '#c9a8e8')[rng.integers(0, 3)])
    ys, xs = np.nonzero((gm & ~below)[::6, ::6])
    for i in rng.integers(0, len(ys), 6200):
        y, x = ys[i] * 6, xs[i] * 6
        if rng.random() < 0.74:
            for d in range(-2, 3):
                h_ = rng.integers(3, 7)
                if x + d * 2 < c.w:
                    c.img[max(0, y - h_):y, x + d * 2] = c.img[y, x] * (1.18 if d % 2 else 0.85)
        else:   # star meadow: white, pale gold and lilac flowers
            c.img[y:y + 2, x:x + 2] = rgb(('#fbf6ec', '#f4e08a', '#c4b2f2', '#a9d8ff')[rng.integers(0, 4)])
    edge = np.minimum.reduce([c.xx, c.yy, c.w - 1 - c.xx, c.h - 1 - c.yy])
    c.img[edge < 10] *= 0.86
    return below


def furnish(m, P, below):
    pr = m.prop
    rng = np.random.default_rng(SEED + 9)
    c = m.c
    pr('hd_observatory', *OBS)
    tx, ty = TERRACE[:2]
    pr('hd_bench', tx - 150, ty - 40); pr('hd_bench', tx + 160, ty - 30)
    pr('hd_stone_lantern', tx - 170, ty + 20); pr('hd_stone_lantern', tx + 180, ty + 24)
    pr('hd_flowerbed', tx - 90, ty - 62); pr('hd_flowerbed', tx + 96, ty - 60)
    lx, ly = LOOKOUT[:2]
    pr('hd_telescope', 1950, 875)
    pr('hd_bench', 1800, 988); pr('hd_bench', 2060, 1010)
    pr('hd_stone_lantern', lx - 210, ly - 40); pr('hd_stone_lantern', lx + 214, ly - 30)
    pr('hd_lantern_post', lx - 120, ly + 108); pr('hd_lantern_post', lx + 130, ly + 104)
    pr('hd_signpost_hill', 240, 740)
    pr('hd_picnic', 875, 1075)
    # chest clearing (opens when CHEST_HILL is set)
    m.props.append(dict(type='hd_chest', x=325, y=375, alt='hd_chest_open', altFlag='CHEST_HILL'))
    pr('hd_star_stone', 420, 352); pr('hd_mushrooms_glow', 250, 430); pr('hd_mushrooms_glow', 410, 440)
    # star stones and lanterns along the paths
    for x, y in ((560, 760), (900, 800), (1150, 790), (1620, 820), (1800, 860), (2140, 640), (1040, 940)):
        pr('hd_star_stone', x, y)
    for x in range(60, 2360, 94):                     # cliff fence with lamps
        pr('hd_fence_h', x, int(edge_y(x)) - 2)
    for x in range(300, 2300, 450):
        pr('hd_lamp_gold', x, int(edge_y(x)) - 50)
    for x in (700, 1520, 2050):
        pr('hd_log_bench', x, int(edge_y(x)) - 58)
    # rock ledges on the cliff face, valley pines far below
    for x in range(60, 2360, 130):
        pr(['hd_rock_ledge', 'hd_rock_ledge_b'][rng.integers(0, 2)], x + rng.uniform(-20, 20), edge_y(x) + 60)
    valley = (~below) | (c.mat != GRASS)
    m.scatter(['hd_tree_pine_a', 'hd_tree_pine_b', 'hd_tree_dark_a', 'hd_tree_dark_b'], [3, 3, 2, 2], 120, (20, 1330, 2360, 270), valley, 26, P)
    # meadow trees, denser towards the edges
    blocked = (c.mat != GRASS) | below
    trees = ['hd_tree_pine_a', 'hd_tree_pine_b', 'hd_tree_oak_a', 'hd_tree_oak_b', 'hd_tree_oak_c', 'hd_tree_blossom',
             'hd_tree_dark_a', 'hd_tree_dark_b', 'hd_tree_lantern', 'hd_tree_cherry_a', 'hd_tree_big_a']
    wts = [4, 4, 3, 2, 2, 2, 2, 2, 1, 2, 1]
    m.scatter(trees, wts, 90, (20, 20, 2360, 240), blocked, 24, P)
    m.scatter(trees, wts, 70, (20, 220, 2360, 460), blocked, 34, P)
    m.scatter(trees, wts, 40, (20, 880, 2360, 300), blocked, 34, P)
    m.scatter(['hd_bush_a', 'hd_bush_b', 'hd_bush_berry', 'hd_bush_rose'], [3, 3, 1, 1], 140, (20, 30, 2360, 1180), blocked, 14, P)
    m.scatter(['hd_flowers_white', 'hd_flowers_violet', 'hd_flowers_yellow', 'hd_flowers_pink'], [2, 2, 1, 1], 240, (20, 30, 2360, 1180), blocked, 8, P)
    m.scatter(['hd_grass_tall', 'hd_grass_tall_b', 'hd_fern_a', 'hd_mushrooms'], [3, 2, 1, 1], 150, (20, 30, 2360, 1180), blocked, 10, P)
    m.scatter(['hd_rock_a', 'hd_rock_b', 'hd_stump', 'hd_log'], [3, 3, 2, 1], 30, (20, 30, 2360, 1180), blocked, 22, P)


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
    m.keep_out = [(x, y, 46) for x, y in pts] + [(40, 775, 80), (1375, 760, 90)]
    below = design(m)
    furnish(m, P, below)
    m.bake_shadows(P)
    m.collision = lambda P_: WALLS
    extra = dict(ellipses=[], stairs=[], water=[], animals=base.get('animals', []),
                 visualStyle='godot_hd_dense', visualUpdate='godot_bukit_bintang_dense',
                 v6Layout=dict(version=3, generator='tools/worldgen/bukit_bintang_hd.py', hd=True))
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    m.write(base, extra, P, Q, apply='--apply' in sys.argv, preview=prev)


if __name__ == '__main__':
    main()
