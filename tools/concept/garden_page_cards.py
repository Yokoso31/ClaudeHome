
# ---------------- "Quoi produire": one card per machine, recipes, what goes in, which Aniimo ----------------
REC = {r['name']: r for r in json.load(open(os.path.join(S, 'all_items.json')))}
TEAM = json.load(open(os.path.join(S, 'my_team.json')))
for line in open(os.path.join(S, 'foyer_data.js')).read().split('\n'):
    if line.startswith('window.ICONS='):
        PICON = json.loads(line[len('window.ICONS='):].rstrip().rstrip(';'))
ABFR = {'Fire': 'Feu', 'Water': 'Eau', 'Earth': 'Terre', 'Grass': 'Herbe', 'Lightning': 'Foudre', 'Ice': 'Glace', 'Wind': 'Vent', 'Dark': 'Obscurité',
        'Light': 'Lumière', 'Artisanship': 'Artisanat', 'Leisure': 'Loisir', 'Perfumery': 'Parfumerie', 'Hauling': 'Transport'}
JOBFR = {'Sowing': 'semer', 'Watering': 'arroser', 'Collecting': 'ramasser', 'Reaping': 'récolter', 'Logging': 'couper', 'Reclaiming': 'défricher'}
PICS = {}   # icon key -> data URI, only those the cards use
def pic_item(item):
    """Icon key of a product, from its internal name (quick_ variants share the plain product's icon)."""
    if not item:
        return None
    if 'fresh_water' in item and 'p:Plain Fresh Water' in PICON:
        PICS['p:Plain Fresh Water'] = PICON['p:Plain Fresh Water']
        return 'p:Plain Fresh Water'
    base = item
    for pre in ('quick_', 'premium_', 'advanced_'):
        base = base[len(pre):] if base.startswith(pre) else base
    for cand in (item, base):
        t = ' '.join(w.capitalize() for w in cand.split('_'))
        for k in ('p:' + t, 'p:' + t.replace(' ', '-', 1)):
            if k in PICON:
                PICS[k] = PICON[k]
                return k
        for k in PICON:
            if k.startswith('p:') and norm(k[2:]) == norm(t):
                PICS[k] = PICON[k]
                return k
    return None
def pic_fac(n):
    k = 'f:' + n
    if k in PICON:
        PICS[k] = PICON[k]
        return k
    return None
def snake(s):
    return '_'.join(norm(w) for w in (s or '').replace('-', ' ').replace('_', ' ').split())
EXTRA_FR = {'wood_block': 'Bloc de bois', 'mineral_sand': 'Sable minéral', 'natural_mineral_spring_water': 'Eau de source minérale naturelle'}
def ifr(item):
    """French name of an ingredient: the plan's own name, else its quick variant without « (rapide) »."""
    if item in EXTRA_FR:
        return EXTRA_FR[item]
    t = ' '.join(w.capitalize() for w in item.split('_'))
    if PROD.get(t) or PRODN.get(norm(t)) or item in MANUAL_FR:
        return pfr(item)
    q = pfr('quick_' + item)
    return q.replace(' (rapide)', '') if q and q != ' '.join(w.capitalize() for w in ('quick_' + item).split('_')) else pfr(item)
def recipe(item, per_h):
    """What one machine needs to put out `per_h` of `item`: inputs per batch and per hour."""
    r = REC.get(item) or REC.get(item.replace('quick_', '')) or {}
    ins = []
    for m, q in zip(r.get('raw_materials') or [], r.get('required_amount') or []):
        src = [p[0] for p in PRODBY.get(snake(m), [])] or ['à acheter ou à ramasser hors du Foyer']
        ins.append({'n': ifr(m), 'ic': pic_item(m), 'q': q, 'h': round(per_h / (r.get('yield_amount') or 1) * q, 1), 'src': src})
    return {'n': pfr(item), 'ic': pic_item(item), 'h': round(per_h, 1), 'ins': ins, 'yield': r.get('yield_amount') or 1}
COUNT = {}
for i in GL['lots']:
    COUNT[i['n']] = COUNT.get(i['n'], 0) + 1
def mlabel(n, k):
    return FR.get(n, n) + (f' {k + 1}' if COUNT.get(n, 0) > 1 else '')
def near_kiosk(it):
    c = (it['x'] + it['w'] / 2, it['y'] + it['h'] / 2)
    k, (x, y) = min(KIOSK.items(), key=lambda kv: math.dist(c, (kv[1][0] + 1, kv[1][1] + 1)))
    return int(k)
CARDS = {}
MJOBS, ALAB = {}, {}
for line in open(os.path.join(S, 'foyer_data.js')).read().split('\n'):
    if line.startswith('window.FOYER='):
        FOYER_L = json.loads(line[len('window.FOYER='):].rstrip().rstrip(';'))['levels']
for L in LEVELS:
    lv = GL['levels'][str(L)]
    lay = json.load(open(os.path.join(S, f'my_lay_in_rv{L}.json')))
    mem = [p['members'][0] for p in lay['pieces'] if not p.get('cluster')]
    team = TEAM['levels'][str(L)]
    # who does what: (facility, product) -> members; climate devices and generators are taken in order
    by_task, by_dev, crew, free = {}, {}, [], []
    for m in team['members']:
        fac_tasks = [t for t in m['tasks'] if t['kind'] == 'fac']
        if not m['tasks']:
            free.append({'p': m['i'], 'ab': [[ABFR.get(a, a), v, False] for a, v in sorted(m['ab'].items(), key=lambda kv: -kv[1])]})
        for t in m['tasks']:
            if t['kind'] == 'job':
                if m['i'] not in [c['i'] for c in crew]:
                    crew.append({'i': m['i'], 'ab': m['ab'], 'jobs': []})
                cj = next(c for c in crew if c['i'] == m['i'])
                cj['jobs'].append(f'{JOBFR.get(t["job"], t["job"])} ({ "champs" if t["where"] == "Farmland" else "pépinières"})')
            elif t.get('item'):
                by_task.setdefault((t['fac'], snake(t['item'])), []).append((m, t))
            else:
                by_dev.setdefault(t['fac'], []).append((m, t))
    # which machine on the plan runs each (facility, product), to name an Aniimo's other posts the way the cards do
    INST = {}
    for it in lv['items']:
        if it['n'] in FP_ALL and (it.get('weight') or 0) > 0:
            m0 = next((m for m in mem if m['facility'] == it['n'] and (m.get('crop') or '') == (it.get('item') or '') and abs((m.get('weight') or 0) - it['weight']) < 1e-6), None)
            for j in (m0.get('jobs') if m0 and m0.get('jobs') else [{'item': it.get('item')}]):
                INST.setdefault((it['n'], snake(j['item'])), mlabel(it['n'], it.get('unit', 0)))
    # who makes each product at this level: machines, fields, by-products, mines, wells, pavilions
    PRODBY = {}
    def addp(item, lab, kind):
        lst = PRODBY.setdefault(snake(item), [])
        if lab not in [p[0] for p in lst]:
            lst.append((lab, kind))
    for (fac, it_s), title in INST.items():
        addp(it_s, title, 'machine')
    cnt = {}
    for it in lv['items']:
        if it['kind'] == 'piece' and it['n'] not in FP_ALL and it.get('item'):
            cnt[(it['n'], it['item'])] = cnt.get((it['n'], it['item']), 0) + 1
    for (n, item), k in sorted(cnt.items(), key=lambda kv: -kv[1]):
        prod = item[6:] if item.startswith('quick_') else item
        de = (lambda x: ("d'" if x[:1].lower() in 'aeiouéèêh' else 'de ') + x)(pfr(item))
        lab = {'Farmland': f'{k} champ{"s" if k > 1 else ""} {de}', 'Woodland': f'{k} pépinière{"s" if k > 1 else ""} {de}',
               'Mine': f'{k} mine{"s" if k > 1 else ""}', 'Well': 'le puits'}.get(n, FR.get(n, n))
        for x in {item, prod}:
            addp(x, lab, 'raw')
        bp = (REC.get(item) or {}).get('byproduct_item')
        if bp:
            addp(bp, {'Woodland': 'la coupe des pépinières', 'Mine': 'les mines'}.get(n, FR.get(n, n)) + ' (sous-produit)', 'by')
    def who(m, t, here):
        others = []
        for t2 in m['tasks']:
            if t2 is t or t2['kind'] != 'fac':
                continue
            lab = INST.get((t2['fac'], snake(t2.get('item'))), FR.get(t2['fac'], t2['fac']) + (f' ({pfr(snake(t2["item"]))})' if t2.get('item') else ''))
            if lab not in others and lab != here:
                others.append(lab)
        return {'p': m['i'], 'ab': [[ABFR.get(a, a), v, a == t.get('ab')] for a, v in sorted(m['ab'].items(), key=lambda kv: (kv[0] != t.get('ab'), -kv[1]))], 'also': others}
    sec = {'rue': [], 'terr': [], 'carr': [], 'pav': [], 'elec': []}
    idle = []
    envs = [i for i in lv['items'] if i['kind'] == 'env']
    sq9 = lambda e: {'x': e['x'] + e['w'] / 2 - 4.5, 'y': e['y'] + e['h'] / 2 - 4.5, 'w': 9, 'h': 9}
    blocks = {id(e): {'e': e, 'crops': {}} for e in envs}
    free_crops, mines, wells = {}, {}, {}
    dev_seen = {}
    for k, it in enumerate(lv['items']):
        iid = f'{L}-{k + 1}'
        n, item, wt = it['n'], it.get('item') or '', it.get('weight') or 0
        if it['kind'] == 'env':
            continue
        if n in FP_ALL:
            title = mlabel(n, it.get('unit', 0))
            if wt <= 0:
                idle.append({'t': title, 'ic': pic_fac(n), 'ids': [iid]})
                continue
            m = next((m for m in mem if m['facility'] == n and (m.get('crop') or '') == item and abs((m.get('weight') or 0) - wt) < 1e-6), None)
            jobs = {}
            for j in (m.get('jobs') if m and m.get('jobs') else [{'item': item, 'rate': wt / 3600}]):
                jobs[j['item']] = jobs.get(j['item'], 0) + j['rate'] * 3600
            recs = [recipe(j, h) for j, h in sorted(jobs.items(), key=lambda kv: -kv[1])]
            ani = []
            for j in jobs:
                for mm, t in by_task.get((n, snake(j)), []):
                    if all(a['p'] != mm['i'] for a in ani):
                        ani.append(who(mm, t, title))
            sec['rue'].append({'ids': [iid], 'ic': pic_fac(n), 't': title, 'where': f'Rue des artisans, côté {"nord" if it["y"] < 17 else "sud"} · stockage {near_kiosk(it)} tout près', 'x': it['x'], 'side': 0 if it['y'] < 17 else 1,
                               'recs': recs, 'ani': ani, 'w': round(wt)})
            continue
        cover = [e for e in envs if ovr(it, sq9(e))]
        if n in ('Farmland', 'Woodland'):
            tgt = blocks[id(cover[0])]['crops'] if cover and (n, item) in NEEDS_L.get(L, set()) else free_crops
            c = tgt.setdefault((n, item), {'n': 0, 'ids': [], 'fac': FR.get(n, n), 'rec': pfr(item), 'ic': pic_item(item), 'facic': pic_fac(n)})
            c['n'] += 1; c['ids'].append(iid)
            continue
        if n == 'Mine':
            c = mines.setdefault(item, {'n': 0, 'ids': []}); c['n'] += 1; c['ids'].append(iid)
            continue
        if n == 'Well':
            c = wells.setdefault(item, {'n': 0, 'ids': []}); c['n'] += 1; c['ids'].append(iid)
            continue
        # pavilions (and the floral windmill)
        title = FR.get(n, n)
        if not item:
            idle.append({'t': title, 'ic': pic_fac(n), 'ids': [iid]})
            continue
        ani = [who(mm, t, title) for mm, t in by_task.get((n, snake(item)), [])]
        r = REC.get(item, {})
        per_h = (r.get('yield_amount') or 1) * 3600 / (r.get('production_time') or 3600)
        mode = MODEFR[cover[0]['mode']] if cover and (n, item) in NEEDS_L.get(L, set()) else None
        sec['pav'].append({'ids': [iid], 'ic': pic_fac(n), 't': title, 'where': {'pavilion': 'Nord, au pied des pavillons', 'terrace': 'Dans une terrasse, pour son climat', 'flower': 'Jardin des fleurs'}.get(it.get('zone'), ''),
                           'mode': mode, 'recs': [recipe(item, 0)], 'ani': ani})
    # climate blocks: the device, its setting, what grows in its square, who runs it
    for e_k, (bid, b) in enumerate(blocks.items()):
        e = b['e']
        eid = f'{L}-{lv["items"].index(e) + 1}'
        lst = by_dev.get(e['n'], [])
        dev_seen[e['n']] = dev_seen.get(e['n'], 0) + 1
        ani = [who(*lst[dev_seen[e['n']] - 1], FR.get(e['n']))] if len(lst) >= dev_seen[e['n']] else []
        crops = sorted(b['crops'].values(), key=lambda c: -c['n'])
        sec['terr'].append({'ids': [eid] + [i for c in crops for i in c['ids']], 'ic': pic_fac(e['n']), 't': f'{FR.get(e["n"])} · {MODEFR.get(e["mode"], e["mode"])}', 'mode': MODEFR.get(e['mode'], e['mode']),
                            'where': 'Terrasse ouest' if e['x'] < 40 else ('Jardin des fleurs' if e['y'] < 12 else 'Terrasse est'),
                            'crops': [{'n': c['n'], 'fac': c['fac'], 'rec': c['rec'], 'ic': c['ic'], 'facic': c['facic'], 'ids': c['ids']} for c in crops], 'ani': ani, 'dev': True})
    if free_crops:
        crops = sorted(free_crops.values(), key=lambda c: -c['n'])
        sec['terr'].append({'ids': [i for c in crops for i in c['ids']], 'ic': pic_fac('Farmland'), 't': 'Sans climat', 'where': 'N\'importe où dans les terrasses',
                            'crops': [{'n': c['n'], 'fac': c['fac'], 'rec': c['rec'], 'ic': c['ic'], 'facic': c['facic'], 'ids': c['ids']} for c in crops], 'ani': []})
    if crew:
        sec['terr'].append({'ids': [], 'ic': pic_fac('Farmland'), 't': 'Équipe des cultures', 'where': 'Pour tous les champs et pépinières',
                            'crew': [{'p': c['i'], 'ab': [[ABFR.get(a, a), v, False] for a, v in sorted(c['ab'].items(), key=lambda kv: -kv[1])], 'jobs': c['jobs']} for c in crew]})
    for item, c in mines.items():
        ani = [who(mm, t, FR.get('Mine')) for mm, t in by_task.get(('Mine', snake(item)), [])]
        r = REC.get(item, {}); per_h = (r.get('yield_amount') or 1) * 3600 / (r.get('production_time') or 3600)
        sec['carr'].append({'ids': c['ids'], 'ic': pic_fac('Mine'), 't': f'{c["n"]} × {FR.get("Mine")}', 'where': 'Carrière', 'recs': [recipe(item, 0)], 'ani': ani})
    for item, c in wells.items():
        ani = [who(mm, t, FR.get('Well')) for mm, t in by_task.get(('Well', snake(item)), [])]
        r = REC.get(item, {}); per_h = (r.get('yield_amount') or 1) * 3600 / (r.get('production_time') or 3600)
        sec['carr'].append({'ids': c['ids'], 'ic': pic_fac('Well'), 't': f'{c["n"]} × {FR.get("Well")}', 'where': 'Puits, au nord de la rue', 'recs': [recipe(item, 0)], 'ani': ani})
    gen_ids = [f'{L}-{len(lv["items"]) + 1 + g}' for g in range(len(lv['gens']))]
    gens = by_dev.get('Crackle Generator', [])
    sec['elec'].append({'ids': gen_ids, 'ic': pic_fac('Crackle Generator'), 't': f'{len(lv["gens"])} × {FR.get("Crackle Generator")}', 'where': f'{len(lv["poles"])} poteaux · {lv["powered"][0]} machines alimentées sur {lv["powered"][1]}',
                        'ani': [who(m, t, FR.get('Crackle Generator')) for m, t in gens], 'recs': []})
    sec['rue'].sort(key=lambda c: (c['side'], c['x']))
    # every Aniimo and its posts at this level
    devlab, devn = {}, {}
    for e in envs:
        devlab.setdefault(e['n'], []).append(f'{FR.get(e["n"])} ({MODEFR.get(e["mode"], e["mode"])})')
    ani_view = []
    for m in team['members']:
        posts, grp = [], None
        for t in m['tasks']:
            if t['kind'] == 'job':
                lab = 'Cultures : ' + JOBFR.get(t['job'], t['job']) + (' (champs)' if t['where'] == 'Farmland' else ' (pépinières)')
                g = 'cult'
            elif t.get('item'):
                lab = INST.get((t['fac'], snake(t['item'])))
                if not lab:
                    lab = FR.get(t['fac'], t['fac']) + ' · ' + pfr(snake(t['item']))
                g = 'rue' if t['fac'] in FP_ALL else 'prod'
            else:
                k = devn.get(t['fac'], 0); devn[t['fac']] = k + 1
                lst = devlab.get(t['fac']) or [FR.get(t['fac'], t['fac'])]
                lab = lst[min(k, len(lst) - 1)] if t['fac'] != 'Crackle Generator' else FR.get(t['fac'], t['fac'])
                g = 'clim'
            if lab not in posts:
                posts.append(lab)
            grp = grp or g
        ani_view.append({'p': m['i'], 'ab': [[ABFR.get(a, a), v] for a, v in sorted(m['ab'].items(), key=lambda kv: -kv[1])], 'busy': round(m.get('busy', 0), 2), 'posts': posts, 'g': grp or 'free'})
    gorder = {'rue': 0, 'prod': 1, 'cult': 2, 'clim': 3, 'free': 4}
    ani_view.sort(key=lambda a: (gorder[a['g']], a['posts'][:1]))
    # production chain: products as nodes, recipes as links, what is sold and what it earns
    fl = FOYER_L.get(str(L), {})
    sold = {}
    for row in (fl.get('profit') or []):
        try:
            sold[snake(row[0])] = {'h': float(str(row[2]).replace(',', '')), 'g': float(str(row[3]).replace(',', '')), 'share': row[4]}
        except (ValueError, IndexError):
            pass
    nodes, edges = {}, []
    def node(it):
        s = snake(it)
        if s not in nodes:
            src = [p for p in PRODBY.get(s, [])]
            nodes[s] = {'id': s, 'n': ifr(it) if not it.startswith('quick_') else pfr(it), 'ic': pic_item(it), 'src': [p[0] for p in src], 'kind': [p[1] for p in src],
                        'sold': sold.get(s) or sold.get(snake(it[6:]) if it.startswith('quick_') else '')}
        return s
    for it in lv['items']:
        if it['n'] in FP_ALL and (it.get('weight') or 0) > 0:
            m0 = next((m for m in mem if m['facility'] == it['n'] and (m.get('crop') or '') == (it.get('item') or '') and abs((m.get('weight') or 0) - it['weight']) < 1e-6), None)
            for j in (m0.get('jobs') if m0 and m0.get('jobs') else [{'item': it.get('item')}]):
                r = REC.get(j['item']) or {}
                out = node(j['item'])
                for mat in r.get('raw_materials') or []:
                    e = [node(mat), out]
                    if e not in edges:
                        edges.append(e)
    for s, v in sold.items():   # raw products sold as they are (crops, ores)
        if s not in nodes:
            nodes[s] = {'id': s, 'n': pfr(s), 'ic': pic_item(s), 'src': [p[0] for p in PRODBY.get(s, [])], 'kind': [p[1] for p in PRODBY.get(s, [])], 'sold': v}
    # what the next level asks for
    goal = None
    if fl.get('luRows'):
        tr = lambda s: str(s).replace('d', ' j').replace('h', ' h').replace('m', ' min')
        rows = [{'n': 'Pièces du Foyer' if r[0] == 'Home Coins' else pfr(snake(r[0])), 'ic': None if r[0] == 'Home Coins' else pic_item(snake(r[0])), 'need': r[1], 'rate': r[2], 'eta': tr(r[3])} for r in fl['luRows']]
        goal = {'next': fl.get('next'), 'eta': tr(fl.get('nextIn') or ''), 'rows': rows}
    nm = sum(1 for it in lv['items'] if it['n'] in FP_ALL or it['zone'] in ('pavilion', 'flower') and it['kind'] == 'piece' and it['n'] not in ('Woodland',))
    CARDS[L] = {'sec': sec, 'idle': idle, 'free': free, 'rate': team.get('rate'), 'nAni': len(team['members']),
                'nAct': len(sec['rue']) + len(sec['pav']), 'nIdle': len(idle), 'ani': ani_view,
                'chain': {'nodes': list(nodes.values()), 'edges': edges}, 'goal': goal}
    MJOBS[L] = {(it['n'], it.get('unit', 0)): [r['n'] for r in next((cc['recs'] for cc in sec['rue'] if cc['ids'][0] == f'{L}-{lv["items"].index(it) + 1}'), [])]
                for it in lv['items'] if it['n'] in FP_ALL}
    ALAB[L] = {a['p']: a['posts'] for a in ani_view}
PORTRAITS = ['data:image/webp;base64,' + p if not p.startswith('data:') else p for p in TEAM['portraits']]
