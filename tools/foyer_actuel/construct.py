"""Construction plan: from the player's current RV14 homeland (current_rv14.json) to the planned one.

Pairs every current building with its spot in the plan (shortest total distance per type), lists
what to put away, move and place, orders the moves so each target spot is free when its turn comes,
and scores both layouts the way the planner does (trips per hour x distance to the nearest storage).
"""
import json, math, os, sys
import numpy as np
from scipy.optimize import linear_sum_assignment

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(S, 'multi'))
from compose import compose  # noqa: E402

CUR = json.load(open(os.path.join(S, 'current_rv14.json')))
AFT = json.load(open(os.path.join(S, sys.argv[1] if len(sys.argv) > 1 else 'cur3_h60.json')))
PLOTS = [[13, 14, 15, 16], [12, 7, 8, 9], [11, 4, 3, 6], [10, 2, 1, 5]]
EMODE = {'Aniipod Maker', 'Blazing Stove', 'Bouncy Brew Keg', 'Carousel Mill', 'Chimney Kiln', 'Claw Game Cooker', 'Crafting Table', 'Dance Pad Polisher',
         'Joy Wheel Loom', 'Jukebox Dryer', 'Mine', 'Phonolfactory Table', 'Pickling Jar', 'Simmering Pot', 'Well', 'Woodworking Bench'}


def ov(a, b):
    return min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']) > 1e-6 and min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']) > 1e-6


def cen(r):
    return (r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)


def where(r, L=None):
    """Plot under the piece's center, and its side of the nearest storage (numbered as on the map)."""
    cx, cy = cen(r)
    col, row = min(3, int(cx // 20)), min(3, int(cy // 15))
    st = [cen(q) for q in (L or AFT)['stores']]
    k = min(range(len(st)), key=lambda j: math.dist((cx, cy), st[j]))
    dx, dy = cx - st[k][0], cy - st[k][1]
    side = ('à droite' if dx > 0 else 'à gauche') if abs(dx) >= abs(dy) else ('en dessous' if dy > 0 else 'au-dessus')
    return {'plot': PLOTS[row][col], 'store': k + 1, 'side': side, 'd': round(math.dist((cx, cy), st[k]), 1)}


# ---------- everything on the ground, as one list of typed rectangles ----------
def ground(L, current):
    out = []
    for i in L['items']:
        if not current and i['kind'] == 'env' and not i.get('mode'):
            continue  # an idle climate building the plan doesn't need: leave it in the bag
        out.append({'n': i['n'], 'x': i['x'], 'y': i['y'], 'w': i['w'], 'h': i['h'], 'kind': i['kind'], 'item': i.get('item') or '',
                    'mode': i.get('mode'), 'weight': i.get('weight') or 0, 'ref': i})
    for k in ('stores', 'gens', 'poles'):
        n = {'stores': 'Storage Unit', 'gens': 'Crackle Generator', 'poles': 'Crackle Power Pole'}[k]
        for r in L[k]:
            out.append({'n': n, 'x': r['x'], 'y': r['y'], 'w': r['w'], 'h': r['h'], 'kind': k, 'item': '', 'mode': None, 'weight': 0, 'ref': r})
    return out


ASSIGN = []
# ---------- scores ----------
def score(L, plan):
    """Trips per hour x distance to the nearest storage, the planner's measure. For the current homeland the
    planned work is given to the matching buildings (busiest work on the building nearest a storage)."""
    st = [cen(r) for r in L['stores']]
    near = lambda r: min(math.dist(cen(r), s) for s in st)
    if plan:
        items = [i for i in L['items'] if i['kind'] == 'piece' and (i.get('weight') or 0) > 0]
        return sum(i['weight'] * near(i) for i in items) / sum(i['weight'] for i in items), items
    work = {}
    for i in AFT['items']:
        if i['kind'] == 'piece' and (i.get('weight') or 0) > 0:
            work.setdefault(i['n'], []).append(i)
    tot = wsum = 0
    items = []
    for n, ws in work.items():
        ws = sorted(ws, key=lambda i: -i['weight'])
        cands = sorted([i for i in L['items'] if i['n'] == n], key=near)
        for w, c in zip(ws, cands):
            ASSIGN.append((w, c))
            tot += w['weight'] * near(c); wsum += w['weight']
            items.append(dict(c, weight=w['weight'], item=w.get('item')))
    return tot / wsum, items


def power(L, items):
    areas = [{'x': g['x'] + g['w'] / 2 - 5.5, 'y': g['y'] + g['h'] / 2 - 5.5, 'w': 11, 'h': 11, 'src': 'gen'} for g in L['gens']]
    todo = list(L['poles'])
    added = True
    while added:
        added = False
        for p in list(todo):
            a = {'x': p['x'] + p['w'] / 2 - 3.5, 'y': p['y'] + p['h'] / 2 - 3.5, 'w': 7, 'h': 7, 'src': 'pole'}
            if any(ov(a, z) for z in areas):
                areas.append(a); todo.remove(p); added = True
    act = [i for i in items if i['n'] in EMODE and i.get('weight', 0) > 0]
    on = [i for i in act if any(ov(i, z) for z in areas)]
    return areas, len(on), len(act)


avg0, items0 = score(CUR, False)
avg1, _ = score(AFT, True)
areas0, on0, act0 = power(CUR, items0)
_, on1, act1 = power(AFT, [i for i in AFT['items'] if i['kind'] == 'piece'])

before, after = ground(CUR, True), ground(AFT, False)
types = sorted({g['n'] for g in before + after})
pairs = []          # (before or None, after or None)
for n in types:
    B = [g for g in before if g['n'] == n]
    A = [g for g in after if g['n'] == n]
    # same spot (and same footprint) first
    for a in A:
        for b in B:
            if not b.get('_u') and abs(a['x'] - b['x']) < .05 and abs(a['y'] - b['y']) < .05 and {a['w'], a['h']} == {b['w'], b['h']}:
                a['_u'] = b['_u'] = True
                pairs.append((b, a))
                break
    B2 = [b for b in B if not b.get('_u')]
    A2 = [a for a in A if not a.get('_u')]
    if B2 and A2:
        cost = np.array([[math.dist(cen(b), cen(a)) for a in A2] for b in B2])
        ri, ci = linear_sum_assignment(cost)
        for r, c in zip(ri, ci):
            B2[r]['_u'] = A2[c]['_u'] = True
            pairs.append((B2[r], A2[c]))
    pairs += [(b, None) for b in B if not b.get('_u')]
    pairs += [(None, a) for a in A if not a.get('_u')]

# ---------- actions ----------
acts = []
for b, a in pairs:
    if b and a:
        same = abs(a['x'] - b['x']) < .05 and abs(a['y'] - b['y']) < .05
        acts.append({'t': 'ok' if same else 'move', 'b': b, 'a': a})
    elif b:
        acts.append({'t': 'store', 'b': b, 'a': None})
    else:
        acts.append({'t': 'new', 'b': None, 'a': a})

# order: a move or placement waits for whatever currently sits on its target to leave
pending = [x for x in acts if x['t'] in ('move', 'new')]
stores_ = [x for x in acts if x['t'] == 'store']
order, temp = [], []
gone = set()   # ids of current rects that have left their spot
for x in stores_:
    gone.add(id(x['b']))
moving = {id(x['b']): x for x in pending if x['b']}
placed_rects = []


def blockers(x):
    return [y for y in acts if y['b'] is not None and id(y['b']) not in gone and y is not x and ov(x['a'], y['b'])]


left = sorted(pending, key=lambda x: (-(x['a']['weight'] or 0), x['a']['n']))
guard = 0
while left and guard < 1000:
    guard += 1
    prog = False
    for x in list(left):
        bl = blockers(x)
        if not bl:
            order.append(x); left.remove(x)
            if x['b']:
                gone.add(id(x['b']))
            prog = True
    if not prog:
        # a cycle: put one blocker in the bag for a moment, it comes back at its own turn
        x = left[0]
        y = blockers(x)[0]
        temp.append(y)
        gone.add(id(y['b']))
        if y['t'] == 'ok':  # a piece that stays but is in the way (shouldn't happen): it moves back after
            y['t'] = 'move'
assert not left, 'could not order the moves'


# the current homeland as a drawable layout (climate squares, power, no walkways or decor)
cur_lay = json.loads(json.dumps(CUR))
for i in cur_lay['items']:
    w = next((x for x in items0 if x['x'] == i['x'] and x['y'] == i['y'] and x['n'] == i['n']), None)
    i['weight'] = w['weight'] if w else 0
    i['idle'] = i['kind'] == 'piece' and not w
    if w and w.get('item'):
        i['item'] = w['item']
    st = [cen(r) for r in CUR['stores']]
    if i['kind'] == 'piece':
        d = [math.dist(cen(i), s) for s in st]
        i['store'] = int(np.argmin(d)); i['dist'] = round(min(d), 2)
cur_lay['items'] = [i for i in cur_lay['items'] if i['n'] != 'Incubateur'] + [i for i in cur_lay['items'] if i['n'] == 'Incubateur']
cur_lay['squares'] = [{'x': e['x'] + e['w'] / 2 - 4.5, 'y': e['y'] + e['h'] / 2 - 4.5, 'w': 9, 'h': 9, 'n': e['n'], 'mode': e.get('mode')} for e in CUR['items'] if e['kind'] == 'env' and e.get('mode')]
cur_lay['areas'] = areas0
cur_lay.update(walk=[], plazas=[], deco=[], decoTot={'cf': 0, 'wheat': 0, 'bud': 0}, metrics={'avg': round(avg0, 2), 'weight': 0, 'unplaced': []},
               powered=on0, targets=act0, unpowered=[], gap=0, gapE=0, diff=None, plots=AFT['plots'])
for i in cur_lay['items']:
    i.pop('added', None)

# the plan, with its decor and each piece's change, step number and where it comes from
aft_lay = json.loads(json.dumps(AFT))
aft_lay['items'] = [i for i in aft_lay['items'] if not (i['kind'] == 'env' and not i.get('mode'))]
placed, used, tot = compose(aft_lay['plazas'][:4])
aft_lay['deco'], aft_lay['decoTot'] = placed, tot
idx = {}
for k, i in enumerate(AFT['items']):
    idx[id(i)] = k
step_no = {}
n = 0
steps = []


def rect(r):
    return {k: round(r[k], 2) for k in ('x', 'y', 'w', 'h')}


for x in stores_:
    n += 1
    steps.append({'no': n, 't': 'store', 'n': x['b']['n'], 'from': rect(x['b']), 'fw': where(x['b'], CUR)})
for y in temp:
    n += 1
    steps.append({'no': n, 't': 'stash', 'n': y['b']['n'], 'from': rect(y['b']), 'fw': where(y['b'], CUR)})
for x in order:
    n += 1
    a = x['a']
    s = {'no': n, 't': x['t'], 'n': a['n'], 'to': rect(a), 'tw': where(a), 'item': a['item'], 'mode': a['mode'], 'w': round(a['weight'], 2)}
    if x['b']:
        s['from'] = rect(x['b']); s['fw'] = where(x['b'], CUR)
        pass
    if a['weight'] > 0 and a['kind'] == 'piece':
        s['dist'] = round(min(math.dist(cen(a), cen(q)) for q in AFT['stores']), 1)
    steps.append(s)
    step_no[id(a['ref'])] = (n, x['t'], rect(x['b']) if x['b'] else None)

# mark the plan's pieces
kept = {id(x['a']['ref']) for x in acts if x['t'] == 'ok'}
for k, i in enumerate(aft_lay['items']):
    src = next((r for r in AFT['items'] if r['x'] == i['x'] and r['y'] == i['y'] and r['n'] == i['n']), None)
    sn = step_no.get(id(src)) if src is not None else None
    i['st0'] = sn[1] if sn else 'ok'
    if sn:
        i['step'] = sn[0]
        if sn[2]:
            i['from'] = sn[2]
for key in ('gens', 'poles', 'stores'):
    for r0, r in zip(AFT[key], aft_lay[key]):
        sn = step_no.get(id(r0))
        r['st0'] = sn[1] if sn else 'ok'
        if sn:
            r['step'] = sn[0]
            if sn[2]:
                r['from'] = sn[2]
aft_lay['diff'] = None

# work to set once everything stands: production of each active building
recipes = {}
for i in AFT['items']:
    if i['kind'] == 'piece' and (i.get('weight') or 0) > 0 and i.get('item'):
        recipes.setdefault((i['n'], i['item']), 0)
        recipes[(i['n'], i['item'])] += 1
climate = [{'n': e['n'], 'mode': e['mode']} for e in AFT['items'] if e['kind'] == 'env' and e.get('mode')]

summary = {
    'avg0': round(avg0, 2), 'avg1': round(avg1, 2), 'pow0': [on0, act0], 'pow1': [on1, act1],
    'counts': {t: sum(1 for s in steps if s['t'] == t) for t in ('store', 'stash', 'move', 'new')},
    'kept': sum(1 for x in acts if x['t'] == 'ok'),
}
out = {'before': cur_lay, 'after': aft_lay, 'steps': steps, 'recipes': [{'n': k[0], 'item': k[1], 'count': v} for k, v in sorted(recipes.items())],
       'climate': climate, 'summary': summary}
json.dump(out, open(os.path.join(S, 'construct_rv14.json'), 'w'))
print(json.dumps(summary))
for s in steps:
    print(s['no'], s['t'], s['n'], s.get('item') or '', s.get('fw'), '->', s.get('tw'))
