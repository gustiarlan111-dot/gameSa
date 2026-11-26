"""Distrik Perumahan, HD rebuild (1200x896 world, 2 texels per unit). All drawn by code: city library
(landmarks.library) with its door exactly on the old door rect, five houses (landmarks.house_variant)
with front yards behind picket fences, quiet asphalt street, pavements, lamps, parked cars, the bus
bench, community garden by Dito's pink house. Same doors, examine spots and quest points.

V8.7: the south houses face the camera, so their front doors now open onto something. The map grew
south (896 -> 1296): the houses stand on a terrace (e=40, assets/data/elevation.json) with a front
walk, each has stone steps down from its door, two side alleys between the houses lead from the
street to the terrace (and down two more stairs) into Gang Melati, a lower lane with the warga
green: pos ronda, community garden beds, a swing, a jemuran, a well, benches and trees.
Everything north of the south fence keeps its coordinates.
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
import common                                              # noqa: E402
from terrace import Terrace, write_elevation                                # noqa: E402

AREA, W, H = 'perumahan', 1200, 1296
SEED = int(hashlib.sha256(b'perumahan_hd').hexdigest()[:8], 16)
TILE_M = 11
N_WALK = (25, 309, 1150, 57)
ROAD = (0, 372, 1200, 128)
S_WALK = (25, 506, 1150, 69)
NORTH = [('hd_house_mint', 190, 252), ('hd_library', 678, 304), ('hd_house_redbrick', 1020, 252)]
SOUTH = [('hd_house_pink', 205, 862), ('hd_house_butter', 600, 870), ('hd_house_violet', 1000, 862)]
FENCE_Y = 590                     # south picket fence (gates now at the two alleys)
ALLEYS = [(355, 450), (750, 850)] # walkable gaps between the south houses (x0, x1)
FACE_Y, FACE_H = 912, 40          # terrace wall in front of the south houses
LOW_Y = FACE_Y + FACE_H
LANE = (20, LOW_Y, 1160, 70)      # Gang Melati
SOUTH_Y = 1256
STAIRS_X = [(179, 52), (374, 56), (574, 52), (772, 56), (974, 52)]   # door steps + alley stairs
TER = Terrace()
# house blocks: you cannot walk behind a house (its picture covers that ground)
BLOCKS = [[25, FENCE_Y + 4, 330, 862 - FENCE_Y - 4], [450, FENCE_Y + 4, 300, 870 - FENCE_Y - 4],
          [850, FENCE_Y + 4, 325, 862 - FENCE_Y - 4]]
WALLS = [[0, 0, 1200, 309], [0, 309, 25, 166], [1175, 309, 25, FACE_Y - 309], [0, 562, 25, FACE_Y - 562],
         [0, LOW_Y, 20, H - LOW_Y], [1180, LOW_Y, 20, H - LOW_Y],
         [0, SOUTH_Y, 1200, H - SOUTH_Y]] + BLOCKS
EXAMINE = [
    {'id': 'pos_ronda', 'x': 300, 'y': 1150, 'label': 'Pos Ronda', 'r': 70, 'lines': {
        'arland': [{'s': 'arland', 'e': 'neutral', 't': 'Ada termos dan papan catur di sini. Bapak-bapak ronda pasti jago catur.'}],
        'sofia': [{'s': 'sofia', 'e': 'senang', 't': 'Kentongannya masih ada. Dulu bunyinya jadi tanda sudah waktunya pulang.'}]}},
    {'id': 'ayunan', 'x': 820, 'y': 1120, 'label': 'Ayunan', 'r': 60, 'lines': {
        'arland': [{'s': 'arland', 'e': 'neutral', 't': 'Ayunannya berderit. Tetap saja, rasanya ingin duduk sebentar.'}],
        'sofia': [{'s': 'sofia', 'e': 'senang', 't': 'Dorong aku sekali saja. Pelan-pelan, ya!'}]}},
    {'id': 'jemuran', 'x': 560, 'y': 1196, 'label': 'Jemuran', 'r': 56, 'lines': {
        'arland': [{'s': 'arland', 'e': 'neutral', 't': 'Bau sabun cuci. Matahari di sini cepat bikin kering.'}],
        'sofia': [{'s': 'sofia', 'e': 'neutral', 't': 'Ada sarung batik yang motifnya mirip punya nenekku.'}]}},
]
ELEVATION = [
    {'id': 'street_terrace', 'kind': 'plateau', 'rect': [0, 0, W, FACE_Y], 'e': FACE_H},
    {'id': 'front_wall', 'kind': 'slope', 'rect': [0, FACE_Y, W, FACE_H], 'axis': 'y', 'from': FACE_H, 'to': 0},
] + [{'id': 'st%d' % i, 'kind': 'slope', 'rect': [x, FACE_Y, w, FACE_H], 'axis': 'y', 'from': FACE_H, 'to': 0, 'stairs': True}
     for i, (x, w) in enumerate(STAIRS_X)]


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
    south_side(m, stone)
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


def south_side(m, stone):
    """Side alleys, the front walk of the south houses, terrace wall + stairs, Gang Melati, warga green."""
    c = m.c
    for x0, x1 in ALLEYS:                                        # alley paths from the fence gate to the front walk
        cx = (x0 + x1) / 2
        c.put(m.rect(cx - 26, 575, 52, FACE_Y - 575), stone, STONE)
    c.put(m.rect(25, 858, W - 50, FACE_Y - 858), c.tiles('#d4ccbf', '#cac1b3', 26, grout='#a3978a', salt=12), TILE_M)
    for t, hx, hy in SOUTH:                                      # porch slab under each front door
        c.put(m.rect(hx - 40, hy - 6, 80, FACE_Y - hy + 6), c.tiles('#e0d6c4', '#d6cbb7', 20, grout='#a89a86', salt=hx), STONE)
    # lower level: lane + green
    lane = m.rect(*LANE)
    c.put(lane, c.bricks(('#b9a08a', '#c2a993', '#cbb39c', '#d3bca6', '#bfa38c'), 30, 15, '#8a735f', salt=13), STONE)
    c.img[m.rect(LANE[0], LANE[1] + LANE[3], LANE[2], 4)] *= 0.8
    for x0, x1 in ((40, 140), (400, 470), (1040, 1150)):          # footpaths into the green
        c.put(m.rect(x0, LOW_Y + LANE[3], x1 - x0, SOUTH_Y - LOW_Y - LANE[3]), stone, STONE)
    c.put(m.rect(40, 1210, W - 80, 30), stone, STONE)              # south footpath along the hedge
    c.put(c.rrect(200 * K, 1094 * K, 210 * K, 76 * K, 10 * K), c.tiles('#cfc4b1', '#c6baa6', 22, grout='#9a8c78', salt=14), STONE)  # pos ronda slab
    sand = c.dirt(('#d8c59c', '#e0cea6', '#e7d6b0', '#cfbb92'))
    c.put(m.ellipse(830, 1110, 80, 34), sand, PATH)               # worn sand under the swing
    TER.__init__()
    TER.run(m, c, 0, W, FACE_Y, FACE_H, STAIRS_X, 50)


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
    fence_line(m, FENCE_Y, 40, 1175, [(ALLEYS[0][0] + 20, ALLEYS[0][1] - 20), (ALLEYS[1][0] + 20, ALLEYS[1][1] - 20)],
               ('hd_fence_picket_b', 'hd_fence_picket'))
    # yards north (behind the fence, out of reach): shrubs, flowers, bike, mailbox posts
    for x0, x1 in ((30, 520), (840, 1170)):
        for _ in range(16):
            x = rng.uniform(x0, x1)
            if abs(x - 190) < 40 or abs(x - 1020) < 40:
                continue
            pr(['hd_flowers_pink', 'hd_flowers_yellow', 'hd_flowers_white', 'hd_bush_rose', 'hd_bush_a'][rng.integers(0, 5)], x, rng.uniform(262, 298))
    pr('hd_tree_oak_a', 450, 250); pr('hd_tree_cherry_a', 520, 236); pr('hd_tree_oak_b', 860, 240); pr('hd_tree_big_a', 1170, 230)
    pr('hd_tree_oak_c', 30, 240); pr('hd_bicycle', 300, 290); pr('hd_bush_yellow', 520, 296); pr('hd_bush_b', 836, 296)
    lower_furnish(m, P, rng)
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


def lower_furnish(m, P, rng):
    pr = m.prop
    # side alleys: planters and flowers along the house walls, a bike, a lamp at each alley mouth
    for x0, x1 in ALLEYS:
        cx = (x0 + x1) / 2
        pr('hd_lamp_gold', cx - 38, 868); pr('hd_planter_pink', cx + 36, 640)
        for y in (700, 770, 840):
            pr(['hd_flowers_pink', 'hd_flowers_yellow', 'hd_flowers_violet'][int(y) % 3], x0 + 10, y)
            pr(['hd_flowers_white', 'hd_flowers_pink', 'hd_grass_tall'][int(y) % 3], x1 - 10, y + 12)
    pr('hd_bicycle', 766, 760)
    # front walk of the south houses: potted plants by the porches, lamps, a bench
    for t, hx, hy in SOUTH:
        pr('hd_planter_violet', hx - 56, hy + 26); pr('hd_planter_pink', hx + 56, hy + 26)
    pr('hd_bench', 1110, 900); pr('hd_mailbox', 110, 896)
    # Gang Melati
    for x in (120, 480, 700, 1080):
        pr('hd_lamp_gold', x, LOW_Y + LANE[3] - 4)
    pr('hd_signpost_res', 1150, LOW_Y + 64)
    # warga green: pos ronda (gazebo), well, garden beds, swing, jemuran, benches, trees, hedge
    pr('hd_gazebo', 305, 1150); pr('hd_bench', 240, 1190); pr('hd_well', 180, 1110)
    pr('hd_garden_plot', 600, 1072); pr('hd_garden_plot', 680, 1106); pr('hd_garden_plot', 600, 1140)   # community garden (moved from the old yard)
    pr('hd_swing', 830, 1118); pr('hd_clothesline', 560, 1196); pr('hd_birdbath', 980, 1100)
    pr('hd_bench', 960, 1200); pr('hd_bush_berry', 740, 1066); pr('hd_flowerbed', 1100, 1150)
    for tx, ty in ((70, 1160), (500, 1080), (1150, 1080), (720, 1236), (1000, 1050)):
        pr(['hd_tree_cherry_b', 'hd_tree_oak_a', 'hd_tree_blossom', 'hd_tree_oak_b'][int(tx) % 4], tx, ty)
    blocked = m.c.mat != GRASS
    m.rng = rng
    m.scatter(['hd_flowers_pink', 'hd_flowers_violet', 'hd_flowers_yellow', 'hd_grass_tall', 'hd_bush_a'], [2, 1, 1, 2, 1],
              50, (30, LOW_Y + 80, W - 60, SOUTH_Y - LOW_Y - 100), blocked, 7, P)
    for row, y in enumerate((SOUTH_Y + 10, H - 6)):
        for x in range(30 + row * 17, W, 34):
            pr(['hd_bush_a', 'hd_bush_b', 'hd_bush_rose'][(int(x) // 34 + row) % 3 if row else int(x) % 2], x + rng.uniform(-5, 5), y)


def main():
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = json.loads(json.dumps(M['areas'][AREA]))
    ex = {e['id']: e for e in base.get('examine', [])}
    for e in EXAMINE:
        ex[e['id']] = e
    base['examine'] = list(ex.values())
    m = HDMap(AREA, W, H, SEED)
    design(m)
    furnish(m, P)
    keep = {'hd_fence_picket', 'hd_fence_picket_b'} | {t for t, _x, _y in NORTH + SOUTH}
    dropped = [p for p in m.props if p['type'] not in keep and TER.hits(p, P)]
    m.props = [p for p in m.props if p['type'] in keep or not TER.hits(p, P)]
    print('terrace walls', len(TER.walls), 'stairs', len(TER.stairs), 'dropped', [(p['type'], p['x'], p['y']) for p in dropped])
    m.bake_shadows(P)
    m.collision = lambda P_: WALLS + TER.walls
    animals = [a for a in base.get('animals', []) if a['type'] != 'chicken']
    animals.append({'type': 'chicken', 'n': 3, 'region': [480, 1030, 300, 150]})
    animals.append({'type': 'cat_grey', 'n': 1, 'region': [60, LOW_Y + 10, 1060, 90], 'day': False})
    extra = dict(ellipses=[], water=[], stairs=TER.stairs, animals=animals, visualStyle='godot_hd_dense', visualUpdate='godot_perumahan_hd',
                 v6Layout=dict(version=3, generator='tools/worldgen/perumahan_hd.py', hd=True))
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    bad = m.write(base, extra, P, Q, apply='--apply' in sys.argv, preview=prev)
    if '--apply' in sys.argv and not bad:
        write_elevation(A, AREA, ELEVATION)


if __name__ == '__main__':
    main()
