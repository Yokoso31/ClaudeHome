"""Pick the best powered layout per RV level and compose a decor proposal in its free plazas."""
import json, os, glob
PFX = os.environ.get('PREFIX', '')

S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FUR = {i['id']: i for i in json.load(open(os.path.join(S, 'web', 'furniture.json')))}
FP = json.load(open(os.path.join(S, 'web', 'deco_fp.json')))

def item(i):
    f = FUR[i]
    p = f.get('price') or ''
    cur = 'wheat' if 'Moonray' in p else 'bud' if 'Bud' in p else 'none'
    w, h = FP[i]['fp']
    return {'id': i, 'w': w, 'h': h, 'cf': f['comfort'], 'pr': f['priceNum'] if cur != 'none' else 0, 'cur': cur, 'max': f['max'] or 1}

CENTER = [item('40300022'), item('40500007'), item('40500002')]          # Laurier, Balançoire, Pavillon
CORNER = [item('40700022'), item('40700025'), item('40700024')]          # Pluie d'étoiles, Pluie d'osmanthe, Lumille
MID = [item('41100009'), item('40900018'), item('40700023')]             # Lune radieuse, Table ronde, Feuilles pourpres
STOOLS = [item('40900020'), item('40900019')]                            # tabourets
STALL = item('40500013')                                                 # Étal de marché 2x1
BORDER = [item('40500012'), item('40200022')]                            # Charme d'osmanthe 2.5x.25, Vague de riz 1x.25

def overlap(a, b):
    return a['x'] < b['x'] + b['w'] - 1e-6 and b['x'] < a['x'] + a['w'] - 1e-6 and a['y'] < b['y'] + b['h'] - 1e-6 and b['y'] < a['y'] + a['h'] - 1e-6

def compose(plazas, keep=None):
    used = {}
    placed = []
    for k in (keep or []):
        placed.append(dict(k)); used[k['id']] = used.get(k['id'], 0) + 1
    def can(it):
        return used.get(it['id'], 0) < it['max']
    def put(it, x, y, rot=False):
        w, h = (it['h'], it['w']) if rot else (it['w'], it['h'])
        r = {'id': it['id'], 'x': round(x, 2), 'y': round(y, 2), 'w': w, 'h': h}
        if any(overlap(r, p) for p in placed):
            return False
        placed.append(r)
        used[it['id']] = used.get(it['id'], 0) + 1
        return True
    for k, pz in enumerate(plazas):
        x0, y0, W, H = pz['x'] + 0.5, pz['y'] + 0.5, pz['w'] - 1, pz['h'] - 1
        if W < 1 or H < 1:
            continue
        inside = lambda r: r['x'] >= x0 - 1e-6 and r['y'] >= y0 - 1e-6 and r['x'] + r['w'] <= x0 + W + 1e-6 and r['y'] + r['h'] <= y0 + H + 1e-6
        def tryput(it, x, y, rot=False):
            w, h = (it['h'], it['w']) if rot else (it['w'], it['h'])
            if not can(it) or not inside({'x': x, 'y': y, 'w': w, 'h': h}):
                return False
            return put(it, x, y, rot)
        cx, cy = x0 + W / 2, y0 + H / 2
        center = None
        for it in CENTER:
            if it['w'] <= W and it['h'] <= H and can(it) and tryput(it, cx - it['w'] / 2, cy - it['h'] / 2):
                center = it
                break
        # corners: 3x3 lanterns
        if W >= 6.5 and H >= 6.5:
            spots = [(x0, y0), (x0 + W - 3, y0), (x0, y0 + H - 3), (x0 + W - 3, y0 + H - 3)]
            for j, (sx, sy) in enumerate(spots):
                for it in CORNER[j % 3:] + CORNER[:j % 3]:
                    if tryput(it, sx, sy):
                        break
        # mid-edges: Lune radieuse / table ronde with stools
        mids = [(cx - 0.75, y0), (cx - 0.75, y0 + H - 1.5), (x0, cy - 0.75), (x0 + W - 1.5, cy - 0.75)]
        for j, (sx, sy) in enumerate(mids):
            for it in MID:
                if tryput(it, sx, sy):
                    if it['id'] == '40900018':  # table: two stools beside it
                        for st, (ox, oy) in zip(STOOLS, [(-0.6, 0.5), (1.6, 0.5)]):
                            tryput(st, sx + ox, sy + oy)
                    break
        # long narrow plazas: market stalls along the axis
        if min(W, H) < 6.5:
            if W >= H:
                x = x0
                while x + 2 <= x0 + W:
                    tryput(STALL, x, cy - 0.5)
                    x += 3
            else:
                y = y0
                while y + 2 <= y0 + H:
                    tryput(STALL, cx - 0.5, y, rot=True)
                    y += 3
        # borders: osmanthus charm, then rice wave, along the plaza's edges
        for b in BORDER:
            step = b['w']
            for (yy) in (pz['y'] + 0.1, pz['y'] + pz['h'] - 0.35):
                x = pz['x'] + 0.25
                while x + step <= pz['x'] + pz['w'] - 0.25 + 1e-6:
                    r = {'id': b['id'], 'x': x, 'y': yy, 'w': b['w'], 'h': b['h']}
                    if can(b) and not any(overlap(r, p) for p in placed):
                        placed.append({k2: (round(v, 2) if isinstance(v, float) else v) for k2, v in r.items()}); used[b['id']] = used.get(b['id'], 0) + 1
                    x += step
            for xx in (pz['x'] + 0.1, pz['x'] + pz['w'] - 0.35):
                y = pz['y'] + 0.6
                while y + step <= pz['y'] + pz['h'] - 0.6 + 1e-6:
                    r = {'id': b['id'], 'x': xx, 'y': y, 'w': b['h'], 'h': b['w']}
                    if can(b) and not any(overlap(r, p) for p in placed):
                        placed.append({k2: (round(v, 2) if isinstance(v, float) else v) for k2, v in r.items()}); used[b['id']] = used.get(b['id'], 0) + 1
                    y += step
    tot = {'cf': 0, 'wheat': 0, 'bud': 0}
    for p in placed:
        it = FUR[p['id']]
        c = 'wheat' if 'Moonray' in (it.get('price') or '') else 'bud'
        tot['cf'] += it['comfort']
        tot[c] += it['priceNum']
    return placed, used, tot

def occupied_rects(d):
    rs = [dict(x=i['x'], y=i['y'], w=i['w'], h=i['h']) for i in d['items']] + d['stores'] + d['gens'] + d['poles']
    rs += [dict(x=x, y=y, w=1, h=1) for x, y in d['walk']]
    return rs

out = {}
evo = {}
for lvl in range(14, 21):
    cands = []
    for f in glob.glob(os.path.join(S, f'{PFX}multi_rv{lvl}_k5_g1_h*_e1.5.json')):
        d = json.load(open(f))
        act = sum(1 for u in d['unpowered'] if not u['idle'])
        cands.append((act, d['metrics']['avg'], -d['powered'], f, d))
    cands.sort(key=lambda c: c[:3])
    act, avg, _, f, d = cands[0]
    if lvl == 14:
        f = os.path.join(S, os.environ.get('BASE14', f'{PFX}multi_rv14_k5_g1_h4_e1.5.json')); d = json.load(open(f))
    placed, used, tot = compose(d['plazas'][:4])
    d['deco'] = placed; d['decoTot'] = tot; d['choice'] = os.path.basename(f)
    out[lvl] = d
    print('opt', lvl, os.path.basename(f), 'avg', d['metrics']['avg'], 'deco', len(placed), tot)
    # evolving chain: keep the previous decor where it still fits
    if lvl == 14:
        e = json.loads(json.dumps(d))
    else:
        e = json.load(open(os.path.join(S, f'{PFX}evo_rv{lvl}.json')))
        occ = occupied_rects(e)
        keep = [k for k in evo[lvl - 1]['deco'] if not any(overlap(k, r) for r in occ)]
        placed, used, tot = compose(e['plazas'][:4], keep)
        prev_ids = {(k['id'], k['x'], k['y']) for k in evo[lvl - 1]['deco']}
        for pz in placed:
            pz['st0'] = 'ok' if (pz['id'], pz['x'], pz['y']) in prev_ids else 'new'
        e['deco'] = placed; e['decoTot'] = tot
        e['decoKept'] = len(keep); e['decoDropped'] = len(evo[lvl - 1]['deco']) - len(keep)
        print('evo', lvl, 'avg', e['metrics']['avg'], 'deco kept', len(keep), 'dropped', e['decoDropped'], 'total', len(placed))
    evo[lvl] = e
json.dump(out, open(os.path.join(S, f'{PFX}final_layouts.json'), 'w'))
json.dump(evo, open(os.path.join(S, f'{PFX}final_evo.json'), 'w'))
