
# ---------------- construction steps: from today's Foyer to RV 14, then level by level ----------------
ov = ovr
CUR = json.load(open(os.path.join(S, 'current_rv14.json')))
def cardinal(r):
    cx, cy = r['x'] + r['w'] / 2, r['y'] + r['h'] / 2
    ns = 'nord' if cy < 20 else ('sud' if cy > 40 else '')
    ew = 'ouest' if cx < 27 else ('est' if cx > 53 else '')
    if not ns and not ew:
        return 'au centre'
    return ("à l'" if not ns else 'au ') + '-'.join(x for x in (ns, ew) if x)
def zone_of(it):
    z = it.get('zone')
    if z == 'street':
        return f'rue des artisans, côté {"nord" if it["y"] < 17 else "sud"}'
    if z == 'terrace':
        return 'terrasse de la montagne' if it['x'] >= 60 and it['y'] < 15 else ('terrasse ouest' if it['x'] < 40 else 'terrasse est')
    return {'quarry': 'carrière', 'wells': 'au nord de la rue', 'pavilion': 'au nord, parmi les pavillons', 'flower': 'jardin des fleurs',
            'kiosk': 'à sa place numérotée', 'hatch': 'pavillon des éclosions', 'power': 'réseau électrique'}.get(z, '')
ZORDER = ['rue des artisans, côté nord', 'rue des artisans, côté sud', 'au nord de la rue', 'au nord, parmi les pavillons', 'carrière', 'terrasse ouest', 'terrasse est',
          'jardin des fleurs', 'terrasse de la montagne', 'à sa place numérotée', 'pavillon des éclosions', 'réseau électrique']
PLUR = {'Farmland': 'champs', 'Woodland': 'pépinières', 'Mine': 'mines', 'Well': 'puits', 'Storage Unit': 'stockages', 'Incubateur': 'éclorateurs', 'Crackle Power Pole': 'poteaux'}
def fname(n, k=1, unit=None):
    if k > 1:
        return f'{k} {PLUR.get(n, FR.get(n, n))}'
    if unit is not None and n in FP_ALL:
        return mlabel(n, unit)
    return {'Storage Unit': 'un stockage', 'Incubateur': 'éclorateur'}.get(n, FR.get(n, n))
def lv_ids(L):
    lv = GL['levels'][str(L)]
    n = len(lv['items'])
    return lv, (lambda k: f'{L}-{k + 1}'), [f'{L}-{n + 1 + g}' for g in range(len(lv['gens']))], [f'{L}-{n + 1 + len(lv["gens"]) + p}' for p in range(len(lv['poles']))]
STEPS = {}

# --- today's Foyer -> RV 14 ---
lv, iid, gids, pids = lv_ids(14)
tgt = []
for k, it in enumerate(lv['items']):
    tgt.append({'n': it['n'], 'r': {q: it[q] for q in 'xywh'}, 'id': iid(k), 'zone': zone_of(it), 'unit': it.get('unit')})
for k, (x, y) in KIOSK.items():
    tgt.append({'n': 'Storage Unit', 'r': {'x': x, 'y': y, 'w': 2, 'h': 2}, 'id': None, 'zone': f'stockage {k}', 'unit': None})
for n, r, ph in PHYS:
    if n == 'éclorateur':
        tgt.append({'n': 'Incubateur', 'r': dict(r), 'id': None, 'zone': 'pavillon des éclosions', 'unit': None})
for g, gid in zip(lv['gens'], gids):
    tgt.append({'n': 'Crackle Generator', 'r': dict(g), 'id': gid, 'zone': 'réseau électrique', 'unit': None})
for p, pid in zip(lv['poles'], pids):
    tgt.append({'n': 'Crackle Power Pole', 'r': dict(p), 'id': pid, 'zone': 'réseau électrique', 'unit': None})
cur = [dict(n=i['n'], r={q: i[q] for q in 'xywh'}) for i in CUR['items']] + [dict(n='Storage Unit', r=dict(s)) for s in CUR['stores']] + \
      [dict(n='Crackle Generator', r=dict(g)) for g in CUR['gens']] + [dict(n='Crackle Power Pole', r=dict(p)) for p in CUR['poles']]
for k, c_ in enumerate(cur):
    c_['k'] = k
cen2 = lambda r: (r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)
pairs, extra_cur, new_tgt = [], [], []
for n in sorted({t['n'] for t in tgt} | {c_['n'] for c_ in cur}):
    T_ = [t for t in tgt if t['n'] == n]; C_ = [c_ for c_ in cur if c_['n'] == n]
    cand = sorted(((math.dist(cen2(t['r']), cen2(c_['r'])), ti, ci) for ti, t in enumerate(T_) for ci, c_ in enumerate(C_)))
    ut, uc = set(), set()
    for d, ti, ci in cand:
        if ti in ut or ci in uc:
            continue
        ut.add(ti); uc.add(ci); pairs.append({'c': C_[ci], 't': T_[ti], 'stored': False, 'done': False})
    extra_cur += [C_[ci] for ci in range(len(C_)) if ci not in uc]
    new_tgt += [T_[ti] for ti in range(len(T_)) if ti not in ut]
occ = {c_['k']: c_['r'] for c_ in cur}
raw = []
if extra_cur:
    for c_ in extra_cur:
        occ.pop(c_['k'])
    by = {}
    for c_ in extra_cur:
        by.setdefault(c_['n'], []).append(c_)
    def back(n):
        c14 = sum(1 for t in tgt if t['n'] == n)
        for L in LEVELS[1:]:
            if sum(1 for it in GL['levels'][str(L)]['items'] if it['n'] == n) > c14:
                return L
        return None
    later = {n: v for n, v in by.items() if back(n)}
    never = {n: v for n, v in by.items() if not back(n)}
    if later:
        raw.append({'grp': 'prep', 'a': 'store_extra', 'txt': 'Range dans l\'inventaire ce qui attend un palier suivant : ' + ', '.join(f'{fname(n, len(v))} ({cardinal(v[0]["r"])}, ressort au VR {back(n)})' for n, v in later.items()) + '.'})
    if never:
        raw.append({'grp': 'prep', 'a': 'store_extra', 'txt': 'Range dans l\'inventaire ce qui ne sert plus jusqu\'au VR 20 : ' + ', '.join(f'{fname(n, len(v))} ({cardinal(v[0]["r"])})' for n, v in never.items()) + '.'})
pend = [p for p in pairs if not (abs(p['c']['r']['x'] - p['t']['r']['x']) < 1e-6 and abs(p['c']['r']['y'] - p['t']['r']['y']) < 1e-6)]
seq = []
last = None
def free_for(p):
    return not any(ov(p['t']['r'], r) for k, r in occ.items() if k != p['c']['k'])
zrank = lambda z: next((i for i, s in enumerate(ZORDER) if z.startswith(s.split(',')[0]) and (s == z or ',' not in s)), len(ZORDER))
while pend:
    ok = [p for p in pend if free_for(p)]
    if ok:
        same = [p for p in ok if last and (p['c']['n'], p['t']['zone']) == last]
        p = (same or sorted(ok, key=lambda p: (zrank(p['t']['zone']), p['t']['r']['y'], p['t']['r']['x'])))[0]
        occ[p['c']['k']] = p['t']['r']
        seq.append(('move', p)); pend.remove(p); last = (p['c']['n'], p['t']['zone'])
        continue
    # stuck: put aside what blocks the piece with the fewest blockers
    best = min(pend, key=lambda p: sum(1 for k, r in occ.items() if k != p['c']['k'] and ov(p['t']['r'], r)))
    for k in [k for k, r in occ.items() if k != best['c']['k'] and ov(best['t']['r'], r)]:
        q = next(q for q in pend if q['c']['k'] == k)
        occ.pop(k); q['stored'] = True
        seq.append(('aside', q))
    last = None
# merge consecutive steps of the same kind, piece and zone
for a, p in seq:
    key = (a, p['c']['n'], p['t']['zone'] if a == 'move' else cardinal(p['c']['r']), p['stored'] if a == 'move' else None)
    if raw and raw[-1].get('key') == key:
        raw[-1]['ps'].append(p)
    else:
        raw.append({'grp': 'move', 'a': a, 'key': key, 'ps': [p]})
steps14 = []
for s in raw:
    if s['a'] == 'store_extra':
        steps14.append({'g': 'Préparer', 't': s['txt'], 'ids': []})
        continue
    ps = s['ps']; n = ps[0]['c']['n']; k = len(ps)
    nm = fname(n, k, ps[0]['t'].get('unit'))
    if s['a'] == 'aside':
        steps14.append({'g': 'Déplacer', 't': f'Range pour un moment {"les " + nm if k > 1 else "le " + nm if not nm[0] in "aeiouéÉ" else "l’" + nm} ({cardinal(ps[0]["c"]["r"])}) : {"ils gênent" if k > 1 else "il gêne"} la suite.', 'ids': [], 'warn': True})
    else:
        z = ps[0]['t']['zone']
        frm = cardinal(ps[0]['c']['r'])
        verb = 'Ressors de l\'inventaire' if ps[0]['stored'] else 'Déplace'
        dest = f'emplacement du {z}' if z.startswith('stockage') else z
        steps14.append({'g': 'Déplacer', 't': f'{verb} {nm}' + ('' if ps[0]['stored'] else f' ({frm})') + f' → {dest}.', 'ids': [p['t']['id'] for p in ps if p['t']['id']],
                        'ic': pic_fac(n) if n != 'Incubateur' else None})
nt = {}
for t in new_tgt:
    nt.setdefault((t['n'], t['zone']), []).append(t)
for (n, z), ts in nt.items():
    steps14.append({'g': 'Déplacer', 't': f'Pose {len(ts)} × {FR.get(n, n)} en plus → {z} (pas posé aujourd\'hui : sors-le de l\'inventaire ou fabrique-le).', 'ids': [t['id'] for t in ts if t['id']], 'ic': pic_fac(n)})
steps14.append({'g': 'Décor', 't': 'Grand arbre violet : pose-le au centre de la cour, taille ×1,6.', 'ids': []})
for b in [b for b in buy if b['ph'] == 14]:
    steps14.append({'g': 'Décor', 't': f'Pose {b["n"]} × {b["fr"]} (voir « Ce qu\'il faut acheter » et le plan).', 'ids': [], 'key': b['id'] if b['id'].startswith('jp') else 'jp' + b['id']})
steps14.append({'g': 'Régler', 't': 'Règle chaque machine et chaque appareil de climat comme sur sa fiche (« Quoi produire »).', 'ids': [], 'go': 'prod'})
steps14.append({'g': 'Régler', 't': 'Affecte les Aniimo comme dans « Qui va où ».', 'ids': [], 'go': 'who'})
STEPS[14] = {'from': 'ton Foyer actuel', 'steps': steps14}

# --- level by level ---
def env_list(L):
    lv = GL['levels'][str(L)]
    return [(k, it) for k, it in enumerate(lv['items']) if it['kind'] == 'env']
for L in LEVELS[1:]:
    P = L - 1
    lv, iid, gids, pids = lv_ids(L)
    pv = GL['levels'][str(P)]
    st = []
    # new ground and decor
    if L == 16:
        st.append({'g': 'Nouveau', 't': 'Les parcelles du nord-est s\'ouvrent : bosquet de bambous, et la rue des artisans s\'allonge vers l\'est.', 'ids': []})
    if L == 20 and lv.get('extra'):
        st.append({'g': 'Nouveau', 't': 'Ouvre la terrasse de la montagne derrière la carrière : range les deux roches et le pin de la montagne pour lui faire place.', 'ids': []})
    for b in [b for b in buy if b['ph'] == L]:
        st.append({'g': 'Nouveau', 't': f'Achète et pose {b["n"]} × {b["fr"]}.', 'ids': [], 'key': b['id'] if b['id'].startswith('jp') else 'jp' + b['id']})
    # street machines
    for k, it in enumerate(lv['items']):
        if it['n'] not in FP_ALL:
            continue
        key = (it['n'], it.get('unit', 0)); t = mlabel(*key)
        now, before = MJOBS[L].get(key, []), MJOBS[P].get(key)
        if before is None:
            st.append({'g': 'Rue des artisans', 't': f'Pose {t} sur son emplacement ({zone_of(it)})' + (f', recette : {", ".join(now)}.' if now else ', à l\'arrêt pour l\'instant.'), 'ids': [iid(k)], 'ic': pic_fac(it['n'])})
        elif now != before:
            if not now:
                st.append({'g': 'Rue des artisans', 't': f'Arrête {t} : plus rien à y produire.', 'ids': [iid(k)], 'ic': pic_fac(it['n'])})
            elif not before:
                st.append({'g': 'Rue des artisans', 't': f'Remets {t} en route : {", ".join(now)}.', 'ids': [iid(k)], 'ic': pic_fac(it['n'])})
            else:
                st.append({'g': 'Rue des artisans', 't': f'{t} : passe de {", ".join(before)} à {", ".join(now)}.', 'ids': [iid(k)], 'ic': pic_fac(it['n'])})
    # climate devices
    pe, ne = env_list(P), env_list(L)
    for k, e in ne:
        same = [x for _, x in pe if x['n'] == e['n'] and abs(x['x'] - e['x']) < 1e-6 and abs(x['y'] - e['y']) < 1e-6]
        lab = FR.get(e['n'])
        if not same:
            st.append({'g': 'Terrasses', 't': f'Place {lab} ici ({zone_of(e)}) et règle-la sur {MODEFR.get(e["mode"], e["mode"])}.', 'ids': [iid(k)], 'ic': pic_fac(e['n'])})
        elif same[0]['mode'] != e['mode']:
            st.append({'g': 'Terrasses', 't': f'Règle {lab} ({zone_of(e)}) sur {MODEFR.get(e["mode"], e["mode"])} au lieu de {MODEFR.get(same[0]["mode"], same[0]["mode"])}.', 'ids': [iid(k)], 'ic': pic_fac(e['n'])})
    # fields, nurseries, terrace pavilions
    def pieces(v):
        return {(it['n'], round(it['x'], 2), round(it['y'], 2)): (k, it.get('item') or '') for k, it in enumerate(v['items'])
                if it['kind'] == 'piece' and it['zone'] in ('terrace', 'flower')}
    a, b = pieces(pv), pieces(lv)
    gone = [p for p in a if p not in b]
    if gone:
        cnt = {}
        for p in gone:
            cnt[p[0]] = cnt.get(p[0], 0) + 1
        st.append({'g': 'Terrasses', 't': 'Retire d\'abord ' + ', '.join(fname(n, c_) if c_ > 1 else 'un ' + fname(n) for n, c_ in cnt.items()) + ' qui changent de place (ils seront reposés juste après).', 'ids': []})
    grp = {}
    for p in b:
        if p not in a:
            grp.setdefault((p[0], b[p][1]), []).append(iid(b[p][0]))
    for (n, crop), ids_ in sorted(grp.items(), key=lambda kv: -len(kv[1])):
        st.append({'g': 'Terrasses', 't': f'Pose {fname(n, len(ids_)) if len(ids_) > 1 else "1 " + fname(n)} : {pfr(crop) if crop else "—"}' + (' (dans le jardin des fleurs).' if n == 'Floral Windmill' else '.'), 'ids': ids_, 'ic': pic_item(crop) or pic_fac(n)})
    rep = {}
    for p in b:
        if p in a and a[p][1] != b[p][1]:
            rep.setdefault((p[0], a[p][1], b[p][1]), []).append(iid(b[p][0]))
    for (n, o, nw), ids_ in rep.items():
        st.append({'g': 'Terrasses', 't': f'Replante {fname(n, len(ids_)) if len(ids_) > 1 else "1 " + fname(n)} sur place : {pfr(o)} → {pfr(nw)}.', 'ids': ids_, 'ic': pic_item(nw)})
    # quarry, wells, northern pavilions
    for zn, nm in (('quarry', 'Mine'), ('wells', 'Well'), ('pavilion', None)):
        pa = {(it['n'], it['x'], it['y']): it.get('item') or '' for it in pv['items'] if it['zone'] == zn}
        grp2 = {}
        for k, it in enumerate(lv['items']):
            if it['zone'] != zn:
                continue
            pos = (it['n'], it['x'], it['y'])
            if pos not in pa:
                grp2.setdefault(('new', it['n'], '', it.get('item') or '', zone_of(it)), []).append(iid(k))
            elif pa[pos] != (it.get('item') or ''):
                grp2.setdefault(('chg', it['n'], pa[pos], it.get('item') or '', zone_of(it)), []).append(iid(k))
        for (kind, n, o, nw, z), ids_ in grp2.items():
            lab = fname(n, len(ids_)) if len(ids_) > 1 else fname(n)
            if kind == 'new':
                st.append({'g': 'Carrière, puits, pavillons', 't': f'Pose {lab if len(ids_) > 1 else "1 × " + lab} ({z}) : {pfr(nw) or "à l’arrêt"}.', 'ids': ids_, 'ic': pic_fac(n)})
            else:
                st.append({'g': 'Carrière, puits, pavillons', 't': f'{lab[0].upper() + lab[1:]} ({z}) : {pfr(o) or "à l’arrêt"} → {pfr(nw) or "à l’arrêt"}.', 'ids': ids_, 'ic': pic_fac(n)})
    # electricity
    pg = {(g['x'], g['y']) for g in pv['gens']}; pp = {(p['x'], p['y']) for p in pv['poles']}
    mg = [gid for g, gid in zip(lv['gens'], gids) if (g['x'], g['y']) not in pg]
    mp = [pid for p, pid in zip(lv['poles'], pids) if (p['x'], p['y']) not in pp]
    if mg:
        st.append({'g': 'Électricité', 't': f'Déplace {len(mg)} générateur{"s" if len(mg) > 1 else ""} (surligné{"s" if len(mg) > 1 else ""} sur le plan).', 'ids': mg, 'ic': pic_fac('Crackle Generator')})
    if mp:
        st.append({'g': 'Électricité', 't': f'Déplace {len(mp)} poteau{"x" if len(mp) > 1 else ""} vers {"leurs" if len(mp) > 1 else "sa"} nouvelle{"s" if len(mp) > 1 else ""} place{"s" if len(mp) > 1 else ""}.', 'ids': mp, 'ic': pic_fac('Crackle Power Pole')})
    # Aniimo
    for p_, posts in ALAB[L].items():
        old = ALAB[P].get(p_, [])
        if posts != old:
            st.append({'g': 'Aniimo', 't': (', '.join(old) or 'libre') + ' → ' + (', '.join(posts) or 'libre'), 'ids': [], 'por': p_})
    STEPS[L] = {'from': f'VR {P}', 'steps': st}
for L, v in STEPS.items():
    for k, s in enumerate(v['steps']):
        s['k'] = f'{L}:{k}'
print('steps', {L: len(v['steps']) for L, v in STEPS.items()})

# ---------------- budget of each level: seeds for the level, new decor, pieces to get ----------------
owned = {}
for it in CUR['items']:
    owned[it['n']] = owned.get(it['n'], 0) + 1
owned['Crackle Generator'] = len(CUR['gens']); owned['Crackle Power Pole'] = len(CUR['poles'])
seen_max = dict(owned)
for L in LEVELS:
    lv = GL['levels'][str(L)]
    need = {}
    for it in lv['items']:
        need[it['n']] = need.get(it['n'], 0) + 1
    need['Crackle Generator'] = len(lv['gens']); need['Crackle Power Pole'] = len(lv['poles'])
    new = []
    for n, k in sorted(need.items(), key=lambda kv: FR.get(kv[0], kv[0])):
        have = seen_max.get(n, 0)
        if k > have:
            new.append({'n': FR.get(n, n), 'k': k - have, 'ic': pic_fac(n)})
            seen_max[n] = k
    fl = FOYER_L.get(str(L), {})
    seeds, stot = [], 0
    for r in fl.get('seeds') or []:
        try:
            cost = float(r[3]) if r[3] not in (None, '', 'free') else 0
        except (TypeError, ValueError):
            cost = 0
        per = 86400 if not fl.get('luRows') else 1   # last level: the plan gives rates per second, shown per day
        nm = pfr(snake(r[0]))
        same = next((x for x in seeds if x['n'] == nm), None)
        if same:
            same['plots'] += int(r[1]); same['seeds'] += round(float(r[2]) * per); same['cost'] += round(cost * per)
        else:
            seeds.append({'n': nm, 'ic': pic_item(snake(r[0])), 'plots': int(r[1]), 'seeds': round(float(r[2]) * per), 'cost': round(cost * per)})
        stot += round(cost * per)
    deco = [{'n': b['fr'], 'k': b['n'], 'pr': b['pr'], 'ic': b['ic']} for b in buy if b['ph'] == L]
    STEPS[L]['budget'] = {'perDay': not fl.get('luRows'), 'seeds': seeds, 'seedsTotal': stot, 'deco': deco, 'decoTotal': sum(d['k'] * d['pr'] for d in deco), 'new': new}

# ---------------- what the design costs: the same production, but porters walk further ----------------
DESIGN = {}
for L in LEVELS:
    fl = FOYER_L.get(str(L), {})
    lv = GL['levels'][str(L)]
    md = json.load(open(os.path.join(S, f'my_data_rv{L}.json')))
    kc = [(x + 1, y + 1) for x, y in KIOSK.values()]
    g, p = {}, {}
    for it in lv['items']:
        w = it.get('weight') or 0
        if w <= 0 or it['kind'] != 'piece':
            continue
        d = min(math.dist((it['x'] + it['w'] / 2, it['y'] + it['h'] / 2), c) for c in kc)
        key = (it['n'], it.get('item') or '')
        g[key] = g.get(key, 0) + w * d
    for pc in md['pieces']:
        st = pc.get('stats') or ''
        if pc.get('kind') != 'piece' or 'tiles from storage' not in st:
            continue
        try:
            w = float(st.split(' trips/hour')[0].replace(',', ''))
            d = float(st.split('· ')[1].split(' tiles')[0])
        except (ValueError, IndexError):
            continue
        key = (pc['name'], snake(pc.get('detail') or ''))
        p[key] = p.get(key, 0) + w * d
    gap = []
    for key, v in g.items():
        pv = p.get((key[0], snake(key[1])), p.get((key[0], snake(key[1][6:] if key[1].startswith('quick_') else key[1])), 0))
        if v - pv > 0:
            gap.append({'n': FR.get(key[0], key[0]) + (' · ' + pfr(key[1]) if key[1] else ''), 'ic': pic_fac(key[0]), 'extra': round(v - pv)})
    gap.sort(key=lambda x: -x['extra'])
    trips = fl.get('trips') or 0
    DESIGN[L] = {'trips': trips, 'garden': lv['avg'], 'plan': fl.get('avg'), 'rate': fl.get('rate'), 'top': gap[:5]}
