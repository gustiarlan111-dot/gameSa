"""Jalan Kota, HD rebuild (1200x896 world, 2 texels per unit). Everything is drawn by code: the shop
row (tools/artkit/landmarks.py shopfront), asphalt road with lane marks and a zebra crossing, curbs,
tiled north pavement, brick south pavement, parked cars, bus stop, Rini's kiosk, flower stall,
iron railings along the road and the park edge, a cherry/oak park strip to the south.
Same size, doors, examine spots and quest points as before, so story and save data are untouched.
Usage: python3 tools/worldgen/jalan_kota_hd.py [--preview OUT.png] [--apply]
"""
import sys, json, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hdmap import HDMap, K, GRASS, STONE, A          # noqa: E402
from paint import rgb, wear, moss                     # noqa: E402
from ground import noise                              # noqa: E402
import common                                         # noqa: E402

AREA, W, H = 'jalan_kota', 1200, 896
SEED = int(hashlib.sha256(b'jalan_kota_hd').hexdigest()[:8], 16)
TILE_M = 11
SHOP_Y = 284                      # shop fronts stand on this line
N_WALK = (20, 262, 1160, 142)     # north pavement
ROAD = (0, 412, 1200, 184)
S_WALK = (20, 604, 1160, 132)     # south pavement
PARK_Y = 736
CROSS = (900, 90)                 # zebra crossing x, width
SHOPS = [('hd_shop_florist', 261), ('hd_shop_bakery', 495), ('hd_shop_mart', 720), ('hd_shop_arcade', 946),
         ('hd_shop_books', 1106)]
WALLS = [[0, 0, 1200, 262], [0, 262, 20, 203], [0, 565, 20, 171], [1180, 262, 20, 203], [1180, 565, 20, 171],
         [0, PARK_Y, 1200, 896 - PARK_Y]]
DOOR_RECTS = {'door_florist': [225, 284, 72, 40], 'door_arcade': [905, 284, 82, 40]}


def design(m):
    c = m.c
    c.put(np.ones((c.h, c.w), bool), c.grass(('#4c8c55', '#54945b', '#5c9c61', '#65a467', '#6fad6d', '#7ab774')), GRASS)
    # north pavement: light square slabs
    x, y, w, h = N_WALK
    c.put(m.rect(x, y, w, h), c.tiles('#d8d0c2', '#cec5b6', 28, grout='#a69a88', salt=3), TILE_M)
    # road: asphalt with fine aggregate, worn wheel tracks, patches
    x, y, w, h = ROAD
    road = m.rect(x, y, w, h)
    asp = c.dirt(('#43464e', '#494c54', '#4f525a', '#555860'))
    c.put(road, asp, STONE)
    n = noise(c.h, c.w, 60, SEED + 1)
    c.img[road] = c.img[road] * (0.92 + 0.12 * n[road][:, None])
    for ty in (y + 46, y + 138):                                   # wheel tracks, slightly darker
        c.img[m.rect(0, ty - 14, W, 28) & road] *= 0.93
    rng = np.random.default_rng(SEED + 2)
    for _ in range(7):                                             # repaired patches
        px, py = rng.uniform(60, 1100), rng.uniform(y + 20, y + h - 50)
        pm = m.rect(px, py, rng.uniform(40, 90), rng.uniform(18, 34))
        c.img[pm] = c.img[pm] * 0.82 + rgb('#3a3d44') * 0.18
    for xx in range(10, W, 64):                                     # centre line, dashed amber
        c.img[m.rect(xx, y + h / 2 - 3, 36, 6)] = rgb('#e8b84a')
    for yy in (y + 10, y + h - 14):                                 # white edge lines
        c.img[m.rect(0, yy, W, 4)] = rgb('#d9dcdf')
    cx0, cw = CROSS
    for k in range(10):                                             # zebra crossing
        c.img[m.rect(cx0 + 4, y + 18 + k * 16.4, cw - 8, 9)] = rgb('#eef0f1')
    for mx in (240, 640, 1080):                                     # manholes
        mh = m.ellipse(mx, y + 92, 15, 9)
        c.img[mh] = rgb('#5a5d63')
        c.img[mh & ((c.yy // 3) % 2 == 0)] = rgb('#3c3f45')
    # curbs + drains
    for yy in (404, 596):
        cb = m.rect(0, yy, W, 8)
        c.put(cb, c.bricks(('#c9c4ba', '#d3cec4', '#ddd8cf'), 40, 16, '#8f897e', salt=4 + yy), STONE)
        c.img[m.rect(0, yy + 8, W, 3)] *= 0.7
        for xx in range(90, W, 260):
            dr = m.rect(xx, yy + (8 if yy == 404 else -10), 28, 10)
            c.img[dr] = rgb('#3a3c41')
            c.img[dr & ((c.xx // K) % 4 == 0)] = rgb('#202226')
    # south pavement: warm herringbone-ish bricks
    x, y, w, h = S_WALK
    c.put(m.rect(x, y, w, h), c.bricks(('#b9a08a', '#c2a993', '#cbb39c', '#d3bca6', '#bfa38c'), 30, 15, '#8a735f', salt=6), STONE)
    for tx in (300, 600, 900):                                      # tactile strip at the crossings
        c.img[m.rect(tx - 20, 606, 40, 12)] = rgb('#e2c24a')
    c.img[m.rect(CROSS[0] + 25, 606, 40, 12)] = rgb('#e2c24a')
    # low stone wall between pavement and park
    lw = m.rect(0, PARK_Y - 4, W, 12)
    c.put(lw, c.bricks(('#9c958a', '#a8a196', '#b4ada1'), 36, 12, '#6f695f', salt=7), STONE)
    c.img[m.rect(0, PARK_Y + 8, W, 4)] *= 0.65
    # shop bases: a darker strip where facades meet the pavement
    c.img[m.rect(20, 262, 1160, 22)] *= 0.82
    # wear, moss, litter (petals, leaves, gum)
    hard = np.isin(c.mat, [STONE, TILE_M]) & ~road
    wear(c, hard, 0.06, salt=2)
    moss(c, np.isin(c.mat, [STONE]) & ~road, c.mat == GRASS, 0.3)
    ys, xs = np.nonzero(np.isin(c.mat, [STONE, TILE_M])[::8, ::8])
    for i in rng.integers(0, len(ys), 700):
        yy, xx = ys[i] * 8, xs[i] * 8
        k = rng.random()
        if k < 0.4:
            c.img[yy:yy + 3, xx:xx + 4] = rgb(('#f3b8c8', '#f7d4de', '#e996ad')[rng.integers(0, 3)])
        elif k < 0.65:
            c.img[yy:yy + 3, xx:xx + 3] = rgb(('#c98b4a', '#a3693a', '#d9a35c')[rng.integers(0, 3)])
        elif k < 0.8:
            c.img[yy:yy + 2, xx:xx + 2] = rgb('#2f3136')
        else:
            for t in range(rng.integers(6, 14)):
                y2, x2 = yy + t // 2, xx + t
                if y2 < c.h and x2 < c.w:
                    c.img[y2, x2] *= 0.75
    gm = c.mat == GRASS
    ys, xs = np.nonzero(gm[::6, ::6])
    for i in rng.integers(0, len(ys), 1400):
        yy, xx = ys[i] * 6, xs[i] * 6
        for d in range(-2, 3):
            h_ = rng.integers(3, 7)
            if xx + d * 2 < c.w:
                c.img[max(0, yy - h_):yy, xx + d * 2] = c.img[yy, xx] * (1.18 if d % 2 else 0.85)
    edge = np.minimum.reduce([c.xx, c.yy, c.w - 1 - c.xx, c.h - 1 - c.yy])
    c.img[edge < 8] *= 0.88


def furnish(m, P):
    pr = m.prop
    for t, x in SHOPS:
        pr(t, x, SHOP_Y)
    # between / beside the shops
    pr('hd_bin', 378, 296); pr('hd_planter_violet', 612, 298); pr('hd_vending', 828, 296)
    pr('hd_tree_oak_a', 70, 262); pr('hd_notice_board', 92, 300); pr('hd_bicycle', 140, 318)
    # north pavement furniture along the curb
    for x in (140, 380, 620, 860, 1100):
        pr('hd_lamp_gold', x, 400)
    for x in (330, 560, 800, 1030):
        pr('hd_tree_planter', x, 396)
    pr('hd_bench', 430, 322); pr('hd_bench', 1022, 322)
    pr('hd_flower_buckets_b', 340, 322); pr('hd_mailbox', 600, 332); pr('hd_bike_rack', 652, 330)
    for x in (182, 236, 470, 524):
        pr('hd_bollard', x, 402)
    # parked cars (north curb faces east, south curb faces west)
    pr('hd_car_red', 330, 450); pr('hd_car_cream', 790, 450)
    pr('hd_car_blue', 520, 588); pr('hd_car_green', 1030, 592)
    # south pavement
    pr('hd_bus_shelter', 150, 662); pr('hd_kiosk', 395, 670); pr('hd_flower_stall', 735, 676)
    pr('hd_notice_board', 860, 650); pr('hd_vending', 1000, 668); pr('hd_vending', 1030, 668)
    pr('hd_bin', 300, 640); pr('hd_planter_pink', 1080, 640); pr('hd_mailbox_old', 560, 650)
    for x in (260, 500, 740, 980):
        pr('hd_lamp_gold', x, 620)
    pr('hd_signpost_town_w', 60, 640); pr('hd_signpost_town_e', 1150, 650)
    # railings: along the road edge of the south pavement (gaps for crossings / bus stop), park edge
    for x in (300, 400, 640, 740, 840):
        pr('hd_railing_iron', x, 606)
    for x in range(70, W, 100):
        pr('hd_railing_iron', x, PARK_Y + 8)
    # park strip south: two rows of trees, shrubs and flowers (out of reach, behind the railing)
    rng = np.random.default_rng(SEED + 9)
    trees = ['hd_tree_cherry_a', 'hd_tree_cherry_b', 'hd_tree_oak_a', 'hd_tree_oak_b', 'hd_tree_blossom', 'hd_tree_oak_c']
    for row, (y0, off) in enumerate(((812, 0), (890, 45))):
        for x in range(30 + off, W, 95):
            pr(trees[rng.integers(0, len(trees))], x + rng.uniform(-18, 18), y0 + rng.uniform(-10, 10))
    for _ in range(40):
        pr(['hd_bush_a', 'hd_bush_b', 'hd_bush_rose', 'hd_bush_yellow'][rng.integers(0, 4)], rng.uniform(20, W - 20), rng.uniform(770, 860))
    for _ in range(50):
        pr(['hd_flowers_pink', 'hd_flowers_white', 'hd_flowers_yellow', 'hd_grass_tall'][rng.integers(0, 4)], rng.uniform(20, W - 20), rng.uniform(756, 890))
    # backdrop: trees behind the roofs
    for x in range(20, W, 85):
        pr(trees[rng.integers(0, len(trees))], x + rng.uniform(-15, 15), rng.uniform(40, 70))
    pr('hd_tree_oak_b', 1188, 262)
    # hedges and shrubs in the gaps between and beside the shop fronts
    for x in list(range(26, 160, 22)) + [372, 386, 606, 620, 1176]:
        pr(['hd_bush_a', 'hd_bush_b', 'hd_bush_rose'][int(x) % 3], x, 258 + rng.uniform(-3, 3))


def main():
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = json.loads(json.dumps(M['areas'][AREA]))
    for d in base['doors']:
        if d['id'] in DOOR_RECTS:
            d['rect'] = DOOR_RECTS[d['id']]
    m = HDMap(AREA, W, H, SEED)
    design(m)
    furnish(m, P)
    m.bake_shadows(P)
    m.collision = lambda P_: WALLS
    extra = dict(ellipses=[], water=[], stairs=[], doors=base['doors'], visualStyle='godot_hd_dense',
                 visualUpdate='godot_jalan_kota_hd', v6Layout=dict(version=3, generator='tools/worldgen/jalan_kota_hd.py', hd=True))
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    m.write(base, extra, P, Q, apply='--apply' in sys.argv, preview=prev)


if __name__ == '__main__':
    main()
