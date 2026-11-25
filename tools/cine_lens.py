"""Adds the film-lens commands (mood, crane, orbit, angle) to the main story cutscenes in
assets/data/quests.json. Idempotent: commands it added carry "lens": true and are replaced on rerun.
Run: python3 tools/cine_lens.py"""
import json

PATH = 'assets/data/quests.json'
q = json.load(open(PATH, encoding='utf-8'))


def cine_at(step_idx, inter=None, act=None, key='interactables'):
    s = q['steps'][step_idx]
    if inter is None:
        return s[key][act] if key == 'onStart' else s[key]['actions'][act]
    return s['interactables'][inter]['actions'][act]


def L(**c):
    c['lens'] = True
    return c


def after_first(cmds, kind, new):
    """Insert new commands right after the first command of this kind (or at the start)."""
    i = next((k + 1 for k, c in enumerate(cmds) if c['c'] == kind), 0)
    cmds[i:i] = new


def before_first(cmds, pred, new):
    i = next((k for k, c in enumerate(cmds) if pred(c)), len(cmds))
    cmds[i:i] = new


PLAN = []


def plan(where, fn):
    PLAN.append((where, fn))


# Prolog morning in the bedroom: warm sunlight look
plan((2, None, 0, 'onStart'), lambda c: after_first(c, 'bars', [L(c='mood', id='warm', t=1.5)]))

# Arriving at the plaza: establishing crane over the town, warm
plan((4, None, 1, 'enterArea'), lambda c: after_first(c, 'bars', [
    L(c='mood', id='warm', a=0.7, t=2.0), L(c='crane', t=4.0, zoom=0.95, block=True)]))


def meet(c):
    # first meeting: cut to a high wide angle and glide down, then a slow orbit while gifts change hands
    after_first(c, 'bars', [L(c='mood', id='warm', t=2.0), L(c='crane', t=3.6, zoom=1.15, block=True)])
    before_first(c, lambda x: x['c'] == 'pose' and x.get('pose') == 'give', [L(c='orbit', deg=14, t=7.0), L(c='dof', a=0.9, t=1.2)])
    before_first(c, lambda x: x['c'] == 'fx' and x.get('kind') == 'glow', [L(c='angle', yaw=0, t=1.6), L(c='dof', a=0.35, t=1.0)])


plan((5, 0, 0), meet)
plan((6, 0, 0), lambda c: after_first(c, 'bars', [L(c='mood', id='dream', t=2.5), L(c='orbit', deg=-10, t=8.0)]))
plan((6, 0, 5), lambda c: after_first(c, 'cam', [L(c='mood', id='dream', t=1.0), L(c='crane', t=4.5, zoom=1.0)]))
plan((7, None, 0, 'complete'), lambda c: after_first(c, 'bars', [L(c='mood', id='dream', t=1.5), L(c='orbit', deg=12, t=6.0)]))
plan((22, 0, 0), lambda c: after_first(c, 'bars', [L(c='mood', id='dream', a=0.8, t=1.5), L(c='dof', a=0.9, t=2.0)]))


def pier(c):
    after_first(c, 'bars', [L(c='mood', id='warm', t=2.5), L(c='crane', t=4.0, zoom=1.1)])
    before_first(c, lambda x: x['c'] == 'fx' and x.get('kind') == 'stars', [L(c='mood', id='night', a=0.7, t=3.0), L(c='orbit', deg=-16, t=9.0)])


plan((31, 0, 8), pier)
plan((57, 0, 0), lambda c: after_first(c, 'bars', [L(c='mood', id='cool', t=2.0), L(c='angle', pitch=26, t=3.0)]))
plan((64, 0, 0), lambda c: after_first(c, 'bars', [L(c='mood', id='memory', a=0.8, t=2.0), L(c='dof', a=1.0, t=2.0)]))


def get_cmds(where):
    s = q['steps'][where[0]]
    if len(where) == 4:
        node = s[where[3]]
        node = node['actions'] if isinstance(node, dict) else node
        return node[where[2]]['cmds']
    return s['interactables'][where[1]]['actions'][where[2]]['cmds']


n = 0
for where, fn in PLAN:
    cmds = get_cmds(where)
    cmds[:] = [c for c in cmds if not c.get('lens')]
    fn(cmds)
    for c in cmds:
        if 'from_' in c:
            del c['from_']
    n += sum(1 for c in cmds if c.get('lens'))
open(PATH, 'w', encoding='utf-8').write(json.dumps(q, ensure_ascii=False, indent=2) + '\n')
print('lens commands:', n, 'in', len(PLAN), 'cutscenes')
