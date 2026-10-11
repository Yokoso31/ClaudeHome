
# ---------------- where to invest: the single upgrades that raise the plan's income most ----------------
def hours(s):
    import re as _re
    d = _re.search(r'(\d+)d', s or ''); h = _re.search(r'(\d+)h', s or '')
    return (int(d.group(1)) * 24 if d else 0) + (int(h.group(1)) if h else 0)
IMPRO = {'levels': {}, 'top': []}
agg = {}
for L in LEVELS:
    fl = FOYER_L[str(L)]
    rate, nxt = fl['rate'], FOYER_L.get(str(L + 1), {}).get('rate')
    H = hours(fl.get('nextIn')) or 7 * 24          # at RV 20: counted over one week
    rows, seen = [], {}
    for g in fl.get('improve') or []:
        pct = float(str(g.get('pct')).replace('+', '')) if g.get('pct') else 0
        coins = g.get('coins') or (pct / 100 * rate)
        mins = g.get('mins') or 0
        value = coins * H   # extra coins over the time spent at this level
        if g['kind'] == 'recipe':
            key = ('recipe', g['name']); title = f'Débloquer la recette {pfr(snake(g["name"]))}'; ic = pic_item(snake(g['name']))
        else:
            key = ('aniimo', g['ab'], g['lv']); title = f'Monter un Aniimo {ABFR.get(g["ab"], g["ab"])} au niveau {g["lv"]}'; ic = None
        row = {'kind': g['kind'], 'title': title, 'ic': ic, 'ab': g.get('ab'), 'lv': g.get('lv'), 'who': g.get('who') or [], 'mins': mins,
               'coins': round(coins), 'pct': g.get('pct'), 'value': round(value)}
        rows.append(row)
        a = agg.setdefault(key, {'kind': g['kind'], 'title': title, 'ic': ic, 'ab': g.get('ab'), 'lv': g.get('lv'), 'who': [], 'per': {}, 'value': 0, 'mins': 0})
        old = a['per'].get(L)
        if old is None or (value, mins) > (old['value'], old['mins']):   # the best entry of this kind at this level
            if old:
                a['value'] -= old['value']; a['mins'] -= old['mins']
            a['per'][L] = {'value': round(value), 'pct': g.get('pct'), 'mins': mins, 'coins': round(coins)}
            a['value'] += value; a['mins'] += mins
        for w in g.get('who') or []:
            if w not in a['who']:
                a['who'].append(w)
    IMPRO['levels'][L] = rows
allg = [{**a, 'value': round(a['value'])} for a in agg.values()]
IMPRO['top'] = sorted((a for a in allg if a['value'] > 0), key=lambda a: -a['value'])[:5]
IMPRO['fast'] = sorted((a for a in allg if a['mins'] > 0), key=lambda a: -a['mins'])[:3]
for a in IMPRO['top'] + IMPRO['fast']:
    print('  invest', a['title'], a['value'], a['mins'], {L: (p['pct'], p['mins']) for L, p in a['per'].items()})
