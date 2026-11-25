"""Distrik Perumahan, HD rebuild (1200x896 world, 2 texels per unit). All drawn by code: city library
(landmarks.library) with its door exactly on the old door rect, five houses (landmarks.house_variant)
with front yards behind picket fences, quiet asphalt street, pavements, lamps, parked cars, the bus
bench, community garden by Dito's pink house. Same size, doors, examine spots and quest points.
Usage: python3 tools/worldgen/perumahan_hd.py [--preview OUT.png] [--apply]
"""
import sys, json, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hdmap import HDMap, K, GRASS, STONE, PATH, SOIL, A   # noqa: E402
from paint import rgb, wear, moss                          # noqa: E402
from ground import noise                                   # noqa: E402

AREA, W, H = 'perumahan', 1200, 896
SEED = int(hashlib.sha256(b'perumahan_hd').hexdigest()[:8], 16)
TILE_M = 11
N_WALK = (25, 309, 1150, 57)
ROAD = (0, 372, 1200, 128)
S_WALK = (25, 506, 1150, 69)
NORTH = [('hd_house_mint', 190, 252), ('hd_library', 678, 304), ('hd_house_redbrick', 1020, 252)]
SOUTH = [('hd_house_pink', 205, 862), ('hd_house_butter', 600, 870), ('hd_house_violet', 1000, 862)]
WALLS = [[0, 0, 1200, 309], [0, 575, 1200, 321], [0, 309, 25, 166], [1175, 309, 25, 266]]


def design(m):
    c = m.c
    c.put(np.ones((c.h, c.w), bool), c.grass(('#4f9157', '#57995d', '#5fa163', '#68a869', '#72b06f', '#7db876')), GRASS)
    lawn = noise(c.h, c.w, 90, SEED + 3) > 0.6
    c.img[lawn] = c.img[lawn] * 0.9 + rgb('#3f7f4a') * 0.1
    x, y, w, h = N_WALK
    c.put(m.rect(x, y, w, h), c.tiles('#d4ccbf', '#cac1b3', 26, grout='#a3978a', salt=3), TILE_M)
    x, y, w, h = S_WALK
    c.put(m.rect(x, y, w, h), c.tiles('#d4ccbf', '#cac1b3', 26, grout='#a3978a', salt=4), TILE_M)
    x, y, w, h = ROAD
    road = m.rect(x, y, w, h)
    c.put(road, c.dirt(('#4a4d55', '#50535b', '#565961', '#5c5f67')), STONE)
    n = noise(c.h, c.w, 50, SEED + 1)
    c.img[road] = c.img[road] * (0.92 + 0.12 * n[road][:, None])
    rng = np.random.default_rng(SEED + 2)
    for _ in range(9):                                           # crack lines / tar seams
        px, py = rng.uniform(40, 1150), rng.uniform(y + 10, y + h - 10)
        for t in range(int(rng.uniform(30, 80)) * K):
            yy, xx = int(py * K + np.sin(t * 0.08) * 6), int(px * K + t)
            if 0 <= xx < c.w:
                c.img[yy:yy + 2, xx] *= 0.7
    for mx in (300, 840):
        mh = m.ellipse(mx, y + 64, 14, 8)
        c.img[mh] = rgb('#5a5d63'); c.img[mh & ((c.yy // 3) % 2 == 0)] = rgb('#3c3f45')
    for yy in (366, 500):
        cb = m.rect(0, yy, W, 6)
        c.put(cb, c.bricks(('#c9c4ba', '#d3cec4', '#ddd8cf'), 40, 12, '#8f897e', salt=5 + yy), STONE)
        c.img[m.rect(0, yy + 6, W, 3)] *= 0.72
        for xx in range(150, W, 300):
            dr = m.rect(xx, yy + (6 if yy == 366 else -9), 26, 9)
            c.img[dr] = rgb('#3a3c41'); c.img[dr & ((c.xx // K) % 4 == 0)] = rgb('#202226')
    # front paths from the fence gates to the doors, stepping stones, yards' flower borders
    stone = c.tiles('#c9bfae', '#bfb4a2', 18, grout='#8f8372', salt=6)
    for t, hx, hy in NORTH:
        if t != 'hd_library':
            c.put(m.rect(hx - 24, hy, 48, 309 - hy), stone, STONE)
    c.put(m.rect(678 - 150, 300, 300, 9), stone, STONE)
    for t, hx, hy in SOUTH:
        c.put(m.rect(hx - 24, 575, 48, hy - 575), stone, STONE)
    soil = c.dirt(('#6e5038', '#7a5a3f', '#866447', '#916f50'))
    for x0, x1 in ((300, 410),):                                 # community garden beds
        for k in range(3):
            c.put(m.rect(x0, 612 + k * 30, x1 - x0, 20), soil, SOIL)
    hard = np.isin(c.mat, [STONE, TILE_M]) & ~road
    wear(c, hard, 0.06, salt=2)
    moss(c, hard, c.mat == GRASS, 0.35)
    c.rim(np.isin(c.mat, [STONE, TILE_M]), c.mat == GRASS)
    ys, xs = np.nonzero(np.isin(c.mat, [STONE, TILE_M])[::8, ::8])
    for i in rng.integers(0, len(ys), 500):
        yy, xx = ys[i] * 8, xs[i] * 8
        k = rng.random()
        if k < 0.5:
            c.img[yy:yy + 3, xx:xx + 3] = rgb(('#c98b4a', '#a3693a', '#d9a35c', '#7a9a4a')[rng.integers(0, 4)])
        elif k < 0.7:
            c.img[yy:yy + 3, xx:xx + 4] = rgb(('#f3b8c8', '#f7d4de')[rng.integers(0, 2)])
        else:
            c.img[yy:yy + 2, xx:xx + 2] = rgb('#8f877c')
    gm = c.mat == GRASS
    ys, xs = np.nonzero(gm[::6, ::6])
    for i in rng.integers(0, len(ys), 2200):
        yy, xx = ys[i] * 6, xs[i] * 6
        if rng.random() < 0.8:
            for d in range(-2, 3):
                h_ = rng.integers(3, 7)
                if xx + d * 2 < c.w:
                    c.img[max(0, yy - h_):yy, xx + d * 2] = c.img[yy, xx] * (1.18 if d % 2 else 0.85)
        else:
            c.img[yy:yy + 2, xx:xx + 2] = rgb(('#fbf6ec', '#f7c9d9', '#f4d870', '#c4b2f2')[rng.integers(0, 4)])
    edge = np.minimum.reduce([c.xx, c.yy, c.w - 1 - c.xx, c.h - 1 - c.yy])
    c.img[edge < 8] *= 0.88


def fence_line(m, y, x0, x1, gaps, kinds=('hd_fence_picket', 'hd_fence_picket_b')):
    """Fill [x0, x1] minus the gate gaps with 98-unit fence pieces, ends flush with each segment."""
    segs, a = [], x0
    for g0, g1 in sorted(gaps):
        segs.append((a, g0)); a = g1
    segs.append((a, x1))
    k = 0
    for a, b in segs:
        n = int((b - a) // 98)
        xs = [a + 49 + i * 98 for i in range(n)]
        if b - a - n * 98 > 24:
            xs.append(b - 49)
        for x in xs:
            m.prop(kinds[k % len(kinds)], x, y)
            k += 1


def furnish(m, P):
    pr = m.prop
    rng = np.random.default_rng(SEED + 9)
    for t, x, y in NORTH + SOUTH:
        pr(t, x, y)
    # picket fences along both pavements, gates at every front path
    fence_line(m, 307, 25, 520, [(160, 220)])
    fence_line(m, 307, 838, 1175, [(990, 1050)])
    fence_line(m, 590, 40, 1175, [(175, 235), (570, 630), (970, 1030)], ('hd_fence_picket_b', 'hd_fence_picket'))
    # yards north (behind the fence, out of reach): shrubs, flowers, bike, mailbox posts
    for x0, x1 in ((30, 520), (840, 1170)):
        for _ in range(16):
            x = rng.uniform(x0, x1)
            if abs(x - 190) < 40 or abs(x - 1020) < 40:
                continue
            pr(['hd_flowers_pink', 'hd_flowers_yellow', 'hd_flowers_white', 'hd_bush_rose', 'hd_bush_a'][rng.integers(0, 5)], x, rng.uniform(262, 298))
    pr('hd_tree_oak_a', 450, 250); pr('hd_tree_cherry_a', 520, 236); pr('hd_tree_oak_b', 860, 240); pr('hd_tree_big_a', 1170, 230)
    pr('hd_tree_oak_c', 30, 240); pr('hd_bicycle', 300, 290); pr('hd_bush_yellow', 520, 296); pr('hd_bush_b', 836, 296)
    # yards south: community garden by Dito's house, washing line spot, trees at the back
    pr('hd_garden_plot', 355, 655); pr('hd_garden_plot', 355, 700); pr('hd_birdbath', 800, 660)
    pr('hd_bush_berry', 440, 620); pr('hd_flowerbed', 760, 625); pr('hd_bench', 1120, 640)
    for x in (30, 420, 780, 1180):
        pr(['hd_tree_cherry_b', 'hd_tree_oak_a', 'hd_tree_blossom', 'hd_tree_oak_b'][int(x) % 4], x, 760 + rng.uniform(-20, 20))
    for _ in range(40):
        x = rng.uniform(25, 1175)
        if any(abs(x - hx) < 36 for _, hx, _y in SOUTH):
            continue
        pr(['hd_flowers_pink', 'hd_flowers_violet', 'hd_flowers_yellow', 'hd_grass_tall', 'hd_bush_a'][rng.integers(0, 5)], x, rng.uniform(600, 700))
    # pavements
    for x in (130, 430, 930, 1130):
        pr('hd_lamp_gold', x, 362)
    for x in (300, 600, 860, 1080):
        pr('hd_lamp_gold', x, 534)
    pr('hd_signpost_res', 70, 362); pr('hd_mailbox', 140, 572); pr('hd_mailbox', 690, 588)
    pr('hd_bench', 800, 580); pr('hd_bin', 420, 572); pr('hd_bicycle', 950, 570); pr('hd_planter_pink', 1160, 568)
    pr('hd_bench', 560, 330); pr('hd_planter_violet', 800, 330); pr('hd_bin', 870, 330)
    # parked cars on the street edges
    pr('hd_car_red', 200, 400); pr('hd_car_green', 1080, 498)


def main():
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = M['areas'][AREA]
    m = HDMap(AREA, W, H, SEED)
    design(m)
    furnish(m, P)
    m.bake_shadows(P)
    m.collision = lambda P_: WALLS
    extra = dict(ellipses=[], water=[], stairs=[], visualStyle='godot_hd_dense', visualUpdate='godot_perumahan_hd',
                 v6Layout=dict(version=3, generator='tools/worldgen/perumahan_hd.py', hd=True))
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    m.write(base, extra, P, Q, apply='--apply' in sys.argv, preview=prev)


if __name__ == '__main__':
    main()
