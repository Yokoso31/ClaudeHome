"""Does a level's production plan fit the Japanese-garden design? Climate blocks onto fixed spots."""
import json, sys, itertools
TEMP = {'Scorching': 2, 'Warm': 1, 'Cool': -1, 'Freeze': -2}
TEMPN = {v: k for k, v in TEMP.items()}
DEV = {'Warm': 'Heat Furnace', 'Scorching': 'Heat Furnace', 'Cool': 'Cooling Unit', 'Freeze': 'Cooling Unit', 'Adequate': 'Sunlamp'}
# fixed climate spots of the design: what each 9x9 square can hold
SLOTS = {'P1': {'farm': 32, 'wood': 0, 'bld': set()}, 'P2': {'farm': 32, 'wood': 0, 'bld': set()},
         'O1': {'farm': 12, 'wood': 12, 'bld': set()}, 'O2': {'farm': 12, 'wood': 12, 'bld': set()},
         'HAM': {'farm': 1, 'wood': 0, 'bld': {'Starfall Hammock'}}, 'SAND': {'farm': 0, 'wood': 0, 'bld': {'Tidewhisper Sandcastle'}},
         'WIND': {'farm': 0, 'wood': 1, 'bld': {'Floral Windmill'}}}
def needs(lay):
    """Climate groups as (mode, farms, woods, buildings), pairs flattened by zone."""
    out = []
    for p in lay['pieces']:
        if not p.get('cluster'):
            continue
        bs = p['buildings']
        zones = {}
        for q in p['plots']:
            z = q.get('zone', 0)
            m = bs[0]['mode'] if len(bs) == 1 or z == 0 else bs[1]['mode'] if z == 2 else TEMPN[TEMP[bs[0]['mode']] + TEMP[bs[1]['mode']]]
            g = zones.setdefault(m, {'mode': m, 'farm': [], 'wood': [], 'bld': [], 'pair': len(bs) > 1})
            if q['facility'] == 'Farmland': g['farm'].append(q['crop'])
            elif q['facility'] == 'Woodland': g['wood'].append(q['crop'])
            else: g['bld'].append(q['facility'])
        out += list(zones.values())
    return out
def fit(groups, owned=2):
    """Assign each group to one or more spots (one climate building each). Returns best plan or None."""
    names = list(SLOTS)
    best = None
    # merge groups of the same mode first, they may share spots
    by = {}
    for g in groups:
        m = by.setdefault(g['mode'], {'mode': g['mode'], 'farm': [], 'wood': [], 'bld': []})
        m['farm'] += g['farm']; m['wood'] += g['wood']; m['bld'] += g['bld']
    G = list(by.values())
    def rec(i, free, used, plan):
        nonlocal best
        if i == len(G):
            if best is None or len(plan) < len(best):
                best = list(plan)
            return
        g = G[i]; dt = DEV[g['mode']]
        # choose a set of spots for this group (1..3) that holds it
        for k in (1, 2, 3):
            if used.get(dt, 0) + k > owned:
                break
            for combo in itertools.combinations(sorted(free), k):
                bl = set().union(*(SLOTS[s]['bld'] for s in combo))
                if not set(g['bld']) <= bl:
                    continue
                if any(SLOTS[s]['bld'] and not (SLOTS[s]['bld'] & set(g['bld'])) for s in combo):
                    continue  # a pavilion spot is only for its own building
                if sum(SLOTS[s]['farm'] for s in combo) < len(g['farm']) or sum(SLOTS[s]['wood'] for s in combo) < len(g['wood']):
                    continue
                rec(i + 1, free - set(combo), dict(used, **{dt: used.get(dt, 0) + k}), plan + [(g['mode'], combo, len(g['farm']), len(g['wood']), g['bld'])])
            if best is not None:
                pass
    rec(0, set(names), {}, [])
    return best, G
if __name__ == '__main__':
    for L in sys.argv[1:]:
        lay = json.load(open(f'my_lay_in_rv{L}.json'))
        gs = needs(lay)
        plan, G = fit(gs)
        print(L, 'needs', [(g['mode'], len(g['farm']), len(g['wood']), g['bld']) for g in G])
        print('   ->', plan if plan else 'IMPOSSIBLE')
