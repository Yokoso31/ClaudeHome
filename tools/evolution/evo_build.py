"""The player's evolving plan, RV14 (after the construction works) to RV20, ready for the page.

For each level: the layout from chain.py, its decor (what the previous level had is kept where it
still fits, then the plazas are filled), the ordered steps from the previous level, and each
piece's change for the map. Writes my_final_evo.json, which build_data.py reads with USE_MY=1.
"""
import json, os, sys
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S); sys.path.insert(0, os.path.join(S, 'multi'))
from evo_steps import pair, order_steps, ov  # noqa: E402
from compose import compose  # noqa: E402

C = json.load(open(os.path.join(S, 'construct_rv14.json')))
base = json.load(open(os.path.join(S, 'cur3_h60.json')))
out = {}
# RV14: the plan after the construction works, its decor as on the construction page
L14 = json.loads(json.dumps(base))
L14['items'] = [i for i in L14['items'] if not (i['kind'] == 'env' and not i.get('mode'))]
for i in L14['items']:
    i.pop('st0', None)
L14['deco'], L14['decoTot'] = C['after']['deco'], C['after']['decoTot']
L14['diff'] = None
L14['steps'] = []
out[14] = L14
prev = L14
for L in range(15, 21):
    nxt = json.load(open(os.path.join(S, f'ev3_rv{L}.json')))
    nxt['items'] = [i for i in nxt['items'] if not (i['kind'] == 'env' and not i.get('mode'))]
    for i in nxt['items']:
        i.pop('st0', None); i.pop('was', None)
    acts = pair(prev, nxt)
    steps = order_steps(acts, prev, nxt)
    # each piece's change and step, for the map
    for x in acts:
        a = x['a']
        if a is None:
            continue
        r = a['ref']
        r['st0'] = x['t']
        if x.get('step'):
            r['step'] = x['step']
        if x['t'] in ('move', 'remplace') and x['b'] is not None:
            r['from'] = {k: round(x['b'][k], 2) for k in 'xywh'}
        if x['t'] == 'replant':
            r['was'] = x['b']['item']
        if x['t'] == 'remplace':
            r['was'] = x['b']['n']
        if x['t'] == 'reglage':
            r['was'] = x['b']['mode']
    # replanting and recipe changes, grouped
    rep = {}
    for x in acts:
        if x['t'] == 'replant' and x['a']['weight'] > 0:
            k = (x['a']['n'], x['b']['item'], x['a']['item'])
            rep[k] = rep.get(k, 0) + 1
    nxt['replant'] = [{'n': k[0], 'was': k[1], 'item': k[2], 'count': v} for k, v in sorted(rep.items(), key=lambda kv: -kv[1])]
    nxt['steps'] = steps
    # decor: keep last level's pieces that still fit, then fill the plazas
    occ = [dict(x=i['x'], y=i['y'], w=i['w'], h=i['h']) for i in nxt['items']] + nxt['stores'] + nxt['gens'] + nxt['poles'] + [dict(x=x, y=y, w=1, h=1) for x, y in nxt['walk']]
    keep = [k for k in prev['deco'] if not any(ov(k, r) for r in occ)]
    placed, used, tot = compose(nxt['plazas'][:4], keep)
    ids = {(k['id'], k['x'], k['y']) for k in prev['deco']}
    for d in placed:
        d['st0'] = 'ok' if (d['id'], d['x'], d['y']) in ids else 'new'
    nxt['deco'], nxt['decoTot'] = placed, tot
    nxt['decoKept'], nxt['decoDropped'] = len(keep), len(prev['deco']) - len(keep)
    nxt['diff'] = {'sum': {t: sum(1 for s in steps if s['t'] == t) for t in ('move', 'new', 'store', 'stash', 'remplace', 'reglage')},
                   'polesKept': 0, 'polesNew': 0}
    out[L] = nxt
    print(L, nxt['diff']['sum'], 'replant groups', len(nxt['replant']), 'deco kept', len(keep), 'total', len(placed), 'avg', nxt['metrics']['avg'])
    prev = nxt
json.dump(out, open(os.path.join(S, 'my_final_evo.json'), 'w'))
