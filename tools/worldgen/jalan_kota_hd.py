"""Jalan Kota, HD rebuild (1200x1296 world, 2 texels per unit). Everything is drawn by code: the shop
row (tools/artkit/landmarks.py shopfront), asphalt road with lane marks and a zebra crossing, curbs,
tiled north pavement, brick south pavement, parked cars, bus stop, Rini's kiosk, flower stall,
iron railings along the road.

V8.6: the street became a terrace. The old park strip south of the pavement is now a retaining
wall with a stone balustrade, two staircases lead down to the Alun-alun Bawah (lower square): a
radial court round a fountain, a wisteria pergola, a small cafe corner, market stalls, lawns, lamps.
The height layer lives in assets/data/elevation.json (street plateau e=FACE_H, wall face, stairs).
Everything north of y=736 keeps its coordinates, doors, examine spots and quest points, so story
and save data are untouched; the map only grew southward.
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
from terrace import Terrace                           # noqa: E402

AREA, W, H = 'jalan_kota', 1200, 1296
SEED = int(hashlib.sha256(b'jalan_kota_hd').hexdigest()[:8], 16)
TILE_M = 11
SHOP_Y = 284                      # shop fronts stand on this line
N_WALK = (20, 262, 1160, 142)     # north pavement
ROAD = (0, 412, 1200, 184)
S_WALK = (20, 604, 1160, 140)     # south pavement, runs up to the terrace coping
PARK_Y = 736                      # end of the south pavement = top of the terrace wall
FACE_Y, FACE_H = 744, 40          # retaining wall face (picture px), e = FACE_H on the street
LOW_Y = FACE_Y + FACE_H           # lower square starts here
STAIRS_X = [(288, 64), (848, 64)] # x, width of the two staircases (centres 320 / 880)
COURT = (600, 1036, 210, 150)     # radial court: centre x, y, radius x, radius y
FOUNTAIN = (600, 1036)
SOUTH_Y = 1252                    # hedge line / map edge wall at the south of the lower square
CROSS = (900, 90)                 # zebra crossing x, width
SHOPS = [('hd_shop_florist', 261), ('hd_shop_bakery', 495), ('hd_shop_mart', 720), ('hd_shop_arcade', 946),
         ('hd_shop_books', 1106)]
WALLS = [[0, 0, 1200, 262], [0, 262, 20, 203], [0, 565, 20, 179], [1180, 262, 20, 203], [1180, 565, 20, 179],
         [0, LOW_Y, 20, H - LOW_Y], [1180, LOW_Y, 20, H - LOW_Y], [0, SOUTH_Y, 1200, H - SOUTH_Y]]
TER = Terrace()
EXAMINE = [
    {'id': 'fountain_low', 'x': 600, 'y': 1080, 'label': 'Air Mancur Alun-alun', 'r': 70, 'lines': {
        'arland': [{'s': 'arland', 'e': 'neutral', 't': 'Dasarnya penuh koin. Semua orang punya permintaan, ternyata.'}],
        'sofia': [{'s': 'sofia', 'e': 'senang', 't': 'Katanya kalau lempar koin di sini, permintaannya harus dirahasiakan.'}]}},
    {'id': 'pergola', 'x': 196, 'y': 980, 'label': 'Pergola Wisteria', 'r': 64, 'lines': {
        'arland': [{'s': 'arland', 'e': 'neutral', 't': 'Wisteria. Sofia pasti betah duduk lama di bawah sini.'}],
        'sofia': [{'s': 'sofia', 'e': 'senang', 't': 'Wisteria! Wanginya manis banget kalau sudah sore.'}]}},
    {'id': 'balustrade_view', 'x': 600, 'y': 728, 'label': 'Pagar Batu', 'r': 50, 'lines': {
        'arland': [{'s': 'arland', 'e': 'neutral', 't': 'Dari sini alun-alun bawah kelihatan semua. Ramai juga.'}],
        'sofia': [{'s': 'sofia', 'e': 'neutral', 't': 'Tangganya ada dua, kiri dan kanan. Ketemu di air mancur, yuk.'}]}},
]
ELEVATION = [
    {'id': 'street', 'kind': 'plateau', 'rect': [0, 0, W, FACE_Y], 'e': FACE_H},
    {'id': 'terrace_wall', 'kind': 'slope', 'rect': [0, FACE_Y, W, FACE_H], 'axis': 'y', 'from': FACE_H, 'to': 0},
] + [{'id': 'st%d' % i, 'kind': 'slope', 'rect': [x, FACE_Y, w, FACE_H], 'axis': 'y', 'from': FACE_H, 'to': 0, 'stairs': True}
     for i, (x, w) in enumerate(STAIRS_X)]
DOOR_RECTS = {'door_florist': [225, 284, 72, 40], 'door_arcade': [905, 284, 82, 40]}


def lower_square(m):
    """Alun-alun Bawah: promenade under the wall, paths from both stairs, radial court, cross walk, lawns."""
    c = m.c
    warm = c.tiles('#e2d6c2', '#d9ccb6', 40, grout='#ad9c84', salt=21)
    c.put(m.rect(20, LOW_Y, W - 40, 58), warm, STONE)                               # promenade under the wall
    c.put(m.rect(20, 1182, W - 40, SOUTH_Y - 1182), warm, STONE)                    # south promenade
    walk = c.bricks(('#c7ad94', '#cfb59c', '#d7bea6', '#bfa48b'), 30, 15, '#8a735f', salt=22)
    cx, cy, rx, ry = COURT
    for sx, sw in STAIRS_X:                                                          # stair foot -> court
        x = sx + sw / 2
        c.put(m.path([(x, LOW_Y + 30), (x, 880), (cx + (x - cx) * 0.62, cy - ry * 0.8)], 58, salt=int(x)), walk, STONE)
    c.put(m.rect(20, cy - 30, W - 40, 60), walk, STONE)                              # east-west walk
    c.put(m.rect(cx - 32, cy, 64, 1182 - cy), walk, STONE)                           # court -> south promenade
    for px, py, pw, ph in ((92, 930, 220, 150), (870, 900, 250, 104)):               # pergola + cafe patios
        c.put(c.rrect(px * K, py * K, pw * K, ph * K, 14 * K), c.tiles('#e8dcc8', '#ddd1bb', 30, grout='#b4a38b', salt=px), STONE)
    court = m.ellipse(cx, cy, rx, ry)
    rad, r, th, ri = c.radial(cx * K, cy * K, ry / rx, ('#d4c7b4', '#dcd0be', '#e4d9c8', '#ebe2d3'), 24, 40, salt=23, mortar='#a99a85')
    c.put(court, rad, STONE)
    c.img[court & (r > (rx - 12) * K)] = rgb('#a2876b')
    c.img[court & (r > (rx - 8) * K)] = rgb('#c9a780')
    pool = m.ellipse(cx, cy + 4, 86, 58)                                             # fountain basin rim + water
    c.img[pool] = rgb('#bfb6a6')
    water = m.ellipse(cx, cy + 4, 76, 50)
    n = noise(c.h, c.w, 18, SEED + 31)
    c.img[water] = rgb('#5f9fc2') * (0.86 + 0.22 * n[water][:, None])
    c.img[water & (n > 0.72)] = rgb('#cfe9f5')
    c.img[m.ellipse(cx, cy - 8, 76, 40) & ~m.ellipse(cx, cy + 4, 76, 50)] *= 1.0
    c.img[m.ellipse(cx, cy + 10, 86, 58) & ~pool] *= 0.75                             # basin contact shadow
    for k in range(10):                                                              # coins glinting
        a = k * 2.3
        c.img[m.ellipse(cx + np.cos(a) * 46, cy + 8 + np.sin(a) * 26, 1.6, 1.2)] = rgb('#e8c25a')
    # flower beds along the wall foot (soil + blooms), not in front of the stairs
    rng = np.random.default_rng(SEED + 33)
    for x0, x1 in ((30, 250), (400, 810), (960, 1170)):
        bed = m.rect(x0, LOW_Y + 14, x1 - x0, 16)
        c.img[bed] = rgb('#5b4031')
        c.img[m.rect(x0, LOW_Y + 28, x1 - x0, 2)] = rgb('#b9ad9b')
        for _ in range(int((x1 - x0) * 0.9)):
            x, y = rng.uniform(x0 + 2, x1 - 2), rng.uniform(LOW_Y + 15, LOW_Y + 27)
            col = ('#3b7040', '#4f8a47', '#f3b8c8', '#f7e08a', '#c7a9ea', '#ffffff')[rng.integers(0, 6)]
            c.img[m.ellipse(x, y, 2.2, 1.8)] = rgb(col)


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
    lower_square(m)
    # terrace edge: retaining wall face below the pavement, broken by the two staircases
    TER.__init__()
    TER.run(m, c, 0, W, FACE_Y, FACE_H, STAIRS_X, 40)
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
    # terrace edge: stone balustrade with urn piers at both sides of each staircase
    rng = np.random.default_rng(SEED + 9)
    trees = ['hd_tree_cherry_a', 'hd_tree_cherry_b', 'hd_tree_oak_a', 'hd_tree_oak_b', 'hd_tree_blossom', 'hd_tree_oak_c']
    posts = ['hd_balustrade_post', 'hd_balustrade_post_b', 'hd_balustrade_post_c']
    xa = 20
    for i, (sx, sw) in enumerate(STAIRS_X + [(W - 20 + 14, 0)]):
        xb = sx - 14
        nseg = max(1, int(round((xb - xa) / 96)))
        step = (xb - xa) / nseg
        for k in range(nseg):
            pr('hd_balustrade', xa + step * (k + 0.5), FACE_Y)
        if sw:
            pr(posts[i % 3], sx - 14, FACE_Y + 1); pr(posts[(i + 1) % 3], sx + sw + 14, FACE_Y + 1)
            pr('hd_stair_planter', sx - 32, LOW_Y + 44); pr('hd_stair_planter', sx + sw + 32, LOW_Y + 44)
        xa = sx + sw + 14
    lower_furnish(m, P, rng, trees)
    # backdrop: trees behind the roofs
    for x in range(20, W, 85):
        pr(trees[rng.integers(0, len(trees))], x + rng.uniform(-15, 15), rng.uniform(40, 70))
    pr('hd_tree_oak_b', 1188, 262)
    # hedges and shrubs in the gaps between and beside the shop fronts
    for x in list(range(26, 160, 22)) + [372, 386, 606, 620, 1176]:
        pr(['hd_bush_a', 'hd_bush_b', 'hd_bush_rose'][int(x) % 3], x, 258 + rng.uniform(-3, 3))


def lower_furnish(m, P, rng, trees):
    pr = m.prop
    cx, cy, rx, ry = COURT
    pr('hd_fountain_tiered', cx, cy + 18)
    for k in range(8):                                                   # lamps round the court
        a = np.pi / 8 + k * np.pi / 4
        pr('hd_lamp_gold', cx + np.cos(a) * (rx + 18), cy + np.sin(a) * (ry + 14))
    for bx, by in ((cx - 140, cy - 92), (cx + 140, cy - 92), (cx - 150, cy + 104), (cx + 150, cy + 104)):
        pr('hd_bench', bx, by)
    # west: wisteria pergola over two benches, birdbath and flower beds
    pr('hd_bench', 160, 1010); pr('hd_bench', 236, 1010); pr('hd_pergola', 198, 1048)
    pr('hd_birdbath', 120, 1120); pr('hd_flowerbed', 270, 1124); pr('hd_planter_pink', 96, 1060)
    # east: little cafe corner with umbrella tables and a kiosk
    pr('hd_stall_blue', 1100, 968)
    for tx, ty in ((920, 968), (1000, 990), (930, 1060)):
        pr('hd_umbrella_table', tx, ty)
    pr('hd_planter_violet', 870, 952); pr('hd_bin', 1150, 1000)
    # south promenade: two market stalls, a cart, notice board, benches
    pr('hd_stall_red', 300, 1236); pr('hd_cart', 900, 1238); pr('hd_bicycle', 150, 1232)
    pr('hd_notice_board', 470, 1220); pr('hd_bench', 740, 1222); pr('hd_bench', 1040, 1222)
    # lawns: trees at the quadrant corners, shrubs, flowers
    for tx, ty in ((70, 900), (430, 916), (770, 914), (1150, 1110), (60, 1150), (1140, 1170)):
        pr(trees[rng.integers(0, len(trees))], tx, ty)
    blocked = m.c.mat != GRASS                                           # lawn planting only on grass
    m.rng = rng
    m.scatter(['hd_bush_a', 'hd_bush_b', 'hd_bush_rose', 'hd_bush_yellow'], [2, 2, 1, 1], 22, (30, 850, W - 60, 330), blocked, 12, P)
    m.scatter(['hd_flowers_pink', 'hd_flowers_white', 'hd_flowers_yellow', 'hd_grass_tall', 'hd_flowers_violet'], [2, 1, 1, 2, 1],
              70, (30, 850, W - 60, 330), blocked, 6, P)
    # south edge: hedge of shrubs and a tree line behind the edge wall
    for row, y in enumerate((SOUTH_Y + 10, H - 6)):             # clipped hedge, two rows; no tall trees
        for x in range(30 + row * 17, W, 34):                     # here so the stalls stay in view
            pr(['hd_bush_a', 'hd_bush_b', 'hd_bush_rose'][(int(x) // 34 + row) % 3 if row else int(x) % 2], x + rng.uniform(-5, 5), y)


def common_elev_dump(E):
    """elevation.json layout: one primitive per line, areas in file order (same as the hand-kept file)."""
    out = ['{', '  "_doc": %s,' % json.dumps(E['_doc'], ensure_ascii=False), '  "areas": {']
    names = list(E['areas'])
    for i, n in enumerate(names):
        prims = E['areas'][n]
        out.append('    %s: [' % json.dumps(n))
        out += ['      %s%s' % (json.dumps(q, ensure_ascii=False), ',' if j < len(prims) - 1 else '') for j, q in enumerate(prims)]
        out.append('    ]%s' % (',' if i < len(names) - 1 else ''))
    out += ['  }', '}']
    return '\n'.join(out) + '\n'


def main():
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = json.loads(json.dumps(M['areas'][AREA]))
    for d in base['doors']:
        if d['id'] in DOOR_RECTS:
            d['rect'] = DOOR_RECTS[d['id']]
    ex = {e['id']: e for e in base.get('examine', [])}
    for e in EXAMINE:
        ex[e['id']] = e
    base['examine'] = list(ex.values())
    m = HDMap(AREA, W, H, SEED)
    design(m)
    furnish(m, P)
    keep = {'hd_balustrade', 'hd_balustrade_post', 'hd_balustrade_post_b', 'hd_balustrade_post_c'}
    dropped = [p for p in m.props if p['type'] not in keep and TER.hits(p, P)]
    m.props = [p for p in m.props if p['type'] in keep or not TER.hits(p, P)]
    print('terrace walls', len(TER.walls), 'stairs', len(TER.stairs), 'props dropped for stairs/walls', len(dropped),
          [(p['type'], p['x'], p['y']) for p in dropped])
    m.bake_shadows(P)
    m.collision = lambda P_: WALLS + TER.walls
    animals = [{'type': 'cat_grey', 'n': 1, 'region': [60, 1100, 1080, 120], 'day': False},
               {'type': 'bird', 'n': 3, 'region': [380, 930, 440, 230]},
               {'type': 'bird', 'n': 2, 'region': [234, 560, 704, 160]},
               {'type': 'dog', 'n': 1, 'region': [527, 612, 528, 110]}]
    extra = dict(ellipses=[[FOUNTAIN[0], FOUNTAIN[1] + 4, 84, 56]], water=[], stairs=TER.stairs, doors=base['doors'], animals=animals,
                 visualStyle='godot_hd_dense',
                 visualUpdate='godot_jalan_kota_hd', v6Layout=dict(version=3, generator='tools/worldgen/jalan_kota_hd.py', hd=True))
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    bad = m.write(base, extra, P, Q, apply='--apply' in sys.argv, preview=prev)
    if '--apply' in sys.argv and not bad:
        ep = A / 'data/elevation.json'
        E = json.loads(ep.read_text(encoding='utf-8'))
        E['areas'][AREA] = ELEVATION
        ep.write_text(common_elev_dump(E), encoding='utf-8')
        print('elevation.json:', AREA, len(ELEVATION), 'primitives')


if __name__ == '__main__':
    main()
