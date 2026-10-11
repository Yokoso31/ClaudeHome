
# ---------------- 3D scene: same pieces, same places, as plain data for the 3D view ----------------
def lv_of(ph):
    """The levels at which something drawn with phase `ph` is on the ground."""
    ext = GL['levels']['20']['extra']
    if ph == 14:
        return LEVELS
    if isinstance(ph, int):
        return [L for L in LEVELS if L >= ph]
    out = []
    for L in LEVELS:
        ok = True
        for tok in ph.split():
            if tok == 'ph20x':
                ok &= L == 20 and ext
            elif tok.startswith('ph'):
                ok &= L >= int(tok[2:])
            elif tok.startswith('until'):
                ok &= L <= int(tok[5:])
        if ok:
            out.append(L)
    return out
r2 = lambda v: round(v, 2)
S3 = {'decor': [], 'ground': [], 'terr': [], 'levels': {}}
for n, r, ph in PHYS:
    S3['decor'].append({'n': n, 'x': r2(r['x']), 'y': r2(r['y']), 'w': r2(r['w']), 'h': r2(r['h']), 'lv': lv_of(ph)})
for key, fr, role, rects, ph, _ in ZONES:
    for (x, y, w, h) in rects:
        S3['ground'].append({'k': key, 'x': x, 'y': y, 'w': w, 'h': h, 'lv': lv_of(ph if key != 'z-terr-m' else 'ph20x')})
for t in GL['terraces']:
    S3['terr'].append({'x': t['x'], 'y': t['y'], 'w': t['w'], 'h': t['h'], 'lv': LEVELS})
for t in GL['terrNE']:
    S3['terr'].append({'x': t['x'], 'y': t['y'], 'w': t['w'], 'h': t['h'], 'lv': [L for L in LEVELS if L >= 18]})
for t in GL['extra']:
    S3['terr'].append({'x': t['x'], 'y': t['y'], 'w': t['w'], 'h': t['h'], 'lv': lv_of('ph20x')})
for L in LEVELS:
    lv = GL['levels'][str(L)]
    envs = [i for i in lv['items'] if i['kind'] == 'env']
    sq9 = lambda e: {'x': e['x'] + e['w'] / 2 - 4.5, 'y': e['y'] + e['h'] / 2 - 4.5, 'w': 9, 'h': 9}
    objs = []
    for it in lv['items']:
        n, item, wt = it['n'], it.get('item') or '', it.get('weight') or 0
        o = {'x': r2(it['x']), 'y': r2(it['y']), 'w': it['w'], 'h': it['h']}
        name_fr, rec = FR.get(n, n), pfr(item)
        cover = [e for e in envs if ovr(it, sq9(e))]
        mode = f' · {MODEFR[cover[0]["mode"]]}' if cover else ''
        if it['kind'] == 'env':
            o |= {'k': 'dev', 'dv': DEVCLS[n], 'm': MODEFR.get(it['mode'], it['mode']), 'lab': f'{name_fr} · réglée en {MODEFR.get(it["mode"], it["mode"])}'}
        elif n == 'Farmland':
            o |= {'k': 'farm', 'c': CROPCOL.get(item, '#5B8E3B'), 'lab': f'{FR.get("Farmland", "Ferme")} · {rec}{mode}'}
        elif n == 'Woodland':
            o |= {'k': 'wood', 't': TREECLS.get(item, 'citrus'), 'lab': f'{FR.get("Woodland", "Pépinière")} · {rec}{mode}'}
        elif n in FP_ALL:
            idle = wt <= 0
            o |= {'k': 'shop', 'idle': idle, 'ic': ic_fac(n).replace(' ', '_'), 'lab': f'{name_fr} · ' + (f'{rec} · {round(wt)} trajets/h' if not idle else 'à l\'arrêt à ce palier')}
        elif n == 'Mine':
            o |= {'k': 'mine', 'ic': ic_fac('Mine'), 'lab': f'{FR.get("Mine")} · {rec}'}
        elif n == 'Well':
            o |= {'k': 'well', 'lab': f'{FR.get("Well")} · {rec}'}
        else:
            o |= {'k': 'pav', 'ic': ic_fac(n).replace(' ', '_'), 'lab': f'{name_fr} · ' + (rec or 'à l\'arrêt') + mode}
        objs.append(o)
    for g in lv['gens']:
        objs.append({'k': 'gen', 'x': g['x'], 'y': g['y'], 'w': 1, 'h': 1, 'lab': FR.get('Crackle Generator', 'Générateur') + ' · tenu par un Aniimo Foudre'})
    for p in lv['poles']:
        objs.append({'k': 'pole', 'x': p['x'], 'y': p['y'], 'w': 1.5, 'h': 1.5, 'lab': FR.get('Crackle Power Pole', 'Poteau électrique')})
    for k, p in enumerate(lv.get('bonus', [])):
        objs.append({'k': 'bonus', 'n': k + 1, 'x': p['x'], 'y': p['y'], 'w': 1.5, 'h': 1.5, 'lab': f'Poteau en plus n° {k + 1} · seulement si le module VR 16 augmente ta limite'})
    S3['levels'][L] = objs
