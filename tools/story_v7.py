"""Story v7: the big story & quest upgrade.

What it does (see docs/STORY_V7.md):
  * Bab 2: Arland's over-tidy date plan, the confession at the pier (they start dating there).
  * Bab 3: Arland's secret projector, Sofia's unfinished sentence, a visit to Nenek Sari's house
    (new interior "rumah_sari") replaces the two shopping lists.
  * Bab 4: Sofia's unsent message (shared fault), Sofia's choice on stage, the long tail trimmed.
  * Bab 5: Nenek Sari starts to forget Wira; new dream map "arsip_memudar" (a listening puzzle)
    replaces Clockwork Station + Moonlight Lake on the main path.
  * Bab 6: the Hall offers to erase the gallery day; climax in the new memory map
    "kenangan_gazebo" (the rainy day forty years ago), which saves Wira & Sari's page.
  * Epilog: Wira's photo finally goes into the empty frame.
  * Moralising lines trimmed, meta objective text cleaned.

It edits assets/data/quests.json, story.json, maps.json (new area entries + one door) and
memory_book.json. Idempotent: originals of every touched step/scene/area are kept in
tools/story_v7_orig.json and restored before each run; everything new is prefixed V7.
Old steps stay in the data, so saves made on any old step still continue (save schema 8).

Run: python3 tools/story_v7.py   then draw the new maps:
  python3 tools/worldgen/rooms_hd.py rumah_sari --apply
  python3 tools/worldgen/dream_hd.py arsip_memudar,kenangan_gazebo --apply
"""
import copy
import json
from pathlib import Path

A = Path(__file__).resolve().parent.parent / 'assets/data'
QP, SP, MP, BP = A / 'quests.json', A / 'story.json', A / 'maps.json', A / 'memory_book.json'
q = json.loads(QP.read_text(encoding='utf-8'))
s = json.loads(SP.read_text(encoding='utf-8'))
m = json.loads(MP.read_text(encoding='utf-8'))
mb = json.loads(BP.read_text(encoding='utf-8'))

# ------------------------------------------------------------------------------ undo the last run
OP = Path(__file__).resolve().parent / 'story_v7_orig.json'
_orig = json.loads(OP.read_text(encoding='utf-8')) if OP.exists() else {}
orig_q = _orig.get('quests', {})
orig_s = _orig.get('story', {})
orig_m = _orig.get('maps', {})
q['steps'] = [x for x in q['steps'] if not x['id'].startswith('V7_')]
for sid, val in orig_q.get('steps', {}).items():
    for i, x in enumerate(q['steps']):
        if x['id'] == sid:
            q['steps'][i] = val
q['townNpcs'] = [x for x in q['townNpcs'] if not x['id'].startswith('v7_')]
q['side'] = [x for x in q['side'] if not x['id'].startswith('v7_')]
q['sideQuests'] = [x for x in q['sideQuests'] if not x['id'].startswith('SQ_V7_')]
for nid, val in orig_q.get('npcs', {}).items():
    for i, x in enumerate(q['townNpcs']):
        if x['id'] == nid:
            q['townNpcs'][i] = val
for k in [k for k in s['scenes'] if k.startswith('V7-')]:
    del s['scenes'][k]
for k, val in orig_s.get('scenes', {}).items():
    s['scenes'][k] = val
for k in ('wira', 'sari_muda'):
    s['speakers'].pop(k, None)
NEW_AREAS = ('rumah_sari', 'arsip_memudar', 'kenangan_gazebo')
keep_drawn = {a: m['areas'][a] for a in NEW_AREAS if a in m['areas']}
for a in NEW_AREAS:
    m['areas'].pop(a, None)
for a, val in orig_m.get('areas', {}).items():
    m['areas'][a] = val
mb['items'] = {k: v for k, v in mb['items'].items() if not k.startswith('v7_')}
mb['entries'] = [e for e in mb['entries'] if not e['id'].startswith('m_v7_')]

ORIG_Q = {'steps': {}, 'npcs': {}}
ORIG_S = {'scenes': {}}
ORIG_M = {'areas': {}}
STEPS = {x['id']: x for x in q['steps']}


def step_(sid):
    if sid not in ORIG_Q['steps']:
        ORIG_Q['steps'][sid] = copy.deepcopy(STEPS[sid])
    return STEPS[sid]


def scene_(sid):
    if sid not in ORIG_S['scenes']:
        ORIG_S['scenes'][sid] = copy.deepcopy(s['scenes'][sid])
    return s['scenes'][sid]


# ------------------------------------------------------------------------------ authoring helpers
def L(who, text, e='neutral'):
    return {'s': who, 't': text, 'e': e}


def N(text):
    return L('narrator', text)


def scene(sid, title, chapter, route, location, lines, choices=None, flags=None, trigger=''):
    assert sid.startswith('V7-'), sid
    sc = {'title': title, 'route': route, 'chapter': chapter, 'location': location, 'trigger': trigger,
          'lines': lines, 'flags': flags or [], 'v7': True}
    if choices:
        sc['choices'] = choices
    s['scenes'][sid] = sc


def ch(text, flags, arland=None, sofia=None, both=None):
    c = {'text': text, 'flags': flags}
    if both is not None:
        arland = sofia = both
    c['byRoute'] = {'arland': arland or [], 'sofia': sofia or []}
    return c


def it(iid, area, x, y, label, actions, r=70, route=None, when=None, hide=None, sprite=None):
    d = {'id': iid, 'area': area, 'x': x, 'y': y, 'r': r, 'label': label, 'actions': actions}
    if route:
        d['route'] = route
    if when:
        d['when'] = when
    if hide:
        d['hideIfFlag'] = hide
    if sprite:
        d['sprite'] = {'image': sprite, 'x': x, 'y': y - 16, 'bob': True}
    return d


def new_step(sid, chapter, quest, obj, interactables=(), **extra):
    assert sid.startswith('V7_'), sid
    if isinstance(obj, str):
        obj = {'arland': obj, 'sofia': obj}
    st = {'id': sid, 'chapter': chapter, 'quest': quest, 'objective': obj, 'interactables': list(interactables)}
    st.update(extra)
    q['steps'].append(st)
    STEPS[sid] = st
    return st


def S(sid):
    return {'do': 'scene', 'id': sid}


def GO(sid):
    return {'do': 'step', 'id': sid}


def IF_ROUTE(a, b):
    return {'do': 'if', 'when': {'route': 'arland'}, 'then': a, 'else': b}


def IF_FLAG(flag, then, els=None):
    return {'do': 'if', 'when': {'flags': [flag]}, 'then': then, 'else': els or []}


def walk(acts, fn):
    """Call fn(list, index, action) for every action in nested action lists (then/else)."""
    i = 0
    while i < len(acts):
        a = acts[i]
        r = fn(acts, i, a)
        if r is not None:
            i = r
            continue
        if isinstance(a, dict):
            for k in ('then', 'else'):
                if isinstance(a.get(k), list):
                    walk(a[k], fn)
        i += 1


def action_lists(st):
    out = [x['actions'] for x in st.get('interactables', [])]
    for k in ('complete', 'enterArea'):
        if isinstance(st.get(k), dict):
            out.append(st[k]['actions'])
    if isinstance(st.get('onStart'), list):
        out.append(st['onStart'])
    return out


def plays(a, scene_id):
    if a.get('do') == 'scene' and a.get('id') == scene_id:
        return True
    if a.get('do') == 'cine':
        return any(c.get('c') == 'say' and c.get('scene') == scene_id for c in a.get('cmds', []))
    return False


def insert_after_scene(sid, scene_id, new_actions, required=True):
    st = step_(sid)
    hits = [0]

    def fn(lst, i, a):
        if isinstance(a, dict) and plays(a, scene_id):
            lst[i + 1:i + 1] = copy.deepcopy(new_actions)
            hits[0] += 1
            return i + 1 + len(new_actions)
    for acts in action_lists(st):
        walk(acts, fn)
    if required and not hits[0]:
        raise SystemExit('scene %s not found in %s' % (scene_id, sid))


def redirect(sid, old, new):
    st = step_(sid)
    hits = [0]

    def fn(lst, i, a):
        if isinstance(a, dict) and a.get('do') == 'step' and a.get('id') == old:
            a['id'] = new
            hits[0] += 1
    for acts in action_lists(st):
        walk(acts, fn)
    if not hits[0]:
        raise SystemExit('step %s -> %s not found' % (sid, old))


def film(scene_ids, mood, end_mood=None, pair='lean', ambient='sparkles', finale='glow', orbit=12, zoom=1.2):
    """Cutscene recipe matching tools/story_cines.py (film camera from PR #1)."""
    c = [{'c': 'bars', 'on': True, 't': 0.5}, {'c': 'mood', 'id': mood, 't': 1.6},
         {'c': 'shot', 'focus': 'couple', 'zoom': zoom, 't': 0, 'bars': False},
         {'c': 'crane', 't': 3.6, 'zoom': zoom, 'block': True}]
    if ambient:
        c.append({'c': 'fx', 'kind': ambient, 'on': 'player', 't': 14.0, 'n': 36})
    if orbit:
        c.append({'c': 'orbit', 'deg': orbit, 't': 12.0})
    c.append({'c': 'dof', 'a': 0.8, 't': 1.5})
    c += [{'c': 'say', 'scene': x} for x in scene_ids]
    if end_mood:
        c.append({'c': 'mood', 'id': end_mood, 't': 2.0})
    c.append({'c': 'shot', 'focus': 'couple', 'zoom': zoom + 0.16, 't': 1.6, 'bars': False, 'async': True})
    if pair:
        c.append({'c': 'pair', 'kind': pair, 't': 2.4})
    if finale:
        c.append({'c': 'fx', 'kind': finale, 'on': 'player', 't': 2.6, 'block': True})
    c += [{'c': 'wait', 't': 0.6}, {'c': 'angle', 'yaw': 0, 't': 1.0}, {'c': 'dof', 'a': 0.35, 't': 0.8},
          {'c': 'bars', 'on': False, 't': 0.6}]
    return {'do': 'cine', 'cmds': c, 'v7': True}


def short_cine(focus='couple', zoom=1.25, caption=None):
    c = [{'c': 'bars', 'on': True, 't': 0.4}, {'c': 'shot', 'focus': focus, 'zoom': zoom, 't': 1.2}]
    if caption:
        c.append({'c': 'caption', 'text': caption[0], 'sub': caption[1], 't': 3.0})
    c.append({'c': 'bars', 'on': False, 't': 0.5})
    return {'do': 'cine', 'cmds': c, 'v7': True}


s['speakers']['wira'] = {'name': 'Wira (kenangan)', 'portrait': None, 'style': 'npc'}
s['speakers']['sari_muda'] = {'name': 'Sari (kenangan)', 'portrait': None, 'style': 'npc'}


def item(iid, name, icon, desc):
    mb['items'][iid] = {'name': name, 'icon': icon, 'desc': desc}


item('v7_proyektor', 'Proyektor Tua', 'items/mini_telescope.png', 'Proyektor peninggalan Ayah Arland. Rencananya jadi kejutan untuk galeri Sofia.')
item('v7_halaman_wira', 'Halaman Abu-abu', 'items/memory_page.png', 'Halaman Wira dan Sari yang memudar. Tulisannya hanya kembali kalau ceritanya diucapkan.')
item('v7_foto_wira', 'Foto di Gazebo', 'items/photo_small.png', 'Wira dan Sari muda di bawah satu payung yang kebesaran.')


def memory(mid, chapter, unlock, icon, title, text):
    mb['entries'].append({'id': mid, 'chapter': chapter, 'route': 'shared', 'type': 'fictional_memory',
                          'unlock': unlock, 'icon': icon, 'title': title, 'text': text})


memory('m_v7_jadian', 'C02', 'V7_JADIAN', 'items/photo_strip.png', 'Senja yang Sama',
       'Di ujung dermaga, dua orang berhenti pura-pura cuma berteman.')
memory('m_v7_rumah_sari', 'C03', 'V7_C03_SARI_VISITED', 'items/dried_flowers.png', 'Bingkai yang Kosong',
       'Rumah Nenek Sari wangi melati. Di rak, satu bingkai menunggu fotonya pulang.')
memory('m_v7_arsip', 'C05', 'V7_C05_ARCHIVE_DONE', 'items/memory_page.png', 'Arsip yang Memudar',
       'Cerita yang ditulis tapi tak pernah diucapkan pelan-pelan kehilangan warnanya.')
memory('m_v7_gazebo', 'C06', 'V7_WIRA_PAGE_SAVED', 'items/lantern_small.png', 'Empat Puluh Tahun Lalu',
       'Hujan yang sama, gazebo yang sama. Kali ini ceritanya selesai diucapkan.')

# =============================================================================== NEW MAP ENTRIES
# Ground, props and collision are drawn by rooms_hd.py / dream_hd.py. The entries carry what the
# story needs: size, spawn, doors and examine spots.  An already drawn map keeps its drawing.


def area_entry(aid, name, w, h, spawn, doors, examine, music, ambient, indoor):
    a = {'name': name, 'image': 'maps/%s.png' % aid, 'w': w, 'h': h, 'music': music, 'ambient': ambient,
         'spawn': spawn, 'indoor': indoor, 'walls': [], 'ellipses': [], 'props': [], 'gates': [],
         'animals': [], 'doors': doors, 'examine': examine, 'stairs': [], 'storyVersion': 'v7'}
    old = keep_drawn.get(aid)
    if old:   # keep the drawn ground/props/collision, refresh the story fields
        for k in ('walls', 'props', 'tiles', 'surface', 'ellipses', 'water', 'waterFlow', 'visualStyle',
                  'visualUpdate', 'v6Layout', 'v4Layout', 'animals', 'gates', 'stairs'):
            if k in old:
                a[k] = old[k]
    m['areas'][aid] = a


def ex(eid, x, y, label, arland, sofia=None, when=None, r=56):
    e = {'id': eid, 'x': x, 'y': y, 'label': label, 'r': r,
         'lines': {'arland': arland, 'sofia': sofia if sofia is not None else arland}}
    if when:
        e['when'] = when
    return e


# Perumahan: the red-brick house (prop at 1020,252) becomes Nenek Sari's house
ORIG_M['areas']['perumahan'] = copy.deepcopy(m['areas']['perumahan'])
m['areas']['perumahan']['doors'].append({'id': 'v7_door_rumah_sari', 'rect': [994, 298, 52, 30],
                                         'label': 'Rumah Nenek Sari', 'to': 'rumah_sari', 'tx': 300, 'ty': 380, 'dir': 'up'})

area_entry('rumah_sari', 'Rumah Nenek Sari', 600, 448, [300, 380],
           [{'id': 'v7_rumah_sari_out', 'rect': [274, 410, 52, 35], 'label': 'Keluar ke Perumahan',
             'to': 'perumahan', 'tx': 1020, 'ty': 345, 'dir': 'down'}],
           [ex('v7_frame_empty', 470, 132, 'Bingkai kosong',
               [N('Bingkai kayu dengan kaca bersih. Tidak ada fotonya. Di sudutnya tergores huruf kecil: W.')],
               when={'notFlags': ['V7_EPI_FRAME']}),
            ex('v7_frame_full', 470, 132, 'Foto di gazebo',
               [N('Wira dan Sari muda di bawah payung yang kebesaran. Keduanya basah, dan keduanya tertawa.')],
               when={'flags': ['V7_EPI_FRAME']}),
            ex('v7_umbrella', 132, 300, 'Payung tua',
               [N('Payung hitam dengan satu ruji yang bengkok. Gagangnya dililit pita melati yang sudah pudar.')]),
            ex('v7_radio', 520, 300, 'Radio kayu',
               [L('arland', 'Radio tua. Masih ada kaset keroncong di dalamnya.')],
               [L('sofia', 'Radio tua. Kasetnya keroncong, labelnya ditulis tangan: "Lagu hujan".')]),
            ex('v7_jasmine', 210, 140, 'Pot melati',
               [L('arland', 'Melatinya dirawat banget. Nggak ada satu daun pun yang kuning.')],
               [L('sofia', 'Wangi melati. Sama seperti teh di kafe Kak Raka.')])],
           'home_evening', None, True)

area_entry('arsip_memudar', 'Arsip yang Memudar', 1600, 1120, [800, 1010],
           [{'id': 'v7_arsip_out', 'rect': [740, 1076, 120, 44], 'label': 'Kembali ke Starfall Village',
             'to': 'starfall_village', 'tx': 1788, 'ty': 1060, 'dir': 'down'}],
           [ex('v7_arsip_shelves', 800, 300, 'Rak tanpa ujung',
               [N('Rak-rak buku melayang di kabut. Judulnya terhapus, hanya tanggal yang tersisa.')]),
            ex('v7_arsip_stamp', 480, 920, 'Cap Arsip No. 7',
               [L('arland', 'Cap yang sama dengan surat di kafe. Semua jalan ternyata mengarah ke sini.')],
               [L('sofia', 'Arsip Nomor Tujuh. Jadi ini tempat cerita yang nggak sempat diucapkan.')])],
           'archive_mystery', 'v50_memory_air', False)

area_entry('kenangan_gazebo', 'Gazebo, Empat Puluh Tahun Lalu', 1600, 1120, [800, 1010],
           [{'id': 'v7_gazebo_out', 'rect': [740, 1076, 120, 44], 'label': 'Kembali ke Eternal Garden',
             'to': 'eternal_garden', 'tx': 1200, 'ty': 900, 'dir': 'up'}],
           [ex('v7_old_poster', 1240, 900, 'Poster tua',
               [N('"Pasar Malam Kota, 1986." Kertasnya basah, tapi warnanya masih cerah.')]),
            ex('v7_old_lamp', 360, 900, 'Lampu taman lama',
               [L('arland', 'Lampu ini masih pakai bohlam kuning. Taman Kota dulu kelihatan begini, ya.')],
               [L('sofia', 'Bangku dan lampunya sama dengan Taman Kota. Cuma catnya yang belum mengelupas.')])],
           'rain_lullaby', 'rain_outdoor', False)

# Nenek Sari at home: evenings, and whenever the story visits her house
ORIG_Q['npcs']['sari'] = copy.deepcopy(next(n for n in q['townNpcs'] if n['id'] == 'sari'))
sari = next(n for n in q['townNpcs'] if n['id'] == 'sari')
for e in sari['schedule']:
    if e.get('at') == '19:30' and e.get('hidden'):
        e.pop('hidden')
        e.update({'area': 'rumah_sari', 'x': 430, 'y': 236, 'dir': 'down', 'wander': 20})
HOME_STEPS = ['V7_C03_SARI_VISIT', 'V7_C03_SARI_SHELF', 'V7_C05_SARI_FADING', 'EPI_FREE']
sari['schedule'].append({'at': '00:00', 'area': 'rumah_sari', 'x': 430, 'y': 236, 'dir': 'down', 'wander': 0,
                         'when': {'steps': HOME_STEPS}})

# =============================================================================== PROLOG
scene('V7-P-LUMI', 'Cahaya yang Bersembunyi', 'PRO', 'shared', 'memory_garden', [
    N('Saat gerbang mulai menutup, sebutir cahaya seukuran kunang-kunang melayang di belakang mereka.'),
    L('sofia', 'Kamu lihat itu?', 'penasaran'),
    L('arland', 'Lihat apa?', 'bingung'),
    N('Cahaya itu sudah menyelinap ke sela halaman Memory Book.'),
    N('Di halaman paling belakang, sebaris tulisan tangan tua muncul sebentar, lalu hilang: "Untuk S..., maaf aku..."'),
])
insert_after_scene('PRO_PORTAL', 'V474-P-PORTAL-A', [S('V7-P-LUMI')])
insert_after_scene('PRO_PORTAL', 'V474-P-PORTAL-S', [S('V7-P-LUMI')])

# =============================================================================== BAB 2
scene('V7-C02-PLAN@arland', 'Rencana Lima Belas Menit', 'C02', 'arland', 'arland_room', [
    N('Arland membuka buku catatan dan menulis cepat.'),
    L('arland', '15.00 kafe. 15.40 taman. 16.15 photobooth. 17.02 senja, tepat waktu matahari turun.', 'serius'),
    L('arland', 'Kalau semuanya pas, Sofia pasti senang.', 'senang'),
    L('sofia_msg', 'Land, kita cuma jalan sore, kan? Kok kamu kirim jadwal kayak rapat?', 'tertawa'),
    L('arland', 'Biar nggak ada yang meleset!', 'malu'),
    L('sofia_msg', 'Yang meleset juga boleh, kok. Aku cuma pengen jalan sama kamu.', 'senyum'),
    N('Arland membaca pesan itu dua kali. Lalu tetap menambahkan satu baris lagi di catatannya.'),
])
scene('V7-C02-PLAN@sofia', 'Jadwal dari Arland', 'C02', 'sofia', 'sofia_room', [
    L('arland_msg', '15.00 kafe. 15.40 taman. 16.15 photobooth. 17.02 senja. Sudah kuhitung jam matahari terbenam!', 'senang'),
    L('sofia', 'Ya ampun. Dia ngitung jam matahari terbenam.', 'tertawa'),
    L('sofia', 'Lucu. Tapi aku jadi takut telat lima menit.', 'khawatir'),
    L('sofia_msg', 'Yang meleset juga boleh, kok. Aku cuma pengen jalan sama kamu.', 'senyum'),
    L('arland_msg', 'Siap! Tapi aku tetap bawa jadwalnya, ya.', 'senang'),
    N('Sofia menaruh ponsel dan tersenyum. Ada sesuatu yang ingin ia katakan nanti, tapi tidak lewat pesan.'),
])
c02_phone = step_('C02_PHONE')
for x in c02_phone['interactables']:
    acts = x['actions']
    for i, a in enumerate(acts):
        if a.get('do') == 'step':
            acts.insert(i, S('V7-C02-PLAN@$ROUTE'))
            break

CONFESS_A = [
    ch('"Aku suka kamu, Sof. Dari sebelum kita ketemu di plaza."', ['V7_CONFESS_A_LONG'], arland=[
        L('sofia', 'Dari sebelum plaza? Kok baru bilang sekarang?', 'kaget'),
        L('arland', 'Aku nunggu momen yang sempurna. Ternyata nggak ada. Jadi sekarang aja.', 'malu'),
        L('sofia', 'Aku juga suka kamu, Land. Jam 17.02 tepat, sesuai jadwalmu.', 'jatuh_cinta')]),
    ch('"Aku pengen kita lebih dari teman jalan sore."', ['V7_CONFESS_A_MORE'], arland=[
        L('sofia', 'Lebih dari teman jalan sore... maksudnya?', 'malu'),
        L('arland', 'Maksudnya, aku pengen jadi orang yang kamu kabari duluan.', 'serius'),
        L('sofia', 'Kamu udah jadi orang itu dari lama. Iya, Land. Aku mau.', 'jatuh_cinta')]),
    ch('"Boleh aku nemenin kamu lihat senja, nggak cuma hari ini?"', ['V7_CONFESS_A_SUNSET'], arland=[
        L('sofia', 'Nggak cuma hari ini?', 'penasaran'),
        L('arland', 'Besok, minggu depan, waktu hujan juga. Kalau kamu mau.', 'malu'),
        L('sofia', 'Aku mau. Tapi waktu hujan kamu yang bawa payung.', 'jatuh_cinta')]),
]
CONFESS_S = [
    ch('"Land, aku suka kamu. Nggak usah dijadwal dulu jawabannya."', ['V7_CONFESS_S_DIRECT'], sofia=[
        L('arland', 'Eh... itu harusnya kalimatku. Aku udah latihan dari kemarin!', 'kaget'),
        L('sofia', 'Kelamaan. Senjanya keburu habis.', 'tertawa'),
        L('arland', 'Aku juga suka kamu, Sof. Banget.', 'jatuh_cinta')]),
    ch('"Hari ini nggak sesuai jadwal. Tapi ini hari favoritku."', ['V7_CONFESS_S_FAVORITE'], sofia=[
        L('arland', 'Karena fotonya lucu?', 'bingung'),
        L('sofia', 'Karena kamu. Aku pengen hari kayak gini lagi, sebagai pacarmu.', 'malu'),
        L('arland', 'Sebagai... iya. Iya! Aku mau.', 'jatuh_cinta')]),
    ch('Tunjukkan gambar dua orang di dermaga yang Sofia buat semalam', ['V7_CONFESS_S_DRAWING'], sofia=[
        L('arland', 'Ini... kita? Di dermaga ini?', 'kaget'),
        L('sofia', 'Aku gambar semalam. Aku nggak jago ngomong, jadi aku gambar.', 'malu'),
        L('arland', 'Gambarnya jelas banget, Sof. Aku juga suka kamu.', 'jatuh_cinta')]),
]
scene('V7-C02-CONFESS@arland', 'Pukul Lima Lewat Dua', 'C02', 'arland', 'riverside', [
    N('Matahari turun tepat seperti yang Arland hitung. Tapi kalimat yang ia siapkan hilang semua.'),
    L('arland', 'Sof... jadwalku habis di sini. Nggak ada baris berikutnya.', 'malu'),
    L('sofia', 'Terus?', 'penasaran'),
    L('arland', 'Terus aku harus ngomong pakai kata-kataku sendiri.', 'serius'),
], choices=CONFESS_A, flags=['V7_JADIAN'])
scene('V7-C02-CONFESS@sofia', 'Pukul Lima Lewat Dua', 'C02', 'sofia', 'riverside', [
    N('Arland melirik jam di ponselnya. 17.02. Senja datang tepat waktu, sesuai jadwalnya.'),
    L('arland', 'Nah. Tepat! Sekarang aku mau ngomong sesuatu yang penting, Sof...', 'serius'),
    L('sofia', 'Tunggu. Kali ini biar aku duluan.', 'malu'),
], choices=CONFESS_S, flags=['V7_JADIAN'])
scene('V7-C02-AFTER', 'Dua Orang di Dermaga', 'C02', 'shared', 'riverside', [
    N('Untuk beberapa saat tidak ada yang bicara. Air danau memantulkan dua bayangan yang duduk lebih dekat dari tadi.'),
    L('sofia', 'Jadi sekarang kita...', 'malu'),
    L('arland', 'Iya. Kita.', 'jatuh_cinta'),
    N('Di Memory Book, halaman senja berubah jingga penuh. Hanya satu sudut kecil yang masih pudar.'),
])
insert_after_scene('C02_SUNSET', 'C02-X04', [S('V7-C02-CONFESS@$ROUTE'), S('V7-C02-AFTER')])

# =============================================================================== BAB 3
scene('V7-C03-A-PROJECTOR', 'Kotak di Bawah Meja', 'C03', 'arland', 'arland_room', [
    N('Di bawah meja ada kardus berdebu. Di dalamnya, proyektor tua milik Ayah.'),
    L('arland', 'Galeri Sofia hari Sabtu. Kalau gambarnya diproyeksikan besar di dinding...', 'penasaran'),
    L('arland', 'Dia pasti kaget. Aku nggak bilang dulu. Biar jadi kejutan.', 'senang'),
    N('Arland mencolokkan kabelnya. Lampunya berkedip sekali, lalu mati. Ia tersenyum seperti baru menemukan tantangan.'),
], flags=['V7_A_PROJECTOR_SECRET'])
insert_after_scene('C03_A_IDEA', 'C03-A00', [S('V7-C03-A-PROJECTOR'), {'do': 'item', 'id': 'v7_proyektor'}])

scene('V7-C03-S-MIRROR', 'Latihan di Depan Cermin', 'C03', 'sofia', 'sofia_room', [
    N('Sofia berdiri di depan cermin dengan undangan galeri di tangan.'),
    L('sofia', 'Land, di galeri nanti aku nggak butuh apa-apa. Aku cuma butuh kamu datang.', 'serius'),
    L('sofia', '...Kedengarannya kayak nuntut, ya?', 'khawatir'),
    L('sofia', 'Land, kalau sempat, datang ya. Kalau nggak sempat juga nggak apa-apa.', 'senyum'),
    L('sofia', 'Bohong. Itu apa-apa.', 'sedih'),
    N('Ia melipat undangannya lagi. Kalimat pertama lebih jujur, tapi kalimat kedua yang terasa lebih aman.'),
], flags=['V7_S_UNSAID'])
insert_after_scene('C03_S_CORNER', 'C03-S01', [S('V7-C03-S-MIRROR')])

# Return to the neighbour -> visit Nenek Sari instead of two shopping lists
redirect('V469_C03_NEIGHBOR', 'C03_A_INGREDIENTS', 'V7_C03_SARI_VISIT')
redirect('V469_C03_NEIGHBOR', 'C03_S_DECOR', 'V7_C03_SARI_VISIT')
st = step_('C03_A_IDEA')
scene_('C03-A00')['lines'][-1] = L('arland', 'Stroberi sama mint bisa dibeli di Pasar Minggu. Madunya... Nenek Sari punya madu paling enak.', 'senang')

scene('V7-C03-SARI-HOME@arland', 'Rumah Bata Merah', 'C03', 'arland', 'rumah_sari', [
    N('Rumah Nenek Sari wangi melati dan teh. Jam dindingnya berdetak pelan.'),
    L('sari', 'Arland! Pasti mau minta madu, ya. Kak Raka sudah cerita kamu mau masak.', 'senang'),
    L('arland', 'Ketahuan. Buat roti lapis, Nek. Buat Sofia.', 'malu'),
    L('sari', 'Buat Sofia. Pantas mukamu merah begitu.', 'tertawa'),
    L('sari', 'Duduk sebentar. Nenek ambilkan toplesnya. Jangan sentuh payung di pojok, ya. Itu sudah tua sekali.', 'senyum'),
])
scene('V7-C03-SARI-HOME@sofia', 'Rumah Bata Merah', 'C03', 'sofia', 'rumah_sari', [
    N('Rumah Nenek Sari wangi melati dan teh. Jam dindingnya berdetak pelan.'),
    L('sari', 'Sofia! Bu Laras bilang kamu sedang menata sudut kenangan.', 'senang'),
    L('sofia', 'Iya, Nek. Aku cari bunga kering. Kata Bu Melati, bunga melati Nenek yang paling awet.', 'senyum'),
    L('sari', 'Ada. Nenek keringkan sendiri. Duduk dulu, Nenek ambilkan di belakang.', 'senyum'),
    L('sari', 'Jangan sentuh payung di pojok, ya. Itu sudah tua sekali.', 'neutral'),
])
scene('V7-C03-FRAME@arland', 'Bingkai Kosong', 'C03', 'arland', 'rumah_sari', [
    N('Di rak, di antara foto cucu-cucu, ada satu bingkai kayu tanpa foto. Kacanya bersih, seperti rajin dilap.'),
    L('arland', 'Ada huruf W kecil di sudut bingkainya.', 'penasaran'),
    L('arland', 'W... Pak Wira? Yang namanya ada di catatan Arsip No. 7?', 'kaget'),
])
scene('V7-C03-FRAME@sofia', 'Bingkai Kosong', 'C03', 'sofia', 'rumah_sari', [
    N('Di rak, di antara foto cucu-cucu, ada satu bingkai kayu tanpa foto. Kacanya bersih, seperti rajin dilap.'),
    L('sofia', 'Bingkai kosong yang dirawat. Berarti fotonya pernah ada.', 'penasaran'),
    L('sofia', 'Huruf W di sudutnya... Pak Wira, dari Arsip No. 7.', 'kaget'),
])
scene('V7-C03-UMBRELLA@arland', 'Payung di Pojok', 'C03', 'arland', 'rumah_sari', [
    N('Payung hitam bersandar di pojok. Satu rujinya bengkok. Gagangnya dililit pita melati pudar.'),
    L('arland', 'Rusak, tapi disimpan rapi. Kayak tiket yang nggak tega dibuang.', 'serius'),
])
scene('V7-C03-UMBRELLA@sofia', 'Payung di Pojok', 'C03', 'sofia', 'rumah_sari', [
    N('Payung hitam bersandar di pojok. Satu rujinya bengkok. Gagangnya dililit pita melati pudar.'),
    L('sofia', 'Payung yang rusak tapi nggak dibuang. Pasti ada ceritanya.', 'penasaran'),
])
scene('V7-C03-SARI-BYE@arland', 'Yang Tidak Diceritakan', 'C03', 'arland', 'rumah_sari', [
    L('sari', 'Ini madunya. Stroberi dan mint sudah kamu beli di pasar, kan?', 'senyum'),
    L('arland', 'Sudah, Nek. Nek... bingkai yang kosong itu punya siapa?', 'penasaran'),
    N('Nenek Sari diam sebentar. Tangannya merapikan taplak yang sebenarnya sudah rapi.'),
    L('sari', 'Punya orang yang suka terlambat. Sudah, sana. Rotinya keburu nggak enak.', 'tersenyum'),
    N('Ia tidak menjawab. Tapi ia juga tidak marah. Seperti cerita yang terlalu lama disimpan sampai lupa cara membukanya.'),
], flags=['V7_C03_SARI_VISITED'])
scene('V7-C03-SARI-BYE@sofia', 'Yang Tidak Diceritakan', 'C03', 'sofia', 'rumah_sari', [
    L('sari', 'Ini bunga keringnya. Bawa juga lampu kecil dan bingkai bintang ini. Sudah lama cuma di laci.', 'senyum'),
    L('sofia', 'Nek, bingkai yang kosong di rak itu punya siapa?', 'penasaran'),
    N('Nenek Sari diam sebentar. Tangannya merapikan taplak yang sebenarnya sudah rapi.'),
    L('sari', 'Punya orang yang suka terlambat. Sudah, sudut kenanganmu menunggu.', 'tersenyum'),
    N('Ia tidak menjawab. Tapi ia juga tidak marah. Seperti cerita yang terlalu lama disimpan sampai lupa cara membukanya.'),
], flags=['V7_C03_SARI_VISITED'])

new_step('V7_C03_SARI_VISIT', 'C03', 'Q_V469_C03_MEMORIES',
         {'arland': 'Minta madu ke rumah Nenek Sari (rumah bata merah, Distrik Perumahan)',
          'sofia': 'Minta bunga kering ke rumah Nenek Sari (rumah bata merah, Distrik Perumahan)'},
         [it('v7_sari_home', 'rumah_sari', 430, 260, 'Bicara dengan Nenek Sari',
             [short_cine('couple', 1.3, ('Rumah Nenek Sari', 'Distrik Perumahan')), S('V7-C03-SARI-HOME@$ROUTE'), GO('V7_C03_SARI_SHELF')])])
new_step('V7_C03_SARI_SHELF', 'C03', 'Q_V469_C03_MEMORIES', 'Sambil menunggu, lihat-lihat rumah Nenek Sari',
         [it('v7_shelf_frame', 'rumah_sari', 470, 160, 'Bingkai kosong di rak',
             [S('V7-C03-FRAME@$ROUTE'), {'do': 'flag', 'id': 'V7_C03_SAW_FRAME'}, {'do': 'count', 'id': 'v7_sari_shelf', 'add': 1}],
             hide='V7_C03_SAW_FRAME'),
          it('v7_shelf_umbrella', 'rumah_sari', 140, 320, 'Payung tua di pojok',
             [S('V7-C03-UMBRELLA@$ROUTE'), {'do': 'flag', 'id': 'V7_C03_SAW_UMBRELLA'}, {'do': 'count', 'id': 'v7_sari_shelf', 'add': 1}],
             hide='V7_C03_SAW_UMBRELLA')],
         counter='v7_sari_shelf', counterMax=2,
         complete={'counter': 'v7_sari_shelf', 'count': 2, 'actions': [
             S('V7-C03-SARI-BYE@$ROUTE'),
             IF_ROUTE([{'do': 'item', 'id': 'stroberi'}, {'do': 'item', 'id': 'madu'}, {'do': 'item', 'id': 'daun_mint'},
                       {'do': 'toast', 'text': 'Bahan lengkap. Ke dapur Kafe Senja.'}, GO('C03_A_KITCHEN')],
                      [{'do': 'item', 'id': 'bunga_kering'}, {'do': 'item', 'id': 'lampu_tumbler'}, {'do': 'item', 'id': 'bingkai_bintang'},
                       {'do': 'toast', 'text': 'Dekorasi lengkap. Pulang dan tata sudut kenangan.'}, GO('C03_S_ARRANGE')])]})

scene('V7-C03-UNSAID@arland', 'Kalimat yang Terpotong', 'C03', 'arland', 'taman_kota', [
    L('sofia', 'Land, soal Sabtu... aku cuma—', 'serius'),
    L('arland', 'Tenang! Pokoknya hari Sabtu aku punya kejutan. Kamu pasti suka.', 'senang'),
    L('sofia', '...Oke.', 'senyum'),
    N('Arland tidak menyadari Sofia berhenti di tengah kalimat. Kepalanya sudah penuh kabel proyektor.'),
])
scene('V7-C03-UNSAID@sofia', 'Kalimat yang Terpotong', 'C03', 'sofia', 'taman_kota', [
    L('sofia', 'Land, soal Sabtu... aku cuma—', 'serius'),
    L('arland', 'Tenang! Pokoknya hari Sabtu aku punya kejutan. Kamu pasti suka.', 'senang'),
    L('sofia', '...Oke.', 'senyum'),
    N('Kalimat yang ia latih di depan cermin kembali masuk ke saku. Nanti saja, pikirnya. Dia pasti datang.'),
])
insert_after_scene('C03_PICNIC', 'V464-C03-PROMISE', [S('V7-C03-UNSAID@$ROUTE')])

# =============================================================================== BAB 4
scene('V7-C04-S-DRAFT', 'Draf yang Menunggu', 'C04', 'sofia', 'sofia_room', [
    N('Sofia menaruh ponselnya terbalik. Terlalu gugup untuk membaca pesan apa pun.'),
    N('Di layar yang tidak ia lihat, satu draf dari minggu lalu masih menunggu: "Land, acaranya jam empat, ya. Kursimu di dekat jendela."'),
    N('Status: belum terkirim.'),
])
insert_after_scene('C04_S_WAKE', 'V464-C04-S-MORNING', [S('V7-C04-S-DRAFT')])

STAGE = [
    ch('Lanjutkan sesuai rencana, walau suaranya bergetar', ['V7_S_STAGE_CONTINUE'], sofia=[
        L('sofia', 'Gambar berikutnya... aku buat waktu hujan pertama bulan ini.', 'serius'),
        N('Suaranya bergetar di kalimat pertama, lalu tenang di kalimat ketiga. Ia menyelesaikan semuanya.')]),
    ch('Persingkat, lalu tutup lebih cepat', ['V7_S_STAGE_SHORT'], sofia=[
        L('sofia', 'Sisanya bisa kalian lihat sendiri. Terima kasih sudah datang.', 'senyum'),
        N('Tepuk tangan tetap datang. Sofia turun dari panggung lebih cepat dari rencana, dan itu juga tidak apa-apa.')]),
    ch('Ceritakan kursi kosong itu kepada pengunjung', ['V7_S_STAGE_CHAIR'], sofia=[
        L('sofia', 'Kursi itu buat orang yang ngajarin aku kalau usaha kecil juga berarti. Dia belum datang.', 'sedih'),
        L('sofia', 'Tapi aku tetap mau cerita. Karena gambarnya juga tentang menunggu.', 'serius'),
        N('Ruangan jadi sunyi, lalu seseorang di belakang mulai bertepuk tangan paling keras.')]),
]
scene('V7-C04-S-STAGE', 'Di Tengah Presentasi', 'C04', 'sofia', 'galeri_komunitas', [
    N('Di tengah presentasi, mata Sofia kembali ke kursi dekat jendela. Masih kosong.'),
    L('sofia', 'Napas. Satu kalimat lagi.', 'khawatir'),
], choices=STAGE)
insert_after_scene('C04_V464_S_GALLERY', 'V464-C04-S-PRESENT', [S('V7-C04-S-STAGE')])

# The long tail: the vow goes straight to the proof steps (the gallery revisits are skipped)
redirect('C04_V26_VOW', 'C04_V465_A_REFLECT', 'V470_C04_A_PROOF')
redirect('C04_V26_VOW', 'C04_V465_S_REFLECT', 'V470_C04_S_PROOF')

scene('V7-C04-SHARED-FAULT', 'Pesan yang Tidak Terkirim', 'C04', 'shared', 'taman_kota', [
    N('Sofia membuka ponsel untuk mencatat rencana mereka. Jempolnya berhenti di sebuah draf lama.'),
    L('sofia', 'Land... pesan jam acaranya nggak pernah terkirim. Aku janji ngingetin kamu pagi itu.', 'kaget'),
    L('arland', 'Sof, itu nggak bikin aku boleh telat. Aku tahu acaranya Sabtu. Aku yang milih benerin proyektor dulu.', 'serius'),
    L('sofia', 'Aku tahu. Aku cuma nggak mau pura-pura semuanya salah kamu. Aku juga sering nunggu kamu nebak.', 'sedih'),
    L('arland', 'Kalau gitu dua-duanya kita perbaiki. Kamu bilang, aku datang.', 'senyum'),
    L('sofia', 'Setuju. Tanpa kejutan proyektor.', 'tertawa'),
    L('arland', 'Proyektornya udah nyala, lho.', 'malu'),
    L('sofia', 'Simpan buat nonton film. Berdua.', 'jatuh_cinta'),
], flags=['V7_SHARED_FAULT'])
insert_after_scene('C04_V465_SECOND_TALK', 'V465-C04-SECOND-TALK', [S('V7-C04-SHARED-FAULT')])

# =============================================================================== BAB 5
scene('V7-C05-SARI-FADING@arland', 'Wajah yang Hilang', 'C05', 'arland', 'rumah_sari', [
    N('Nenek Sari duduk di depan bingkai kosong. Tehnya sudah dingin.'),
    L('arland', 'Nek? Semua orang nyariin Nenek di persiapan festival.', 'khawatir'),
    L('sari', 'Arland... Nenek lagi mencoba mengingat wajahnya.', 'sedih'),
    L('sari', 'Empat puluh tahun Nenek ingat payungnya. Tapi pagi ini Nenek nggak bisa ingat suaranya.', 'sedih'),
    L('arland', 'Suara Pak Wira?', 'kaget'),
    L('sari', 'Nenek nggak pernah cerita tentang dia ke siapa pun. Mungkin cerita yang nggak pernah diucapkan memang pelan-pelan pergi.', 'sedih'),
    N('Di tas Arland, Memory Book bergetar. Sebuah halaman bertuliskan "W & S" berubah abu-abu di depan matanya.'),
    L('arland', 'The Quiet... nggak cuma ada di dunia mimpi.', 'serius'),
], flags=['V7_C05_SARI_FADING'])
scene('V7-C05-SARI-FADING@sofia', 'Wajah yang Hilang', 'C05', 'sofia', 'rumah_sari', [
    N('Nenek Sari duduk di depan bingkai kosong. Tehnya sudah dingin.'),
    L('sofia', 'Nek? Semua orang nyariin Nenek di persiapan festival.', 'khawatir'),
    L('sari', 'Sofia... Nenek lagi mencoba mengingat wajahnya.', 'sedih'),
    L('sari', 'Empat puluh tahun Nenek ingat payungnya. Tapi pagi ini Nenek nggak bisa ingat suaranya.', 'sedih'),
    L('sofia', 'Suara Pak Wira?', 'kaget'),
    L('sari', 'Nenek nggak pernah cerita tentang dia ke siapa pun. Mungkin cerita yang nggak pernah diucapkan memang pelan-pelan pergi.', 'sedih'),
    N('Di tas Sofia, Memory Book bergetar. Sebuah halaman bertuliskan "W & S" berubah abu-abu di depan matanya.'),
    L('sofia', 'The Quiet... nggak cuma ada di dunia mimpi.', 'serius'),
], flags=['V7_C05_SARI_FADING'])

free = step_('C05_FREE')
acts = free['complete']['actions']
cut = next(i for i, a in enumerate(acts) if a.get('do') == 'warp')
free['complete']['actions'] = acts[:cut] + [{'do': 'toast', 'text': 'Nenek Sari tidak datang hari ini...'}, GO('V7_C05_SARI_FADING')]
rest = acts[cut:]          # warp to the room + route step, run after the visit
new_step('V7_C05_SARI_FADING', 'C05', 'Q_C05_FREE', 'Nenek Sari tidak datang. Jenguk dia di rumahnya (Distrik Perumahan)',
         [it('v7_sari_fading', 'rumah_sari', 430, 260, 'Nenek Sari',
             [{'do': 'music', 'id': 'cinema_quiet'},
              {'do': 'cine', 'v7': True, 'cmds': [{'c': 'bars', 'on': True, 't': 0.5}, {'c': 'mood', 'id': 'cool', 't': 1.4},
                                                  {'c': 'shot', 'focus': 'player', 'zoom': 1.35, 't': 1.4}]},
              S('V7-C05-SARI-FADING@$ROUTE'),
              {'do': 'cine', 'v7': True, 'cmds': [{'c': 'fx', 'kind': 'mist', 'on': 'player', 't': 2.4, 'n': 24, 'block': True},
                                                  {'c': 'bars', 'on': False, 't': 0.5}]},
              {'do': 'item', 'id': 'v7_halaman_wira'}] + rest)],
         tint='#ff9a5a', tintAlpha=0.1)

# Archive of fading memories (new dream map) instead of Clockwork Station + Moonlight Lake
redirect('C05_V26_STARGAZE', 'V471_C05_CLOCK_ENTRY', 'V7_C05_ARCHIVE_ENTRY')
scene('V7-C05-ARCHIVE-OPEN', 'Halaman yang Terbang', 'C05', 'shared', 'starfall_village', [
    N('Bintang jatuh terakhir tidak padam. Ia berubah menjadi selembar halaman abu-abu yang terbang ke timur desa.'),
    L('sofia', 'Itu halaman Nenek Sari! Yang ada tulisan W dan S.', 'kaget'),
    L('arland', 'Kita ikuti. Kalau halamannya hilang di sini, mungkin di dunia nyata juga.', 'serius'),
    L('lumi', 'Di sana ada arsip tempat cerita yang tidak pernah diucapkan menunggu. Dengarkan baik-baik. Jangan menebak.', 'serius'),
])
new_step('V7_C05_ARCHIVE_ENTRY', 'C05', 'Q_V471_C05', 'Ikuti halaman abu-abu ke timur Starfall Village',
         [it('v7_archive_gate', 'starfall_village', 1788, 1112, 'Ikuti halaman abu-abu',
             [{'do': 'music', 'id': 'archive_mystery'}, S('V7-C05-ARCHIVE-OPEN'),
              {'do': 'warp', 'area': 'arsip_memudar', 'x': 800, 'y': 1000, 'dir': 'up'},
              {'do': 'companion', 'on': True}, GO('V7_C05_ARCHIVE_ECHOES')],
             r=95, sprite='items/memory_page.png')])

ECHOES = [
    ('a', 360, 700, 'Gema: kartu perpustakaan', 'Kartu Perpustakaan', [
        N('Kabut membentuk perpustakaan kota, empat puluh tahun lalu. Dua suara terdengar dari dua sisi rak.'),
        L('wira', 'Aku pinjam buku bintang yang sama dengan dia. Biar ada bahan obrolan.'),
        L('sari_muda', 'Dia selalu pinjam buku yang kubaca. Aku pengen dengar buku yang dia suka sendiri.'),
        L('lumi', 'Apa yang sebenarnya Sari harapkan?', 'serius')],
     [('Wira meminjam buku yang sama dengannya', False),
      ('Wira bercerita tentang hal yang ia sukai sendiri', True),
      ('Wira berhenti datang ke perpustakaan', False)]),
    ('b', 800, 520, 'Gema: gazebo hujan', 'Gazebo Hujan', [
        N('Kabut membentuk gazebo taman. Hujan turun tanpa suara.'),
        L('wira', 'Aku telat karena mampir beli payung baru buat dia. Payungnya bagus.'),
        L('sari_muda', 'Waktu dia datang, aku sudah basah. Aku nggak butuh payung baru. Aku butuh dia ada sebelum hujan.'),
        L('lumi', 'Kenapa Sari sedih hari itu?', 'serius')],
     [('Payung barunya jelek', False),
      ('Wira datang terlambat, padahal sudah janji', True),
      ('Hujannya terlalu deras', False)]),
    ('c', 1240, 700, 'Gema: surat yang disimpan', 'Surat yang Disimpan', [
        N('Kabut membentuk meja arsip. Sepucuk amplop bertuliskan "Untuk Sari" tergeletak tanpa perangko.'),
        L('wira', 'Aku sudah tulis maafnya. Tapi kalau kukirim dan dia nggak mau baca... lebih baik kusimpan di arsip dulu.'),
        L('sari_muda', 'Bertahun-tahun aku menunggu dia bilang maaf. Ternyata dia menulisnya, lalu menyimpannya.'),
        L('lumi', 'Apa yang membuat The Quiet tumbuh?', 'serius')],
     [('Cerita yang ditulis tapi tidak pernah diucapkan', True),
      ('Surat yang terlalu panjang', False),
      ('Arsip yang berdebu', False)]),
]
echo_its = []
for key, x, y, label, title, lines, opts in ECHOES:
    ok_flag = 'V7_ECHO_%s_OK' % key.upper()
    done_flag = 'V7_ECHO_%s_DONE' % key.upper()
    choices = []
    for text, right in opts:
        if right:
            choices.append(ch(text, [ok_flag], both=[N('Warna kembali ke gema itu, pelan, seperti tinta yang baru ditulis.')]))
        else:
            choices.append(ch(text, ['V7_ECHO_MISS'], both=[N('Gema itu tetap abu-abu. Mungkin ada yang belum benar-benar didengar.')]))
    scene('V7-C05-ECHO-%s' % key.upper(), title, 'C05', 'shared', 'arsip_memudar', lines, choices=choices)
    echo_its.append(it('v7_echo_' + key, 'arsip_memudar', x, y, label, [
        {'do': 'unflag', 'id': 'V7_ECHO_MISS'}, S('V7-C05-ECHO-%s' % key.upper()),
        IF_FLAG(ok_flag, [{'do': 'flag', 'id': done_flag}, {'do': 'sfx', 'id': 'v471_memory_chime'},
                          {'do': 'count', 'id': 'v7_echoes', 'add': 1}],
                [{'do': 'sfx', 'id': 'soft_wrong'}, {'do': 'toast', 'text': 'Dengarkan lagi kedua suaranya.'}])],
        r=95, hide=done_flag, sprite='items/memory_page.png'))

A_CHOICE = s['scenes']['V471-C05-A-CHOICE']['choices']
S_CHOICE = s['scenes']['V471-C05-S-CHOICE']['choices']
scene('V7-C05-ARCHIVE-QUIET', 'The Quiet', 'C05', 'shared', 'arsip_memudar', [
    N('Ketiga gema berwarna lagi. Di tengah arsip, kabut abu-abu mengumpul jadi sosok tanpa wajah.'),
    L('lumi', 'Itu The Quiet. Ia bukan monster. Ia adalah semua kalimat yang ditahan terlalu lama.', 'serius'),
    L('sofia', 'Kalimat kayak... "aku cuma butuh kamu datang"?', 'sedih'),
    L('arland', 'Atau "maaf, aku lebih sibuk sama kejutanku sendiri".', 'serius'),
    N('Kabut itu tidak menyerang. Ia hanya menunggu, seperti kursi kosong di galeri.'),
])
scene('V7-C05-ARCHIVE-VOW@arland', 'Kalimat Arland', 'C05', 'arland', 'arsip_memudar', [
    L('arland', 'Aku nggak bisa mengulang hari galeri. Tapi aku bisa mengucapkan yang dulu kutahan.', 'serius'),
], choices=A_CHOICE)
scene('V7-C05-ARCHIVE-VOW@sofia', 'Kalimat Sofia', 'C05', 'sofia', 'arsip_memudar', [
    L('sofia', 'Aku nggak mau lagi menyimpan kalimat di saku sampai jadi kabut.', 'serius'),
], choices=S_CHOICE)
scene('V7-C05-ARCHIVE-PAGE', 'Halaman yang Belum Selesai', 'C05', 'shared', 'arsip_memudar', [
    N('Kabut menipis. Halaman "W & S" melayang turun ke tangan mereka. Sebagian tulisannya kembali, sebagian masih abu-abu.'),
    L('lumi', 'Separuhnya sudah pulang. Separuhnya lagi hanya bisa diselesaikan oleh orang yang mau bercerita.', 'senyum'),
    L('sofia', 'Kita bawa ke Nenek Sari?', 'penasaran'),
    L('lumi', 'Nanti. Jembatan kenangan kalian sendiri juga masih retak. Pulihkan dulu, lalu ikuti halamannya.', 'serius'),
], flags=['V7_C05_ARCHIVE_DONE'])
new_step('V7_C05_ARCHIVE_ECHOES', 'C05', 'Q_V471_C05', 'Dengarkan tiga gema Wira dan Sari, lalu jawab dengan jujur',
         echo_its, counter='v7_echoes', counterMax=3, tint='#8a8aa8', tintAlpha=0.22,
         complete={'counter': 'v7_echoes', 'count': 3, 'actions': [
             {'do': 'music', 'id': 'score_quiet_truth_v480'},
             film(['V7-C05-ARCHIVE-QUIET', 'V7-C05-ARCHIVE-VOW@$ROUTE'], 'dream', ambient='sparkles', pair=None,
                  finale='restore', orbit=-12),
             GO('V7_C05_ARCHIVE_PAGE')]})
new_step('V7_C05_ARCHIVE_PAGE', 'C05', 'Q_V471_C05', 'Ambil halaman Wira dan Sari di tengah arsip',
         [it('v7_archive_page', 'arsip_memudar', 800, 640, 'Halaman W & S',
             [S('V7-C05-ARCHIVE-PAGE'), {'do': 'item', 'id': 'v471_reflection'}, {'do': 'sfx', 'id': 'v472_memory_glint'},
              {'do': 'warp', 'area': 'memory_bridge', 'x': 180, 'y': 1090, 'dir': 'up'},
              GO('V471_C05_BRIDGE_FRAGMENTS')], r=95, sprite='items/memory_page.png')])

# =============================================================================== BAB 6
scene('V7-C06-ERASE', 'Cermin Keempat', 'C06', 'shared', 'hall_of_tomorrow', [
    N('Saat tiga cermin padam, cermin keempat menyala sendiri. Di dalamnya: galeri, tepuk tangan, dan Arland duduk di kursi dekat jendela.'),
    L('lumi', 'Balai ini bisa mengganti satu halaman. Kursi itu bisa terisi. Hari hujan itu tidak perlu terjadi.', 'serius'),
    L('arland', 'Jadi aku nggak pernah telat...', 'sedih'),
    L('sofia', 'Dan aku nggak pernah belajar bilang apa yang aku butuhkan.', 'serius'),
], choices=[
    ch('"Hari itu milik kami. Jangan diganti."', ['V7_ERASE_REFUSE_OURS'], both=[
        L('arland', 'Itu hari terburukku. Tapi itu juga hari aku mulai benar-benar mendengar.', 'serius'),
        L('sofia', 'Jangan diganti. Biar kursinya tetap kosong di halaman itu.', 'senyum')]),
    ch('"Kalau dihapus, kami lupa caranya belajar."', ['V7_ERASE_REFUSE_LEARN'], both=[
        L('sofia', 'Kita jadi orang yang sekarang karena hari itu.', 'serius'),
        L('arland', 'Aku nggak mau versi aku yang nggak pernah salah. Dia nggak akan pernah belajar.', 'serius')]),
    ch('Tutup cermin itu bersama, tanpa kata-kata', ['V7_ERASE_REFUSE_TOGETHER'], both=[
        N('Dua tangan menutup cermin itu bersamaan. Pantulan kursi yang terisi memudar.'),
        L('sofia', 'Sudah.', 'lega'),
        L('arland', 'Sudah.', 'lega')]),
], flags=['V7_ERASE_REFUSED'])
scene('V7-C06-STAGE-CONTINUE', 'Suara yang Bergetar', 'C06', 'sofia', 'hall_of_tomorrow', [
    L('sofia', 'Di cermin itu aku nggak gemetar sama sekali. Tapi aku lebih bangga sama aku yang gemetar dan tetap selesai.', 'senyum')])
scene('V7-C06-STAGE-SHORT', 'Turun Lebih Cepat', 'C06', 'sofia', 'hall_of_tomorrow', [
    L('sofia', 'Di cermin itu presentasiku panjang dan sempurna. Padahal berhenti lebih cepat juga boleh.', 'senyum')])
scene('V7-C06-STAGE-CHAIR', 'Kursi yang Diceritakan', 'C06', 'sofia', 'hall_of_tomorrow', [
    L('sofia', 'Kalau hari itu dihapus, cerita yang paling jujur yang pernah aku ucapkan di depan orang juga ikut hilang.', 'serius')])
futures = step_('V472_C06_FUTURES')
fa = futures['complete']['actions']
i = next(i for i, a in enumerate(fa) if plays(a, 'V472-C06-THREE-FUTURES'))
fa[i + 1:i + 1] = [S('V7-C06-ERASE'),
                   IF_FLAG('V7_S_STAGE_CONTINUE', [S('V7-C06-STAGE-CONTINUE')]),
                   IF_FLAG('V7_S_STAGE_SHORT', [S('V7-C06-STAGE-SHORT')]),
                   IF_FLAG('V7_S_STAGE_CHAIR', [S('V7-C06-STAGE-CHAIR')])]

# Hall exit -> the rainy day forty years ago, then back to the Tree
promise = step_('V472_C06_PROMISE')
ret = next(x for x in promise['interactables'] if x['id'] == 'v472_return')
ret['label'] = 'Ikuti halaman Wira dan Sari'
acts = ret['actions']
w = next(i for i, a in enumerate(acts) if a.get('do') == 'warp')
acts[w:] = [{'do': 'warp', 'area': 'kenangan_gazebo', 'x': 800, 'y': 1000, 'dir': 'up'}, GO('V7_C06_GAZEBO_BENCH')]

scene('V7-C06-GAZEBO-ARRIVE', 'Hujan yang Sama', 'C06', 'shared', 'kenangan_gazebo', [
    N('Halaman abu-abu menarik mereka ke sebuah taman yang mereka kenal, tapi lebih muda. Lampunya kuning. Hujan turun.'),
    L('sofia', 'Ini Taman Kota... empat puluh tahun lalu.', 'kaget'),
    L('arland', 'Gazebonya sama. Bangkunya sama. Bahkan hujannya kerasa sama.', 'serius'),
])
scene('V7-C06-GAZEBO-BENCH', 'Sari Menunggu', 'C06', 'shared', 'kenangan_gazebo', [
    N('Di bangku dekat gazebo, bayangan cahaya seorang gadis duduk memeluk tas. Rambutnya basah.'),
    L('sari_muda', 'Dia bilang jam empat. Ini sudah jam lima.'),
    L('sari_muda', 'Kalau dia datang, aku harus bilang apa? Marah? Pura-pura nggak apa-apa?'),
    L('sofia', 'Dia persis aku di galeri. Lihat pintu terus. Nyiapin kalimat yang nggak jadi diucapkan.', 'sedih'),
])
scene('V7-C06-GAZEBO-PATH', 'Wira Berlari', 'C06', 'shared', 'kenangan_gazebo', [
    N('Dari jalan setapak, bayangan seorang pemuda berlari membawa payung baru yang masih berlabel harga.'),
    L('wira', 'Payungnya harus yang paling bagus. Biar dia tahu aku serius.'),
    L('wira', 'Telat sejam... nggak apa-apa, kan? Yang penting payungnya bagus.'),
    L('arland', 'Itu aku. Itu persis aku sama proyektornya.', 'sedih'),
])
scene('V7-C06-TELL', 'Dua Sisi, Diucapkan', 'C06', 'shared', 'kenangan_gazebo', [
    N('Di gazebo, dua bayangan berdiri berhadapan dan tidak bicara. Halaman "W & S" di tangan mereka bergetar.'),
    L('lumi', 'Mereka tidak pernah menyelesaikan percakapan ini. Kalian bisa menceritakan kisah kalian sendiri, supaya mereka mendengar jalan keluarnya.', 'serius'),
    L('arland', 'Aku pernah telat juga. Karena kejutan. Aku pikir itu bukti sayang.', 'serius'),
    L('sofia', 'Dan aku pernah diam. Karena takut kalimatku kedengaran menuntut.', 'serius'),
], choices=[
    ch('"Yang dia butuhkan bukan payungnya. Tapi kamu, sebelum hujan."', ['V7_TELL_PRESENCE'], both=[
        L('arland', 'Datang dulu. Kejutannya belakangan. Atau nggak usah sama sekali.', 'serius')]),
    ch('"Bilang aja, walaupun kedengarannya menuntut."', ['V7_TELL_VOICE'], both=[
        L('sofia', 'Kalimat yang ditahan nggak bikin dia ngerti. Cuma bikin dia nebak.', 'serius')]),
    ch('"Kalian masih bisa duduk di bangku yang sama."', ['V7_TELL_SIT'], both=[
        L('arland', 'Nggak usah langsung baikan. Duduk dulu aja. Berdua.', 'senyum'),
        L('sofia', 'Kami juga mulai dari situ.', 'senyum')]),
])
scene('V7-C06-PAGE-SAVED', 'Halaman yang Pulang', 'C06', 'shared', 'kenangan_gazebo', [
    N('Bayangan pemuda itu menurunkan payungnya. Label harganya jatuh ke genangan.'),
    L('wira', 'Sari, maaf. Aku telat karena sibuk dengan caraku sendiri. Aku di sini sekarang.'),
    L('sari_muda', 'Kamu basah.'),
    L('wira', 'Kamu juga. Mau basah bareng sampai rumah?'),
    N('Dua bayangan berjalan di bawah satu payung yang kebesaran. Hujan berhenti. Halaman "W & S" kembali berwarna penuh.'),
    N('Di sudut halaman, sebuah foto kecil muncul: dua orang muda di gazebo, basah, tertawa.'),
    L('sofia', 'Ini foto yang hilang dari bingkai Nenek Sari.', 'jatuh_cinta'),
    L('arland', 'Kita bawa pulang. Nenek Sari harus dengar ceritanya dari awal.', 'senyum'),
], flags=['V7_WIRA_PAGE_SAVED'])

new_step('V7_C06_GAZEBO_BENCH', 'C06', 'Q_V472_C06', 'Dekati bangku dekat gazebo',
         [it('v7_gz_bench', 'kenangan_gazebo', 560, 640, 'Bangku tempat Sari menunggu',
             [{'do': 'music', 'id': 'rain_lullaby'}, short_cine('couple', 1.1, ('Empat Puluh Tahun Lalu', 'Taman Kota, hari hujan')),
              S('V7-C06-GAZEBO-ARRIVE'), S('V7-C06-GAZEBO-BENCH'), {'do': 'companion', 'on': True}, GO('V7_C06_GAZEBO_PATH')],
             r=90, sprite='items/lantern_small.png')],
         weather='rain', tint='#d2b07a', tintAlpha=0.2, enterArea={'area': 'kenangan_gazebo', 'actions': [{'do': 'companion', 'on': True}]})
new_step('V7_C06_GAZEBO_PATH', 'C06', 'Q_V472_C06', 'Lihat siapa yang berlari dari jalan setapak',
         [it('v7_gz_path', 'kenangan_gazebo', 1150, 820, 'Jalan setapak', [S('V7-C06-GAZEBO-PATH'), GO('V7_C06_GAZEBO_TELL')],
             r=90, sprite='items/lantern_small.png')], weather='rain', tint='#d2b07a', tintAlpha=0.2)
new_step('V7_C06_GAZEBO_TELL', 'C06', 'Q_V472_C06', 'Ceritakan kisah kalian di gazebo untuk Wira dan Sari',
         [it('v7_gz_tell', 'kenangan_gazebo', 800, 600, 'Gazebo', [
             {'do': 'music', 'id': 'score_open_page_v480'},
             film(['V7-C06-TELL'], 'cool', end_mood='dream', ambient='rainlight', pair=None, finale=None, orbit=10, zoom=1.15),
             {'do': 'music', 'id': 'eternal_promise'},
             film(['V7-C06-PAGE-SAVED'], 'dream', end_mood='warm', ambient='sparkles', pair='hug', finale='restore', orbit=-14),
             {'do': 'item', 'id': 'v7_foto_wira'},
             {'do': 'warp', 'area': 'eternal_garden', 'x': 1200, 'y': 888, 'dir': 'up'},
             GO('C06_LETTER')], r=100, sprite='items/memory_page.png')], weather='rain', tint='#d2b07a', tintAlpha=0.2)

# =============================================================================== EPILOG
scene('V7-EPI-SARI-REMEMBER', 'Suaranya', 'EPI', 'shared', 'taman_kota', [
    N('Arland dan Sofia menyerahkan foto kecil dari halaman itu. Nenek Sari memandanginya lama sekali.'),
    L('sari', 'Payungnya kebesaran. Dia beli yang paling mahal, lalu kami tetap basah.', 'tertawa'),
    L('sari', 'Nenek ingat suaranya sekarang. Dia nyanyi keroncong sepanjang jalan pulang, fals sekali.', 'senang'),
    L('sari', 'Mampir ke rumah, ya. Bingkai itu sudah terlalu lama kosong.', 'senyum'),
])
insert_after_scene('EPI_SARI_CLOSURE', 'Q-EPI-SARI@$ROUTE', [S('V7-EPI-SARI-REMEMBER')])
scene('V7-EPI-FRAME', 'Bingkai yang Terisi', 'EPI', 'shared', 'rumah_sari', [
    N('Nenek Sari memasukkan foto kecil itu ke bingkai kayu. Ukurannya pas, seolah bingkainya dibuat untuk menunggu foto ini.'),
    L('sari', 'Wira, ini Arland dan Sofia. Mereka yang membawamu pulang.', 'senyum'),
    L('sofia', 'Nek, ceritain lagi soal payungnya. Dari awal.', 'senang'),
    L('sari', 'Dari awal? Wah, itu panjang. Duduk, Nenek buatkan teh melati.', 'tertawa'),
    N('Sore itu tidak ada yang terburu-buru. Radio kayu memutar lagu hujan, dan tiga orang bergantian bercerita.'),
], flags=['V7_EPI_FRAME'])
epi = step_('EPI_FREE')
epi['interactables'].append(it('v7_epi_frame', 'rumah_sari', 470, 160, 'Pasang foto di bingkai Nenek Sari',
                               [{'do': 'music', 'id': 'score_lake_coda_v480'},
                                film(['V7-EPI-FRAME'], 'memory', end_mood='warm', ambient='fireflies', pair='lean', finale='glow', orbit=8),
                                {'do': 'removeItem', 'id': 'v7_foto_wira'}],
                               r=80, when={'notFlags': ['V7_EPI_FRAME']}, sprite='items/photo_small.png'))

# =============================================================================== SIDE QUEST: LAGU HUJAN
# Changes the world: once the tape is fixed, the radio in Nenek Sari's house plays the rain song.
q['sideQuests'].append({'id': 'SQ_V7_KASET', 'title': 'Lagu Hujan',
                        'desc': 'Kaset keroncong di radio Nenek Sari kusut. Minta Bang Juna di Arcade Bintang memperbaikinya, lalu putar lagi di rumah Nenek Sari.',
                        'startFlag': 'SQ_V7_KASET_START', 'doneFlag': 'SQ_V7_KASET_DONE', 'chapter': 'C03'})
item('v7_kaset', 'Kaset "Lagu Hujan"', 'items/music_box.png', 'Kaset keroncong tulisan tangan. Pitanya sudah digulung ulang oleh Bang Juna.')
scene('V7-SQ-KASET-1', 'Radio yang Tersendat', 'SIDE', 'shared', 'rumah_sari', [
    N('Radio kayu berbunyi "krrk", lalu diam. Pita kaset di dalamnya kusut.'),
    L('sari', 'Ah, kasetnya macet lagi. Itu lagu kesukaan... seseorang.', 'sedih'),
    L('sari', 'Bang Juna di arcade pintar membetulkan mesin. Tapi Nenek nggak enak merepotkan.', 'senyum'),
])
scene('V7-SQ-KASET-2', 'Tangan Bang Juna', 'SIDE', 'shared', 'arcade', [
    L('juna', 'Kaset tahun delapan puluhan? Wah, barang langka. Sini, gulung pakai pensil, kayak zaman dulu.', 'senang'),
    N('Bang Juna memutar pita dengan pensil, pelan dan sabar, sampai rapi kembali.'),
    L('juna', 'Beres. Bilang ke Nenek Sari, jangan diputar pas hujan petir. Radionya sudah tua.', 'tertawa'),
])
scene('V7-SQ-KASET-3', 'Lagu Hujan', 'SIDE', 'shared', 'rumah_sari', [
    N('Radio berdesis sebentar, lalu suara keroncong mengisi ruangan. Suaranya agak fals di nada tinggi.'),
    L('sari', 'Itu bukan penyanyinya. Itu dia. Dia merekam dirinya sendiri waktu muda.', 'kaget'),
    L('sari', 'Nenek sampai lupa kalau suaranya pernah disimpan di sini.', 'senang'),
    N('Mochi bangun dari bantalnya dan duduk di dekat radio, seperti ikut mendengarkan.'),
], flags=['SQ_V7_KASET_DONE'])
q['side'] += [
    it('v7_kaset_start', 'rumah_sari', 520, 300, 'Radio kayu', [S('V7-SQ-KASET-1'), {'do': 'flag', 'id': 'SQ_V7_KASET_START'},
       {'do': 'toast', 'text': 'Misi sampingan: Lagu Hujan'}], r=56,
       when={'flags': ['V7_C03_SARI_VISITED'], 'notFlags': ['SQ_V7_KASET_START']}),
    it('v7_kaset_fix', 'arcade', 350, 410, 'Minta Bang Juna memperbaiki kaset', [S('V7-SQ-KASET-2'), {'do': 'item', 'id': 'v7_kaset'},
       {'do': 'flag', 'id': 'SQ_V7_KASET_FIXED'}, {'do': 'sfx', 'id': 'sparkle'}], r=60,
       when={'flags': ['SQ_V7_KASET_START'], 'notFlags': ['SQ_V7_KASET_FIXED']}),
    it('v7_kaset_play', 'rumah_sari', 520, 300, 'Putar kaset di radio', [{'do': 'music', 'id': 'rain_lullaby'}, S('V7-SQ-KASET-3'),
       {'do': 'removeItem', 'id': 'v7_kaset'}, {'do': 'sfx', 'id': 'quest_complete'}], r=56,
       when={'items': ['v7_kaset'], 'notFlags': ['SQ_V7_KASET_DONE']}),
]
memory('m_v7_kaset', 'C03', 'SQ_V7_KASET_DONE', 'items/music_box.png', 'Lagu Hujan',
       'Suara yang disimpan di pita kaset ternyata tidak pernah benar-benar hilang.')
m['areas']['rumah_sari']['examine'].append(ex('v7_radio_after', 520, 300, 'Radio kayu',
    [N('Radio memutar lagu hujan pelan-pelan. Suara Wira muda, fals di nada tinggi.')], when={'flags': ['SQ_V7_KASET_DONE']}))
for e in m['areas']['rumah_sari']['examine']:
    if e['id'] == 'v7_radio':
        e['when'] = {'notFlags': ['SQ_V7_KASET_DONE']}

# =============================================================================== LESS PREACHING
TRIM = {
    'C04-X02': {'Jangan sedih. Kabut itu bukan hukuman. Ia cuma tanda bahwa ada yang perlu dibicarakan.':
                'Jangan sedih dulu. Lenteranya masih hangat. Artinya masih bisa dinyalakan.'},
    'C04-X03': {'Memulihkan cahaya bukan berarti menghapus hari yang menyakitkan.': None},
    'C04-A02': {'Kalau kamu minta maaf, coba dengerin dulu apa yang dia rasakan, ya.':
                'Dia keluar tanpa payung. Kalau mau nyusul, bawa ini.'},
    'C04-S-LIBRARY': {'Berkata jujur dengan lembut juga bentuk keberanian, Sofia.':
                      'Kursi baca di pojok itu kosong. Duduklah dulu. Nanti Ibu bawakan teh.'},
    'V471-C05-QUIET-REVEAL': {'Tidak. Dan niat Arland tidak menghapus dampak tindakannya.': 'Tidak. Dua-duanya benar-benar terjadi.'},
    'Q-C06-REVEAL@arland': {'Pak Wira meninggalkan petunjuk bukan untuk mencari siapa yang salah.': None,
                            'Tapi untuk mengingatkan bahwa hubungan perlu diberi ruang, bahkan ketika salah satu sedang diam.': None},
    'Q-C06-REVEAL@sofia': {'Pak Wira meninggalkan petunjuk bukan untuk mencari siapa yang salah.': None,
                           'Tapi untuk mengingatkan bahwa hubungan perlu diberi ruang, bahkan ketika salah satu sedang diam.': None},
    'V468-C02-A-REPLY': {'Arland menyimpan ponsel. Ajakan yang baik tidak mengikat siapa pun.': 'Arland menyimpan ponsel, lalu mengambilnya lagi untuk mengecek jam.'},
    'V469-C03-HALF-A': {'Pemain memilih cara Arland menyimpan kalimat yang belum selesai, bukan menebak isi surat.': None},
}
for sid, rep in TRIM.items():
    sc = scene_(sid)
    out = []
    for ln in sc['lines']:
        if ln['t'] in rep:
            if rep[ln['t']] is None:
                continue
            ln = dict(ln, t=rep[ln['t']])
        out.append(ln)
    if len(out) == len(sc['lines']) and all(a['t'] == b['t'] for a, b in zip(out, sc['lines'])):
        raise SystemExit('trim had no effect: ' + sid)
    sc['lines'] = out

# =============================================================================== OBJECTIVE TEXT
META = [(' (boleh dicoba ulang)', ''), (' yang boleh dibatalkan dan dicoba ulang', ''), (' (0/3)', ''),
        ('Aktivitas pribadi Arland (route lain)', 'Susun foto dan perbaiki bingkai di meja Arland'),
        ('Aktivitas pribadi Sofia (route lain)', 'Susun halaman scrapbook')]
for st in q['steps']:
    o = st.get('objective', {})
    for r in ('arland', 'sofia'):
        t = o.get(r, '')
        nt = t
        for a, b in META:
            nt = nt.replace(a, b)
        if nt != t:
            step_(st['id'])['objective'][r] = nt

# =============================================================================== write
s['meta']['storyV7'] = 'v7.0: jadian di Bab 2, rahasia proyektor, Rumah Nenek Sari, andil Sofia, Arsip yang Memudar, Gazebo 40 tahun lalu'
OP.write_text(json.dumps({'quests': ORIG_Q, 'story': ORIG_S, 'maps': ORIG_M}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
QP.write_text(json.dumps(q, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
SP.write_text(json.dumps(s, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
MP.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
BP.write_text(json.dumps(mb, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('v7: steps +%d, scenes +%d, touched steps %d, touched scenes %d' % (
    sum(x['id'].startswith('V7_') for x in q['steps']), sum(k.startswith('V7-') for k in s['scenes']),
    len(ORIG_Q['steps']), len(ORIG_S['scenes'])))
