"""Story cutscenes for the moments that only had plain dialogue, and longer versions of the short
title-card cutscenes. Edits assets/data/quests.json and is idempotent: every cutscene it builds is
marked "made": "story_cines" and is turned back into the original actions before rebuilding.
Dialogue always comes from the existing story scenes (the cutscene plays them with "say"), so the
story text and its choices/flags stay exactly the same.
Run: python3 tools/story_cines.py   (then tools/cine_lens.py is not needed again)"""
import copy
import json

PATH = 'assets/data/quests.json'
TAG = 'story_cines'
q = json.load(open(PATH, encoding='utf-8'))
STEPS = {s['id']: s for s in q['steps']}


# ---- undo previous runs ---------------------------------------------------------------------------
def undo(o):
    if isinstance(o, dict):
        for v in o.values():
            undo(v)
    elif isinstance(o, list):
        i = 0
        while i < len(o):
            a = o[i]
            if isinstance(a, dict) and a.get('made') == TAG:
                o[i:i + 1] = a['orig']
                continue
            undo(a)
            i += 1


undo(q['steps'])


def made(cmds, orig):
    return {'do': 'cine', 'cmds': cmds, 'made': TAG, 'orig': orig}


# ---- film recipe ----------------------------------------------------------------------------------
def film(scenes, mood, *, open='crane', zoom=1.2, focus='couple', pair=None, ambient=None, finale=None,
         orbit=12, end_mood=None, caption=None, from_short=None):
    c = [{'c': 'bars', 'on': True, 't': 0.5}, {'c': 'mood', 'id': mood, 't': 1.6}]
    if from_short:       # keep the original title card's caption/fx
        c += [x for x in from_short if x['c'] not in ('bars', 'shot', 'wait')]
    c.append({'c': 'shot', 'focus': focus, 'zoom': zoom, 't': 0, 'bars': False})
    if open == 'crane':
        c.append({'c': 'crane', 't': 3.6, 'zoom': zoom, 'block': True})
    else:
        c.append({'c': 'shot', 'focus': focus, 'zoom': zoom + 0.08, 't': 1.4, 'bars': False})
    if caption:
        c.append({'c': 'caption', 'text': caption[0], 'sub': caption[1], 't': 3.0})
    if ambient:
        c.append({'c': 'fx', 'kind': ambient, 'on': 'player', 't': 14.0, 'n': 36})
    if orbit:
        c.append({'c': 'orbit', 'deg': orbit, 't': 12.0})
    c.append({'c': 'dof', 'a': 0.8, 't': 1.5})
    for s in scenes:
        c.append({'c': 'say', 'scene': s})
    if end_mood:
        c.append({'c': 'mood', 'id': end_mood, 't': 2.0})
    c.append({'c': 'shot', 'focus': focus, 'zoom': zoom + 0.16, 't': 1.6, 'bars': False, 'async': True})
    if pair:
        c.append({'c': 'pair', 'kind': pair, 't': 2.4})
    else:
        c += [{'c': 'emote', 'who': 'player', 'e': 'heart', 't': 1.6}, {'c': 'emote', 'who': 'partner', 'e': 'heart', 't': 1.6}]
    if finale:
        c.append({'c': 'fx', 'kind': finale, 'on': 'player', 't': 2.6, 'block': True})
    c += [{'c': 'wait', 't': 0.6}, {'c': 'angle', 'yaw': 0, 't': 1.0}, {'c': 'dof', 'a': 0.35, 't': 0.8},
          {'c': 'bars', 'on': False, 't': 0.6}]
    return c


def wrap(step, scene_ids, mood, *, it=None, **kw):
    """Replace the step's plain 'scene' actions for these ids (and any directly following scene
    actions in the list) with one cutscene that plays them."""
    s = STEPS[step]
    lists = [x['actions'] for x in s.get('interactables', []) if it is None or x['id'] == it]
    for acts in lists:
        for i, a in enumerate(acts):
            if a.get('do') == 'scene' and a.get('id') == scene_ids[0]:
                j = i + 1
                ids = [a['id']]
                while j < len(acts) and acts[j].get('do') == 'scene' and acts[j]['id'] in scene_ids:
                    ids.append(acts[j]['id']); j += 1
                acts[i:j] = [made(film(ids, mood, **kw), copy.deepcopy(acts[i:j]))]
                return 1
    raise SystemExit('scene not found: %s %s' % (step, scene_ids))


n_new = 0
n_new += wrap('C02_DATE', ['V468-C02-GAZEBO'], 'warm', it='gazebo', pair='lean', ambient='petals', orbit=10)
n_new += wrap('C02_SUNSET', ['C02-X04'], 'warm', pair='lean', ambient='fireflies', finale='glow', orbit=-14, zoom=1.15)
n_new += wrap('C03_COOK', ['C03-X01'], 'warm', open='shot', pair='highfive', finale='sparkles', orbit=0, zoom=1.15)
n_new += wrap('C03_PICNIC', ['C03-X02', 'V469-C03-PICNIC-REFLECTION'], 'warm', pair='lean', ambient='petals', finale='hearts', orbit=14)
n_new += wrap('C04_V26_RECONCILE', ['V26-C04-ME@$ROUTE'], 'cool', it='v26_c04_gazebo', pair='hug', ambient='rainlight', end_mood='warm', orbit=-10)
n_new += wrap('C05_V26_STARGAZE', ['V26-C05-STAR'], 'night', pair='lean', ambient='stars', finale='aurora', orbit=16, zoom=1.1)
n_new += wrap('V471_C05_BRIDGE_RESTORE', ['V471-C05-BRIDGE-STEP'], 'dream', it='v471_bridge_step', pair='handwalk', ambient='sparkles', finale='restore', orbit=-12)
n_new += wrap('V471_C05_FINAL_WALK', ['V471-C05-HANDOFF'], 'dream', open='shot', pair='handwalk', ambient='fireflies', finale='beam', orbit=10)
n_new += wrap('C06_TREE', ['C06-X02'], 'dream', pair='hug', ambient='petals', finale='lanterns', orbit=14, zoom=1.1)
n_new += wrap('EPI_SARI_CLOSURE', ['Q-EPI-SARI@$ROUTE'], 'memory', open='shot', ambient='sparkles', end_mood='warm', finale='glow', orbit=8)
n_new += wrap('V473_EPI_LAKE_MEMORIES', ['V473-EPI-LAKE-PHOTO'], 'memory', it='v473_lake_photo', pair='lean', ambient='fireflies', end_mood='warm', orbit=-12)

# Rain Garden: the fifth light completes the set -> the lanterns rise together
lights = STEPS['C04_LIGHTS']['complete']['actions']
lights[0:0] = [made([
    {'c': 'bars', 'on': True, 't': 0.5}, {'c': 'mood', 'id': 'dream', 't': 1.5},
    {'c': 'shot', 'focus': 'couple', 'zoom': 1.05, 't': 0, 'bars': False}, {'c': 'crane', 't': 3.2, 'zoom': 1.05, 'block': True},
    {'c': 'sfx', 'id': 'lantern'}, {'c': 'fx', 'kind': 'lanterns', 'on': 'player', 't': 6.0, 'n': 18},
    {'c': 'orbit', 'deg': 16, 't': 7.0}, {'c': 'fx', 'kind': 'restore', 'on': 'player', 't': 2.4, 'block': True},
    {'c': 'emote', 'who': 'player', 'e': 'heart', 't': 1.6}, {'c': 'emote', 'who': 'partner', 'e': 'heart', 't': 1.6},
    {'c': 'shot', 'focus': 'couple', 'zoom': 1.25, 't': 2.0}, {'c': 'wait', 't': 1.0},
    {'c': 'angle', 'yaw': 0, 't': 1.0}, {'c': 'bars', 'on': False, 't': 0.6}], [])]
n_new += 1


# ---- longer versions of the short title-card cutscenes (chapter 2 onwards) -------------------------
LONG_CH = {'C02', 'C03', 'C04', 'C05', 'C06', 'EPI'}
MOOD = {'C02': 'warm', 'C03': 'warm', 'C04': 'cool', 'C05': 'night', 'C06': 'dream', 'EPI': 'memory'}
AMBIENT = {'C02': 'petals', 'C03': 'fireflies', 'C04': 'rainlight', 'C05': 'stars', 'C06': 'sparkles', 'EPI': 'fireflies'}
n_long = 0


def lengthen(acts, chapter):
    global n_long
    i = 0
    while i < len(acts):
        a = acts[i]
        cm = a.get('cmds') if a.get('do') == 'cine' and 'made' not in a else None
        if cm and len(cm) <= 6 and cm[0].get('c') == 'bars' and any(x['c'] in ('shot', 'cam') for x in cm):
            j = i + 1
            ids = []
            while j < len(acts) and acts[j].get('do') == 'scene':
                ids.append(acts[j]['id']); j += 1
            if ids:
                focus = next((x.get('focus', 'couple') for x in cm if x['c'] == 'shot'), 'couple')
                cmds = film(ids, MOOD[chapter], open='crane', focus=focus, ambient=AMBIENT[chapter],
                            orbit=-10 if n_long % 2 else 10, from_short=cm, finale='glow')
                acts[i:j] = [made(cmds, copy.deepcopy(acts[i:j]))]
                n_long += 1
        elif isinstance(a, dict):
            for k in ('then', 'else'):
                if isinstance(a.get(k), list):
                    lengthen(a[k], chapter)
        i += 1


for s in q['steps']:
    if s.get('chapter') not in LONG_CH:
        continue
    for it in s.get('interactables', []):
        lengthen(it.get('actions', []), s['chapter'])
    for key in ('complete', 'enterArea'):
        if isinstance(s.get(key), dict):
            lengthen(s[key].get('actions', []), s['chapter'])

open(PATH, 'w', encoding='utf-8').write(json.dumps(q, ensure_ascii=False, indent=2) + '\n')
print('new cutscenes:', n_new, ' lengthened:', n_long)
