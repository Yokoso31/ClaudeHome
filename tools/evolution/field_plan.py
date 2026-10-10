"""Climate blocks of a level placed on the climate spots the player already has.

For each block of the level's plan (one climate building and the plots it must cover), find a spot
of the previous layout whose 9x9 square already holds most of those plots, put the right building
there (same one, another setting, or another kind), reuse the plots inside, and add only what is
missing at free spots inside the square. A block too big for one spot is split over two when a
spare building of that kind is owned. Blocks that fit nowhere stay as clusters for the planner.

Writes the level's planner input (fitted blocks as single pinned pieces) and a pin file: the
previous layout with the fitted pieces at their chosen spots, which plan_multi.mjs reads as PREV.
Usage: field_plan.py <lvl> <prev layout> <lay_in> <out lay_in> <out pins>
"""
import json, math, sys

OWNED = {'Heat Furnace': 2, 'Cooling Unit': 2, 'Sunlamp': 2}
SIZE = {'Heat Furnace': 1, 'Cooling Unit': 2, 'Sunlamp': 1}
DEV_OF = {'Warm': 'Heat Furnace', 'Scorching': 'Heat Furnace', 'Cool': 'Cooling Unit', 'Freeze': 'Cooling Unit', 'Adequate': 'Sunlamp'}
E = 1e-6


def ov(a, b):
    return min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']) > E and min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']) > E


def square(d):
    return {'x': d['x'] + d['w'] / 2 - 4.5, 'y': d['y'] + d['h'] / 2 - 4.5, 'w': 9, 'h': 9}


def main(lvl, prevf, inf, outf, pinf):
    P = json.load(open(prevf))
    L = json.load(open(inf))
    cells = L['cells']
    inside = lambda r: sum(max(0, min(r['x'] + r['w'], c['x'] + c['w']) - max(r['x'], c['x'])) * max(0, min(r['y'] + r['h'], c['y'] + c['h']) - max(r['y'], c['y'])) for c in cells) >= r['w'] * r['h'] - E
    prev_items = [dict(i) for i in P['items'] if not (i['kind'] == 'env' and not i.get('mode'))]
    for k, i in enumerate(prev_items):
        i['_k'] = k
    statics = [dict(r, n='Storage Unit') for r in P['stores']] + [dict(r, n='Crackle Generator') for r in P['gens']] + [dict(r, n='Crackle Power Pole') for r in P['poles']]
    slots = [i for i in prev_items if i['kind'] == 'env']
    crops = [i for i in prev_items if i['n'] in ('Farmland', 'Woodland')]

    # the level's climate blocks
    units, rest = [], []
    for p in L['pieces']:
        if p.get('cluster'):
            units.append(p)
        elif p['members'][0].get('building'):
            pass  # an idle climate building: stays in the bag
        else:
            rest.append(p)
    used_dev = {k: 0 for k in OWNED}
    for u in units:
        for b in u['buildings']:
            used_dev[b['facility']] += 1

    claimed = set()      # prev item keys reused by a fitted block
    chosen = []          # fitted blocks: {dev, square, plots: [(member, rect, prev_key or None)]}
    added = []           # new rects placed by fitting
    unfit = []
    pushed_all = set()   # spare crop plots pushed out of a block's square

    def blocked(r, own_sq=None, near=None):
        """r collides with something that stays (or was added), or reaches another block's square."""
        if not inside(r):
            return True
        for i in (near if near is not None else prev_items):
            if i['_k'] not in pushed_all and ov(r, i):
                return True
        for s in statics:
            if ov(r, s):
                return True
        for a in added:
            if ov(r, a):
                return True
        for c in chosen:
            if c['square'] is not own_sq and ov(r, c['square']):
                return True
        return False

    def try_slot(slot, members, devfac, dry=True, extra_free=()):
        """Fit `members` (plot dicts: facility, w, h) around `slot`; returns a fit or None."""
        best = None
        cx0, cy0 = slot['x'] + slot['w'] / 2, slot['y'] + slot['h'] / 2
        s = SIZE[devfac]
        for dx in (0, -.5, .5, -1, 1):
            for dy in (0, -.5, .5, -1, 1):
                dev = {'x': cx0 + dx - s / 2, 'y': cy0 + dy - s / 2, 'w': s, 'h': s}
                # the device may sit on its own old spot, nothing else
                if not inside(dev) or any(ov(dev, i) for i in prev_items if i['_k'] != slot['_k']) or any(ov(dev, x) for x in statics + added):
                    continue
                sq = square(dev)
                if any(ov(sq, c['square']) for c in chosen) or any(ov(sq, r) for c in chosen for _, r, _ in c['plan']):
                    continue
                plan, local_add, reuse = [], [], 0
                pushed = set()
                zone = {'x': sq['x'] - 6, 'y': sq['y'] - 6, 'w': 21, 'h': 21}
                near = [i for i in prev_items if ov(i, zone)]
                avail = [i for i in prev_items if i['_k'] not in claimed and i['kind'] == 'piece' and ov(i, sq) and not any(ov(i, c['square']) for c in chosen)]
                ok = True
                for m in members:
                    cand = next((i for i in avail if i['n'] == m['facility'] and {i['w'], i['h']} == {m['w'], m['h']} and not any(i is q for _, _, q in plan)), None)
                    if cand is not None:
                        plan.append((m, {k: cand[k] for k in 'xywh'}, cand)); reuse += 1
                        continue
                    # a free spot overlapping the square, nearest its center
                    spot = None; bd = 1e9
                    x = sq['x'] - m['w'] + .5
                    while x < sq['x'] + 9 - .5 + E:
                        y = sq['y'] - m['h'] + .5
                        while y < sq['y'] + 9 - .5 + E:
                            r = {'x': x, 'y': y, 'w': m['w'], 'h': m['h']}
                            if ov(r, sq) and not ov(r, dev) and not any(ov(r, q) for q in local_add) and not blocked(r, None, near):
                                d = math.hypot(x + m['w'] / 2 - (sq['x'] + 4.5), y + m['h'] / 2 - (sq['y'] + 4.5))
                                if d < bd:
                                    bd = d; spot = r
                            y += .5
                        x += .5
                    if spot is None:
                        # make room by pushing out spare crop plots the block doesn't use (the planner re-places them)
                        bd = 1e9; best_push = None
                        mine = {id(q) for _, _, q in plan if q is not None}
                        x = sq['x'] - m['w'] + .5
                        while x < sq['x'] + 9 - .5 + E:
                            y = sq['y'] - m['h'] + .5
                            while y < sq['y'] + 9 - .5 + E:
                                r = {'x': x, 'y': y, 'w': m['w'], 'h': m['h']}
                                if ov(r, sq) and not ov(r, dev) and inside(r) and not any(ov(r, q) for q in local_add):
                                    hit = [i for i in near if ov(r, i)]
                                    if all(i['n'] in ('Farmland', 'Woodland') and i['_k'] not in claimed and id(i) not in mine and i['_k'] not in pushed for i in hit) \
                                            and not any(ov(r, z) for z in statics + added) and not any(ov(r, c['square']) for c in chosen):
                                        d = len(hit) * 20 + math.hypot(x + m['w'] / 2 - (sq['x'] + 4.5), y + m['h'] / 2 - (sq['y'] + 4.5))
                                        if d < bd:
                                            bd = d; best_push = (r, hit)
                                y += .5
                            x += .5
                        if best_push is None:
                            ok = False; break
                        spot = best_push[0]
                        for i in best_push[1]:
                            pushed.add(i['_k'])
                        avail[:] = [i for i in avail if i['_k'] not in pushed]
                    local_add.append(spot); plan.append((m, spot, None))
                if not ok:
                    continue
                score = reuse * 10 - len(local_add) - 3 * len(pushed) - (0 if devfac == slot['n'] else .5) - abs(dx) - abs(dy)
                if best is None or score > best['score']:
                    best = {'score': score, 'dev': dev, 'square': sq, 'plan': plan, 'add': local_add, 'reuse': reuse, 'slot': slot, 'pushed': set(pushed)}
        return best

    def commit(fit, devfac, mode):
        claimed.add(fit['slot']['_k'])
        claimed.update(fit['pushed']); pushed_all.update(fit['pushed'])
        for m, r, q in fit['plan']:
            if q is not None:
                claimed.add(q['_k'])
        added.extend(fit['add'])
        chosen.append({'devfac': devfac, 'mode': mode, 'dev': fit['dev'], 'square': fit['square'], 'plan': fit['plan'], 'slot': fit['slot'], 'pushed': set(fit['pushed']), 'add': list(fit['add'])})

    def undo(c):
        chosen.remove(c); claimed.discard(c['slot']['_k'])
        for k2 in c['pushed']:
            claimed.discard(k2); pushed_all.discard(k2)
        for m, r, q in c['plan']:
            if q is not None:
                claimed.discard(q['_k'])
        for r in c['add']:
            added.remove(r)

    # blocks of the same setting share their plots: spread them over the spots that hold them best
    groups = {}
    for u in units:
        if len(u['buildings']) != 1:
            unfit.append(u); continue
        b = u['buildings'][0]
        g = groups.setdefault(b['mode'], {'devfac': b['facility'], 'mode': b['mode'], 'units': [], 'members': []})
        g['units'].append(u); g['members'] += u['plots']
    spare = {k: OWNED[k] - used_dev[k] for k in OWNED}
    rank = lambda m: (0 if m['facility'] not in ('Farmland', 'Woodland') else 1 if m['facility'] == 'Woodland' else 2, -m.get('weight', 0))
    import os
    if os.environ.get('NOFIT'):
        for g in groups.values():
            unfit.extend(g['units'])
        groups = {}
    for g in sorted(groups.values(), key=lambda g: -len(g['members'])):
        devfac, mode = g['devfac'], g['mode']
        devices = len(g['units'])
        left = sorted(g['members'], key=rank)
        mine = []
        while left and devices + spare[devfac] > 0:
            best = None
            for slot in [s for s in slots if s['_k'] not in claimed]:
                for order in (left, [m for m in left if m['facility'] in ('Farmland', 'Woodland')] + [m for m in left if m['facility'] not in ('Farmland', 'Woodland')]):
                    lo, hi, fit = 0, len(order), None
                    f = try_slot(slot, order, devfac)
                    if f:
                        lo, fit = len(order), f
                    else:
                        while lo < hi - 1 or (lo == 0 and hi == 1 and fit is None):
                            mid = (lo + hi + 1) // 2 if lo < hi - 1 else 1
                            f = try_slot(slot, order[:mid], devfac)
                            if f:
                                lo, fit = mid, f
                            else:
                                hi = mid
                            if lo == 0 and hi == 1:
                                break
                    if fit and (best is None or (lo, fit['score']) > (best[0], best[1]['score'])):
                        best = (lo, fit, order)
            if not best:
                break
            n, fit, order = best
            commit(fit, devfac, mode); mine.append(chosen[-1])
            taken = order[:n]
            left = [m for m in left if not any(m is t for t in taken)]
            if devices > 0:
                devices -= 1
            else:
                spare[devfac] -= 1
        if left:
            # what doesn't fit goes back to the planner as the plan's own blocks
            for c in mine:
                undo(c)
            spare[devfac] += max(0, len(mine) - len(g['units']))
            unfit.extend(g['units'])
        elif len(mine) != len(g['units']):
            print(lvl, 'regrouped', devfac, mode, [len(u['plots']) for u in g['units']], '->', [len(c['plan']) for c in mine])

    # planner input: fitted blocks become pinned single pieces
    pieces = list(rest) + unfit
    pins = []
    for c in chosen:
        pieces.append({'members': [{'x': 0, 'y': 0, 'w': c['dev']['w'], 'h': c['dev']['h'], 'weight': 0, 'facility': c['devfac'], 'crop': None, 'building': True, 'mode': c['mode'], 'sensitive': False, 'pinAt': {'x': c['dev']['x'], 'y': c['dev']['y']}}]})
        pins.append({'n': c['devfac'], 'kind': 'env', 'group': None, 'mode': c['mode'], **c['dev']})
        for m, r, q in c['plan']:
            pieces.append({'members': [{'x': 0, 'y': 0, 'w': r['w'], 'h': r['h'], 'weight': m['weight'], 'cycle': m.get('cycle'), 'facility': m['facility'], 'crop': m.get('crop'), 'sensitive': False, 'pinAt': {'x': r['x'], 'y': r['y']}}]})
            pins.append({'n': m['facility'], 'kind': 'piece', 'item': m.get('crop') or '', 'reserved': True, **r})
    L['pieces'] = pieces
    json.dump(L, open(outf, 'w'))
    # pin file: what was claimed is replaced by its new role; everything else as it was
    others = [{k: v for k, v in i.items() if k != '_k'} for i in prev_items if i['_k'] not in claimed and i['kind'] == 'piece']
    pinL = {'lvl': int(lvl), 'items': pins + others, 'stores': P['stores'], 'gens': P['gens'], 'poles': P['poles'], 'hubIdx': P.get('hubIdx'),
            'fixedSquares': [c['square'] for c in chosen],
            'fixedSensitive': [r for c in chosen for m, r, q in c['plan']]}
    json.dump(pinL, open(pinf, 'w'))
    rep = [(c['devfac'], c['mode'], len(c['plan']), sum(1 for _, _, q in c['plan'] if q is not None), (c['slot']['n'], c['slot']['x'], c['slot']['y'])) for c in chosen]
    print(lvl, 'fitted', rep, 'unfit', [[(b['facility'], b['mode']) for b in u['buildings']] + [len(u['plots'])] for u in unfit])


if __name__ == '__main__':
    main(*sys.argv[1:6])
