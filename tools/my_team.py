"""Pick the roster variant per level and work out each Aniimo's job, including who runs the generators."""
import json, os, re, shutil, base64

S = os.path.dirname(os.path.abspath(__file__))

# facility -> ability its worker needs (Aniimax facility-config + environment buildings)
FAC_AB = {'Mine': 'Earth', 'Well': 'Water', 'Tidewhisper Sandcastle': 'Leisure', 'Dewy House': 'Leisure', 'Nimbus Bed': 'Leisure',
          'Starfall Hammock': 'Leisure', 'Floral Windmill': 'Leisure', 'Carousel Mill': 'Wind', 'Crafting Table': 'Artisanship',
          'Claw Game Cooker': 'Fire', 'Jukebox Dryer': 'Dark', 'Simmering Pot': 'Fire', 'Phonolfactory Table': 'Perfumery',
          'Bouncy Brew Keg': 'Water', 'Blazing Stove': 'Fire', 'Pickling Jar': 'Dark', 'Joy Wheel Loom': 'Wind',
          'Dance Pad Polisher': 'Lightning', 'Aniipod Maker': 'Lightning', 'Woodworking Bench': 'Artisanship', 'Chimney Kiln': 'Fire',
          'Heat Furnace': 'Fire', 'Cooling Unit': 'Ice', 'Sunlamp': 'Light'}
JOB_AB = {'Sowing': 'Grass', 'Collecting': 'Grass', 'Watering': 'Water', 'Reaping': 'Dark', 'Reclaiming': 'Earth', 'Logging': 'Dark'}
RESIDENT = {'Tidewhisper Sandcastle', 'Dewy House', 'Nimbus Bed', 'Starfall Hammock', 'Floral Windmill', 'Heat Furnace', 'Cooling Unit', 'Sunlamp'}

def rate_of(d):
    m = re.search(r'([\d,]+)\s*Home Coins/hour', d['rate'])
    if m:
        return float(m.group(1).replace(',', ''))
    m = re.search(r'([\d,.]+)\s*Home Coins/sec', d['rate'])
    return float(m.group(1).replace(',', '')) * 3600 if m else 0

def parse_task(t):
    t = t.strip()
    m = re.match(r'(\w+) on (Farmland|Woodland)', t)
    if m:
        return {'kind': 'job', 'job': m.group(1), 'where': m.group(2), 'ab': JOB_AB.get(m.group(1))}
    m = re.match(r'(?:(\d+)× )?(.+?)(?: \((.+)\))?$', t)
    fac, item = m.group(2), m.group(3)
    return {'kind': 'fac', 'fac': fac, 'item': item, 'n': int(m.group(1) or 1), 'ab': FAC_AB.get(fac)}

roster = json.load(open(os.path.join(S, 'roster.json')))
portraits = [base64.b64encode(open(os.path.join(S, 'portraits', f'a{i:02d}.webp'), 'rb').read()).decode() for i in range(len(roster))]
out = {}
for lvl in range(14, 21):
    cands = []
    for v in 'AB':
        f = os.path.join(S, f'my{v}_data_rv{lvl}.json')
        if os.path.exists(f) and os.path.exists(os.path.join(S, f'my{v}_lay_in_rv{lvl}.json')):
            d = json.load(open(f))
            m = re.search(r'in (?:(\d+)d)?\s*(?:(\d+)h)?', d['levelUp'])
            hours = (int(m.group(1) or 0) * 24 + int(m.group(2) or 0)) if m and (m.group(1) or m.group(2)) else 0
            cands.append((-hours, rate_of(d), v, d))
    if not cands:
        continue
    cands.sort()
    _, low, v, d = cands[0]
    rates = sorted(c[1] for c in cands)
    high = rates[-1]
    shutil.copy(os.path.join(S, f'my{v}_data_rv{lvl}.json'), os.path.join(S, f'my_data_rv{lvl}.json'))
    shutil.copy(os.path.join(S, f'my{v}_lay_in_rv{lvl}.json'), os.path.join(S, f'my_lay_in_rv{lvl}.json'))
    rows = d['team'][1:]
    members = []
    for i, ab in enumerate(roster):
        r = rows[i] if i < len(rows) else ['', '1', '0', 'idle']
        where = r[3].strip()
        tasks = [] if where in ('idle', '') else [parse_task(t) for t in re.split(r', (?![^()]*\))', where)]
        members.append({'i': i, 'ab': ab, 'busy': float(r[2] or 0), 'tasks': tasks})
    # generators: each needs a Lightning Aniimo of its own
    swaps = []
    gen_ops = []
    def idle_members():
        return [m for m in members if not m['tasks'] and m['i'] not in gen_ops]
    for _ in range(2):
        best = None
        for m in members:
            if 'Lightning' not in m['ab'] or m['i'] in gen_ops:
                continue
            if not m['tasks']:
                best = (0, m, None)
                break
            # spread its tasks over idle Aniimo able to do each one at the same level
            share = m['busy'] / max(1, len(m['tasks']))
            spare = [x for x in members if x['tasks'] and x is not m and x['i'] not in gen_ops and not any(tt.get('fac') in RESIDENT for tt in x['tasks']) and x['busy'] + share <= 1.0]
            pool = idle_members() + sorted(spare, key=lambda x: x['busy']); plan = []; ok = True
            for t in m['tasks']:
                h = next((h for h in pool if t['ab'] and h['ab'].get(t['ab'], 0) >= m['ab'].get(t['ab'], 0)), None)
                if not h:
                    h = next((x for x, _ in plan if t['ab'] and x['ab'].get(t['ab'], 0) >= m['ab'].get(t['ab'], 0) and not any(tt.get('fac') in RESIDENT for _, tt in plan if _ is x)), None) if plan else None
                if not h:
                    ok = False; break
                plan.append((h, t))
                if h in pool: pool.remove(h)
            if ok:
                cost = len({id(h) for h, _ in plan})
                if not best or cost < best[0]:
                    best = (cost, m, plan)
        if not best:
            break
        _, m, plan = best
        if plan:
            for h, t in plan:
                h['tasks'] = h['tasks'] + [t]; h['busy'] = min(1.0, h['busy'] + m['busy'] / len(m['tasks']))
            for h in {id(h): h for h, _ in plan}.values():
                swaps.append({'from': m['i'], 'to': h['i']})
        m['tasks'] = [{'kind': 'fac', 'fac': 'Crackle Generator', 'item': None, 'n': 1, 'ab': 'Lightning'}]
        m['busy'] = 1.0
        gen_ops.append(m['i'])
    used = sum(1 for m in members if m['tasks'])
    out[lvl] = {'variant': v, 'rate': low, 'rateHigh': high, 'members': members, 'genOps': gen_ops, 'swaps': swaps, 'used': used}
    print(lvl, 'variant', v, 'rate', round(low), '-', round(high), 'used', used, 'gens', gen_ops, 'swaps', swaps)
json.dump({'levels': out, 'portraits': portraits}, open(os.path.join(S, 'my_team.json'), 'w'))
