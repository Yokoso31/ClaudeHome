
import sys; sys.path.insert(0, S)
from garden_plan import QUARRY as QSLOTS, FP as FP_MACH
FP_ALL = set(FP_MACH)
phys('grand arbre', 37, 28, 6, 6)

# ---------------- moss garden, along the courtyard ----------------
for x, y in ((31.5, 30.5), (29.5, 31.6), (27.5, 32.7)):
    deco('40100006', x, y, layer=3)
deco('40300014', 29, 26.4); deco('40300014', 31.6, 34.6)
pond(27.6, 29)
deco('40600065', 30.4, 28.4)
deco('40700016', 27.6, 35.4); deco('40700016', 33, 28.6)

# ---------------- tea garden, east of the courtyard ----------------
for x in (47, 49, 51):
    deco('40200023', x, 26.1)
for x in (47, 51):
    deco('40200023', x, 32.6)
for y in (26.4, 28.4, 30.4):
    deco('40200023', 46.8, y, rot=True); deco('40200023', 53.2, y, rot=True)
deco('40400018', 47.4, 26.35); deco('40400018', 49.6, 26.35)
deco('40600083', 48, 28.2); deco('40600066', 48.9, 29.1); deco('40600055', 51.6, 29.6)
deco('40300014', 51, 26.9); deco('40100006', 49, 30.4, layer=3); deco('40700016', 47.4, 31.2)

# ---------------- craftsmen's street, kiosks ----------------
rect(1, 16.5, 59, 3, 'url(#slabs)', layer=2)
rect(38, 19.5, 4, 5.5, 'url(#slabs)', layer=2)
CLEAR += [('rue', {'x': 1, 'y': 16.5, 'w': 59, 'h': 3}), ('lien', {'x': 38, 'y': 19.5, 'w': 4, 'h': 5.5})]
num(2.2, 18, 4)
GL = json.load(open(os.path.join(S, 'garden_levels.json')))
KIOSK = {int(k): tuple(v) for k, v in GL['kiosks'].items()}
for k, (x, y) in KIOSK.items():
    phys('stockage %d' % k, x, y, 2, 2)
    T('Storage Unit', FR.get('Storage Unit', 'Unité de stockage'), 'Stockage', ic_fac('Storage Unit'), '2 × 2', 'Les porteurs y déposent la production.')
    add(f'<g class="obj kiosk"{tag("Storage Unit", "Unité de stockage " + str(k))}><rect x="{x - .15}" y="{y - .15}" width="2.3" height="2.3" rx=".25" class="eave"/><rect x="{x + .15}" y="{y + .15}" width="1.7" height="1.7" class="roof"/>'
        f'<path d="M{x + .15} {y + .15}L{x + 1.85} {y + 1.85}M{x + 1.85} {y + .15}L{x + .15} {y + 1.85}" class="ridge"/>'
        f'<g class="kno"><circle cx="{x + 2}" cy="{y}" r=".6"/><text x="{x + 2}" y="{y + .25}" text-anchor="middle">{k}</text></g></g>', 14, 7)

# ---------------- quarry ground, mountain ----------------
rect(60, 15, 20, 15, 'url(#stone)', layer=1, rx=.4)
num(78.6, 16.6, 5)
MOUNT = 'ph16 until19' if GL['levels']['20']['extra'] else 'ph16'
for x in (61.5, 70.5):
    deco('40700030', x, 2, phase=MOUNT)
deco('40300007', 75.5, 10.5, phase=MOUNT)

# ---------------- terraces ----------------
for t in GL['terraces']:
    rect(t['x'] - .25, t['y'] - .25, t['w'] + .5, t['h'] + .5, 'url(#dike)', layer=1, rx=.6)
    rect(t['x'] + .15, t['y'] + .15, t['w'] - .3, t['h'] - .3, 'url(#terr)', layer=1, rx=.4)
for t in GL['extra']:
    rect(t['x'] - .25, t['y'] - .25, t['w'] + .5, t['h'] + .5, 'url(#dike)', phase='ph20x', layer=1, rx=.6)
    rect(t['x'] + .15, t['y'] + .15, t['w'] - .3, t['h'] - .3, 'url(#terr)', phase='ph20x', layer=1, rx=.4)
rect(40.4, 3.8, 11.6, 6.4, 'url(#gravel)', phase=18, layer=1, rx=.8)       # flower garden ground
num(3.6, 26.6, 6); num(79, 32, 7)

# ---------------- hatchery pavilion ----------------
rect(47.4, 54.6, 9.2, 4.8, 'url(#slabs)', layer=2, rx=.4)
for g in range(3):
    rect(42 + 2 * g, 56.1, 2, 2, 'url(#gravelpath)', layer=2, rx=.3)
    used[('40100010', 14)] = used.get(('40100010', 14), 0) + 1
T('Incubateur', FR.get('Incubateur', 'Éclorateur'), 'Production', ic_jp('10500001'), '2 × 2', 'Tes éclorateurs, regroupés en pavillon près de l\'entrée.')
for i in range(4):
    for j in range(2):
        x, y = 48 + 2 * i, 55 + 2 * j
        phys('éclorateur', x, y, 2, 2)
        add(f'<g class="obj hatch"{tag("Incubateur")}>' + shadow(x + 1, y + 1, .85) + f'<circle cx="{x + 1}" cy="{y + 1}" r=".88" class="dome"/><circle cx="{x + .75}" cy="{y + .75}" r=".32" class="dome-l"/></g>', 14, 6)
num(57.8, 55, 8)

# ---------------- dry garden ----------------
rect(12, 52, 15, 7.5, 'url(#raked)', layer=2, rx=.6)
add('<g class="rakes">' + ''.join(f'<circle cx="20.5" cy="55.8" r="{r}"/>' for r in (1.1, 1.6, 2.1)) + '</g>', 14, 3)
deco('40700029', 2, 51)
deco('40600083', 20.25, 55.55); deco('40700017', 24.2, 53.4); deco('40700016', 14.2, 57.6)
num(12.4, 51.4, 9)

# ---------------- north: raked garden, hedges ----------------
rect(17.5, 1, 8, 8.2, 'url(#raked)', layer=2, rx=.6)
add('<g class="rakes">' + ''.join(f'<circle cx="21.5" cy="5" r="{r}"/>' for r in (1, 1.5, 2)) + '</g>', 14, 3)
deco('40600027', 21, 4.5); deco('40700017', 18.6, 2.4)
for x in (2, 4.6, 22.6, 25.2):
    deco('40700001', x, 9.9)
num(1.3, 1.3, 10)

# ---------------- north-east: bamboo grove, cherry tree ----------------
for x in range(41, 59, 2):
    deco('40300002', x, 0.4, phase=16)
deco('40300004', 53, 3.4, phase=18)
for x in range(60, 79, 3):
    deco('40300002', x, 57.6)
deco('40300014', 63.4, 54.2); deco('40300014', 72.6, 54.4)
deco('40300002', .6, 37.6); deco('40300002', .6, 42); deco('40300002', .6, 46.4)

# ---------------- production, level by level ----------------
LEVELS = [int(k) for k in sorted(GL['levels'], key=int)]
PROD = {}
for line in open(os.path.join(S, 'foyer_data.js')).read().split('\n'):
    if line.startswith('window.FOYER='):
        PROD = json.loads(line[len('window.FOYER='):-1])['products']
norm = lambda v: ''.join(c for c in v.lower() if c.isalpha())
PRODN = {norm(k): v for k, v in PROD.items()}
MANUAL_FR = {'quick_natural_mineral_spring_water': 'Eau de source minérale naturelle (rapide)'}
def pfr(item):
    if not item:
        return None
    if item in MANUAL_FR:
        return MANUAL_FR[item]
    t = ' '.join(w.capitalize() for w in item.split('_'))
    p = PROD.get(t) or PRODN.get(norm(t))
    return p['fr'] if p else t
MODEFR = {'Scorching': 'Torride', 'Warm': 'Chaud', 'Cool': 'Frais', 'Freeze': 'Glacial', 'Adequate': 'Ensoleillé'}
DEVCLS = {'Sunlamp': 'sun', 'Heat Furnace': 'heat', 'Cooling Unit': 'cool'}
CROPCOL = {'grape': '#7E57A8', 'quick_rice': '#CFC66E', 'ginseng': '#C9955A', 'cranberry': '#B83350', 'premium_wheat': '#D9B64B', 'quick_strawberry': '#E2525F', 'strawberry': '#E2525F'}
TREECLS = {'coconut': 'palm', 'quick_coconut': 'palm', 'palm_bark': 'palm', 'quick_lemon': 'citrus', 'quick_maple_syrup': 'maplet', 'cocoa': 'cocoa', 'orange_flower': 'oflower'}
SHORT = {'Carousel Mill': 'Moulin', 'Chimney Kiln': 'Four', 'Joy Wheel Loom': 'Roue à tisser', 'Woodworking Bench': 'Menuiserie', 'Crafting Table': 'Établi',
         'Jukebox Dryer': 'Séchoir', 'Simmering Pot': 'Marmite', 'Phonolfactory Table': 'Parfums', 'Pickling Jar': 'Bocal', 'Blazing Stove': 'Cuisinière',
         'Bouncy Brew Keg': 'Tonneau', 'Claw Game Cooker': 'Attrape-popote', 'Aniipod Maker': 'Aniipod', 'Dance Pad Polisher': 'Polissoir',
         'Nimbus Bed': 'Lit de Cumulaine', 'Starfall Hammock': 'Hamac', 'Tidewhisper Sandcastle': 'Château de sable', 'Dewy House': 'Plumiel', 'Floral Windmill': 'Moulin floral'}
LOTS = {}
for i in GL['lots']:
    if i['lot']:
        LOTS[(i['n'], i['k'])] = i['lot']
def ovr(a, b):
    return min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']) > 1e-6 and min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']) > 1e-6
TAB = {}
LV = {}
for L in LEVELS:
    lv = GL['levels'][str(L)]
    out = []
    ids = 0
    envs = [i for i in lv['items'] if i['kind'] == 'env']
    sq = lambda e: {'x': e['x'] + e['w'] / 2 - 4.5, 'y': e['y'] + e['h'] / 2 - 4.5, 'w': 9, 'h': 9}
    rows = {'street': [], 'blocks': {}, 'free': {}, 'quarry': {}, 'wells': {}, 'pav': [], 'power': []}
    for e in envs:
        rows['blocks'][id(e)] = {'dev': e['n'], 'mode': e['mode'], 'crops': {}, 'ids': []}
    NEEDS = set()   # (facility, crop) that this level grows under a climate
    for p in json.load(open(os.path.join(S, f'my_lay_in_rv{L}.json')))['pieces']:
        if p.get('cluster'):
            for q in p['plots']:
                NEEDS.add((q['facility'], q.get('crop')))
    for it in lv['items']:
        ids += 1
        iid = f'{L}-{ids}'
        x, y, w, h = it['x'], it['y'], it['w'], it['h']
        n, item, wt = it['n'], it.get('item') or '', it.get('weight') or 0
        name_fr = FR.get(n, n)
        rec = pfr(item)
        if it['kind'] == 'env':
            T(n, FR.get(n), 'Climat et énergie', ic_fac(n), f'{f(w)} × {f(h)}', 'Règle la température ou la lumière des cultures dans son carré de 9 × 9 (vue technique). Tenu par un Aniimo.')
            lab = f'{name_fr} · réglée en {MODEFR.get(it["mode"], it["mode"])}'
            out.append(f'<g class="obj dev {DEVCLS[n]}"{tag(n, lab)} data-id="{iid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx=".25"/><rect x="{f(x + w / 2 - 4.5)}" y="{f(y + h / 2 - 4.5)}" width="9" height="9" class="sq tech"/></g>')
            out.append(f'<text x="{f(x + w / 2)}" y="{f(y - .35)}" font-size=".5" text-anchor="middle" class="nm">{SHORT.get(n, name_fr.split(" ")[0])}</text>')
            rows['blocks'][id(it)]['ids'].append(iid)
            continue
        cover = [e for e in envs if ovr(it, sq(e))]
        if n == 'Farmland':
            T('Farmland', FR.get('Farmland', 'Ferme'), 'Production', ic_fac('Farmland'), '2 × 2', 'Champ des terrasses.')
            col = CROPCOL.get(item, '#5B8E3B')
            lab = f'{FR.get("Farmland", "Ferme")} · {rec}' + (f' · {MODEFR[cover[0]["mode"]]}' if cover else '')
            out.append(f'<g class="obj"{tag("Farmland", lab)} data-id="{iid}"><rect x="{x + .1}" y="{y + .1}" width="1.8" height="1.8" rx=".22" class="pd"/>'
                       + ''.join(f'<circle cx="{f(x + .5 + (k % 3) * .5)}" cy="{f(y + .55 + (k // 3) * .45)}" r=".17" fill="{col}"/>' for k in range(9)) + '</g>')
        elif n == 'Woodland':
            T('Woodland', FR.get('Woodland', 'Pépinière'), 'Production', ic_fac('Woodland'), '4 × 4', 'Pépinière des terrasses.')
            cx, cy = x + 2, y + 2
            cls = TREECLS.get(item, 'citrus')
            lab = f'{FR.get("Woodland", "Pépinière")} · {rec}' + (f' · {MODEFR[cover[0]["mode"]]}' if cover else '')
            if cls == 'palm':
                art = shadow(cx, cy, 1.5) + star(cx, cy, 1.75, .55, 7, 'palm') + star(cx, cy, .9, .3, 7, 'palm-l')
            else:
                art = shadow(cx, cy, 1.4) + blob(cx, cy, 1.55, cls, 8, .18, int(x * 7 + y)) + ''.join(f'<circle cx="{f(cx + .8 * math.cos(a))}" cy="{f(cy + .8 * math.sin(a))}" r=".2" class="{cls}-f"/>' for a in (0.4, 2.2, 4.1))
            out.append(f'<g class="obj wood"{tag("Woodland", lab)} data-id="{iid}"><rect x="{x + .15}" y="{y + .15}" width="3.7" height="3.7" rx=".5" class="bed"/>{art}</g>')
        elif n in FP_ALL:
            idle = wt <= 0
            T(n, name_fr, 'Ateliers', ic_fac(n), f'{f(w)} × {f(h)}', 'Atelier de la rue des artisans, à la même place à tous les paliers.')
            lab = f'{name_fr} · ' + (f'{rec} · {round(wt)} trajets/h' if not idle else 'à l\'arrêt à ce palier')
            ridge = f'M{f(x + .35)} {f(y + h / 2)}H{f(x + w - .35)}' if w >= h else f'M{f(x + w / 2)} {f(y + .35)}V{f(y + h - .35)}'
            out.append(f'<g class="obj shop{" idle" if idle else ""}"{tag(n, lab)} data-id="{iid}"><rect x="{f(x + .25)}" y="{f(y + .3)}" width="{f(w)}" height="{f(h)}" rx=".3" class="shd"/>'
                       f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx=".3" class="eave"/><rect x="{f(x + .25)}" y="{f(y + .25)}" width="{f(w - .5)}" height="{f(h - .5)}" rx=".2" class="roof"/>'
                       f'<path d="{ridge}" class="ridge"/><use href="#i-{ic_fac(n).replace(" ", "_")}" x="{f(x + w * .2)}" y="{f(y + h * .2)}" width="{f(w * .6)}" height="{f(h * .6)}" class="sign"/></g>')
            out.append(f'<text x="{f(x + w / 2)}" y="{f(y + h / 2 + .2)}" font-size="{.5 if w < 3 else .6}" text-anchor="middle" class="nm">{SHORT.get(n, n)}</text>')
            rows['street'].append({'id': iid, 'n': n, 'ic': ic_fac(n).replace(' ', '_'), 'title': name_fr, 'what': rec if not idle else None, 'w': round(wt, 1), 'x': x})
            continue
        elif n == 'Mine':
            T('Mine', FR.get('Mine'), 'Production', ic_fac('Mine'), '5 × 5', 'Mine de la carrière.')
            out.append(f'<g class="obj mine"{tag("Mine", FR.get("Mine") + " · " + str(rec))} data-id="{iid}">' + shadow(x + 2.5, y + 2.5, 2.1) + blob(x + 2.5, y + 2.5, 2.35, 'rock', 8, .22, int(x + y)) +
                       blob(x + 2.1, y + 2.1, 1.1, 'rock-l', 6, .3, int(x)) + f'<use href="#i-{ic_fac("Mine")}" x="{x + 1.1}" y="{y + 1.1}" width="2.8" height="2.8" class="sign"/></g>')
            r = rows['quarry'].setdefault(rec, {'what': rec, 'ids': []}); r['ids'].append(iid)
            continue
        elif n == 'Well':
            T('Well', FR.get('Well'), 'Production', ic_fac('Well'), '2 × 2', 'Puits, près de la rue pour l\'électricité.')
            out.append(f'<g class="obj well"{tag("Well", FR.get("Well") + " · " + str(rec))} data-id="{iid}"><circle cx="{x + 1}" cy="{y + 1}" r=".95" class="wellr"/><circle cx="{x + 1}" cy="{y + 1}" r=".55" class="wellw"/></g>')
            out.append(f'<text x="{x + 1}" y="{y + 2.75}" font-size=".5" text-anchor="middle" class="nm">Puits</text>')
            r = rows['wells'].setdefault(rec, {'what': rec, 'ids': []}); r['ids'].append(iid)
            continue
        else:   # pavilions: in the north, or in a terrace / the flower garden when their product needs a climate
            T(n, name_fr, 'Production', ic_fac(n), f'{f(w)} × {f(h)}', 'Bâtiment de matériaux.')
            lab = f'{name_fr} · ' + (rec or 'à l\'arrêt') + (f' · {MODEFR[cover[0]["mode"]]}' if cover else '')
            out.append(f'<g class="obj pav"{tag(n, lab)} data-id="{iid}"><rect x="{x + .25}" y="{y + .3}" width="{w}" height="{h}" rx=".9" class="shd"/><rect x="{x}" y="{y}" width="{w}" height="{h}" rx=".9" class="eave"/>'
                       f'<rect x="{x + .4}" y="{y + .4}" width="{w - .8}" height="{h - .8}" rx=".6" class="roof"/><use href="#i-{ic_fac(n).replace(" ", "_")}" x="{f(x + w * .18)}" y="{f(y + h * .18)}" width="{f(w * .64)}" height="{f(h * .64)}" class="sign"/></g>')
            out.append(f'<text x="{f(x + w / 2)}" y="{f(y + h + .75)}" font-size=".6" text-anchor="middle" class="nm">{SHORT.get(n, n)}</text>')
            rows['pav'].append({'id': iid, 'n': n, 'ic': ic_fac(n).replace(' ', '_'), 'title': name_fr, 'what': rec, 'mode': MODEFR[cover[0]['mode']] if cover else None})
            if cover and (n, item) in NEEDS:
                b = rows['blocks'][id(cover[0])]
                b['crops'].setdefault(name_fr, {'fac': name_fr, 'ic': ic_fac(n).replace(' ', '_'), 'verb': 'Produire', 'what': rec, 'n': 0, 'ids': []}); b['crops'][name_fr]['n'] += 1; b['crops'][name_fr]['ids'].append(iid)
            continue
        # crops: group by climate block or as free crops
        key = f'{FR.get(n, n)}|{rec}'
        if cover and (n, item) in NEEDS:
            b = rows['blocks'][id(cover[0])]
            c = b['crops'].setdefault(key, {'fac': FR.get(n, n), 'ic': n, 'verb': 'Planter', 'what': rec, 'n': 0, 'ids': []}); c['n'] += 1; c['ids'].append(iid)
        else:
            c = rows['free'].setdefault(key, {'fac': FR.get(n, n), 'ic': n, 'verb': 'Planter', 'what': rec, 'n': 0, 'ids': []}); c['n'] += 1; c['ids'].append(iid)
    used_q = sum(1 for it in lv['items'] if it['n'] == 'Mine')
    for k, (qx, qy) in enumerate(QSLOTS):
        if k >= used_q:
            out.append(f'<rect x="{qx + .4}" y="{qy + .4}" width="4.2" height="4.2" rx=".6" class="slot"><title>Emplacement de mine libre</title></rect>')
    T('Crackle Generator', FR.get('Crackle Generator'), 'Climat et énergie', ic_fac('Crackle Generator'), '1 × 1', 'Alimente les machines dans un carré de 11 × 11. Tenu par un Aniimo Foudre.')
    T('Crackle Power Pole', FR.get('Crackle Power Pole'), 'Climat et énergie', ic_fac('Crackle Power Pole'), '1.5 × 1.5', 'Prolonge le réseau électrique (carré de 7 × 7).')
    for g in lv['gens']:
        ids += 1
        out.append(f'<g class="obj gen"{tag("Crackle Generator")} data-id="{L}-{ids}"><rect x="{g["x"]}" y="{g["y"]}" width="1" height="1" rx=".2"/></g>')
        out.append(f'<rect x="{f(g["x"] - 5)}" y="{f(g["y"] - 5)}" width="11" height="11" rx=".5" class="pwa tech"/>')
    for p in lv['poles']:
        ids += 1
        out.append(f'<g class="obj pole"{tag("Crackle Power Pole")} data-id="{L}-{ids}"><rect x="{p["x"]}" y="{p["y"]}" width="1.5" height="1.5" rx=".3"/><circle cx="{p["x"] + .75}" cy="{p["y"] + .75}" r=".3"/></g>')
        out.append(f'<rect x="{f(p["x"] - 2.75)}" y="{f(p["y"] - 2.75)}" width="7" height="7" rx=".4" class="pwa tech"/>')
    LV[L] = '\n'.join(out)
    blocks = [b for b in rows['blocks'].values()]
    TAB[L] = {
        'street': sorted(rows['street'], key=lambda r: (r['what'] is None, -r['w'])),
        'blocks': [{'dev': FR.get(b['dev']), 'devIc': ic_fac(b['dev']).replace(' ', '_'), 'mode': MODEFR.get(b['mode'], b['mode']), 'ids': b['ids'],
                    'crops': sorted(b['crops'].values(), key=lambda c: -c['n'])} for b in blocks],
        'free': sorted(rows['free'].values(), key=lambda c: -c['n']),
        'quarry': list(rows['quarry'].values()), 'wells': list(rows['wells'].values()), 'pav': rows['pav'],
        'avg': lv['avg'], 'powered': lv['powered'], 'extra': lv['extra'],
        'poles': len(lv['poles']), 'gens': len(lv['gens']),
    }
    # overlaps between the garden's fixed decor and this level's production
    prod = [dict(n=it['n'], x=it['x'], y=it['y'], w=it['w'], h=it['h']) for it in lv['items']] + [dict(n='générateur', **g) for g in lv['gens']] + [dict(n='poteau', **p) for p in lv['poles']]
    vis = lambda ph: ph == 14 or (isinstance(ph, int) and L >= ph) or (ph == 'ph16 until19' and 16 <= L <= 19)
    clash = [(a['n'], n2) for a in prod for (n2, r, ph) in PHYS if vis(ph) and ovr(a, r)]
    clash += [(a['n'], cn) for a in prod for cn, cr in CLEAR if ovr(a, cr)]
    print(f'RV{L}: {len(lv["items"])} pièces, marche {lv["avg"]}, courant {lv["powered"]}, chevauchements déco {clash[:8]}')
