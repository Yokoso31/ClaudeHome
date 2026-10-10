"""Production of each level (RV14-20) laid into the Japanese-garden design.

Fixed by the design: kiosks (storages), one permanent lot per machine on the craftsmen's street,
quarry slots for mines, wells, pavilions, hatchery. Laid per level by the planner: the climate
blocks and crops, inside two bordered terraces (west and east), anchored on the previous level.
Then electricity (2 generators, 12 poles) and checks: climate for every crop, overlaps, power.
Writes garden_levels.json.
"""
import json, math, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evo_steps import climate

S = os.path.dirname(os.path.abspath(__file__))
LEVELS = list(range(14, 21))
E = 1e-6
FP = {'Woodworking Bench': (2, 1.5), 'Chimney Kiln': (5.5, 5.5), 'Jukebox Dryer': (2.5, 2.5), 'Simmering Pot': (1.5, 1.5), 'Phonolfactory Table': (3.5, 3.5),
      'Carousel Mill': (5.5, 5.5), 'Pickling Jar': (2.5, 2), 'Blazing Stove': (2.5, 1.75), 'Joy Wheel Loom': (4, 4), 'Crafting Table': (4, 4),
      'Bouncy Brew Keg': (3, 3), 'Claw Game Cooker': (3.5, 3.5), 'Aniipod Maker': (4.5, 4.5), 'Dance Pad Polisher': (2.5, 2.5)}
EMODE = set(FP) | {'Mine', 'Well'}
KIOSK = {1: (17, 19.75), 2: (51, 19.75), 3: (17, 43), 4: (62, 44), 5: (58, 21)}
TERRACES = [{'x': 2.8, 'y': 25.5, 'w': 23.2, 'h': 25.5, 'name': 'Terrasse ouest'}, {'x': 26, 'y': 37.2, 'w': 8, 'h': 13.8, 'name': 'Terrasse ouest'},
            {'x': 55, 'y': 25.5, 'w': 5, 'h': 28.5, 'name': 'Terrasse est'}, {'x': 60, 'y': 30.5, 'w': 20, 'h': 23.5, 'name': 'Terrasse est'},
            {'x': 46, 'y': 33.5, 'w': 9, 'h': 20.5, 'name': 'Terrasse est'}]
TERR_NE = [{'x': 40.2, 'y': 0.6, 'w': 12, 'h': 10.2, 'name': 'Jardin des fleurs'}]
CLEAR = [{'x': 1, 'y': 16.5, 'w': 59, 'h': 3}, {'x': 38, 'y': 19.5, 'w': 4, 'h': 5.5}, {'x': 38, 'y': 25, 'w': 4, 'h': 35},
         {'x': 34, 'y': 25, 'w': 12, 'h': 12}, {'x': 26, 'y': 25.5, 'w': 8, 'h': 11.5}, {'x': 46.5, 'y': 25.5, 'w': 8.5, 'h': 7.5},
         {'x': 2, 'y': 51, 'w': 25, 'h': 9}, {'x': 26, 'y': 50.5, 'w': 20, 'h': 6}, {'x': 47.4, 'y': 54.6, 'w': 9.2, 'h': 4.8},
         {'x': 17.5, 'y': 1, 'w': 8, 'h': 8.2}, {'x': 0, 'y': 36, 'w': 2.8, 'h': 13}, {'x': 56, 'y': 54, 'w': 24, 'h': 6},
         {'x': 2, 'y': 9.9, 'w': 5.1, 'h': 1}, {'x': 22.6, 'y': 9.9, 'w': 5.1, 'h': 1}]   # last two: box hedges in the north
QUARRY = sorted([(x, y) for y in (15, 20, 25) for x in (60, 65, 70, 75)], key=lambda p: math.dist((p[0] + 2.5, p[1] + 2.5), (59, 22)))
WELLS = [(30, 8), (33, 8), (36, 8)]
PAV = {'Nimbus Bed': (2, 2, 5), 'Starfall Hammock': (9, 2, 5), 'Tidewhisper Sandcastle': (27, 2, 5), 'Dewy House': (34, 3, 2), 'Floral Windmill': (41, 4.5, 5)}
HATCH = [(48 + 2 * i, 55 + 2 * j) for i in range(4) for j in range(2)]


def ov(a, b):
    return min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']) > E and min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']) > E


def cen(r):
    return (r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)


def plot_open(r, lvl):
    """Plots 15 and 16 (x >= 40, y < 15) open at RV16."""
    return lvl >= 16 or not ov(r, {'x': 40, 'y': 0, 'w': 40, 'h': 15})


LAY = {L: json.load(open(os.path.join(S, f'my_lay_in_rv{L}.json'))) for L in LEVELS}

# ---------------- machines: one permanent lot each ----------------
def machine_weights():
    """Per machine kind, per level, the work of each unit, busiest first."""
    out = {}
    for L in LEVELS:
        for p in LAY[L]['pieces']:
            if p.get('cluster'):
                continue
            m = p['members'][0]
            if m['facility'] in FP:
                out.setdefault(m['facility'], {}).setdefault(L, []).append((m.get('weight') or 0, m.get('crop')))
    inst = []
    for n, by in out.items():
        cnt = max(len(v) for v in by.values())
        for k in range(cnt):
            w = {}
            for L in LEVELS:
                lst = sorted(by.get(L, []), key=lambda t: -t[0])
                w[L] = lst[k] if k < len(lst) else (0, None)
            inst.append({'n': n, 'k': k, 'w': w, 'tot': sum(v[0] for v in w.values())})
    return inst

RUNS = [('S', 19.5, True, 1, 16.8, 14), ('S', 19.5, True, 19.4, 37.8, 14), ('S', 19.5, True, 42.2, 50.8, 14), ('S', 19.5, True, 53.4, 57.8, 14),
        ('N', 16.5, False, 1, 39.8, 14), ('N', 16.5, False, 40.2, 59.6, 16)]
def assign_lots(inst):
    placed = []
    order = sorted(inst, key=lambda i: -i['tot'])
    for it in order:
        w, h = FP[it['n']]
        early = it['w'][14][0] > 0 or it['w'][15][0] > 0
        best = None
        for side, y0, down, a, b, opens in RUNS:
            if opens > 14 and early:
                continue
            occ = sorted((p['x'], p['x'] + p['w']) for p in placed if p['side'] == side and a - E <= p['x'] < b)
            for x0 in [a] + [q + 1 for _, q in occ]:
                if x0 + w > b + E or any(not (x0 + w + 1 <= s + E or x0 >= q + 1 - E) for s, q in occ):
                    continue
                y = y0 if down else y0 - h
                c = (x0 + w / 2, y + h / 2)
                d = min(math.dist(c, (kx + 1, ky + 1)) for kx, ky in (KIOSK[1], KIOSK[2], KIOSK[5]))
                cost = it['tot'] * d + (0.5 if opens > 14 else 0)
                if best is None or cost < best[0]:
                    best = (cost, side, x0, y, opens)
        if best is None:
            it['lot'] = None
            continue
        _, side, x0, y, opens = best
        it['lot'] = {'x': x0, 'y': y, 'w': w, 'h': h, 'opens': opens}
        placed.append({'side': side, 'x': x0, 'w': w})
    return inst

# ---------------- crops: the planner inside the terraces ----------------
CROP_FAC = {'Farmland', 'Woodland'}
def crop_input(L):
    lay = LAY[L]
    pieces = []
    fixed = []   # non-crop pieces placed by the design
    flower = []  # the Floral Windmill's block goes to the flower garden, placed by hand
    for p in lay['pieces']:
        if p.get('cluster'):
            if any(q['facility'] == 'Floral Windmill' for q in p['plots']):
                flower.append(p)
            else:
                pieces.append(p)
            continue
        m = p['members'][0]
        if m.get('building'):
            continue  # idle climate building: in the bag
        if m['facility'] in CROP_FAC:
            pieces.append(p)
        else:
            fixed.append(m)
    cells = [{k: t[k] for k in 'xywh'} for t in TERRACES]
    return {'pieces': pieces, 'cells': cells}, (fixed, flower)


EXTRA = [{'x': 60, 'y': 0.5, 'w': 20, 'h': 14.3, 'name': 'Terrasse de la montagne'}]
def run_planner(L, prev_items, extra=False):
    inp, (fixed, flower) = crop_input(L)
    if extra:
        inp['cells'] += [{k: t[k] for k in 'xywh'} for t in EXTRA]
    json.dump(inp, open(os.path.join(S, f'gd_lay_in_rv{L}.json'), 'w'))
    subprocess.run(['cp', f'my_data_rv{L}.json', f'gd_data_rv{L}.json'], cwd=S, check=True)
    stores = [{'x': x, 'y': y, 'w': 2, 'h': 2} for x, y in KIOSK.values()]
    prev = {'lvl': L - 1, 'items': prev_items, 'stores': stores, 'gens': [], 'poles': [], 'hubIdx': None}
    json.dump(prev, open(os.path.join(S, f'gd_prev_rv{L}.json'), 'w'))
    best = None
    for gap in ('1', '0.5', '0'):
        env = dict(os.environ, PREFIX='gd_', PREV=f'../gd_prev_rv{L}.json', MOVEC='150', OUT=f'gd_out_rv{L}.json', NOSTEAL='1')
        r = subprocess.run(['node', 'plan_multi.mjs', str(L), '5', gap, '0', '0', '0', gap], cwd=os.path.join(S, 'multi'), env=env, capture_output=True, text=True, timeout=1500)
        out = json.load(open(os.path.join(S, f'gd_out_rv{L}.json')))
        probs = climate(out, LAY[L])[0]
        miss = sum(p['want'] - p['have'] for p in probs)
        un = len(out['metrics']['unplaced'])
        print(f'  RV{L} gap {gap}: unplaced {un}, climate miss {miss}, avg {out["metrics"]["avg"]}', flush=True)
        key = (un, miss)
        if best is None or key < best[0]:
            best = (key, gap, out)
        if key == (0, 0):
            break
    if best[0][0] and not extra and L >= 16:
        print(f'  RV{L}: not everything fits, opening the mountain terrace', flush=True)
        return run_planner(L, prev_items, True)
    return best[2], (fixed, flower), best[0] + (extra,)

# ---------------- power ----------------
def power(items, occupied, lvl, gens_prev=None, poles_n=12):
    """2 generators (11 x 11) and up to 12 poles (7 x 7, each touching the network): the best
    generator pair among the strongest spots, each tried with its poles laid greedily."""
    targets = [i for i in items if i['n'] in EMODE and i.get('weight', 0) > 0]
    inside = lambda r: 0 <= r['x'] and 0 <= r['y'] and r['x'] + r['w'] <= 80 and r['y'] + r['h'] <= 60 and plot_open(r, lvl)
    free0 = lambda r: inside(r) and not any(ov(r, o) for o in occupied)
    area = lambda p, s: {'x': p['x'] + p['w'] / 2 - s / 2, 'y': p['y'] + p['h'] / 2 - s / 2, 'w': s, 'h': s}
    cands = lambda s: [{'x': x / 2, 'y': y / 2, 'w': s, 'h': s} for x in range(0, int((80 - s) * 2) + 1) for y in range(0, int((60 - s) * 2) + 1)]
    hits = lambda a: frozenset(k for k, t in enumerate(targets) if ov(a, t))
    gc = [c for c in cands(1) if free0(c)]
    gh = [(c, hits(area(c, 11))) for c in gc]
    pc = [c for c in cands(1.5) if free0(c)]
    ph = [(c, hits(area(c, 7)), area(c, 7)) for c in pc]
    ph = [t for t in ph if t[1]] + [t for t in ph if not t[1]][::7]   # poles that reach nothing: keep a sample as stepping stones
    def lay(gens):
        powered = set().union(*(h for _, h in gens))
        areas = [area(c, 11) for c, _ in gens]
        poles = []
        for _ in range(poles_n):
            left = [k for k in range(len(targets)) if k not in powered]
            if not left:
                break
            best, bv = None, -1
            for c, h, a in ph:
                if any(ov(c, q) for q in poles) or any(ov(c, g) for g, _ in gens):
                    continue
                if not any(ov(a, z) for z in areas):
                    continue
                v = sum(100 + targets[k]['weight'] for k in h if k not in powered)
                if v == 0:
                    v = -min(math.dist(cen(a), cen(targets[k])) for k in left)
                if best is None or v > bv:
                    best, bv = (c, h, a), v
            if best is None:
                break
            c, h, a = best
            poles.append(c); areas.append(a); powered |= h
        return powered, poles, areas
    top = sorted(gh, key=lambda t: -sum(100 + targets[k]['weight'] for k in t[1]))
    seen, short = set(), []
    for c, h in top:
        if h and h not in seen:
            seen.add(h); short.append((c, h))
        if len(short) >= 9:
            break
    best = None
    for i in range(len(short)):
        for j in range(i + 1, len(short)):
            if ov(short[i][0], short[j][0]):
                continue
            pw, poles, areas = lay([short[i], short[j]])
            score = (len(pw), sum(targets[k]['weight'] for k in pw))
            if best is None or score > best[0]:
                best = (score, [short[i][0], short[j][0]], poles, areas, pw)
    _, gens, poles, areas, pw = best
    return gens, poles, areas, len(pw), len(targets)


def power_greedy(items, occupied, lvl, poles_n=12):
    targets = [i for i in items if i['n'] in EMODE and i.get('weight', 0) > 0]
    inside = lambda r: 0 <= r['x'] and 0 <= r['y'] and r['x'] + r['w'] <= 80 and r['y'] + r['h'] <= 60 and plot_open(r, lvl)
    occ = list(occupied)
    free = lambda r: inside(r) and not any(ov(r, o) for o in occ)
    area = lambda p, s: {'x': p['x'] + p['w'] / 2 - s / 2, 'y': p['y'] + p['h'] / 2 - s / 2, 'w': s, 'h': s}
    powered = set()
    gain = lambda a: sum((100 + t['weight']) for k, t in enumerate(targets) if k not in powered and ov(a, t))
    mark = lambda a: powered.update(k for k, t in enumerate(targets) if ov(a, t))
    cands = lambda s: [{'x': x / 2, 'y': y / 2, 'w': s, 'h': s} for x in range(0, int((80 - s) * 2) + 1) for y in range(0, int((60 - s) * 2) + 1)]
    gens, poles, areas = [], [], []
    gc = [c for c in cands(1) if free(c)]
    for _ in range(2):
        best = max(gc, key=lambda c: gain(area(c, 11)) if not any(ov(c, g) for g in gens) else -1)
        gens.append(best); occ.append(best); a = area(best, 11); areas.append(a); mark(a)
        gc = [c for c in gc if not ov(c, best)]
    pc = [c for c in cands(1.5) if free(c)]
    for _ in range(poles_n):
        left = [k for k in range(len(targets)) if k not in powered]
        if not left:
            break
        conn = [c for c in pc if not any(ov(c, q) for q in poles + gens) and any(ov(area(c, 7), a) for a in areas)]
        if not conn:
            break
        pick = max(conn, key=lambda c: gain(area(c, 7)))
        if gain(area(pick, 7)) == 0:
            def dist_to(c):
                a = area(c, 7)
                return min(math.dist(cen(a), cen(targets[k])) for k in left)
            pick = min(conn, key=dist_to)
        poles.append(pick); occ.append(pick); a = area(pick, 7); areas.append(a); mark(a)
    return gens, poles, areas, len(powered), len(targets)


def regularize(out, L, cells):
    """Farms and woodlands in straight rows: for each climate building, its pieces are put back on a grid of their size
    around it (the grid phase that holds them best, nearest cells first); then the farms that need
    no climate, in a tidy block. Anything that can't be done cleanly stays as the planner left it."""
    items = out['items']
    envs = [i for i in items if i['kind'] == 'env' and i.get('mode')]
    sq = lambda e: {'x': e['x'] + e['w'] / 2 - 4.5, 'y': e['y'] + e['h'] / 2 - 4.5, 'w': 9, 'h': 9}
    needs = set()
    for p in LAY[L]['pieces']:
        if p.get('cluster'):
            for q in p['plots']:
                needs.add((q['facility'], q.get('crop')))
    inside = lambda r: sum(max(0, min(r['x'] + r['w'], c['x'] + c['w']) - max(r['x'], c['x'])) * max(0, min(r['y'] + r['h'], c['y'] + c['h']) - max(r['y'], c['y'])) for c in cells) >= r['w'] * r['h'] - E
    kiosks = [{'x': x, 'y': y, 'w': 2, 'h': 2} for x, y in KIOSK.values()]
    done = tot = 0
    for N, P in (('Farmland', 2), ('Woodland', 4)):
        groups = []
        for e in envs:
            # pieces shared with another building's square (pair zones) stay where the planner put them
            F = [i for i in items if i['n'] == N and (i['n'], i.get('item')) in needs and ov(i, sq(e))
                 and not any(ov(i, sq(o)) for o in envs if o is not e)]
            if F:
                groups.append((e, F))
        free_f = [i for i in items if i['n'] == N and (i['n'], i.get('item')) not in needs]
        tot += len(groups) + (1 if free_f else 0)
        for e, F in groups + [(None, free_f)]:
            if not F:
                continue
            others = [i for i in items if not any(i is f for f in F)]
            other_sq = [sq(o) for o in envs if o is not e]
            if e is not None:
                cx, cy = e['x'] + e['w'] / 2, e['y'] + e['h'] / 2
                S = sq(e)
            else:
                cx, cy = None, None
            best = None
            for ox in [k / 2 for k in range(2 * P)]:
                for oy in [k / 2 for k in range(2 * P)]:
                    cand = []
                    for gx in range(0, 80 // P):
                        for gy in range(0, 60 // P):
                            r = {'x': ox + P * gx, 'y': oy + P * gy, 'w': P, 'h': P}
                            if e is not None and not ov(r, S):
                                continue
                            if not inside(r) or any(ov(r, o) for o in others) or any(ov(r, k) for k in kiosks):
                                continue
                            if e is not None and any(ov(r, q) for q in other_sq):
                                continue
                            cand.append(r)
                    if len(cand) < len(F):
                        continue
                    if e is None:
                        # a compact block next to the pieces' current centre
                        mx = sum(f['x'] for f in F) / len(F); my = sum(f['y'] for f in F) / len(F)
                        key = lambda r: math.dist((r['x'], r['y']), (mx, my))
                    else:
                        key = lambda r: (abs(r['x'] + P / 2 - cx) + abs(r['y'] + P / 2 - cy), r['y'], r['x'])
                    pick = sorted(cand, key=key)[:len(F)]
                    score = sum(math.dist((r['x'] + P / 2, r['y'] + P / 2), (cx, cy) if e is not None else (mx + P / 2, my + P / 2)) for r in pick)
                    if best is None or score < best[0]:
                        best = (score, pick)
            if best is None:
                continue
            pick = sorted(best[1], key=lambda r: (r['y'], r['x']))
            crops = sorted((f.get('item') or '', f.get('weight') or 0) for f in F)
            before = [(f['x'], f['y'], f.get('item'), f.get('weight')) for f in F]
            bad0 = len(climate(out, LAY[L])[0])
            for f, r, (crop, wgt) in zip(sorted(F, key=lambda f: (f['y'], f['x'])), pick, crops):
                f['x'], f['y'] = r['x'], r['y']
                f['item'], f['weight'] = crop, wgt
            if len(climate(out, LAY[L])[0]) > bad0:   # never trade climate for neatness
                for f, (x, y, it, w) in zip(F, before):
                    f['x'], f['y'], f['item'], f['weight'] = x, y, it, w
                continue
            done += 1
    return done, tot


def main():
    inst = assign_lots(machine_weights())
    reserve = [(i['n'], i['k']) for i in inst if i['lot'] is None]
    print('lots placed', sum(1 for i in inst if i['lot']), 'reserve', reserve)
    prev_items = []
    levels = {}
    for L in LEVELS:
        out, (fixed, flower), key = run_planner(L, prev_items)
        cells = [{k: t[k] for k in 'xywh'} for t in TERRACES] + ([{k: t[k] for k in 'xywh'} for t in EXTRA] if key[-1] else [])
        rd, rn = regularize(out, L, cells)
        print(f'  RV{L}: rows straightened for {rd} of {rn} groups of farms and woodlands', flush=True)
        items = []
        # crops and climate from the planner
        for it in out['items']:
            items.append({k: it.get(k) for k in ('kind', 'n', 'item', 'mode', 'x', 'y', 'w', 'h', 'weight', 'idle')} | {'zone': 'terrace'})
        squares = [q for q in out['squares']]
        for p in flower:   # flower garden: windmill, its sunlamp, the orange-flower woodland beside
            b = p['buildings'][0]
            items.append({'kind': 'env', 'n': b['facility'], 'item': '', 'mode': b['mode'], 'x': 46.5, 'y': 6.5, 'w': 1, 'h': 1, 'weight': 0, 'idle': False, 'zone': 'flower'})
            squares.append({'x': 42.5, 'y': 2.5, 'w': 9, 'h': 9, 'n': b['facility'], 'mode': b['mode'], 'group': None})
            for q in p['plots']:
                if q['facility'] == 'Floral Windmill':
                    items.append({'kind': 'piece', 'n': q['facility'], 'item': q.get('crop') or '', 'x': 41, 'y': 4.5, 'w': 5, 'h': 5, 'weight': q.get('weight') or 0, 'idle': False, 'zone': 'flower'})
                elif q['facility'] == 'Woodland':
                    items.append({'kind': 'piece', 'n': 'Woodland', 'item': q.get('crop') or '', 'x': 47.5, 'y': 4.5, 'w': 4, 'h': 4, 'weight': q.get('weight') or 0, 'idle': False, 'zone': 'flower'})
                else:
                    raise SystemExit(f'flower garden: unexpected {q["facility"]}')
        # machines on their lots
        for i in inst:
            if not i['lot'] or i['lot']['opens'] > L:
                continue
            w, crop = i['w'][L]
            items.append({'kind': 'piece', 'n': i['n'], 'item': crop or '', 'x': i['lot']['x'], 'y': i['lot']['y'], 'w': i['lot']['w'], 'h': i['lot']['h'], 'weight': w, 'idle': w == 0, 'zone': 'street', 'unit': i['k']})
        # mines, wells, pavilions that need no climate
        mines = sorted([m for m in fixed if m['facility'] == 'Mine'], key=lambda m: -(m.get('weight') or 0))
        for k, m in enumerate(mines):
            x, y = QUARRY[k]
            items.append({'kind': 'piece', 'n': 'Mine', 'item': m.get('crop') or '', 'x': x, 'y': y, 'w': 5, 'h': 5, 'weight': m.get('weight') or 0, 'idle': not m.get('weight'), 'zone': 'quarry'})
        wells = [m for m in fixed if m['facility'] == 'Well']
        for k, m in enumerate(wells):
            x, y = WELLS[k]
            items.append({'kind': 'piece', 'n': 'Well', 'item': m.get('crop') or '', 'x': x, 'y': y, 'w': 2, 'h': 2, 'weight': m.get('weight') or 0, 'idle': not m.get('weight'), 'zone': 'wells'})
        in_terr = {i['n'] for i in items if i['zone'] in ('terrace', 'flower')}
        for m in fixed:
            if m['facility'] in PAV and m['facility'] not in in_terr and not (m['facility'] == 'Floral Windmill' and flower):
                x, y, s = PAV[m['facility']]
                items.append({'kind': 'piece', 'n': m['facility'], 'item': m.get('crop') or '', 'x': x, 'y': y, 'w': s, 'h': s, 'weight': m.get('weight') or 0, 'idle': not m.get('weight'), 'zone': 'pavilion'})
        others = [m['facility'] for m in fixed if m['facility'] not in FP and m['facility'] not in ('Mine', 'Well') and m['facility'] not in PAV]
        # occupancy for power: everything placed, kiosks, hatchery, kept-clear paths, terraces
        occupied = [dict(x=i['x'], y=i['y'], w=i['w'], h=i['h']) for i in items] + [{'x': x, 'y': y, 'w': 2, 'h': 2} for x, y in KIOSK.values()] + CLEAR + [{k: t[k] for k in 'xywh'} for t in TERRACES + (TERR_NE if L >= 18 else [])] + ([{'x': 40.2, 'y': .6, 'w': 18, 'h': 10.2}] if L >= 16 else []) + ([{k: t[k] for k in 'xywh'} for t in EXTRA] if key[-1] else [])
        occupied += [{'x': x, 'y': y, 'w': 2, 'h': 2} for x, y in HATCH]
        r1 = power(items, occupied, L); r2 = power_greedy(items, occupied, L)
        gens, poles, areas, pw, tg = max((r1, r2), key=lambda r: r[3])
        # checks
        probs = climate({'items': items}, LAY[L])[0]
        allr = [dict(n=i['n'], x=i['x'], y=i['y'], w=i['w'], h=i['h']) for i in items] + [dict(n='kiosk', x=x, y=y, w=2, h=2) for x, y in KIOSK.values()] + [dict(n='gen', **g) for g in gens] + [dict(n='pole', **p) for p in poles]
        bad = [(a['n'], b['n']) for k, a in enumerate(allr) for b in allr[k + 1:] if ov(a, b)]
        bad += [(a['n'], 'locked') for a in allr if not plot_open(a, L)]
        stw = [cen({'x': x, 'y': y, 'w': 2, 'h': 2}) for x, y in KIOSK.values()]
        act = [i for i in items if i['kind'] == 'piece' and (i.get('weight') or 0) > 0]
        avg = sum(i['weight'] * min(math.dist(cen(i), s) for s in stw) for i in act) / sum(i['weight'] for i in act)
        levels[L] = {'extra': key[-1], 'items': items, 'squares': squares, 'gens': gens, 'poles': poles, 'areas': areas, 'powered': [pw, tg], 'avg': round(avg, 2),
                     'climateMiss': probs, 'overlaps': bad, 'unplaced': out['metrics']['unplaced'], 'others': others}
        print(f'RV{L}: items {len(items)}, walk {avg:.2f}, power {pw}/{tg}, climate problems {probs}, overlaps {bad[:6]}, unplaced {out["metrics"]["unplaced"]}', flush=True)
        prev_items = [it for it in out['items']]
    json.dump({'levels': levels, 'lots': [{'n': i['n'], 'k': i['k'], 'lot': i['lot'], 'w': {L: i['w'][L] for L in LEVELS}} for i in inst], 'kiosks': KIOSK,
               'terraces': TERRACES, 'terrNE': TERR_NE, 'extra': EXTRA, 'reserve': reserve}, open(os.path.join(S, 'garden_levels.json'), 'w'))


if __name__ == '__main__':
    main()
