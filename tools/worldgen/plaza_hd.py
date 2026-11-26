"""Plaza Kota, dense HD redesign (2400x1600 world, 2 texels per unit).

Same districts, doors, collision walls and quest points as before; every surface is repainted
with HD materials and each district is furnished so it reads lived-in:
  * north gardens behind the houses: hedges, flower beds, a tree line, benches on the loop path
  * boulevard in front of the houses: brick road with curbs, drains, tree planters, lamps
  * central square: stone tiles, radial court with a star inlay around the fountain
  * west market: terracotta checker tiles, two rows of stalls, crates, sacks, carts, bunting
  * east cafe terrace: deck, umbrella tables, planters, lantern strings
  * canal with stone walls, lilies and reeds; three bridges; tree-lined south bank
Usage: python3 tools/worldgen/plaza_hd.py [--preview OUT.png] [--apply]
"""
import sys, json, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hdmap import HDMap, K, GRASS, PATH, STONE, WATER, DECK, SOIL, A   # noqa: E402
from paint import rgb, wear, moss                                     # noqa: E402
from ground import dist_from, noise                                   # noqa: E402
import common                                                         # noqa: E402

AREA, W, H = 'plaza', 2400, 1600
SEED = int(hashlib.sha256(b'plaza_hd_dense').hexdigest()[:8], 16)
TILE_M = 11            # market tiles material id

BLVD = (40, 520, 2320, 110)                 # x, y, w, h  (front of the houses)
SQUARE = (820, 640, 760, 650)
RING = (1200, 950, 300, 225)
MARKET = (250, 720, 520, 460)
TERRACE = (1690, 720, 440, 350)
CANAL = (20, 1330, 2360, 86)
BRIDGES = [(436, 100), (1136, 128), (1856, 100)]  # x, width
SIDE_PATHS = [((0, 918), (250, 918)), ((770, 918), (820, 918)), ((1580, 918), (1690, 918)), ((2130, 918), (2400, 918))]
NORTH_LOOP = [(225, 520), (190, 380), (240, 250), (420, 200), (700, 205), (950, 240), (1200, 250), (1450, 230),
              (1700, 195), (1980, 210), (2180, 290), (2204, 420), (2204, 520)]
NORTH_SPURS = [[(1060, 520), (1030, 380), (1060, 245)], [(1660, 520), (1680, 380), (1700, 200)]]
SOUTH_LOOP = [(485, 1180), (485, 1330), (485, 1440), (560, 1520), (900, 1540), (1150, 1545)]
SOUTH_LOOP_E = [(1905, 1070), (1905, 1330), (1905, 1440), (1830, 1520), (1500, 1540), (1250, 1545)]
SOUTH_EXIT = (1140, 1420, 120, 180)
# elevation: the north gardens sit one storey-step above the street behind a stone retaining wall,
# and the cafe terrace is a raised deck above the square/lawn. Both are reached only by stairs.
N_WALL = (20, 2380, 436, 30)                # x0, x1, top y, face height
N_STAIRS = [(196, 60), (1032, 56), (1632, 56), (2176, 56)]
T_FACE = 34                                 # terrace south face height (below y = ty + th)
T_STAIRS_S = (1878, 54)
T_STAIRS_SIDE = (884, 68)                   # y, height of the west/east side stairs
ELEV_WALLS = []                             # filled by elevation(): collision rects for faces/cheeks
ELEV_CLEAR = []                             # stair rects that must stay free of props
BEDS = []                                   # flower beds in front of the terrace wall
# designed walls before elevation (map edges + canal); maps.json already holds older elevation walls
BASE_WALLS = [[0, 0, 20, 862], [0, 974, 20, 626], [2380, 0, 20, 862], [2380, 974, 20, 626], [0, 0, 2400, 20],
              [0, 1582, 1140, 18], [1260, 1582, 1140, 18], [20, 1324, 410, 98], [540, 1324, 590, 98],
              [1270, 1324, 580, 98], [1960, 1324, 420, 98], [430, 1312, 8, 114], [532, 1312, 8, 114],
              [1130, 1312, 8, 114], [1262, 1312, 8, 114], [1850, 1312, 8, 114], [1952, 1312, 8, 114]]
STAIRS = []                                 # stairs written to maps.json for tools/maptool.py

# old landmark types -> the new HD drawings in tools/artkit/landmarks.py (same spots, alt flags kept)
KEEP = {'v43_v41_bld_arland_house_house_blue': 'hd_house_arland', 'v43_v41_bld_sofia_house_house_brick': 'hd_house_sofia',
        'v43_bld_cafe': 'hd_cafe_senja', 'v43_v41_fountain_fountain': 'hd_fountain_grand', 'mural': 'hd_mural_old',
        'notice_board': 'hd_notice_board', 'mailbox': 'hd_mailbox', 'old_mailbox': 'hd_mailbox_old', 'bicycle': 'hd_bicycle',
        'vending': 'hd_vending', 'signpost_w': 'hd_signpost_w', 'signpost_e': 'hd_signpost_e', 'signpost_s': 'hd_signpost_s',
        'v51_banner_cafe': 'hd_banner_cafe', 'v51_lantern_gold': 'hd_lamp_gold', 'v51_birdbath': 'hd_birdbath',
        'garden_plot_tk': 'hd_garden_plot', 'flower_buckets': 'hd_flower_buckets', 'flower_buckets_b': 'hd_flower_buckets_b',
        'flower_buckets_c': 'hd_flower_buckets_c', 'v51_fountain_tiered': 'hd_fountain_tiered', 'v51_column_stone': 'hd_column_stone'}
ALT = {'mural_new': 'hd_mural_new'}


def _face(m, c, x0, x1, y0, h, salt):
    """Retaining wall seen from the south: coping, cut-stone face darkening downward, contact shadow."""
    face = m.rect(x0, y0, x1 - x0, h)
    c.put(face, c.bricks(('#8d877b', '#999285', '#a49d90', '#afa89b'), 46, 20, '#5f5a51', salt=salt), STONE)
    t = np.clip((c.yy / K - y0) / h, 0, 1)
    c.img[face] *= (1.0 - 0.38 * t[face])[:, None]
    cop = m.rect(x0 - 2, y0 - 7, x1 - x0 + 4, 8)
    c.put(cop, c.bricks(('#cfc8ba', '#d8d2c5', '#e1dbcf'), 64, 16, '#9a9386', salt=salt + 1), STONE)
    c.img[m.rect(x0 - 2, y0 - 7, x1 - x0 + 4, 1.5)] = rgb('#f1ece2')
    c.img[m.rect(x0, y0 + 1, x1 - x0, 2)] *= 0.6                          # coping shadow on the face
    sh = m.rect(x0, y0 + h, x1 - x0, 12)
    tt = np.clip((c.yy / K - (y0 + h)) / 12, 0, 1)
    c.img[sh] *= (0.55 + 0.45 * tt[sh])[:, None]
    rng = np.random.default_rng(salt)
    for _ in range(int((x1 - x0) / 9)):                                     # ivy / grass hanging over
        x = rng.uniform(x0, x1)
        ln = rng.uniform(3, h * (0.8 if rng.random() < 0.2 else 0.35))
        col = rgb(('#3b7040', '#4f8a47', '#2b5537')[rng.integers(0, 3)])
        c.img[m.rect(x, y0 - 2, 2.5, ln)] = col
        if rng.random() < 0.15:
            c.img[m.ellipse(x + 1, y0 + ln, 2, 1.6)] = rgb('#f3b8c8')


def _stairs(m, c, x0, y0, w, h, salt, side=0):
    """Stone stairs. side=0: descend southward (treads are horizontal bands); side=-1/+1: descend
    toward west/east (bands run vertically). Cheek walls get collision so you can only use the steps."""
    n = max(3, int(round((w if side else h) / 7)))
    STAIRS.append(dict(id='st%d' % len(STAIRS), rect=[int(x0), int(y0), int(w), int(h)], dir={0: 'down', -1: 'west', 1: 'east'}[side]))
    tex_t = c.bricks(('#ddd6c8', '#e5dfd2', '#ece7dc'), 52, 18, '#a8a092', salt=salt)
    for i in range(n):
        if side == 0:
            a = y0 + i * h / n
            tread, riser = m.rect(x0, a, w, h / n * 0.58), m.rect(x0, a + h / n * 0.58, w, h / n * 0.42 + 0.5)
        else:
            a = (x0 + w - (i + 1) * w / n) if side < 0 else (x0 + i * w / n)
            tw = w / n
            tread = m.rect(a + (0 if side < 0 else tw * 0.42), y0, tw * 0.58, h)
            riser = m.rect(a + (tw * 0.58 if side < 0 else 0), y0, tw * 0.42 + 0.5, h)
        c.put(tread, tex_t, STONE)
        c.put(riser, tex_t, STONE)
        c.img[riser] *= 0.62 + 0.04 * i
    c.img[m.rect(x0, y0, w, h)] *= 1.0
    cheek = rgb('#8d877b')
    if side == 0:
        for cx_ in (x0 - 8, x0 + w):
            r = m.rect(cx_, y0 - 7, 8, h + 7)
            c.img[r] = cheek
            c.img[m.rect(cx_, y0 - 7, 8, 2)] = rgb('#e1dbcf')
            c.img[m.rect(cx_ + 6, y0 - 5, 2, h + 5)] *= 0.7
            ELEV_WALLS.append([int(cx_), int(y0 - 2), 8, int(h + 2)])
        ELEV_CLEAR.append((x0 - 8, y0 - 30, w + 16, h + 60))
    else:
        for cy_ in (y0 - 8, y0 + h):
            r = m.rect(x0, cy_, w, 8)
            c.img[r] = cheek
            c.img[m.rect(x0, cy_, w, 2)] = rgb('#e1dbcf')
            ELEV_WALLS.append([int(x0), int(cy_), int(w), 8])
        ELEV_CLEAR.append((x0 - 30, y0 - 8, w + 60, h + 16))


def elevation(m, c):
    ELEV_WALLS.clear(); ELEV_CLEAR.clear(); STAIRS.clear()
    x0, x1, y0, h = N_WALL
    cuts = sorted(N_STAIRS)
    xa = x0
    for i, (sx, sw) in enumerate(cuts + [(x1, 0)]):
        if sx > xa:
            _face(m, c, xa, sx - (8 if sw else 0), y0, h, 40 + i)
            ELEV_WALLS.append([int(xa), int(y0 - 3), int(sx - (8 if sw else 0) - xa), int(h + 3)])
        if sw:
            _stairs(m, c, sx, y0, sw, h, 60 + i)
        xa = sx + sw + 8
    # cafe terrace: raised deck, open to the boulevard on the north side
    tx, ty, tw, th_ = TERRACE
    fy = ty + th_
    sx, sw = T_STAIRS_S
    _face(m, c, tx - 8, sx - 8, fy, T_FACE, 80)
    _face(m, c, sx + sw + 8, tx + tw + 8, fy, T_FACE, 81)
    ELEV_WALLS.append([tx - 8, fy - 3, sx - 8 - (tx - 8), T_FACE + 3])
    ELEV_WALLS.append([sx + sw + 8, fy - 3, tx + tw + 8 - (sx + sw + 8), T_FACE + 3])
    _stairs(m, c, sx, fy, sw, T_FACE, 82)
    sy, sh = T_STAIRS_SIDE
    for side, ex in ((-1, tx - 8), (1, tx + tw)):
        # side edge: thin visible face + collision, broken by side stairs
        for ya, yb in ((ty + 40, sy - 8), (sy + sh + 8, fy + T_FACE)):
            r = m.rect(ex, ya, 8, yb - ya)
            c.img[r] = rgb('#8d877b')
            c.img[m.rect(ex + (6 if side > 0 else 0), ya, 2, yb - ya)] = rgb('#d8d2c5')
            ELEV_WALLS.append([int(ex), int(ya), 8, int(yb - ya)])
        stx = ex - 30 if side < 0 else ex
        _stairs(m, c, stx, sy, 38, sh, 90 + side, side=side)
    # deck rises gently from the boulevard (north) - a short ramp of planks with rails
    for rx in (tx - 8, tx + tw):
        c.img[m.rect(rx, ty, 8, 40)] = rgb('#5e3b27')
        ELEV_WALLS.append([int(rx), int(ty + 20), 8, 20])


def design(m, P):
    c = m.c
    grass = c.grass(('#4f9157', '#57995d', '#5fa163', '#68a869', '#72b06f', '#7db876'))
    c.put(np.ones((c.h, c.w), bool), grass, GRASS)
    # clover / darker lawn patches so the lawn is not one flat green
    n = noise(c.h, c.w, 120, SEED + 3)
    lawn = (n > 0.62)
    c.img[lawn] = c.img[lawn] * 0.9 + rgb('#3f7f4a') * 0.1
    gravel = c.dirt(('#b49b74', '#bfa77f', '#c9b28a', '#d4be97'))
    # ---- dirt loops
    paths = m.path(NORTH_LOOP, 46, 2, 1) | m.path(SOUTH_LOOP, 44, 2, 2) | m.path(SOUTH_LOOP_E, 44, 2, 3)
    for sp_ in NORTH_SPURS:
        paths |= m.path(sp_, 40, 2, 4)
    c.put(paths, gravel, PATH)
    # ---- boulevard: brick road with light curbs and drains
    bx, by, bw, bh = BLVD
    road = m.rect(bx, by, bw, bh)
    c.put(road, c.bricks(('#b98a66', '#c4946e', '#cc9d77', '#d6a882', '#bf8f6a'), 36, 18, '#8c6a52', salt=5), STONE)
    for yy in (by, by + bh - 8):
        curb = m.rect(bx, yy, bw, 8)
        c.put(curb, c.bricks(('#d9d3c8', '#e2dcd2', '#ebe6dd'), 60, 16, '#a59d90', salt=6), STONE)
    for x in range(bx + 120, bx + bw - 60, 300):
        dr = m.rect(x, by + bh - 20, 26, 10)
        c.img[dr] = rgb('#4b4f57')
        c.img[dr & ((c.xx // K) % 4 == 0)] = rgb('#2c2f35')
    # side lanes to the exits / districts
    for (x0, y0), (x1, y1) in SIDE_PATHS:
        lane = m.rect(min(x0, x1), y0 - 52, abs(x1 - x0), 104)
        c.put(lane, c.bricks(('#c9b79c', '#d3c2a8', '#dccbb2', '#e4d5be'), 34, 17, '#a08c73', salt=7), STONE)
    # ---- central square: big light stone slabs + radial court
    sx, sy, sw, sh = SQUARE
    sq = c.rrect(sx * K, sy * K, sw * K, sh * K, 40 * K)
    c.put(sq, c.tiles('#e4d8c4', '#ddd0ba', 48, grout='#b7a68c', salt=8), STONE)
    rx, ry, rr, rv = RING
    court = m.ellipse(rx, ry, rr, rv)
    rad, r, th, ri = c.radial(rx * K, ry * K, rv / rr, ('#d4c7b4', '#dcd0be', '#e4d9c8', '#ebe2d3'), 26, 44, salt=9, mortar='#a99a85')
    c.put(court, rad, STONE)
    c.img[court & (r > (rr - 12) * K)] = rgb('#a2876b')
    c.img[court & (r > (rr - 8) * K)] = rgb('#c19d7a')
    for k in range(8):                                   # star inlay
        a = k * np.pi / 4
        tip = (rx + np.cos(a) * rr * 0.86, ry + np.sin(a) * rv * 0.86)
        l = (rx + np.cos(a + 0.2) * rr * 0.5, ry + np.sin(a + 0.2) * rv * 0.5)
        rgt = (rx + np.cos(a - 0.2) * rr * 0.5, ry + np.sin(a - 0.2) * rv * 0.5)
        from matplotlib.path import Path as MP
        pts = np.array([tip, l, rgt]) * K
        tri = MP(pts).contains_points(np.stack([c.xx.ravel(), c.yy.ravel()], 1)).reshape(c.h, c.w)
        c.img[tri] = rgb('#c9835c' if k % 2 else '#efe2c6')
    # ---- west market: checker tiles
    mx, my, mw, mh = MARKET
    mk = c.rrect(mx * K, my * K, mw * K, mh * K, 18 * K)
    c.put(mk, c.tiles('#d79a74', '#f0dcc0', 40, grout='#a7765a', salt=10), TILE_M)
    # ---- east terrace deck
    tx, ty, tw, th_ = TERRACE
    deck = m.rect(tx, ty, tw, th_)
    c.put(deck, c.planks(('#8b5d3c', '#996a46', '#a5754f', '#b07f57'), 20, salt=11), DECK)
    c.img[m.rect(tx, ty + th_, tw, 6)] *= 0.6
    # ---- canal with stone walls
    cx_, cy_, cw_, ch_ = CANAL
    water = m.rect(cx_, cy_ + 10, cw_, ch_ - 20)
    c.put(water, c.water(water, ('#1f5378', '#27638a', '#30759c', '#3d89ae', '#57a0c2')), WATER)
    for yy, hh in ((cy_ - 6, 16), (cy_ + ch_ - 10, 16)):
        lip = m.rect(cx_, yy, cw_, hh)
        c.put(lip, c.bricks(('#9c958a', '#a8a196', '#b4ada1', '#c0b9ad'), 40, 16, '#6f695f', salt=12), STONE)
    c.img[m.rect(cx_, cy_ + 10, cw_, 6) & water] *= 0.55            # wall shadow on the water
    dl = dist_from(~water, 6)
    for i, f in ((1, 0.5), (2, 0.25)):
        sel = water & (dl == i)
        c.img[sel] = c.img[sel] * (1 - f) + rgb('#dcf0f6') * f
    for bx_, bw_ in BRIDGES:
        br = m.rect(bx_, cy_ - 6, bw_, ch_ + 12)
        if bw_ > 110:
            c.put(br, c.bricks(('#d9cdb8', '#e1d6c3', '#e9dfce'), 40, 20, '#a8997f', salt=13), STONE)
        else:
            c.put(br, c.planks(('#8b5d3c', '#996a46', '#a5754f', '#b07f57'), 16, salt=14, vertical=True), DECK)
        for xx in (bx_, bx_ + bw_ - 8):
            c.img[m.rect(xx, cy_ - 6, 8, ch_ + 12)] = rgb('#7a6a58' if bw_ > 110 else '#5e3b27')
        c.img[m.rect(bx_, cy_ + ch_ + 6, bw_, 6)] *= 0.7
    m.water_mask = water
    ex, ey, ew, eh = SOUTH_EXIT
    c.put(m.rect(ex, ey, ew, eh), c.bricks(('#c9b79c', '#d3c2a8', '#dccbb2', '#e4d5be'), 34, 17, '#a08c73', salt=15), STONE)
    # ---- flower beds along the north side of the boulevard, between the houses
    soil = c.dirt(('#6e5038', '#7a5a3f', '#866447', '#916f50'))
    beds = []
    BEDS.clear()
    for x0, x1 in ((40, 290), (600, 1150), (1480, 1820), (2160, 2340)):
        segs = [(x0, x1)]
        for sx, sw in N_STAIRS:
            segs = [q for a, b in segs for q in ((a, min(b, sx - 14)), (max(a, sx + sw + 14), b)) if q[1] - q[0] > 30]
        beds += segs
    for x0, x1 in beds:
        bed = m.rect(x0, 470, x1 - x0, 46)
        c.put(bed, soil, SOIL)
        BEDS.append((x0, x1))
        c.img[m.rect(x0 - 4, 466, x1 - x0 + 8, 4)] = rgb('#9c958a')
    elevation(m, c)
    # ---- edges, wear, ground clutter
    gm = c.mat == GRASS
    c.rim(c.mat == PATH, gm, dark='#86704f', ao=(0.9, 0.95))
    c.overhang(c.mat == PATH, gm, 0.25, 1)
    c.rim(np.isin(c.mat, [STONE, DECK, TILE_M]), gm | (c.mat == PATH))
    wear(c, np.isin(c.mat, [STONE, TILE_M]), 0.06, salt=2)
    moss(c, np.isin(c.mat, [STONE]), gm, 0.4)
    rng = np.random.default_rng(SEED + 5)
    hard = np.isin(c.mat, [STONE, TILE_M])
    ys, xs = np.nonzero(hard[::8, ::8])
    for i in rng.integers(0, len(ys), 900):        # cracks, pebbles and fallen petals on the paving
        y, x = ys[i] * 8, xs[i] * 8
        kind = rng.random()
        if kind < 0.3:
            for t in range(rng.integers(6, 16)):
                yy, xx = y + t // 2 * (1 if rng.random() < .5 else -1), x + t
                if 0 <= yy < c.h and 0 <= xx < c.w:
                    c.img[yy, xx] *= 0.7
        elif kind < 0.65:
            c.img[y:y + 3, x:x + 4] = rgb(('#f3b8c8', '#f7d4de', '#e996ad')[rng.integers(0, 3)])
        elif kind < 0.85:
            c.img[y:y + 3, x:x + 3] = rgb(('#c98b4a', '#a3693a', '#d9a35c')[rng.integers(0, 3)])
        else:
            c.img[y:y + 2, x:x + 2] = rgb('#8f877c')
    ys, xs = np.nonzero(gm[::6, ::6])
    for i in rng.integers(0, len(ys), 2600):      # grass tufts and tiny flowers on the lawn
        y, x = ys[i] * 6, xs[i] * 6
        if rng.random() < 0.75:
            for d in range(-2, 3):
                h_ = rng.integers(3, 7)
                c.img[max(0, y - h_):y, x + d * 2] = c.img[y, x] * (1.18 if d % 2 else 0.85)
        else:
            c.img[y:y + 2, x:x + 2] = rgb(('#fbf6ec', '#f7c9d9', '#f4d870', '#c4b2f2')[rng.integers(0, 4)])
    edge = np.minimum.reduce([c.xx, c.yy, c.w - 1 - c.xx, c.h - 1 - c.yy])
    c.img[edge < 10] *= 0.86


def furnish(m, P, old):
    pr = m.prop
    for p in old:                                       # landmarks, story props and their exact spots
        if p['type'] in KEEP:
            q = dict(p)
            q['type'] = KEEP[p['type']]
            if q['type'] == 'hd_flower_buckets_b':          # was standing on the new terrace wall
                q['x'], q['y'] = 2010, 1140
            if 'alt' in q:
                q['alt'] = ALT.get(q['alt'], q['alt'])
            m.props.append(q)
    rng = np.random.default_rng(SEED + 11)
    # boulevard: planters with trees, lamps between them, benches, bollards at the square
    for x in range(160, 2300, 240):
        if 760 < x < 1640:
            continue
        pr('hd_tree_planter', x, 668)
    for x in range(280, 2300, 240):
        if 760 < x < 1640:
            pr('hd_lamp', x - 120 if x < 1200 else x + 120, 650) if x in (760, 1600) else None
            continue
        pr('hd_lamp', x, 652)
    for x in (840, 1560):
        pr('hd_lamp', x, 660)
    for x in (1110, 1150, 1250, 1290):
        pr('hd_bollard', x, 650)
    for x in (680, 1520, 2240):
        pr('hd_bench', x, 470 + 70)
    pr('hd_bike_rack', 230, 560)
    pr('hd_bin', 610, 560); pr('hd_bin', 1770, 560)
    # fences along the streets: picket fence between the boulevard and the lawn (gap at the
    # market entrance and the open terrace side), iron railings on both canal banks
    def fence_run(pid, x0, x1, y):
        n = int((x1 - x0) // 96)
        start = x0 + ((x1 - x0) - n * 96) / 2
        for i in range(n):
            pr(pid if pid != 'picket' else ('hd_fence_picket', 'hd_fence_picket_b')[i % 2], start + 48 + i * 96, y)
    for x0, x1 in ((40, 440), (584, 776), (2132, 2360)):
        fence_run('picket', x0, x1, 712)
    gaps = [(bx - 6, bx + bw + 6) for bx, bw in BRIDGES]
    edges = [20] + [v for g in gaps for v in g] + [2380]
    for i in range(0, len(edges), 2):
        fence_run('hd_railing_iron', edges[i], edges[i + 1], 1322)
        fence_run('hd_railing_iron', edges[i], edges[i + 1], 1440)
    # flower beds under the terrace wall: real flower clumps instead of painted dots
    for x0, x1 in BEDS:
        for k, x in enumerate(range(int(x0) + 14, int(x1) - 8, 26)):
            pr(('hd_flowers_pink', 'hd_flowers_yellow', 'hd_flowers_violet', 'hd_flowers_white')[(k + x0 // 7) % 4],
               x + rng.integers(-4, 5), 486 + (k % 2) * 16 + rng.integers(-3, 4))
    # north gardens
    for x in range(40, 2400, 58):                        # back tree line, overlapping crowns
        kind = ('hd_tree_pine_a', 'hd_tree_oak_a', 'hd_tree_pine_b', 'hd_tree_oak_b', 'hd_tree_big_a', 'hd_tree_cherry_a')[rng.integers(0, 6)]
        pr(kind, x + rng.integers(-12, 12), 70 + rng.integers(-10, 25))
    for x in range(70, 2400, 110):
        pr(('hd_bush_a', 'hd_bush_b', 'hd_bush_rose')[rng.integers(0, 3)], x + rng.integers(-15, 15), 128 + rng.integers(0, 14))
    for x, y in ((560, 330), (860, 360), (1350, 340), (1880, 330), (330, 300)):
        pr('hd_flowerbed', x, y)
    for x, y in ((470, 250), (1300, 280), (1900, 245)):
        pr('hd_bench', x, y)
    for x, y in ((320, 230), (840, 225), (1560, 225), (2080, 260)):
        pr('hd_lamp', x, y)
    for x, y in ((150, 470), (760, 300), (1150, 330), (1500, 330), (2280, 470), (2250, 330), (120, 330)):
        pr(('hd_tree_cherry_a', 'hd_tree_cherry_b', 'hd_tree_oak_b')[rng.integers(0, 3)], x, y)
    # west market
    mx, my, mw, mh = MARKET
    for i, x in enumerate((330, 480, 630)):
        pr(('hd_stall_red', 'hd_stall_blue')[i % 2], x, 800)
        pr(('hd_stall_blue', 'hd_stall_red')[i % 2], x, 1150)
    for x, y in ((280, 830), (690, 830), (700, 1160), (270, 1160)):
        pr('hd_crate_stack', x, y)
    for x, y in ((405, 820), (560, 1170), (700, 1000)):
        pr('hd_sacks', x, y)
    for x, y in ((280, 1000), (720, 760)):
        pr('hd_barrel', x, y); pr('hd_barrel', x + 26, y + 6)
    pr('hd_cart', 380, 1045)
    pr('hd_bunting', 510, 760); pr('hd_bunting', 510, 1110)
    for x, y in ((250, 720), (770, 720), (250, 1185), (770, 1185)):
        pr('hd_planter_pink', x, y)
    # central square
    for k in range(8):
        a = k * np.pi / 4 + np.pi / 8
        x, y = RING[0] + np.cos(a) * 345, RING[1] + np.sin(a) * 260
        if 700 < y < 1300 and not (abs(x - 1200) < 80 and y > 1100):
            pr('hd_planter_violet' if k % 2 else 'hd_planter_pink', x, y)
    for x, y in ((960, 700), (1440, 700), (900, 1240), (1500, 1240)):
        pr('hd_lamp', x, y)
    for x, y in ((1010, 1170), (1390, 1170), (1000, 730), (1400, 730)):
        pr('hd_bench', x, y)
    pr('hd_bunting', 1200, 690)
    # east terrace
    for i, (x, y) in enumerate(((1760, 790), (1890, 790), (2020, 790), (1760, 920), (1890, 920), (2020, 920), (1825, 1040), (1975, 1040))):
        pr('hd_umbrella_table', x, y)
    pr('hd_lantern_string', 1910, 760); pr('hd_lantern_string', 1910, 1000)
    for x in (1700, 2120):
        for y in (760, 900, 1060):
            pr('hd_planter_violet' if y == 900 else 'hd_planter_pink', x, y)
    # canal banks
    for x in range(60, 2380, 90):
        if any(bx - 30 < x < bx + bw + 30 for bx, bw in BRIDGES):
            continue
        if rng.random() < 0.55:
            pr('hd_reeds', x + rng.integers(-10, 10), 1340 + rng.integers(0, 10))
    for x in range(80, 2380, 70):
        if rng.random() < 0.5 and not any(bx - 10 < x < bx + bw + 10 for bx, bw in BRIDGES):
            pr(('hd_lily_a', 'hd_lily_b')[rng.integers(0, 2)], x, 1380 + rng.integers(-6, 14))
    for x, y in ((420, 1330), (560, 1330), (1120, 1330), (1280, 1330), (1840, 1330), (1970, 1330)):
        pr('hd_lamp', x, y)
    # south bank: dense trees with the loop path through them
    for x in range(30, 2400, 62):
        if 1080 < x < 1320:
            continue
        for row, y0 in enumerate((1478, 1590)):
            kind = ('hd_tree_cherry_a', 'hd_tree_oak_a', 'hd_tree_willow', 'hd_tree_cherry_b', 'hd_tree_oak_c', 'hd_tree_big_b')[rng.integers(0, 6)]
            tx_, ty_ = x + rng.integers(-14, 14) + row * 30, y0 + rng.integers(-8, 8)
            near_path = m.c.mat[min(m.c.h - 1, int(ty_ * K)) - 80:min(m.c.h, int(ty_ * K) + 20),
                                max(0, int(tx_ * K) - 70):int(tx_ * K) + 70] == PATH
            if not near_path.any() and tx_ < 2370:
                pr(kind, tx_, ty_)
    # lawn corners around the market/terrace and square: shrubs and flowers
    blocked = (m.c.mat != GRASS) | (dist_from(m.c.mat != GRASS, 30 * K) < 22 * K)
    blocked |= (np.abs(m.c.yy - 918 * K) < 60 * K)       # keep the E-W walk lines clear
    for x, y, r in m.points:
        m.keep_out.append((x, y, r))
    m.scatter(['hd_bush_a', 'hd_bush_b', 'hd_bush_rose', 'hd_bush_yellow', 'hd_tree_oak_a', 'hd_tree_cherry_b', 'hd_rock_a'],
              [5, 5, 3, 3, 2, 2, 1], 70, (30, 160, 2340, 1150), blocked, 20, P)
    m.scatter(['hd_flowers_pink', 'hd_flowers_yellow', 'hd_flowers_violet', 'hd_flowers_white'], [1, 1, 1, 1], 160,
              (30, 140, 2340, 1440), blocked, 8, P)
    m.scatter(['hd_grass_tall', 'hd_grass_tall_b', 'hd_fern_a'], [3, 2, 1], 80, (30, 140, 2340, 1440), blocked, 10, P)
    m.props = [p for p in m.props if p is not None]


def main():
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = M['areas'][AREA]
    old = json.loads((HERE.parent / 'pre_hd' / 'plaza.props.json').read_text(encoding='utf-8'))
    m = HDMap(AREA, W, H, SEED)
    m.points = [(p[3], p[4], 46) for p in common.migrate_quests(json.loads(json.dumps(Q)), AREA, lambda x, y: (x, y))]
    m.points += [(e['x'], e['y'], 46) for e in base.get('examine', [])]
    m.points += [(d['tx'], d['ty'], 50) for b in M['areas'].values() for d in b.get('doors', []) if d.get('to') == AREA]
    for d in base['doors']:
        x, y, w, h = d['rect']; m.points.append((x + w / 2, y + h / 2, max(w, h) / 2 + 40))
    design(m, P)
    furnish(m, P, old)
    # collision stays the designed one (map edges, canal walls, fountain), not derived from water
    keep_types = set(KEEP.values())

    def hit(p):
        if p['type'] in keep_types:
            return False
        d = P[p['type']]
        fx0, fy0, fw, fh = p['x'] - d.get('cw', 0) / 2, p['y'] - max(d.get('ch', 0), 6), max(d.get('cw', 0), 6), max(d.get('ch', 0), 6)
        for x, y, w, h in ELEV_WALLS + [list(r) for r in ELEV_CLEAR]:
            if fx0 < x + w and x < fx0 + fw and fy0 < y + h and y < fy0 + fh:
                return True
        return False
    dropped = [p for p in m.props if hit(p)]
    m.props = [p for p in m.props if not hit(p)]
    print('elevation walls', len(ELEV_WALLS), 'props dropped for stairs/walls', len(dropped))
    m.bake_shadows(P)
    m.collision = lambda P_: BASE_WALLS + ELEV_WALLS
    extra = dict(ellipses=base.get('ellipses', []), water=base.get('water', []), animals=base.get('animals', []),
                 waterFlow=base.get('waterFlow'), stairs=STAIRS, visualStyle='godot_hd_dense', visualUpdate='godot_plaza_dense',
                 v6Layout=dict(version=3, generator='tools/worldgen/plaza_hd.py', hd=True))
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    m.write(base, extra, P, Q, apply='--apply' in sys.argv, preview=prev)
    if '--apply' in sys.argv:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import bridges_u2b                              # U2b: the canal bridges' arches and end posts
        bridges_u2b.apply(['plaza'])


if __name__ == '__main__':
    main()
