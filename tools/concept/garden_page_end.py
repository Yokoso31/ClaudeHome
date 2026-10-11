
# ---------------- places of the garden ----------------
TW = [t for t in GL['terraces'] if t['x'] < 40]
TE = [t for t in GL['terraces'] if t['x'] >= 40]
ZONES = [
    ('z-allee', 'Allée des lanternes', 'L\'entrée du Foyer, en bas : dalles moussues bordées de lampes en pierre, jusqu\'à la cour du grand arbre.', [(38, 37, 4, 23)], 14, (40, 46.2)),
    ('z-stream', 'Rivière sèche et pont', 'Lit de gravier ratissé et de galets qui évoque l\'eau, né du bassin rond et enjambé par le pont en pierre.', [(26, 52, 18, 3)], 14, (31.6, 56.9)),
    ('z-cour', 'Cour du grand arbre', 'Cour de gravier de 12 × 12 avec 4 grandes lampes et 4 haies coniques.', [(34, 25, 12, 12)], 14, (40, 36.3)),
    ('z-mousse', 'Jardin de mousse', 'Bassin rond, érables rouges et pas japonais le long de la cour.', [(26, 25.5, 8, 11.5)], 14, (30, 25.1)),
    ('z-the', 'Jardin de thé', 'Petit clos de cordes : glycine, mortier, théière, érable.', [(46.5, 25.5, 8.5, 7.5)], 14, (50.75, 33.9)),
    ('z-rue', 'Rue des artisans', 'Chaque machine y a sa place pour de bon, façade sur la rue, les plus fréquentées près des stockages.', [(1, 16.5, 59, 3), (38, 19.5, 4, 5.5)], 14, (30, 18.35)),
    ('z-carriere', 'Carrière', '12 emplacements de mines 5 × 5, remplis au fil des paliers.', [(60, 15, 20, 15)], 14, (70, 29.6)),
    ('z-terr-o', 'Terrasse ouest', 'Terrasse de culture bordée de diguettes : champs, pépinières et leurs appareils de climat, réglés à chaque palier.', [(t['x'], t['y'], t['w'], t['h']) for t in TW], 14, (14.4, 25.1)),
    ('z-terr-e', 'Terrasse est', 'Terrasse de culture bordée de diguettes : champs, pépinières et leurs appareils de climat, réglés à chaque palier.', [(t['x'], t['y'], t['w'], t['h']) for t in TE], 14, (70, 54.3)),
    ('z-sec', 'Jardin sec', 'Gravier ratissé, grande roche, souche moussue et mortier en pierre.', [(12, 52, 15, 7.5), (2, 51, 9, 9)], 14, (19.5, 59.3)),
    ('z-nord', 'Jardin ratissé du nord', 'Gravier ratissé entre les pavillons, avec une figurine en pierre.', [(17.5, 1, 8, 8.2)], 14, (21.5, 8.6)),
    ('z-eclo', 'Pavillon des éclosions', 'Tes 8 éclorateurs sur un parvis de dalles.', [(47.4, 54.6, 9.2, 4.8)], 14, (52, 54.2)),
    ('z-bosquet', 'Bosquet de bambous', 'Bambous dès le VR 16, un cerisier au VR 18.', [(52, 0, 8, 11)], 16, (56, 11.4)),
    ('z-fleurs', 'Jardin des fleurs', 'Le Moulin floral, sa lampe et un pied de fleur d\'oranger, à partir du VR 18.', [(40.4, 3.8, 11.6, 6.4)], 18, (46.2, 3.4)),
    ('z-montagne', 'Montagne', 'Deux roches « Pics majestueux » et un pin derrière la carrière.', [(60, 0, 20, 13)], MOUNT, (70, 12.4)),
    ('z-terr-m', 'Terrasse de la montagne', 'Ouverte au VR 20 seulement, pour que toutes les cultures trouvent leur climat.', [(t['x'], t['y'], t['w'], t['h']) for t in GL['extra']], 'ph20x', (70, 14.6)),
]
for key, fr, role, rects, ph, (lx, ly) in ZONES:
    T(key, fr, 'Lieux', None, '', role)
    for (x, y, w, h) in rects:
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="obj zone"{tag(key)}/>', ph, 2.5)
    nlabel(lx, ly, fr, .82, ph)
for x, y, txt, sz, ph in NAMES:
    add(f'<text x="{f(x)}" y="{f(y)}" font-size="{sz}" text-anchor="middle" class="nm">{txt}</text>', ph, 13)
for L in LEVELS:
    add(f'<g class="lv" data-lv="{L}">{LV[L]}</g>', 14, 5)

# ---------------- page ----------------
def phcls(p):
    return '' if p == 14 else (f'ph{p}' if isinstance(p, int) else p)
order = sorted(svg, key=lambda t: t[1])
body = '\n'.join(f'<g class="{phcls(p)}">{m}</g>' if p != 14 else m for p, _, m in order)
shop_list = {}
phn = lambda p: p if isinstance(p, int) else 16 if 'ph16' in p else 20
for (i, ph), n in used.items():
    shop_list.setdefault(i, [0, 99]); shop_list[i][0] += n; shop_list[i][1] = min(shop_list[i][1], phn(ph))
buy = []
for i, (n, ph) in sorted(shop_list.items(), key=lambda kv: (kv[1][1], -JP[kv[0]]['cf'] * kv[1][0])):
    j = JP[i]
    pr = int(''.join(c for c in (j['price'] or '0').split(' ')[0] if c.isdigit()) or 0)
    if n > (j['max'] or 999):
        print('OVER CAP', j['fr'], n, j['max'])
    buy.append({'id': i, 'fr': j['fr'], 'n': n, 'ph': ph, 'cf': j['cf'], 'pr': pr, 'fp': j['fp'], 'ic': ic_jp(i)})
exec(open(os.path.join(S, 'garden_page_3d.py')).read())
exec(open(os.path.join(S, 'garden_page_cards.py')).read())
exec(open(os.path.join(S, 'garden_page_steps.py')).read())
defs = ''.join(f'<symbol id="i-{k.replace(" ", "_")}" viewBox="0 0 1 1"><image href="{v}" width="1" height="1" preserveAspectRatio="xMidYMid meet"/></symbol>' for k, v in ICON.items())
for k in ICON:
    if ' ' in k:
        body = body.replace(f'#i-{k}"', f'#i-{k.replace(" ", "_")}"')
data = {'types': TYPES, 'tab': {L: {'avg': v['avg'], 'powered': v['powered']} for L, v in TAB.items()}, 'roster': json.load(open(os.path.join(S, 'roster.json'))), 'levels': LEVELS, 'buy': buy, 'avgPlan': 4.66, 'scene': S3, 'cards': CARDS, 'pics': PICS, 'portraits': PORTRAITS, 'steps': STEPS, 'design': DESIGN}
tpl = open(os.path.join(S, 'garden_template.html')).read()
html = tpl.replace('/*DEFS*/', defs).replace('/*PLAN*/', body).replace('/*DATA*/', json.dumps(data, ensure_ascii=False)).replace('/*G3D*/', open(os.path.join(S, 'garden_3d.js')).read())
open('/home/user/ClaudeHome/jardin-foyer-concept.html', 'w').write(html)
print('size', len(html))
