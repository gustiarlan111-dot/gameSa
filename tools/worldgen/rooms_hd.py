"""HD interiors drawn from code with tools/worldgen/interior.py. One function per room; every quest
point, examine spot, door and the sleep spot of the old room stay where they were and are validated
reachable before anything is written.

Run:  python3 tools/worldgen/rooms_hd.py <area|all> [--preview DIR] [--apply]
"""
import sys, json, hashlib, math
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hdmap import HDMap, A          # noqa: E402
from interior import Room           # noqa: E402

ROOMS = {}


def room(fn):
    ROOMS[fn.__name__] = fn
    return fn


# ---------------------------------------------------------------------------------------- homes
@room
def sofia_room(r):
    W, H = 600, 448
    r.shell(W, H, floor='planks', wall='#f6e2d8', wainscot='#e2a7a8', trim='#fff3ea', pattern='dots',
            floor_pal=('#c08e62', '#c9996c', '#d2a476', '#b98760'), door=(274, 52))
    # back wall: windows, frames, fairy lights, hanging plants
    r.window(160, 20, 64, 46, curtain='#f6c3cd')
    r.window(386, 20, 62, 46, curtain='#f6c3cd')
    r.string_lights(34, 150, 16, sag=10, n=10)
    r.frame(244, 24, 24, 30, 3); r.frame(276, 30, 18, 22, 0); r.frame(300, 22, 22, 18, 2)
    r.frame(336, 26, 20, 26, 1)
    r.poster(470, 22, 28, 38, '#fbe9ef', '#9fd3f0'); r.poster(512, 26, 30, 34, '#eef5fb', '#f2a0b8')
    r.hanging_plant(40, 10, 34); r.hanging_plant(560, 10, 34)
    r.clock(232, 70, 7, '#d98a9a')
    # floor
    r.rug(300, 300, 74, 46, '#e9a7ad', '#f8d7d3')
    r.rug(150, 214, 22, 12, '#f2cdd3', '#fff1f1', round_=False)
    r.rug(452, 202, 34, 16, '#f2cdd3', '#fff1f1', round_=True)
    r.doormat(279, 404, 42, 14, '#d98a8a')
    # bed corner (sleep spot 65,190)
    r.block.append(r.bed(36, 72, 78, 116, blanket='#f2a9b6', pattern='quilt'))
    r.plush(98, 110, 0.9, '#d9a477')
    r.block.append(r.nightstand(118, 74))
    r.slippers(84, 200)
    r.plush(126, 214, 0.8, '#f2c4cf')
    # vanity under the second window side (phone / gift at 350-356,192)
    r.block.append(r.vanity(320, 64, 72, 46))
    r.frame(304, 66, 12, 14, 4)
    r.block.append(r.basket(400, 92, 22, 22))
    # dresser with plant, wardrobe on the right wall (outfit point 442,348 in front)
    r.block.append(r.cabinet(500, 92, 56, 48, '#f3e7dc', drawers=3))
    r.pot(514, 92, 0.6, kind='flower'); r.plush(540, 92, 0.6, '#c9c9d9')
    r.block.append(r.wardrobe(486, 226, 70, 100, '#f3e7dc', '#d9b48a'))
    r.pot(548, 360, 1.0, kind='tall'); r.block.append([536, 330, 24, 32])
    # reading corner left: bookshelf + sofa + floor cushions
    r.block.append(r.bookshelf(30, 236, 98, 74, '#c99a6a', rows=3))
    r.block.append(r.sofa(36, 336, 92, 42, '#eba2ac', ('#fbe3c0', '#bfe3f4')))
    r.pot(144, 410, 0.8, kind='leafy'); r.block.append([132, 392, 24, 20])
    r.cushion(236, 362, 1.0, '#f4b6c2'); r.cushion(262, 370, 0.9, '#c4b2f2')
    # writing desk bottom right (letters / stamp crafting happen at the rug)
    r.block.append(r.desk(420, 368, 96, 40, '#f0dccb', items=('laptop', 'lamp', 'mug'), chair=None))
    r.plush(214, 330, 0.7, '#f2c4cf')
    r.slippers(366, 404, '#c4b2f2')
    # little lived-in clutter
    for i, cc in enumerate(('#c45a5a', '#5a7ac4', '#e0b04a')):
        r.rect(190, 300 - i * 3, 16, 3, cc)
    r.rect(392, 330, 14, 10, '#fbf8f0'); r.rect(396, 334, 14, 10, '#fff6e8')
    r.pot(170, 132, 0.9, kind='flower'); r.block.append([160, 108, 22, 26])
    r.block.append(r.basket(214, 98, 20, 18, '#d9b48a', laundry=False))
    r.pot(224, 98, 0.5, kind='leafy')
    r.block.append(r.floor_lamp(150, 372, '#fbd3dc'))
    r.block.append(r.table(408, 160, 26, 20, '#f0dccb', chairs=0, round_=True, items=('vase',)))
    r.pot(36, 214, 0.7, kind='flower'); r.block.append([28, 196, 18, 18])
    r.wall_shelf(470, 74, 70, ('book', 'plush'))
    r.glow(300, 300, 150, 90, '#ffe9c8', 0.08)


@room
def arland_room(r):
    W, H = 600, 448
    r.shell(W, H, floor='planks', wall='#dfe8ee', wainscot='#7d9cb3', trim='#f4f7f9', pattern='stripe',
            floor_pal=('#9c7a5a', '#a6845f', '#b08e68', '#927050'), door=(276, 52))
    r.window(170, 20, 62, 46, curtain='#9fb9d4')
    r.poster(244, 22, 28, 38, '#f2ead8', '#e0866a'); r.poster(278, 26, 24, 30, '#e8f0f6', '#5a7ac4')
    r.clock(312, 40, 9, '#5a6a7a')
    r.frame(440, 24, 36, 26, 1); r.frame(484, 28, 18, 22, 4)
    r.wall_shelf(40, 52, 90, ('book', 'plant', 'jar'))
    r.hanging_plant(560, 10, 30)
    # floor
    r.rug(300, 292, 82, 48, '#5f7f9c', '#a9c3d8', round_=False)
    r.doormat(281, 404, 42, 14, '#8a6a4a')
    # computer corner (phone / projector / screen / fuse 348-380, 194-225)
    r.block.append(r.desk(326, 70, 116, 44, '#8a6a52', items=('monitor', 'lamp', 'mug', 'books'), chair='#4a5a6c'))
    r.block.append(r.crate(446, 96, 22, 22, '#6a7684'))
    # bed on the right (sleep spot 415,190)
    r.block.append(r.bed(476, 72, 80, 116, blanket='#5a7ac4', sheet='#eef2f6', frame='#7a5a40', pattern='stripes'))
    r.block.append(r.nightstand(446, 140, 26, c='#7a5a40'))
    r.slippers(440, 200, '#5a6a7a')
    # wardrobe + bookshelf left (note at 103,244 stays open in front)
    r.block.append(r.wardrobe(30, 96, 64, 100, '#9c7a5a', '#d9b48a'))
    r.block.append(r.bookshelf(100, 96, 56, 66, '#7a5a40', rows=3, deco=False))
    r.pot(176, 130, 1.0, kind='tall'); r.block.append([164, 100, 24, 32])
    # gaming / guitar corner bottom left, beanbag bottom right
    r.block.append(r.sofa(40, 330, 96, 42, '#6a8aa8', ('#f0d0a0', '#e0866a')))
    r.block.append(r.table(160, 352, 44, 26, '#8a6a52', chairs=0, items=('cup',)))
    r.block.append(r.beanbag(500, 370, '#e0866a'))
    r.block.append(r.cabinet(520, 250, 40, 60, '#6a7684', drawers=3))
    r.pot(544, 250, 0.6, kind='leafy')
    r.basket(456, 300, 20, 18, '#8a9aa8')
    r.cushion(236, 360, 0.9, '#a9c3d8')
    r.block.append(r.guitar(148, 412))
    r.block.append(r.floor_lamp(32, 320, '#f0dcb0'))
    r.block.append(r.tv(196, 96, 70, 40))
    r.rect(410, 330, 18, 6, '#6a7684'); r.rect(412, 326, 4, 14, '#4a5260'); r.rect(422, 326, 4, 14, '#4a5260')
    for i, cc in enumerate(('#5a7ac4', '#e0b04a', '#6aa86a', '#c45a5a')):
        r.rect(470, 410 - i * 3, 18, 3, cc)
    r.glow(380, 100, 80, 40, '#bfe8ff', 0.1)


# ---------------------------------------------------------------------------------------- shops
@room
def dapur(r):
    W, H = 600, 448
    r.shell(W, H, floor='tiles', wall='#eef3ea', wainscot='#9cc7b8', trim='#ffffff', pattern='stripe',
            floor_pal=('#efe6d8', '#d9cbb6'), door=(270, 61), bottom=423)
    r.upper_cabinets(36, 14, 120, 30, '#f6f0e6'); r.upper_cabinets(250, 14, 90, 30, '#f6f0e6')
    r.window(168, 18, 64, 40, curtain='#f2d27a')
    r.pot_rail(450, 30, 110)
    r.clock(372, 34, 8, '#9cc7b8')
    r.wall_shelf(452, 74, 110, ('jar', 'jar', 'plant', 'jar'))
    # counter run along the back wall: sink under the window, stove at 192
    r.block.append(r.counter(30, 92, 140, 50, '#f2ede4', '#8fb8aa', items=('board', 'jars', 'kettle')))
    r.block.append(r.counter(170, 92, 60, 50, '#f2ede4', '#8fb8aa', items=('stove',)))
    r.block.append(r.counter(230, 92, 130, 50, '#f2ede4', '#8fb8aa', items=('sink', 'bread')))
    r.block.append(r.fridge(388, 76, 40, 76))
    r.block.append(r.cabinet(436, 92, 46, 52, '#8fb8aa', drawers=2))
    r.pot(458, 92, 0.6, kind='leafy')
    # island + stools
    r.block.append(r.counter(206, 222, 156, 54, '#f6f1e8', '#c99a6a', items=('board', 'gap', 'bread', 'jars'), doors=True))
    for x in (226, 266, 306, 346):
        r.fill(r.E(x, 292, 8, 5), '#e8b04a'); r.outline(r.E(x, 292, 8, 5), '#9a6a2a'); r.rect(x - 1, 296, 2, 6, '#6b6b78')
    r.block.append([214, 286, 140, 18])
    # pantry shelves on the right wall
    r.block.append(r.bookshelf(520, 160, 56, 96, '#c99a6a', rows=4, deco=False))
    for i in range(4):
        for k in range(4):
            r.rect(526 + k * 12, 178 + i * 21, 9, 10, ['#e0b04a', '#c45a5a', '#e6f1f4', '#a87443'][(i + k) % 4])
    r.block.append(r.basket(530, 270, 34, 20, '#c9a46a', laundry=False))
    r.dots(r.E(547, 272, 13, 4), ['#e06a5a', '#f2a04a', '#7ac06a'], 18, 3)
    # breakfast table
    r.block.append(r.table(104, 320, 88, 40, '#c99a6a', cloth='#f6d3dc', chairs=2, chair_c='#9cc7b8', items=('cup', 'cake', 'vase')))
    r.rug(300, 384, 40, 14, '#e8b04a', '#f6e2a8', round_=False)
    r.pot(40, 410, 0.9, kind='tall'); r.block.append([28, 384, 24, 30])
    r.block.append(r.crate(470, 350, 28, 24, '#c99a6a')); r.block.append(r.crate(500, 370, 28, 24, '#b48a5e'))
    r.dots(r.R(472, 346, 24, 6), ['#7ac06a', '#e06a5a'], 10, 3)
    r.pot(560, 410, 0.8, kind='leafy'); r.block.append([548, 392, 24, 20])
    r.glow(200, 60, 90, 30, '#fff1c8', 0.12)


@room
def toko_bunga(r):
    W, H = 600, 448
    r.shell(W, H, floor='planks', wall='#f3f0e2', wainscot='#a9c99a', trim='#ffffff', pattern='stripe',
            floor_pal=('#c9a37a', '#d2ad84', '#bf986f', '#d8b68e'), door=(273, 60))
    r.window(60, 18, 90, 46, curtain='#f2c4cf')
    r.window(430, 18, 90, 46, curtain='#f2c4cf')
    r.rect(220, 14, 160, 20, '#6a9a5a'); r.rect(224, 17, 152, 14, '#f6f0dc')
    for i, cc in enumerate(('#e06a7a', '#f2a04a', '#e0b04a', '#6aa86a', '#5a7ac4', '#9a6ac4', '#e06a7a')):
        r.fill(r.E(236 + i * 21, 24, 4, 4), cc)
    for x in range(180, 420, 24):      # dried bunches hanging from a rail
        r.rect(x, 40, 1, 10, '#8a6a4a'); r.leaves(x, 56, 5, 7, n=6, pal=('#6a5a3a', '#8a7a4a', '#a89a5a', '#c9b87a', '#e0d09a'))
        r.dots(r.E(x, 56, 5, 7), ['#d98a9a', '#e0c08a'], 4, 2)
    r.rect(176, 38, 248, 2, '#8a6a4a')
    r.hanging_plant(30, 10, 36); r.hanging_plant(570, 10, 36)
    # left wall flower shelf (examine 136,205)
    r.block.append(r.bookshelf(30, 110, 96, 84, '#a87443', rows=3, deco=False))
    for i in range(3):
        for k in range(6):
            r.pot(40 + k * 15, 136 + i * 24, 0.42, kind='flower' if (i + k) % 2 else 'leafy')
    # central arranging table (route point 300,266 just below)
    r.block.append(r.flower_table(170, 196, 128, 42, '#a87443'))
    # sales counter with register (florist point 414,230 in front)
    r.block.append(r.counter(370, 150, 140, 46, '#f3ece2', '#7aa86a', items=('register', 'gap', 'jars'), doors=False))
    r.leaves(486, 150, 10, 8, n=16); r.dots(r.E(486, 148, 9, 6), ['#f2a0b8', '#ffffff'], 10, 2)
    r.rect(392, 196, 96, 2, '#5a7a4a')
    # bucket rows along the bottom-left and right walls
    for i, x in enumerate(range(44, 186, 22)):
        r.block.append(r.bucket(x, 404, [('#f2a0b8', '#ffffff'), ('#f6d36a', '#f2a04a'), ('#c4b2f2', '#ffffff'), ('#e04a5a', '#f2a0b8')][i % 4]))
    for i, y in enumerate(range(240, 320, 24)):
        r.block.append(r.bucket(560, y, [('#e04a5a', '#ffffff'), ('#f6d36a', '#ffffff'), ('#f2a0b8', '#c4b2f2')][i % 3]))
    r.block.append(r.plant_big(520, 300, 'tall', 1.0))
    r.block.append(r.table(500, 380, 50, 30, '#c99a6a', round_=True, chairs=0, items=('vase',)))
    r.pot(40, 230, 1.0, kind='tall'); r.block.append([28, 200, 24, 32])
    r.rug(250, 330, 50, 22, '#a9c99a', '#eef5e6', round_=False)
    r.doormat(280, 404, 46, 14, '#7aa86a')
    # tiered display in the middle-right and pot clusters on the left
    r.block.append(r.flower_table(330, 316, 84, 34, '#c99a6a'))
    for i, (x, y) in enumerate(((44, 300), (64, 312), (86, 300), (108, 314), (52, 336), (96, 338))):
        r.pot(x, y, 0.7, kind=('flower', 'leafy', 'flower', 'tall', 'flower', 'leafy')[i])
    r.block.append([30, 278, 96, 64])
    for x in (200, 250, 300, 350, 400):
        r.hanging_plant(x, 64, 24)
    r.glow(300, 120, 200, 60, '#fff6d8', 0.08)


@room
def arcade(r):
    W, H = 600, 448
    r.shell(W, H, floor='checker', wall='#3a2c5c', wainscot='#2a2046', trim='#f26a9a', pattern='stars',
            floor_pal=('#2f2a48', '#3a3460'), door=(272, 55), bottom=426)
    r.neon(200, 18, 96, 18, '#f26a9a'); r.neon(310, 22, 70, 14, '#5ad8f0')
    r.rect(206, 24, 84, 6, '#ffd0e0', 0.5)
    r.string_lights(30, 190, 14, sag=8, n=12, colors=('#f26a9a', '#5ad8f0', '#f6d36a'))
    r.string_lights(400, 570, 14, sag=8, n=12, colors=('#f26a9a', '#5ad8f0', '#f6d36a'))
    r.poster(440, 24, 30, 40, '#2a2046', '#f26a9a'); r.poster(480, 24, 30, 40, '#2a2046', '#5ad8f0')
    # row of cabinets on the back wall (examine 154,123)
    for i, x in enumerate((40, 80, 120, 160)):
        r.block.append(r.arcade_cab(x, 62, 36, 64, ['#4b3a8c', '#8c3a5a', '#2a6a8c', '#3a8c5a'][i], ['#5ad8f0', '#f6d36a', '#f26a9a', '#9af06a'][i]))
    for i, x in enumerate((330, 370, 410)):
        r.block.append(r.arcade_cab(x, 62, 36, 64, ['#8c3a5a', '#4b3a8c', '#3a8c5a'][i], ['#9af06a', '#5ad8f0', '#f6d36a'][i]))
    # claw machine (booth / claw 261,196)
    r.block.append(r.claw(228, 92, 56, 92, '#f26a9a'))
    # photo booth on the left wall (photo panel 171,200; tickets 112,227)
    r.block.append(r.box(30, 140, 56, 10, 74, '#7a5ac4', '#5a3a9c'))
    r.rect(36, 156, 44, 40, '#f6d36a'); r.rect(40, 160, 36, 32, '#fff2b0')
    r.rect(36, 200, 44, 8, '#f26a9a')
    r.block.append(r.box(94, 168, 30, 8, 30, '#e8e0f0', '#9a8ab8'))
    r.rect(100, 182, 18, 6, '#f26a9a')
    # prize counter (right)
    r.block.append(r.counter(456, 150, 110, 46, '#f6e8f0', '#5a3a9c', items=('register', 'gap'), doors=False))
    for i in range(6):
        r.plush(466 + i * 16, 150, 0.6, ['#d9a477', '#f2c4cf', '#bfe3ff', '#f6d36a', '#c9e8a8', '#c4b2f2'][i])
    r.block.append(r.bookshelf(500, 220, 66, 70, '#5a3a9c', rows=3, deco=False))
    # air hockey table centre
    r.block.append(r.box(300, 222, 116, 50, 16, '#e8f4fb', '#4b3a8c'))
    r.rect(356, 224, 2, 46, '#f26a9a', 0.7); r.outline(r.E(357, 247, 10, 10), '#f26a9a')
    r.fill(r.E(320, 247, 5, 4), '#e04a4a'); r.fill(r.E(396, 247, 5, 4), '#4ae0a0')
    # rhythm game + benches near the door
    r.block.append(r.box(40, 360, 80, 12, 48, '#2a2046', '#4b3a8c'))
    for k in range(4):
        r.rect(46 + k * 18, 362, 14, 8, ['#f26a9a', '#5ad8f0', '#f6d36a', '#9af06a'][k])
    r.block.append(r.box(470, 380, 90, 12, 18, '#f26a9a', '#a8405e'))
    r.block.append(r.box(140, 392, 60, 10, 14, '#5ad8f0', '#2a6a8c'))
    r.rug(300, 330, 54, 24, '#5ad8f0', '#2a2046', round_=False)
    r.doormat(278, 408, 44, 14, '#f26a9a')
    r.glow(300, 80, 220, 50, '#f26a9a', 0.08)
    r.glow(261, 140, 50, 50, '#ffd0e0', 0.1)


# ---------------------------------------------------------------------------------------- cafe wing
@room
def cafe(r):
    W, H = 960, 640
    r.shell(W, H, floor='planks', wall='#f4e6d2', wainscot='#a8744c', trim='#fff4e4', pattern='panel',
            floor_pal=('#a87a52', '#b3845a', '#bd8e62', '#9e714b'), door=None, wall_h=228, side=14, bottom=628)
    # back wall: two doors, windows, menu boards, cup shelves, pendants, fairy lights
    r.wall_door(370, 226, 60, 86, '#8a5a3a', sign='#e8b04a')
    r.wall_door(830, 226, 60, 86, '#8a5a3a', glass=False, sign='#9cc7b8')
    r.window(60, 60, 110, 76, curtain='#e8b04a'); r.window(480, 60, 96, 76, curtain='#e8b04a')
    r.chalkboard(200, 56, 120, 70, 5); r.chalkboard(640, 60, 90, 56, 4)
    r.frame(270, 136, 40, 30, 1); r.clock(520, 168, 10, '#8a5a3a'); r.poster(752, 98, 36, 50, '#fbe9d4', '#e06a7a')
    r.wall_shelf(200, 160, 120, ('jar', 'jar', 'plant', 'jar', 'jar')); r.wall_shelf(620, 150, 150, ('book', 'plant', 'jar', 'book'))
    r.string_lights(20, 940, 22, sag=18, n=36)
    for x in (120, 300, 560, 760):
        r.pendant(x, 10, 26)
    r.hanging_plant(30, 10, 60); r.hanging_plant(930, 10, 60)
    # service counter (left) and cake display (examine 380,340)
    r.block.append(r.counter(122, 292, 170, 48, '#e9dccb', '#7a4a32', items=('machine', 'register', 'cup' if False else 'jars', 'bread'), doors=True))
    r.block.append(r.box(338, 292, 74, 18, 28, '#dff0f6', '#7a4a32'))
    for k in range(5):
        r.fill(r.E(348 + k * 13, 300, 5, 3.5), ['#f2a0b8', '#fbe3c0', '#c98b4a', '#f6d36a', '#e06a7a'][k])
    r.rect(340, 294, 70, 2, '#ffffff', 0.6)
    r.block.append(r.cabinet(40, 240, 60, 52, '#7a4a32', drawers=2)); r.pot(60, 240, 0.6, kind='flower')
    # bookshelf corner (examine 700,324)
    r.block.append(r.bookshelf(650, 246, 104, 56, '#8a5a3a', rows=2))
    # symbol puzzle table on a round rug
    r.rug(480, 486, 96, 52, '#c9793a', '#f2d5a8')
    r.block.append(r.table(452, 448, 56, 34, '#7a4a32', cloth='#e8d4a8', round_=True, chairs=0))
    for k, cc in enumerate(('#e06a7a', '#5a7ac4', '#e0b04a', '#6aa86a')):
        r.fill(r.E(466 + k * 9, 460, 3, 2.5), cc)
    # guest tables
    for x, y, cl in ((136, 544, '#f6d3dc'), (776, 544, '#dfe8f4'), (756, 404, '#f6e2a8'), (596, 584, '#e8f0dc'), (276, 584, '#f6d3dc')):
        r.block.append(r.table(x, y, 48, 32, '#8a5a3a', cloth=cl, round_=True, chairs=2, chair_c='#a87443', items=('cup', 'cake')))
    # sofa nook with coffee table (right)
    r.block.append(r.sofa(822, 436, 100, 44, '#9cc7b8', ('#f6d3dc', '#f6e2a8')))
    r.rug(870, 520, 50, 18, '#9cc7b8', '#eef5f0', round_=False)
    # gallery entrance on the left (door 80..150, 430..500)
    r.portal_door(84, 432, 62, 60, '#f2d5a8')
    r.rect(92, 420, 46, 10, '#7a4a32'); r.rect(96, 422, 38, 6, '#f6e2a8')
    # plants and a bench
    for x, y in ((40, 330), (920, 330), (40, 616), (920, 616)):
        r.block.append(r.plant_big(x, y, 'tall' if x < 500 else 'leafy', 1.0))
    r.block.append(r.bench(560, 360, 70, '#a87443')); r.pot(600, 360, 0.7, kind='flower')
    r.glow(480, 420, 300, 140, '#ffe6b8', 0.07)


@room
def galeri_komunitas(r):
    W, H = 960, 640
    r.shell(W, H, floor='planks', wall='#f2eee8', wainscot='#c9c2d6', trim='#ffffff', pattern='panel',
            floor_pal=('#d8c4a4', '#cfb998', '#e0ccae', '#c7b08e'), door=(375, 210), wall_h=84, side=80, bottom=614)
    for x, w, art in ((100, 60, 0), (180, 44, 3), (240, 70, 1), (590, 70, 2), (680, 44, 4), (740, 60, 0), (820, 40, 3)):
        r.frame(x, 20, w, 40, art, '#b08a5a')
        r.glow(x + w / 2, 30, w, 30, '#fff4d8', 0.15)
    r.rect(330, 16, 250, 26, '#f6e2c8'); r.rect(336, 20, 238, 18, '#e8b04a')
    for i in range(10):
        r.rect(346 + i * 23, 26, 14, 6, '#fff4e4')
    r.string_lights(84, 876, 70, sag=10, n=30, colors=('#fff1c8', '#ffe0a8'))
    for x in (140, 360, 600, 820):
        r.pot(x, 200, 0.7, kind='flower'); r.block.append([x - 8, 182, 16, 18])
    # plinths and display benches (old blocking spots kept)
    r.block.append(r.plinth(160, 112, 40, 54, art='vase', tint='#f2a0b8'))
    r.block.append(r.plinth(228, 112, 40, 54, art='bust'))
    r.block.append(r.box(403, 104, 150, 14, 24, '#f6f0e6', '#c9c2d6'))
    for k in range(4):
        r.frame(412 + k * 36, 80, 28, 22, k + 1, '#8a6a4a')
    r.block.append(r.plinth(676, 112, 40, 54, art='orb', tint='#9fd3f0'))
    r.block.append(r.plinth(752, 112, 40, 54, art='vase', tint='#e8b04a'))
    # easels along the side walls (sketch points stay in front)
    for i, (x, y) in enumerate(((96, 210), (96, 330), (96, 450), (820, 220), (820, 340))):
        r.block.append(r.easel(x, y, 40, 56, i))
    # centre: bench and big rug
    r.rug(480, 420, 150, 70, '#c9c2d6', '#f2eef8', round_=False)
    r.block.append(r.bench(560, 560, 70, '#a87443'))
    r.block.append(r.bench(330, 560, 70, '#a87443'))
    # the sealed door to Ruang Dua Surat
    r.portal_door(776, 458, 68, 60, '#c4b2f2', sealed=True)
    for x, y in ((100, 600), (860, 600)):
        r.block.append(r.plant_big(x, y, 'tall', 1.0))
    r.glow(480, 300, 300, 160, '#fff4e0', 0.06)


# ---------------------------------------------------------------------------------------- library wing
@room
def perpustakaan(r):
    W, H = 1200, 896
    r.shell(W, H, floor='planks', wall='#efe4cf', wainscot='#4f6a52', trim='#f6ecd8', pattern='stripe',
            floor_pal=('#8a5e3e', '#946645', '#9e6f4c', '#80573a'), door=(555, 95), wall_h=195, side=38, bottom=845)
    # built-in shelves and tall windows on the back wall
    for x in (50, 230, 690, 870):
        r.bookshelf(x, 22, 150, 138, '#6e4a30', rows=5, deco=False)
    for x in (410, 560):
        r.window(x + 8, 30, 70, 110, curtain='#7a9a6a')
    r.clock(586, 156, 12, '#6e4a30')
    r.bookshelf(1050, 22, 100, 138, '#6e4a30', rows=5, deco=False)
    for x in (200, 520, 840):
        r.pendant(x + 20, 4, 40, '#e8c46a')
    # long carpet runner from the door to the reading hall
    r.rug(602, 700, 50, 140, '#7a3a4a', '#a85060', round_=False)
    # reading corner (globe 161,290 and sofa 154,365)
    r.block.append(r.bookshelf(60, 206, 140, 50, '#6e4a30', rows=2))
    r.block.append(r.globe(196, 306))
    r.block.append(r.sofa(56, 330, 96, 44, '#7a3a4a', ('#e8c46a', '#f2d5a8')))
    r.block.append(r.floor_lamp(46, 420, '#f2d5a8'))
    r.rug(110, 420, 60, 26, '#4f6a52', '#a8c09a', round_=False)
    # freestanding shelf rows
    r.block.append(r.bookshelf(400, 418, 160, 54, '#6e4a30', rows=2))
    r.block.append(r.bookshelf(110, 520, 150, 54, '#6e4a30', rows=2))
    r.block.append(r.bookshelf(860, 474, 180, 56, '#6e4a30', rows=2))
    r.block.append(r.bookshelf(860, 640, 180, 56, '#6e4a30', rows=2))
    # reading tables with lamps
    r.block.append(r.table(650, 440, 160, 50, '#6e4a30', chairs=2, chair_c='#7a3a4a'))
    for x in (680, 760):
        r.rect(x, 446, 2, 12, '#7a6a5a'); r.fill(r.E(x + 1, 446, 6, 3.5), '#4f6a52'); r.glow(x, 460, 30, 18, '#ffe6a8', 0.15)
    r.rect(712, 452, 22, 14, '#fbf8f0'); r.rect(716, 454, 20, 12, '#f6ecd8')
    r.block.append(r.table(100, 640, 110, 44, '#6e4a30', chairs=2, chair_c='#4f6a52', items=('cup', 'vase')))
    # librarian's desk by the entrance
    r.block.append(r.counter(370, 742, 130, 46, '#e9dccb', '#6e4a30', items=('books' if False else 'jars', 'register'), doors=False))
    r.block.append(r.cabinet(240, 760, 50, 50, '#6e4a30', drawers=3))
    # the old shelf that hides the archive (opens with LIB_SECRET_OPEN)
    r.block.append(r.bookshelf(1066, 240, 74, 92, '#5a3a24', rows=4, deco=False))
    r.rect(1066, 332, 74, 3, '#e8c46a', 0.6)
    # plants, lamps, notice board
    for x, y in ((60, 830), (1140, 830), (1140, 220), (700, 260)):
        r.block.append(r.plant_big(x, y, 'tall', 1.0))
    r.block.append(r.floor_lamp(840, 410, '#f2d5a8'))
    r.block.append(r.bench(700, 760, 90, '#6e4a30'))
    r.poster(300, 210, 40, 0 + 30, '#f6ecd8', '#4f6a52')
    r.glow(600, 300, 360, 160, '#fff1c8', 0.06)


@room
def ruang_arsip(r):
    W, H = 600, 448
    r.shell(W, H, floor='stone', wall='#4a4a66', wainscot='#33334a', trim='#8a86a8', pattern='brick',
            floor_pal=('#5a5a6c', '#4e4e60'), door=(271, 57), bottom=425,
            brick_pal=('#4a4a62', '#52526c', '#5a5a74', '#444458'))
    r.rect(24, 10, 552, 56, '#000000', 0.35)
    for x in (60, 200, 340, 480):
        r.glow(x + 30, 40, 40, 26, '#9ff0e0', 0.12)
    r.block.append(r.jar_shelf(96, 94, 110, 74, '#9ff0e0'))
    r.block.append(r.jar_shelf(236, 92, 128, 58, '#f6d36a'))
    r.block.append(r.jar_shelf(386, 94, 110, 74, '#c4b2f2'))
    # investigation desk with papers and a lamp (points 300-310, 283-352 stay in front)
    r.block.append(r.desk(250, 222, 100, 44, '#5a4a3a', items=('papers', 'lamp', 'books'), chair=None))
    r.rect(262, 214, 30, 1, '#e04a4a'); r.rect(290, 208, 1, 14, '#e04a4a')
    r.block.append(r.cabinet(500, 196, 56, 70, '#5a5a6c', drawers=4))
    r.block.append(r.cabinet(500, 290, 56, 56, '#5a5a6c', drawers=3))
    r.block.append(r.bench(40, 370, 90, '#5a5a6c'))
    r.block.append(r.plinth(36, 240, 40, 56, art='crystal', tint='#9ff0e0'))
    r.block.append(r.plinth(470, 350, 40, 56, art='crystal', tint='#c4b2f2'))
    for x, y in ((150, 300), (420, 330), (180, 410), (520, 140)):
        r.fill(r.E(x, y, 4, 3), '#9ff0e0'); r.rect(x - 1, y + 2, 2, 4, '#e6f1f4'); r.glow(x, y, 16, 12, '#9ff0e0', 0.25)
    r.rug(300, 340, 70, 30, '#3a3a5a', '#5a5a80', round_=False)
    r.glow(300, 240, 120, 60, '#ffe6a8', 0.1)


@room
def ruang_dua_surat(r):
    W, H = 960, 640
    r.shell(W, H, floor='planks', wall='#2a3058', wainscot='#1e2244', trim='#c4b2f2', pattern='stars',
            floor_pal=('#5a4a6a', '#644f74', '#6e587e', '#544364'), door=(430, 100), wall_h=64, side=55, bottom=616)
    r.window(150, 10, 90, 40, lit=True, curtain='#8a7ac4'); r.window(720, 10, 90, 40, lit=True, curtain='#8a7ac4')
    r.string_lights(60, 900, 54, sag=14, n=30, colors=('#fff1c8', '#c4b2f2'))
    # two writing desks, one for each letter
    for x, c in ((256, '#f2a0b8'), (606, '#9fd3f0')):
        r.block.append(r.desk(x, 290, 92, 44, '#5a4a3a', items=('papers', 'lamp'), chair=None))
        r.rect(x + 50, 296, 14, 10, '#fbf4e6'); r.rect(x + 52, 298, 10, 2, c)
        r.glow(x + 46, 300, 70, 40, c, 0.12)
    # memory pedestal in the middle
    r.block.append(r.plinth(460, 226, 40, 56, art='orb', tint='#f6e7a8'))
    r.rug(480, 470, 120, 60, '#4a3a6a', '#7a68a8', round_=True)
    # shelves of letters along the side walls
    for y in (120, 300, 470):
        r.block.append(r.bookshelf(64, y, 70, 90, '#3a2c44', rows=3, deco=False))
        r.block.append(r.bookshelf(826, y, 70, 90, '#3a2c44', rows=3, deco=False))
    for x in (200, 760):
        r.block.append(r.plinth(x - 20, 120, 40, 50, art='crystal', tint='#c4b2f2'))
    for x, y in ((160, 600), (800, 600)):
        r.block.append(r.plant_big(x, y, 'leafy', 0.9))
    r.glow(480, 300, 320, 200, '#c4b2f2', 0.06)


@room
def rumah_sari(r):
    """Nenek Sari's house (story v7): jasmine, tea, an old radio, the empty frame and Wira's umbrella."""
    W, H = 600, 448
    r.shell(W, H, floor='planks', wall='#f2e4c8', wainscot='#a8784e', trim='#fbf1dc', pattern='stripe',
            floor_pal=('#9a6a46', '#a3724c', '#ad7c54', '#94643f'), door=(274, 52))
    r.window(96, 20, 64, 46, curtain='#e8d4a8')
    r.window(250, 20, 64, 46, curtain='#e8d4a8')
    r.clock(352, 46, 9, '#7a5234')
    r.frame(372, 26, 18, 22, 2); r.frame(560, 30, 16, 20, 0)
    r.hanging_plant(40, 10, 30)
    # the shelf of family photos with the one empty frame (quest point 470,160)
    r.block.append(r.bookshelf(410, 98, 120, 48, '#7a5234', rows=2, deco=False))
    for i, x in enumerate((418, 438, 458, 500, 516)):
        r.rect(x, 100, 14, 12, '#d9b48a'); r.rect(x + 2, 102, 10, 8, ('#9fc4e0', '#e8c0a8', '#b8d8a8', '#e0b8c8', '#c8c0e8')[i])
    r.rect(474, 96, 20, 18, '#8c5a34'); r.rect(477, 99, 14, 12, '#f4ecdc')      # the empty frame
    r.rect(478, 100, 3, 1, '#ffffff')
    # Sari's armchair and tea table (Sari stands at 430,236)
    r.rug(214, 254, 52, 26, '#c89a6a', '#f0dcc0', round_=False)
    r.block.append(r.sofa(320, 170, 84, 40, '#b8746a', ('#f4e2c0', '#d8c8e8')))
    r.block.append(r.table(186, 232, 58, 38, '#8c5a34', cloth='#f6efe0', round_=True, chairs=2, chair_c='#7a5234', items=('vase',)))
    r.rect(204, 238, 8, 6, '#ffffff'); r.rect(224, 240, 8, 6, '#ffffff')    # tea cups
    # jasmine by the window
    r.pot(210, 140, 1.0, kind='flower'); r.block.append([196, 116, 28, 26])
    r.pot(140, 140, 0.8, kind='leafy'); r.block.append([128, 120, 24, 22])
    # old radio on a cabinet (examine 520,300)
    r.block.append(r.cabinet(492, 236, 64, 46, '#7a5234', drawers=2))
    r.rect(500, 226, 48, 14, '#5a3a24'); r.rect(504, 229, 26, 8, '#d9b48a'); r.rect(534, 229, 10, 8, '#2a1a12')
    # Wira's umbrella leaning in the corner (quest point 140,320): hooked handle, folded canopy, tip
    for a in range(0, 180, 12):
        r.rect(int(66 + 5 * math.cos(math.radians(a))), int(262 - 5 * math.sin(math.radians(a))), 2, 2, '#3a2a1e')
    r.rect(70, 262, 2, 10, '#3a2a1e')
    for i in range(44):
        w = max(1, int(8 * math.sin(math.pi * min(1.0, i / 40.0)) ** 0.7))
        r.rect(70 - w // 2, 272 + i, w + 1, 1, '#24202a' if i % 9 else '#3a3444')
    r.rect(70, 316, 1, 4, '#9a9aa8')
    r.rect(68, 274, 5, 3, '#e8e0c8')                                         # jasmine ribbon on the handle
    r.block.append([52, 258, 34, 62])
    # Mochi the orange cat asleep on a cushion by the armchair
    r.cushion(292, 214, 1.1, '#d8c8e8')
    r.fill(r.E(292, 210, 9, 6), '#e8954a'); r.fill(r.E(299, 206, 4, 4), '#e8954a')
    r.rect(296, 202, 2, 2, '#e8954a'); r.rect(301, 202, 2, 2, '#e8954a'); r.rect(284, 212, 6, 2, '#c87a36')
    # tea sideboard on the right wall, more photos
    r.block.append(r.cabinet(540, 120, 40, 60, '#8c5a34', drawers=3))
    r.rect(544, 112, 10, 8, '#ffffff'); r.rect(558, 114, 8, 6, '#f4ecdc'); r.rect(568, 112, 6, 8, '#e8c0a8')
    r.frame(400, 30, 16, 20, 1)
    # cosy clutter
    r.rug(300, 320, 90, 44, '#b8746a', '#e8c8a0')
    r.doormat(279, 404, 42, 14, '#8c5a34')
    r.block.append(r.floor_lamp(560, 380, '#f4dcb0'))
    r.block.append(r.basket(36, 380, 24, 20, '#c9a46a', laundry=False))
    r.pot(116, 410, 0.7, kind='leafy'); r.block.append([104, 392, 24, 20])
    r.glow(300, 300, 170, 100, '#ffe2b0', 0.1)
    r.glow(210, 150, 40, 30, '#fff4d8', 0.12)


# ======================================================================================== v2 density
# Extra layers on top of each room (2026-11-25 "ramaikan interior"). PRE runs right after shell()
# (floor rugs and light pools under the furniture), EXTRA after the room script (more furniture,
# wall decor, clutter). Every blocking piece sits in floor space the overlay
# (rooms_hd.py <area> --preview DIR --overlay) shows free of quest/examine/door points.
PRE, EXTRA = {}, {}


def pre(fn):
    PRE[fn.__name__[4:]] = fn
    return fn


def extra(fn):
    EXTRA[fn.__name__[4:]] = fn
    return fn


@pre
def pre_cafe(r):
    for x, y in ((136, 544), (276, 584), (596, 584), (776, 544), (756, 404)):
        r.rug(x + 24, y + 18, 44, 24, '#c98a5a', '#ecd2ac')
    r.rug(400, 252, 34, 12, '#a8744c', '#e8b04a', round_=False)
    r.rug(205, 412, 40, 24, '#9cc7b8', '#eef5f0')
    for x in (120, 300, 560, 760):
        r.glow(x, 400, 110, 60, '#ffe6b8', 0.07)


@extra
def ext_cafe(r):
    # wall: sconces, mugs, plates, notice board, calendar, hooks, little frames, more greenery
    for x in (350, 452, 806, 914):
        r.sconce(x, 146)
    r.mug_shelf(60, 176, 5); r.plates(120, 160, 3)
    r.corkboard(650, 166, 46, 32, 6); r.calendar(706, 172, '#e8b04a')
    r.hooks(896, 160, ('#e06a7a', '#9cc7b8'))
    r.frame(590, 176, 20, 24, 3); r.frame(614, 182, 14, 18, 1)
    r.frame(180, 176, 14, 18, 4)
    r.baseboard_bits(206, (176, 604, 724))
    r.hanging_plant(180, 10, 40); r.hanging_plant(460, 10, 34); r.hanging_plant(700, 10, 40)
    # floor: pastry case + coffee sacks by the counter side, coat rack by the kitchen door
    r.block.append(r.display_case(466, 244, 60, 34, '#7a4a32', ('#f2a0b8', '#c98b4a', '#f6d36a', '#e06a7a')))
    r.block.append(r.sack(560, 292, '#d8c49a', '#7a4a32', '#5a3a24'))
    r.block.append(r.sack(584, 296, '#cdb88a', '#7a4a32', '#5a3a24'))
    r.block.append(r.sign_stand(612, 300))
    r.block.append(r.coat_rack(790, 296, ('#5a7ac4', '#e0b04a')))
    r.block.append(r.umbrella_stand(814, 300))
    # reading armchair by the gallery door, another by the sofa nook
    r.block.append(r.armchair(32, 348, '#c98a5a', cushion='#f6e2a8'))
    r.block.append(r.side_table(70, 360, 22, item='lamp'))
    r.block.append(r.armchair(880, 350, '#9cc7b8', cushion='#f6d3dc'))
    r.block.append(r.floor_lamp(936, 424, '#f6e2a8'))
    # extra two-seat table on the left, plants and a bin to break up the bottom floor
    r.block.append(r.table(196, 396, 48, 32, '#8a5a3a', cloth='#e8f0dc', round_=True, chairs=2, chair_c='#a87443', items=('cup', 'vase')))
    r.block.append(r.plant_big(520, 626, 'leafy', 0.9))
    r.block.append(r.bin(704, 624))
    r.book_stack(706, 296, 3)
    r.block.append(r.stool(470, 300, '#e8b04a'))
    r.block.append(r.bookshelf(28, 516, 40, 62, '#8a5a3a', rows=3, deco=False))
    r.block.append(r.plant_big(744, 626, 'tall', 0.9))
    r.block.append(r.plant_big(362, 626, 'leafy', 0.8))
    r.wear(160, (20, 232, 940, 626))


@pre
def pre_galeri_komunitas(r):
    r.rug(480, 560, 46, 50, '#a8304a', '#c9586a', round_=False)
    for x in (140, 270, 690, 820):
        r.glow(x, 150, 70, 40, '#fff4d8', 0.08)
    r.rug(522, 440, 46, 26, '#e8e0f0', '#ffffff')


@extra
def ext_galeri_komunitas(r):
    # free-standing walls with more framed pieces, a glass case on the big rug, extra plinths
    r.block.append(r.partition(250, 214, 90, arts=(1, 3)))
    r.block.append(r.partition(610, 214, 90, arts=(4, 2)))
    r.block.append(r.display_case(494, 412, 56, 30, '#8a6a9a', ('#9fd3f0', '#f6d36a', '#f2a0b8')))
    r.block.append(r.plinth(170, 318, 36, 50, art='orb', tint='#f2a0b8'))
    r.block.append(r.plinth(170, 410, 36, 50, art='bust'))
    r.block.append(r.plinth(730, 270, 36, 50, art='crystal', tint='#c4b2f2'))
    # velvet ropes in front of the back-wall plinths
    r.block.append(r.stanchions(150, 270, 184))
    r.block.append(r.stanchions(670, 800, 184))
    # welcome desk with brochures by the entrance, sign, bin and plants
    r.block.append(r.counter(150, 540, 110, 40, '#f6f0e6', '#8a6a9a', items=('register', 'gap', 'jars'), doors=False))
    r.papers(196, 544, 4, 20, 6)
    r.block.append(r.sign_stand(300, 590, '#f6f0e6', '#8a6a9a'))
    r.block.append(r.bin(130, 600))
    r.block.append(r.plant_big(860, 470, 'leafy', 0.9))
    r.block.append(r.plant_big(440, 200, 'tall', 0.8)); r.block.append(r.plant_big(520, 200, 'tall', 0.8))
    for x, y in ((100, 316), (100, 436), (840, 314), (840, 434)):
        r.block.append(r.plant_big(x, y, 'leafy', 0.75))
    r.block.append(r.bench(360, 506, 60, '#8a6a9a'))
    for x, w in ((100, 60), (240, 70), (590, 70), (740, 60)):
        r.sconce(x + w / 2, 4, '#fff1c8', '#b08a5a')
    r.wear(120, (82, 90, 878, 610))


@pre
def pre_perpustakaan(r):
    r.rug(505, 258, 104, 40, '#4f6a52', '#a8c09a', round_=False)
    r.rug(950, 586, 86, 26, '#7a3a4a', '#d9b48a', round_=False)
    r.rug(980, 790, 80, 34, '#7a3a4a', '#f2d5a8')
    r.rug(370, 620, 100, 40, '#4f6a52', '#d8c8a0')
    r.rug(760, 330, 100, 40, '#7a3a4a', '#e8c89a')
    for x in (215, 395, 676, 855, 1035):
        r.glow(x, 260, 90, 50, '#fff1c8', 0.06)


@extra
def ext_perpustakaan(r):
    for x in (215, 395, 676, 855, 1035):
        r.sconce(x, 96, '#ffe6a8', '#6e4a30')
    r.ladder(362, 34, 158); r.ladder(1010, 34, 158)
    # second reading table under the windows and a new shelf row on the right
    r.block.append(r.table(430, 236, 150, 44, '#6e4a30', chairs=2, chair_c='#4f6a52'))
    for x in (460, 548):
        r.rect(x, 242, 2, 12, '#7a6a5a'); r.fill(r.E(x + 1, 242, 6, 3.5), '#4f6a52'); r.glow(x, 256, 30, 18, '#ffe6a8', 0.15)
    r.rect(492, 246, 14, 10, '#fbf8f0'); r.book_stack(516, 256, 3)
    r.block.append(r.bookshelf(760, 236, 200, 54, '#6e4a30', rows=2))
    # reading table between the right shelf rows, study table bottom-left, card catalogues
    r.block.append(r.table(884, 566, 130, 40, '#6e4a30', chairs=0, items=('cup', 'vase')))
    r.block.append(r.table(300, 596, 140, 44, '#6e4a30', chairs=2, chair_c='#7a3a4a', items=('cup',)))
    r.rect(352, 604, 22, 14, '#fbf8f0'); r.rect(356, 606, 20, 12, '#f6ecd8')
    r.block.append(r.card_catalog(700, 620, 60, 44))
    r.block.append(r.card_catalog(90, 740, 56, 44))
    r.block.append(r.bookshelf(1070, 640, 80, 90, '#6e4a30', rows=3, deco=False))
    # cosy armchairs bottom-right, a lamp table near the sofa, book carts and piles
    r.block.append(r.armchair(930, 770, '#7a3a4a', cushion='#e8c46a'))
    r.block.append(r.side_table(966, 782, 22, item='books'))
    r.block.append(r.armchair(992, 770, '#4f6a52', cushion='#f2d5a8'))
    r.block.append(r.floor_lamp(1050, 810, '#f2d5a8'))
    r.block.append(r.side_table(214, 322, 24, item='lamp'))
    r.block.append(r.book_stack(470, 548, 5)); r.block.append(r.book_stack(490, 552, 3))
    r.block.append(r.crate(500, 520, 30, 26, '#8a5e3e'))
    r.book_stack(1000, 606, 2)
    r.block.append(r.plant_big(600, 236, 'leafy', 0.9))
    r.block.append(r.sign_stand(500, 790, '#3a4a3a', '#6e4a30'))
    r.block.append(r.bookshelf(880, 320, 150, 44, '#6e4a30', rows=2))
    r.block.append(r.bookshelf(42, 460, 40, 70, '#6e4a30', rows=3, deco=False))
    r.wear(260, (40, 200, 1160, 842))


@pre
def pre_ruang_dua_surat(r):
    r.rug(302, 316, 68, 36, '#3a2c5a', '#6a58a0', round_=False)
    r.rug(652, 316, 68, 36, '#3a2c5a', '#6a58a0', round_=False)
    for x, y in ((200, 260), (760, 260), (480, 560)):
        r.glow(x, y, 90, 60, '#c4b2f2', 0.06)


@extra
def ext_ruang_dua_surat(r):
    # paper-star garland, sconces and little frames on the night wall
    for i in range(18):
        x = 260 + i * 25; y = 30 + 8 * math.sin(i * 0.9)
        r.rect(x, 10, 0.6, y - 10, '#8a7ac4')
        m = r.E(x, y + 2, 3, 3); r.fill(m, ['#f6e7a8', '#f2a0b8', '#9fd3f0'][i % 3]); r.glow(x, y + 2, 7, 6, '#f6e7a8', 0.3)
    for x in (110, 280, 680, 850):
        r.sconce(x, 22, '#f6e7a8', '#8a7ac4')
    # telescope by the left window, memory chests, an armchair corner each side
    r.rect(290, 128, 2, 32, '#6a5a7a'); r.rect(282, 150, 2, 14, '#6a5a7a'); r.rect(298, 150, 2, 14, '#6a5a7a')
    m = r.R(270, 124, 34, 8); r.fill(m, '#c9a24a'); r.outline(m, '#6a4a2a'); r.rect(266, 125, 5, 6, '#e8d8a8')
    r.block.append([272, 124, 32, 42])
    r.block.append(r.chest(398, 150, 40, '#5a3a5a')); r.block.append(r.chest(522, 150, 40, '#3a4a6a'))
    r.papers(440, 176, 5, 40, 10)
    r.block.append(r.sofa(150, 236, 90, 40, '#4a3a6a', ('#f2a0b8', '#9fd3f0')))
    r.block.append(r.armchair(700, 236, '#4a3a6a', cushion='#f6e7a8'))
    r.block.append(r.side_table(742, 248, 22, item='books'))
    # drawers full of letters on both sides, candle tables, cushions round the rug
    r.block.append(r.card_catalog(150, 420, 56, 44, '#3a2c44'))
    r.block.append(r.card_catalog(754, 420, 56, 44, '#3a2c44'))
    for x in (220, 720):
        r.block.append(r.side_table(x, 560, 24, item='tea'))
        r.candle(x + 12, 562, 0.8)
    for x, y in ((380, 520), (580, 520)):
        r.pillow_pile(x, y, ('#f2a0b8', '#c4b2f2', '#9fd3f0'))
    for x, y in ((400, 470), (560, 470), (430, 560), (530, 560), (380, 420), (580, 420)):
        r.candle(x, y, 0.7)
    r.block.append(r.plant_big(860, 250, 'tall', 0.9)); r.block.append(r.plant_big(100, 250, 'tall', 0.9))
    r.block.append(r.book_stack(620, 400, 4))
    r.block.append(r.bookshelf(250, 420, 110, 44, '#3a2c44', rows=2))
    r.block.append(r.bookshelf(600, 420, 110, 44, '#3a2c44', rows=2))
    r.block.append(r.floor_lamp(340, 196, '#f6e7a8')); r.block.append(r.floor_lamp(620, 196, '#f6e7a8'))
    r.block.append(r.plant_big(160, 616, 'tall', 0.8)); r.block.append(r.plant_big(800, 616, 'tall', 0.8))
    for i in range(14):       # letters dropped on the floor
        r.papers(r.rng.uniform(120, 820), r.rng.uniform(380, 600), 1, 4, 4)
    r.wear(140, (58, 70, 902, 612), c='#1a1428')


@extra
def ext_arcade(r):
    r.block.append(r.vending(470, 70, 36, 62, '#e04a5a'))
    r.block.append(r.pinball(516, 80, 30, 56, '#9af06a'))
    r.block.append(r.pinball(442, 240, 28, 56, '#f26a9a'))
    r.block.append(r.vending(520, 300, 36, 56, '#5a3a9c', '#f6d36a'))
    r.block.append(r.bin(452, 376, '#5a5a7a'))
    for i in range(40):       # spilled tickets and confetti
        x = r.rng.uniform(40, 560); y = r.rng.uniform(140, 410)
        r.rect(x, y, 3, 1.5, ['#f6d36a', '#f26a9a', '#5ad8f0', '#9af06a'][i % 4], 0.8)
    for x, c in ((120, '#f26a9a'), (380, '#5ad8f0'), (500, '#f6d36a')):
        r.glow(x, 300, 80, 60, c, 0.05)
    r.wear(60, (30, 100, 570, 420), c='#000000')


@extra
def ext_ruang_arsip(r):
    for x in (80, 220, 380, 520):
        r.sconce(x, 40, '#9ff0e0', '#5a5a74')
    r.corkboard(424, 18, 64, 38, 8)
    for a, b in (((432, 26), (470, 40)), ((446, 30), (476, 24))):
        for t in range(30):
            r.rect(a[0] + (b[0] - a[0]) * t / 30, a[1] + (b[1] - a[1]) * t / 30, 1, 0.6, '#e04a4a')
    r.block.append(r.chest(130, 260, 34, '#4a3a2a'))
    r.block.append(r.box_stack(150, 316, '#8a7a5a'))
    r.block.append(r.card_catalog(400, 200, 60, 44, '#4a4a5a'))
    r.block.append(r.box_stack(422, 282, '#7a6a50', n=1))
    r.papers(170, 360, 6, 60, 20); r.papers(380, 320, 4, 40, 20)
    r.block.append(r.book_stack(220, 400, 4))
    r.block.append(r.box_stack(50, 296, '#7a6a50'))
    r.block.append(r.crate(84, 312, 24, 20, '#6a5a44'))
    for x, y in ((120, 230), (460, 260), (230, 300)):
        r.candle(x, y, 0.8)
    r.wear(70, (26, 100, 574, 420), c='#000000')


@extra
def ext_rumah_sari(r):
    r.frame(176, 26, 16, 20, 3); r.frame(198, 32, 22, 16, 1); r.frame(226, 24, 14, 18, 4)
    r.calendar(530, 40, '#a8784e'); r.mirror(322, 30, 20, 30, '#8c5a34')
    r.sconce(170, 64, '#ffe2b0', '#7a5234'); r.sconce(330, 70, '#ffe2b0', '#7a5234')
    r.block.append(r.cabinet(36, 110, 52, 60, '#7a5234', drawers=3))
    r.pot(50, 110, 0.55, kind='flower'); r.rect(64, 100, 12, 10, '#d9b48a'); r.rect(66, 102, 8, 6, '#e8c0a8')
    r.block.append(r.armchair(40, 188, '#a87a5a', cushion='#f4e2c0'))
    r.block.append(r.side_table(440, 350, 24, item='plant'))
    r.block.append(r.basket(404, 362, 22, 16, '#c9a46a', laundry=False))
    r.dots(r.E(415, 364, 8, 3), ['#e06a7a', '#5a7ac4', '#f6d36a'], 6, 2)          # yarn
    r.book_stack(190, 384, 3)
    r.slippers(250, 396, '#c89a6a')
    r.wear(70, (24, 100, 576, 420))


@pre
def pre_dapur(r):
    r.rug(148, 340, 66, 32, '#9cc7b8', '#eef5e6')
    r.rug(200, 152, 120, 8, '#e8b04a', '#f6e2a8', round_=False)


@extra
def ext_dapur(r):
    r.mug_shelf(254, 62, 7)
    r.hooks(346, 48, ('#e06a7a', '#f6d36a'))
    r.baseboard_bits(74, (160, 238, 366))
    r.block.append(r.sack(470, 250, '#e8dcc0', '#9cc7b8', '#fbf8f0'))
    r.block.append(r.sack(494, 256, '#d8c49a', '#c45a5a', '#e0b04a'))
    r.block.append(r.box_stack(40, 230, '#c9a06a'))
    r.fruit_bowl(148, 328)
    r.block.append(r.bin(250, 410, '#9cc7b8'))
    r.block.append(r.cabinet(80, 236, 50, 56, '#9cc7b8', drawers=2))
    r.mug_shelf(82, 232, 4)
    r.block.append(r.table(400, 300, 40, 26, '#c99a6a', chairs=0, items=('cake',)))
    r.block.append(r.plant_big(440, 420, 'leafy', 0.8))
    r.hooks(40, 50, ('#f6d36a', '#9cc7b8', '#e06a7a'))
    r.wear(80, (30, 150, 570, 420))


@extra
def ext_toko_bunga(r):
    r.block.append(r.crate(170, 250, 40, 26, '#a87443'))
    r.dots(r.R(172, 246, 36, 8), ['#f2a0b8', '#ffffff', '#e04a5a', '#f6d36a'], 24, 2)
    r.leaves(190, 250, 18, 5, n=12)
    r.block.append(r.sack(160, 330, '#b89a6a', '#6a9a5a', '#5a3a24'))
    r.block.append(r.flower_table(372, 356, 70, 30, '#c99a6a'))
    for k in range(4):
        r.pot(384 + k * 15, 362, 0.45, kind='flower')
    r.block.append(r.box_stack(470, 400, '#d8b88a', n=1))
    # watering can
    m = r.E(222, 300, 7, 5); r.fill(m, '#7aa8c4'); r.outline(m, '#3a5a74'); r.rect(228, 294, 8, 2, '#7aa8c4')
    for i in range(70):       # fallen petals and leaves
        x = r.rng.uniform(140, 470); y = r.rng.uniform(200, 400)
        r.rect(x, y, 1.5, 1, ['#f2a0b8', '#ffffff', '#e04a5a', '#6aa86a', '#f6d36a'][i % 5], 0.9)
    r.wear(60, (24, 100, 576, 420))


@extra
def ext_arland_room(r):
    r.corkboard(330, 20, 50, 30, 5); r.calendar(400, 30, '#5a7ac4')
    r.baseboard_bits(86, (150, 420))
    r.book_stack(212, 312, 3)
    r.block.append(r.basket(150, 270, 22, 18, '#8a9aa8'))
    # skateboard and a backpack on the floor
    r.rect(396, 402, 30, 6, '#e0866a'); r.outline(r.R(396, 402, 30, 6), '#7a3a2a')
    for x in (400, 418):
        r.fill(r.E(x, 409, 2, 1.5), '#3a3a48')
    m = r.R(364, 220, 16, 18) | r.E(372, 220, 8, 4); r.fill(m, '#5a7ac4'); r.outline(m, '#2a3a6a')
    r.rect(367, 228, 10, 6, '#4a6ab4')
    r.wear(60, (24, 100, 576, 420))


@extra
def ext_sofia_room(r):
    r.calendar(128, 34, '#e2a7a8')
    r.baseboard_bits(86, (150, 452))
    r.wear(60, (24, 100, 576, 420))


def build(area, apply=False, preview=None):
    P = json.loads((A / 'data/props.json').read_text(encoding='utf-8'))['props']
    Q = json.loads((A / 'data/quests.json').read_text(encoding='utf-8'))
    M = json.loads((A / 'data/maps.json').read_text(encoding='utf-8'))
    base = M['areas'][area]
    seed = int(hashlib.sha256(area.encode()).hexdigest()[:8], 16)
    m = HDMap(area, base['w'], base['h'], seed)
    r = Room(m, seed)
    shell = r.shell

    def shell_then_pre(*a, **k):
        w = shell(*a, **k)
        if area in ROOMS3D:
            r.start_capture()
        if area in PRE:
            PRE[area](r)
        return w
    r.shell = shell_then_pre
    r.dynamic_light = area in ROOMS3D          # U2a: sunlight comes from the game (time and weather)
    ROOMS[area](r)
    if area in EXTRA:
        EXTRA[area](r)
    if area in ROOMS3D:
        stand_up(area, r, m, P, apply)
    keep = keep_points(area, base, Q, M)
    nshell = r.nshell
    for b in r.block[nshell:]:
        if b is None:
            continue
        x, y, w, h = b
        for label, px, py, rad in keep:
            if x - CLEAR < px < x + w + CLEAR and y - CLEAR < py < y + h + CLEAR:
                print('CROWDED', area, label, px, py, 'by', [round(v) for v in b])
    r.block = [b for b in r.block if b is not None]
    walls = [[int(round(v)) for v in b] for b in r.block]
    m.collision = lambda P_: walls
    extra = dict(visualStyle='godot_hd_interior', visualUpdate='godot_rooms_hd', v4Layout=None, indoor=True,
                 room3d=area in ROOMS3D, windows=r.windows if area in ROOMS3D else [],
                 v6Layout=dict(version=3 if area not in ROOMS3D else 4, generator='tools/worldgen/rooms_hd.py', hd=True))
    out = None
    if preview:
        Path(preview).mkdir(parents=True, exist_ok=True)
        out = str(Path(preview) / ('%s.png' % area))
    res = m.write(base, extra, P, Q, apply=apply, preview=out)
    if preview and '--overlay' in sys.argv:
        from PIL import Image, ImageDraw
        im = Image.open(out.replace('.png', '_hd.png')).convert('RGB')
        d = ImageDraw.Draw(im, 'RGBA')
        for x, y, w, h in walls:
            d.rectangle([x * 2, y * 2, (x + w) * 2 - 1, (y + h) * 2 - 1], fill=(255, 0, 0, 50), outline=(255, 0, 0, 160))
        for label, px, py, rad in keep:
            d.ellipse([px * 2 - 2 * CLEAR, py * 2 - 2 * CLEAR, px * 2 + 2 * CLEAR, py * 2 + 2 * CLEAR], outline=(0, 90, 255, 230), width=2)
            d.text((px * 2 + 4, py * 2 - 6), str(label)[:14], fill=(0, 40, 160, 255))
        for gx in range(0, base['w'], 50):
            d.line([gx * 2, 0, gx * 2, 8], fill=(0, 0, 0, 255)); d.text((gx * 2 + 2, 0), str(gx), fill=(255, 255, 255, 255))
        for gy in range(0, base['h'], 50):
            d.line([0, gy * 2, 8, gy * 2], fill=(0, 0, 0, 255)); d.text((0, gy * 2 + 2), str(gy), fill=(255, 255, 255, 255))
        im.save(out.replace('.png', '_overlay.png'))
    return res


ROOMS3D = set(ROOMS)      # rooms shown in full HD-2D 3D: furniture stands up, the back wall is a standing sprite


def stand_up(area, r, m, P, apply):
    """Cut the captured furniture pieces and the back wall out of the room picture as standing props
    (assets/props/rooms/<area>_NN@2x.png); the floor picture keeps rugs, shadows and floor clutter."""
    from PIL import Image
    K = 2
    floor, wall, pieces = r.finish_capture(r.wall_h, r.side)
    img = r.img
    outdir = A / 'props/rooms'
    outdir.mkdir(parents=True, exist_ok=True)
    for f in outdir.glob('%s_*' % area):
        f.unlink()
    for k in [k for k in P if k.startswith('room_%s_' % area)]:
        del P[k]                                   # pieces that no longer exist leave no dead entry behind
    cuts = [(dict(name='wall'), wall)] + pieces
    for i, (pc, mask) in enumerate(cuts):
        ys, xs = np.nonzero(mask)
        x0, x1 = xs.min(), xs.max() + 1
        y0, y1 = ys.min(), ys.max() + 1
        x0 -= x0 % 2; y0 -= y0 % 2; y1 += y1 % 2
        x1 += (-(x0 + x1)) % 4                     # foot centre lands on a whole map pixel
        x1 = min(x1, img.shape[1]) if (x0 + x1) % 4 == 0 else x1
        rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        hh, ww = min(y1, img.shape[0]) - y0, min(x1, img.shape[1]) - x0
        rgba[:hh, :ww, :3] = np.clip(img[y0:y0 + hh, x0:x0 + ww], 0, 255).astype(np.uint8)
        rgba[:hh, :ww, 3] = mask[y0:y0 + hh, x0:x0 + ww] * 255
        tag = 'lamp' if pc['name'] == 'floor_lamp' else pc['name'].replace('_', '')
        pid = 'room_%s_%02d_%s' % (area, i, tag)
        rel = 'props/rooms/%s_%02d_%s@2x.png' % (area, i, tag)
        Image.fromarray(rgba, 'RGBA').save(A / rel, optimize=True)
        P[pid] = dict(image=rel, cw=0, ch=0, layer='sort')
        body = pc.get('body')
        if body and body[2] >= 14 and body[4] >= 12:
            # U2a: the piece's main block in map px from its foot (left, top, w, top depth, front height);
            # src/view3d/furniture_volume.gd builds the 3D sides from it
            fx, fy = (x0 + x1) / 2 / K, y1 / K
            P[pid]['vol'] = [round(body[0] - fx, 1), round(body[1] - fy, 1), round(body[2], 1), round(body[3], 1), round(body[4], 1)]
        m.prop(pid, (x0 + x1) / 2 / K, y1 / K)
    floor[wall] = np.asarray([20, 15, 26], np.float32)
    img[:] = floor
    if apply:
        pj = A / 'data/props.json'
        data = json.loads(pj.read_text(encoding='utf-8'))
        data['props'] = {k: v for k, v in data['props'].items() if not k.startswith('room_%s_' % area)}
        data['props'].update({k: v for k, v in P.items() if k.startswith('room_%s_' % area)})
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import propsjson
        pj.write_text(propsjson.dumps(data), encoding='utf-8')
    print(area, 'stood up', len(cuts), 'pieces (wall included)')


CLEAR = 16      # furniture keeps this many world units free around every quest/examine/door point


def keep_points(area, base, Q, M):
    """Every spot the game sends a character to in this room: quest points and cutscene moves,
    examine spots, arrival points of doors leading here, the spawn and the exits."""
    import common
    pts = [(mv[0], mv[3], mv[4], mv[5]) for mv in common.migrate_quests(json.loads(json.dumps(Q)), area, lambda x, y: (x, y))]
    pts += [('ex ' + e['id'], e['x'], e['y'], e.get('r')) for e in base.get('examine', [])]
    pts += [(d['id'], d['tx'], d['ty'], None) for b in M['areas'].values() for d in b.get('doors', []) if d.get('to') == area]
    pts += [(d['id'], d['rect'][0] + d['rect'][2] / 2, d['rect'][1] + d['rect'][3] / 2, None) for d in base.get('doors', [])]
    pts.append(('spawn', base['spawn'][0], base['spawn'][1], None))
    if base.get('bed'):
        b = base['bed']
        pts.append(('bed', b['x'], b['y'], None) if isinstance(b, dict) else ('bed', b[0], b[1], None))
    return pts


if __name__ == '__main__':
    which = sys.argv[1]
    prev = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    for a in (ROOMS if which == 'all' else which.split(',')):
        build(a, apply='--apply' in sys.argv, preview=prev)
