"""What changes from one level's layout to the next, step by step, and a climate check.

pair(prev, nxt): every building of the previous layout matched to its place in the next one (same
spot first, then the shortest total distance per kind) -> actions ok / replant / reglage / remplace /
move / new / store, ordered so each target spot is free when its turn comes.
climate(layout, lay_in): does every climate crop get exactly the temperature its block asks for?
"""
import json, math, sys
import numpy as np
from scipy.optimize import linear_sum_assignment

PLOTS = [[13, 14, 15, 16], [12, 7, 8, 9], [11, 4, 3, 6], [10, 2, 1, 5]]
ENVN = ('Heat Furnace', 'Cooling Unit', 'Sunlamp')
TEMP = {'Scorching': 2, 'Warm': 1, 'Cool': -1, 'Freeze': -2}
TEMPN = {v: k for k, v in TEMP.items()}
E = 1e-6


def ov(a, b):
    return min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']) > E and min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']) > E


def cen(r):
    return (r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)


def where(r, L):
    cx, cy = cen(r)
    col, row = min(3, int(cx // 20)), min(3, int(cy // 15))
    st = [cen(q) for q in L['stores']]
    k = min(range(len(st)), key=lambda j: math.dist((cx, cy), st[j]))
    dx, dy = cx - st[k][0], cy - st[k][1]
    side = ('à droite' if dx > 0 else 'à gauche') if abs(dx) >= abs(dy) else ('en dessous' if dy > 0 else 'au-dessus')
    return {'plot': PLOTS[row][col], 'store': k + 1, 'side': side, 'd': round(math.dist((cx, cy), st[k]), 1)}


def ground(L):
    out = []
    for i in L['items']:
        if i['kind'] == 'env' and not i.get('mode'):
            continue
        out.append({'n': i['n'], 'x': i['x'], 'y': i['y'], 'w': i['w'], 'h': i['h'], 'kind': i['kind'], 'item': i.get('item') or '', 'mode': i.get('mode'),
                    'weight': i.get('weight') or 0, 'ref': i})
    for k, n in (('stores', 'Storage Unit'), ('gens', 'Crackle Generator'), ('poles', 'Crackle Power Pole')):
        for r in L[k]:
            out.append({'n': n, 'x': r['x'], 'y': r['y'], 'w': r['w'], 'h': r['h'], 'kind': k, 'item': '', 'mode': None, 'weight': 0, 'ref': r})
    return out


def rect(r):
    return {k: round(r[k], 2) for k in ('x', 'y', 'w', 'h')}


def pair(prev, nxt):
    before, after = ground(prev), ground(nxt)
    # climate buildings: a spot keeps its building or swaps it for another kind
    kind = lambda g: 'ENV' if g['n'] in ENVN else g['n']
    acts = []
    for n in sorted({kind(g) for g in before + after}):
        B = [g for g in before if kind(g) == n]
        A = [g for g in after if kind(g) == n]
        used_b, used_a = set(), set()
        for ia, a in enumerate(A):
            for ib, b in enumerate(B):
                if ib not in used_b and abs(a['x'] - b['x']) < .05 and abs(a['y'] - b['y']) < .05 and {a['w'], a['h']} == {b['w'], b['h']}:
                    used_b.add(ib); used_a.add(ia)
                    if a['n'] != b['n']:
                        t = 'remplace'
                    elif a['kind'] == 'env':
                        t = 'reglage' if a['mode'] != b['mode'] else 'ok'
                    elif a['item'] != b['item'] and a['weight'] > 0:
                        t = 'replant'
                    else:
                        t = 'ok'
                    acts.append({'t': t, 'b': b, 'a': a})
                    break
        # same kind of climate building close to its old spot (a bigger one centred on it)
        B2 = [b for ib, b in enumerate(B) if ib not in used_b]
        A2 = [a for ia, a in enumerate(A) if ia not in used_a]
        if n == 'ENV':
            for a in list(A2):
                b = next((b for b in B2 if math.dist(cen(a), cen(b)) < 1.01), None)
                if b is not None:
                    B2.remove(b); A2.remove(a)
                    acts.append({'t': 'remplace' if a['n'] != b['n'] else ('reglage' if a['mode'] != b['mode'] else 'ok') if math.dist(cen(a), cen(b)) < .05 else ('remplace' if a['n'] != b['n'] else 'move'), 'b': b, 'a': a})
            # other climate buildings: by kind
            for nn in ENVN:
                b3 = [b for b in B2 if b['n'] == nn]; a3 = [a for a in A2 if a['n'] == nn]
                if b3 and a3:
                    cost = np.array([[math.dist(cen(b), cen(a)) for a in a3] for b in b3])
                    ri, ci = linear_sum_assignment(cost)
                    for r, c in zip(ri, ci):
                        acts.append({'t': 'move', 'b': b3[r], 'a': a3[c]}); B2.remove(b3[r]); A2.remove(a3[c])
            acts += [{'t': 'store', 'b': b, 'a': None} for b in B2]
            acts += [{'t': 'new', 'b': None, 'a': a} for a in A2]
            continue
        if B2 and A2:
            cost = np.array([[math.dist(cen(b), cen(a)) for a in A2] for b in B2])
            ri, ci = linear_sum_assignment(cost)
            for r, c in zip(ri, ci):
                acts.append({'t': 'move', 'b': B2[r], 'a': A2[c]})
            B2 = [b for k, b in enumerate(B2) if k not in set(ri)]
            A2 = [a for k, a in enumerate(A2) if k not in set(ci)]
        acts += [{'t': 'store', 'b': b, 'a': None} for b in B2]
        acts += [{'t': 'new', 'b': None, 'a': a} for a in A2]
    return acts


def order_steps(acts, prev, nxt):
    """Ordered steps: put away, then moves and placements once their spot is free, then settings."""
    gone = set(id(x['b']) for x in acts if x['t'] == 'store')
    pend = [x for x in acts if x['t'] in ('move', 'new') or (x['t'] == 'remplace')]
    for x in pend:
        if x['t'] == 'remplace':
            gone.add(id(x['b']))  # the old building comes off its spot as the new one goes on
    order, temp = [], []
    blockers = lambda x: [y for y in acts if y['b'] is not None and id(y['b']) not in gone and y is not x and ov(x['a'], y['b'])]
    left = sorted([x for x in pend], key=lambda x: (-(x['a']['weight'] or 0), x['a']['n']))
    while left:
        prog = False
        for x in list(left):
            if not blockers(x):
                order.append(x); left.remove(x)
                if x['b'] is not None:
                    gone.add(id(x['b']))
                prog = True
        if not prog:
            y = blockers(left[0])[0]
            temp.append(y); gone.add(id(y['b']))
    steps, n = [], 0
    for x in [a for a in acts if a['t'] == 'store']:
        n += 1; steps.append({'no': n, 't': 'store', 'n': x['b']['n'], 'from': rect(x['b']), 'fw': where(x['b'], prev)})
    for y in temp:
        n += 1; steps.append({'no': n, 't': 'stash', 'n': y['b']['n'], 'from': rect(y['b']), 'fw': where(y['b'], prev)})
    for x in order:
        n += 1
        a = x['a']
        s = {'no': n, 't': x['t'], 'n': a['n'], 'to': rect(a), 'tw': where(a, nxt), 'item': a['item'], 'mode': a['mode'], 'w': round(a['weight'], 2)}
        if x['b'] is not None:
            s['from'] = rect(x['b']); s['fw'] = where(x['b'], prev)
            if x['t'] == 'remplace':
                s['was'] = x['b']['n']
        if a['weight'] > 0 and a['kind'] == 'piece':
            s['dist'] = round(min(math.dist(cen(a), cen(q)) for q in nxt['stores']), 1)
        steps.append(s)
        x['step'] = n
    for x in acts:
        if x['t'] == 'reglage':
            n += 1; a = x['a']
            steps.append({'no': n, 't': 'reglage', 'n': a['n'], 'to': rect(a), 'tw': where(a, nxt), 'mode': a['mode'], 'wasMode': x['b']['mode'], 'w': 0})
            x['step'] = n
    return steps


def climate(L, lay_in):
    """Required (crop, temperature/light) counts vs what the layout gives. Returns list of problems."""
    need = {}
    for p in lay_in['pieces']:
        if p.get('cluster'):
            bs = p['buildings']
            for q in p['plots']:
                z = q.get('zone', 0)
                if len(bs) == 1:
                    m = bs[0]['mode']
                else:
                    m = bs[0]['mode'] if z == 0 else bs[1]['mode'] if z == 2 else TEMPN.get(TEMP[bs[0]['mode']] + TEMP[bs[1]['mode']], '?')
                k = (q['facility'], q.get('crop'), m); need[k] = need.get(k, 0) + 1
        else:
            m = p['members'][0]
            if m.get('building') and m.get('mode') and m.get('crop') is None:
                continue
    envs = [i for i in L['items'] if i['kind'] == 'env' and i.get('mode')]
    sq = lambda e: {'x': e['x'] + e['w'] / 2 - 4.5, 'y': e['y'] + e['h'] / 2 - 4.5, 'w': 9, 'h': 9}
    got = {}
    for i in L['items']:
        if i['kind'] != 'piece' or not i.get('item'):
            continue
        ms = [e['mode'] for e in envs if ov(i, sq(e))]
        t = sum(TEMP.get(m, 0) for m in ms)
        light = 'Adequate' in ms
        tm = TEMPN.get(t) if t else None
        modes = [m for m in (tm, 'Adequate' if light else None) if m]
        for m in modes or [None]:
            k = (i['n'], i['item'], m); got[k] = got.get(k, 0) + 1
    probs = []
    for k, v in need.items():
        if got.get(k, 0) < v:
            probs.append({'need': k, 'want': v, 'have': got.get(k, 0)})
    return probs, need, got


if __name__ == '__main__':
    prev, nxt, lay = (json.load(open(f)) for f in sys.argv[1:4])
    acts = pair(prev, nxt)
    steps = order_steps(acts, prev, nxt)
    from collections import Counter
    print(Counter(s['t'] for s in steps), 'ok', sum(1 for a in acts if a['t'] == 'ok'))
    probs, need, got = climate(nxt, lay)
    print('climate problems', probs)
