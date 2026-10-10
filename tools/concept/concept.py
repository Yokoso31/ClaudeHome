"""Concept masterplan: the player's homeland as a Japanese garden, design first.

Everything is in game tiles on the 80 x 60 homeland (plots of 20 x 15). Zones are drawn first;
production goes into the places the design leaves for it. Every decor piece drawn is a real
piece from the game's furniture shop, at its real footprint, and is counted in the shopping list.
Writes jardin-foyer-concept.html.
"""
import base64, json, math, os, random

S = os.path.dirname(os.path.abspath(__file__))
FAC = {l.split('|')[0]: l.split('|')[1].strip().split('/')[-1] for l in open(os.path.join(S, 'web', 'icon_list.txt')) if '|' in l}
JP = json.load(open(os.path.join(S, 'web', 'jp_fp.json')))
FR = {}
for line in open(os.path.join(S, 'foyer_data.js')).read().split('\n'):
    if line.startswith('window.FOYER='):
        D = json.loads(line[len('window.FOYER='):-1])
        FR = {k: v['fr'] for k, v in D['fac'].items()}
rnd = random.Random(7)


def b64(path):
    return 'data:image/webp;base64,' + base64.b64encode(open(path, 'rb').read()).decode()


ICON = {}
def ic_fac(n):
    if n not in ICON:
        ICON[n] = b64(os.path.join(S, 'web', 'icons', FAC[n]))
    return n
def ic_jp(i):
    k = 'jp' + i
    if k not in ICON:
        ICON[k] = b64(os.path.join(S, 'jp_icons', f'{i}.webp'))
    return k


svg = []          # (phase, layer, markup)
def add(markup, phase=14, layer=1):
    svg.append((phase, layer, markup))
def rect(x, y, w, h, fill, phase=14, layer=1, rx=0, extra=''):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>', phase, layer)
def num(x, y, n, phase=14):
    add(f'<g class="num"><circle cx="{x}" cy="{y}" r="1.2"/><text x="{x}" y="{y + .43}" text-anchor="middle">{n}</text></g>', phase, 12)
def f(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')

# ---------------- top-down drawings of the decor pieces ----------------
def shadow(cx, cy, r):
    return f'<circle cx="{f(cx + .35)}" cy="{f(cy + .45)}" r="{f(r)}" class="shd"/>'
def blob(cx, cy, r, cls, n=7, jit=.18, seed=0):
    rr = random.Random(seed)
    pts = []
    for k in range(n * 2):
        a = math.pi * 2 * k / (n * 2)
        rad = r * (1 - jit * rr.random())
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    d = 'M' + ' '.join(f'{f(px)} {f(py)}' for px, py in pts) + 'Z'
    return f'<path d="{d}" class="{cls}" stroke-linejoin="round"/>'
def star(cx, cy, r, ri, n, cls):
    pts = []
    for k in range(n * 2):
        a = math.pi * k / n - math.pi / 2
        rad = r if k % 2 == 0 else ri
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return f'<path d="M{" ".join(f"{f(px)} {f(py)}" for px, py in pts)}Z" class="{cls}"/>'

def paint(i, x, y, w, h):
    cx, cy = x + w / 2, y + h / 2
    s = rnd.randint(0, 999)
    if i == '40300014':   # red maple
        return shadow(cx, cy, 1.55) + blob(cx, cy, 1.6, 'maple', 9, .22, s) + blob(cx - .35, cy - .35, .8, 'maple-l', 6, .25, s + 1)
    if i == '40300003':
        return shadow(cx, cy, 2.4) + blob(cx, cy, 2.4, 'gold', 9, .2, s)
    if i == '40300007':   # pine
        return shadow(cx, cy, 2.3) + star(cx, cy, 2.5, 1.7, 13, 'pine') + star(cx, cy, 1.4, .9, 9, 'pine-l')
    if i == '40300002':   # bamboo
        out = shadow(cx, cy, .95)
        for k in range(7):
            a = k * 2.4 + s
            out += f'<circle cx="{f(cx + .55 * math.cos(a) * (k % 3) / 2)}" cy="{f(cy + .55 * math.sin(a) * (k % 3) / 2)}" r=".42" class="bamboo"/>'
        return out + f'<circle cx="{f(cx)}" cy="{f(cy)}" r=".22" class="bamboo-l"/>'
    if i == '40300004':   # cherry
        out = shadow(cx, cy, 3.6) + blob(cx, cy, 3.7, 'cherry', 11, .16, s) + blob(cx - .8, cy - .7, 1.9, 'cherry-l', 8, .2, s + 2)
        for k in range(14):
            a = rnd.random() * 6.28; rr = rnd.random() * 3
            out += f'<circle cx="{f(cx + rr * math.cos(a))}" cy="{f(cy + rr * math.sin(a))}" r=".14" class="petal"/>'
        return out
    if i in ('40600065', '40600066'):  # glowing stone lamps
        r = .95 if i == '40600065' else .55
        return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r * 1.9)}" class="glow"/><rect x="{f(cx - r / 2)}" y="{f(cy - r / 2)}" width="{f(r)}" height="{f(r)}" rx=".08" class="lamp"/><circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r * .22)}" class="lamp-l"/>'
    if i == '40700002':   # cone hedge
        return shadow(cx, cy, .5) + f'<circle cx="{f(cx)}" cy="{f(cy)}" r=".5" class="hedge"/><circle cx="{f(cx)}" cy="{f(cy)}" r=".24" class="hedge-l"/>'
    if i in ('40700001', '40700032'):  # box hedge
        return f'<rect x="{f(x + .05)}" y="{f(y + .05)}" width="{f(w - .1)}" height="{f(h - .1)}" rx=".42" class="hedge"/><rect x="{f(x + .3)}" y="{f(y + .28)}" width="{f(w - .6)}" height="{f(h - .56)}" rx=".25" class="hedge-l"/>'
    if i == '40700016':   # flowering shrub
        out = shadow(cx, cy, .5) + blob(cx, cy, .52, 'shrub', 6, .2, s)
        for k in range(4):
            out += f'<circle cx="{f(cx + .25 * math.cos(k * 1.7))}" cy="{f(cy + .25 * math.sin(k * 1.7))}" r=".09" class="petal"/>'
        return out
    if i == '40700017':   # moss stump
        return f'<circle cx="{f(cx)}" cy="{f(cy)}" r=".46" class="stump"/><circle cx="{f(cx - .1)}" cy="{f(cy - .1)}" r=".2" class="moss"/>'
    if i in ('40700028', '40700029', '40700030'):  # big rocks
        return shadow(cx, cy, w * .42) + blob(cx, cy, w * .46, 'rock', 8, .3, s) + blob(cx - w * .08, cy - h * .1, w * .26, 'moss', 6, .35, s + 3) + blob(cx + w * .12, cy + h * .12, w * .14, 'rock-l', 5, .3, s + 5)
    if i in ('40600027', '40600083'):
        return blob(cx, cy, max(w, h) * .45, 'rock', 6, .25, s)
    if i == '40600055':
        return f'<circle cx="{f(cx)}" cy="{f(cy)}" r=".26" class="tea"/>'
    if i == '40500003':   # stone bridge (drawn lengthwise along its long side)
        out = f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx=".5" class="bridge"/>'
        if h > w:
            for k in range(1, int(h * 2)):
                out += f'<line x1="{f(x + .35)}" y1="{f(y + k * .5)}" x2="{f(x + w - .35)}" y2="{f(y + k * .5)}" class="plank"/>'
            out += f'<rect x="{f(x)}" y="{f(y)}" width=".3" height="{f(h)}" rx=".15" class="rail"/><rect x="{f(x + w - .3)}" y="{f(y)}" width=".3" height="{f(h)}" rx=".15" class="rail"/>'
        return out
    if i == '40100006':   # moss stepping stones
        out = ''
        for dx, dy, r in ((.6, .6, .5), (1.4, 1.3, .55), (.7, 1.5, .32), (1.5, .45, .3)):
            out += blob(x + dx, y + dy, r, 'step', 6, .25, s + int(dx * 10))
        return out
    if i == '40200023':   # wood-and-rope fence
        if w >= h:
            return f'<line x1="{f(x)}" y1="{f(cy)}" x2="{f(x + w)}" y2="{f(cy)}" class="rope"/><circle cx="{f(x + .1)}" cy="{f(cy)}" r=".14" class="post"/><circle cx="{f(x + w - .1)}" cy="{f(cy)}" r=".14" class="post"/>'
        return f'<line x1="{f(cx)}" y1="{f(y)}" x2="{f(cx)}" y2="{f(y + h)}" class="rope"/><circle cx="{f(cx)}" cy="{f(y + .1)}" r=".14" class="post"/><circle cx="{f(cx)}" cy="{f(y + h - .1)}" r=".14" class="post"/>'
    if i == '40400018':   # wisteria
        return ''.join(f'<ellipse cx="{f(x + .2 + k * .3)}" cy="{f(cy + .25)}" rx=".13" ry=".32" class="wist"/>' for k in range(3))
    if i == '40400045':   # white flowering vine
        out = blob(cx, cy, max(w, h) * .4, 'vine', 7, .3, s)
        for k in range(5):
            out += f'<circle cx="{f(cx + (k - 2) * .4 * (w > h))}" cy="{f(cy + (k - 2) * .4 * (h > w))}" r=".1" class="whitef"/>'
        return out
    return None

TYPES = {}  # key -> {fr, cat, ic, size, role}
def T(key, fr, cat, ic=None, size='', role=''):
    if key not in TYPES:
        TYPES[key] = {'fr': fr, 'cat': cat, 'ic': ic, 'size': size, 'role': role}
    return key
def tag(key, label=None):
    lab = (label or TYPES[key]['fr']).replace('"', '&quot;')
    return f' data-t="{key}" data-n="{lab}"'
SHORT = {'Carousel Mill': 'Moulin', 'Chimney Kiln': 'Four', 'Joy Wheel Loom': 'Roue à tisser', 'Woodworking Bench': 'Menuiserie', 'Crafting Table': 'Établi',
         'Jukebox Dryer': 'Séchoir', 'Simmering Pot': 'Marmite', 'Phonolfactory Table': 'Parfums', 'Pickling Jar': 'Bocal', 'Blazing Stove': 'Cuisinière',
         'Bouncy Brew Keg': 'Tonneau', 'Claw Game Cooker': 'Attrape-popote', 'Aniipod Maker': 'Aniipod', 'Dance Pad Polisher': 'Polissoir',
         'Nimbus Bed': 'Lit de Cumulaine', 'Starfall Hammock': 'Hamac', 'Tidewhisper Sandcastle': 'Château de sable', 'Dewy House': 'Plumiel'}
NAMES = []  # (x, y, text, size, phase) labels shown with « Noms sur le plan »
def nlabel(x, y, txt, size=.62, phase=14):
    NAMES.append((x, y, txt, size, phase))
used = {}   # decor counts for the shopping list
PHYS = []   # (name, rect, phase) for the collision check
CLEAR = []  # paths that must stay walkable
def phys(name, x, y, w, h, phase=14):
    PHYS.append((name, {'x': x, 'y': y, 'w': w, 'h': h}, phase))
def deco(i, x, y, phase=14, rot=False, layer=6, draw=True):
    w, h = JP[i]['fp']
    if rot:
        w, h = h, w
    used[(i, phase)] = used.get((i, phase), 0) + 1
    phys(JP[i]['fr'], x, y, w, h, phase)
    if not draw:
        return w, h
    art = paint(i, x, y, w, h)
    if art is None:
        art = f'<use href="#i-{ic_jp(i)}" x="{x}" y="{y}" width="{w}" height="{h}"/>'
    j = JP[i]
    T('jp' + i, j['fr'], 'Déco', ic_jp(i), f'{f(j["fp"][0])} × {f(j["fp"][1])}', f'Déco · {j["price"]} · {j["cf"]} de confort' + (f' · se débloque au VR {j["rv"]}' if j.get('rv') and j['rv'] > 14 else ''))
    add(f'<g class="obj dc"{tag("jp" + i)}>{art}</g>', phase, layer)
    return w, h

# ---------------- ground ----------------
rect(0, 0, 80, 60, 'url(#grass)', layer=0)
for (x, y, w, h) in ((20, 25.5, 14, 11.5), (46.5, 25.5, 13, 11), (0, 50.5, 28, 9.5), (56, 53, 24, 7)):
    rect(x, y, w, h, 'url(#mossy)', layer=0, rx=2.5)
rect(40, 0, 40, 15, 'url(#later)', layer=11, extra='class="lock16"')
add('<text x="60" y="7.9" class="lock16 locktxt" font-size="1.3" text-anchor="middle">S\'ouvre au VR 16</text>', 14, 11)

# ---------------- 1 · entrance and approach ----------------
rect(38, 37, 4, 23, 'url(#slabs)', layer=2)
CLEAR += [('allée', {'x': 38, 'y': 37, 'w': 4, 'h': 13.5}), ('allée', {'x': 38, 'y': 55.5, 'w': 4, 'h': 4.5})]
deco('40600065', 35.9, 58.2); deco('40600065', 42.35, 58.2)
for y in (39.5, 43.5, 47.5, 57.2):
    deco('40600066', 37.1, y); deco('40600066', 42.15, y)
num(40, 59.4, 1)

# ---------------- 2 · dry stream, round pond and bridge ----------------
# A kare-nagare: a winding bed of raked gravel and river stones that stands for water, laid with
# 2 x 2 gravel floor tiles, rising from a real round pond and crossed by the stone bridge.
STREAM = [(26, 52), (28, 52.5), (30, 53), (32, 53), (34, 52.5), (36, 52), (38, 52), (40, 52), (42, 52.5)]
pts = [(x + 1, y + 1) for x, y in STREAM]
d = 'M' + ' '.join(f'{f(px)} {f(py)}' for px, py in pts)
add(f'<path d="{d}" class="stream-edge"/><path d="{d}" class="stream"/>', 14, 2)
for x, y in STREAM:
    used[('40100008', 14)] = used.get(('40100008', 14), 0) + 1
    phys('Sol en gravier', x, y, 2, 2)
for k, (px, py) in enumerate(pts[:-1]):
    qx, qy = pts[k + 1]
    for t in (.3, .75):
        add(blob(px + (qx - px) * t + (.45 if k % 2 else -.45), py + (qy - py) * t + (.3 if k % 3 else -.35), .2 + .08 * (k % 3), 'pebble', 5, .3, k * 7 + int(t * 10)), 14, 3)
T('z-stream', 'Rivière sèche', 'Lieux', None, '', '')
def pond(x, y, phase=14):
    """The game's round pond: grassy rim, stones, water lilies (2 x 2 on the shop sheet)."""
    cx, cy = x + 1, y + 1
    used[('40700003', phase)] = used.get(('40700003', phase), 0) + 1
    phys('Bassin', x, y, 2, 2, phase)
    j = JP['40700003']
    T('jp40700003', j['fr'], 'Déco', ic_jp('40700003'), '2 × 2', f'Petit étang rond complet, avec son bord d\'herbe · {j["price"]} · {j["cf"]} de confort')
    art = (shadow(cx, cy, 1) + f'<circle cx="{cx}" cy="{cy}" r="1.02" class="pond-rim"/><ellipse cx="{f(cx + .05)}" cy="{f(cy + .05)}" rx=".68" ry=".62" class="pond-w"/>'
           f'<circle cx="{f(cx - .1)}" cy="{f(cy - .05)}" r=".2" class="lily"/><circle cx="{f(cx + .3)}" cy="{f(cy + .25)}" r=".11" class="lily"/><circle cx="{f(cx - .35)}" cy="{f(cy + .2)}" r=".13" class="lily"/>'
           + blob(cx + .2, cy - .7, .26, 'pebble', 5, .3, int(x)) + blob(cx + .75, cy - .15, .16, 'pebble', 5, .3, int(y)) + blob(cx - .3, cy + .78, .14, 'pebble', 5, .3, 3)
           + f'<circle cx="{f(cx - .45)}" cy="{f(cy - .62)}" r=".14" class="whitef"/>')
    add(f'<g class="obj dc"{tag("jp40700003")}>{art}</g>', phase, 6)
pond(44, 52.2)            # the source of the dry stream
deco('40500003', 38.5, 50.5, rot=True, layer=7)
for x, y in ((23.9, 50.6), (43.8, 48.6), (30.6, 55.6)):
    deco('40300014', x, y)
deco('40700017', 46.6, 56.2); deco('40700016', 33.4, 50.6); deco('40700016', 35.6, 55.2)
num(31, 50.2, 2)

# ---------------- 3 · courtyard of the great tree ----------------
rect(34, 25, 12, 12, 'url(#gravel)', layer=2, rx=.6)
add('<circle cx="40" cy="31" r="5.3" class="ring"/><circle cx="40" cy="31" r="5.8" class="ring"/>', 14, 3)
T('bigtree', 'Grand arbre violet', 'Lieux', None, 'à confirmer', 'Ton grand arbre actuel, déplacé au centre de la cour. Sa taille au sol reste à mesurer.')
add(f'<g class="obj bigtree"{tag("bigtree")}>' + shadow(40, 31, 4) +
    blob(40, 31, 4.3, 'wis', 12, .14, 3) + blob(38.6, 29.9, 2.3, 'wis-l', 8, .2, 4) + blob(41.8, 32.2, 2.2, 'wis-l', 8, .2, 5) + blob(40.6, 29.2, 1.4, 'wis-ll', 7, .2, 6) + '</g>', 14, 8)
for x, y in ((34.4, 25.4), (43.85, 25.4), (34.4, 35.1), (43.85, 35.1)):
    deco('40600065', x, y)
for x, y in ((39.5, 25.3), (39.5, 35.7), (34.3, 30.5), (44.7, 30.5)):
    deco('40700002', x, y)
num(46.4, 24.6, 3)

# ---------------- moss garden, west of the courtyard ----------------
for x, y in ((31.5, 30.5), (29.5, 31.6), (27.5, 32.7), (25.5, 33.8), (23.5, 34.9), (21.4, 36)):
    deco('40100006', x, y, layer=3)
deco('40300014', 21.5, 26.6); deco('40300014', 29, 26.4); deco('40300014', 31.6, 34.6)
deco('40300007', 23.6, 28.4)
pond(27.6, 29)
deco('40600065', 30.4, 28.4)
deco('40700016', 27.6, 35.4); deco('40700016', 33, 28.6); deco('40700017', 20.6, 31.6)

# ---------------- tea garden, east of the courtyard ----------------
for x in (47.6, 49.6, 51.6, 53.6, 55.6):
    deco('40200023', x, 26.1)
for x in (47.6, 49.6, 53.6, 55.6):
    deco('40200023', x, 35.4)
for y in (26.4, 28.4, 30.4, 32.4):
    deco('40200023', 47.4, y, rot=True); deco('40200023', 57.6, y, rot=True)
deco('40400018', 48.2, 26.35); deco('40400018', 50.4, 26.35); deco('40400018', 52.6, 26.35)
deco('40400045', 57.1, 30.4, rot=True)
deco('40100006', 51.6, 32.6, layer=3); deco('40100006', 52.4, 30.3, layer=3)
deco('40600083', 49.4, 28.6); deco('40600066', 48.6, 29.4); deco('40600055', 54.6, 29.6)
deco('40300014', 54.8, 27.2); deco('40700016', 49, 33.4); deco('40700016', 55.6, 33.6)

# ---------------- 4 · craftsmen's street ----------------
rect(1, 16.5, 59, 3, 'url(#slabs)', layer=2)
rect(38, 19.5, 4, 5.5, 'url(#slabs)', layer=2)
CLEAR += [('rue', {'x': 1, 'y': 16.5, 'w': 59, 'h': 3}), ('lien', {'x': 38, 'y': 19.5, 'w': 4, 'h': 5.5})]
num(2.2, 18, 4)
KIOSK = {1: (17, 19.75), 2: (51, 19.75), 3: (17, 43), 4: (62, 44), 5: (58, 21)}
for k, (x, y) in KIOSK.items():
    phys('stockage %d' % k, x, y, 2, 2)
    T('Storage Unit', FR.get('Storage Unit', 'Unité de stockage'), 'Stockage', ic_fac('Storage Unit'), '2 × 2', 'Les porteurs y déposent la production. Numérotés en vue technique.')
    add(f'<g class="obj kiosk"{tag("Storage Unit", "Unité de stockage " + str(k))}><rect x="{x - .15}" y="{y - .15}" width="2.3" height="2.3" rx=".25" class="eave"/><rect x="{x + .15}" y="{y + .15}" width="1.7" height="1.7" class="roof"/>'
        f'<path d="M{x + .15} {y + .15}L{x + 1.85} {y + 1.85}M{x + 1.85} {y + .15}L{x + .15} {y + 1.85}" class="ridge"/>'
        f'<g class="tech"><circle cx="{x + 2}" cy="{y}" r=".6"/><text x="{x + 2}" y="{y + .25}" text-anchor="middle">{k}</text></g></g>', 14, 7)
L14 = json.load(open(os.path.join(S, 'my_lay_in_rv14.json')))
FP = {'Woodworking Bench': (2, 1.5), 'Chimney Kiln': (5.5, 5.5), 'Jukebox Dryer': (2.5, 2.5), 'Simmering Pot': (1.5, 1.5), 'Phonolfactory Table': (3.5, 3.5),
      'Carousel Mill': (5.5, 5.5), 'Pickling Jar': (2.5, 2), 'Blazing Stove': (2.5, 1.75), 'Joy Wheel Loom': (4, 4), 'Crafting Table': (4, 4),
      'Bouncy Brew Keg': (3, 3), 'Claw Game Cooker': (3.5, 3.5), 'Aniipod Maker': (4.5, 4.5), 'Dance Pad Polisher': (2.5, 2.5)}
shops = []
for p in L14['pieces']:
    if p.get('cluster'):
        continue
    m = p['members'][0]
    if m['facility'] in FP:
        shops.append((m['facility'], m.get('weight') or 0, m.get('crop')))
shops.sort(key=lambda s: -s[1])
SIDES = {'S': {'y': 19.5, 'runs': [[1, 16.8], [19.4, 33], [47, 50.8], [53.4, 57.6]], 'down': True},
         'N': {'y': 16.5, 'runs': [[1, 37.5]], 'down': False}}
placed_shops, reserve = [], []
def try_place(w):
    best = None
    for side, sd in SIDES.items():
        for run in sd['runs']:
            occ = sorted([(s['x'], s['x'] + s['w']) for s in placed_shops if s['side'] == side and run[0] - 1e-6 <= s['x'] < run[1]])
            for x0 in [run[0]] + [b + 1 for a, b in occ]:
                if x0 + w > run[1] + 1e-6 or any(not (x0 + w + 1 <= a + 1e-6 or x0 >= b + 1 - 1e-6) for a, b in occ):
                    continue
                d = min(abs(x0 + w / 2 - 18), abs(x0 + w / 2 - 52))
                if best is None or d < best[0]:
                    best = (d, side, x0)
    return best
for name, wgt, crop in shops:
    w, h = FP[name]
    b = try_place(w)
    if b is None or (wgt == 0 and b[0] > 30):
        reserve.append(name); continue
    _, side, x0 = b
    y = SIDES[side]['y'] if SIDES[side]['down'] else SIDES[side]['y'] - h
    placed_shops.append({'n': name, 'x': x0, 'y': y, 'w': w, 'h': h, 'side': side, 'wgt': wgt, 'crop': crop})
    phys(name, x0, y, w, h)
for s in placed_shops:
    idle = s['wgt'] == 0
    x, y, w, h = s['x'], s['y'], s['w'], s['h']
    ridge = f'M{f(x + .35)} {f(y + h / 2)}H{f(x + w - .35)}' if w >= h else f'M{f(x + w / 2)} {f(y + .35)}V{f(y + h - .35)}'
    T(s['n'], FR.get(s['n'], s['n']), 'Ateliers', ic_fac(s['n']), f'{f(w)} × {f(h)}', 'Atelier de transformation, façade sur la rue des artisans.')
    lab = FR.get(s['n'], s['n']) + (' · inactif au VR 14' if idle else f' · {round(s["wgt"])} trajets/h')
    nlabel(x + w / 2, y + h / 2 + .2, SHORT.get(s['n'], s['n']), .5 if w < 3 else .6)
    add(f'<g class="obj shop{" idle" if idle else ""}"{tag(s["n"], lab)}>'
        f'<rect x="{f(x + .25)}" y="{f(y + .3)}" width="{f(w)}" height="{f(h)}" rx=".3" class="shd"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx=".3" class="eave"/><rect x="{f(x + .25)}" y="{f(y + .25)}" width="{f(w - .5)}" height="{f(h - .5)}" rx=".2" class="roof"/>'
        f'<path d="{ridge}" class="ridge"/>'
        f'<use href="#i-{ic_fac(s["n"])}" x="{f(x + w * .2)}" y="{f(y + h * .2)}" width="{f(w * .6)}" height="{f(h * .6)}" class="sign"/></g>', 14, 6)
def gap_spot(cx, y):
    for d in [k * .5 for k in range(0, 60)]:
        for x in (cx + d, cx - d):
            r = {'x': x, 'y': y, 'w': 1, 'h': 1}
            if all(not (min(r['x'] + 1, s['x'] + s['w']) - max(r['x'], s['x']) > 1e-6 and min(r['y'] + 1, s['y'] + s['h']) - max(r['y'], s['y']) > 1e-6) for s in placed_shops) \
               and all(not (min(r['x'] + 1, kx + 2) - max(r['x'], kx) > 1e-6 and min(r['y'] + 1, ky + 2) - max(r['y'], ky) > 1e-6) for kx, ky in KIOSK.values()):
                return x
    return None
GENS = [(gap_spot(20, 15.4), 15.4), (gap_spot(48, 19.6), 19.6)]
for x, y in GENS:
    phys('générateur', x, y, 1, 1)
    T('Crackle Generator', FR.get('Crackle Generator', 'Générateur'), 'Climat et énergie', ic_fac('Crackle Generator'), '1 × 1', 'Alimente les machines dans un carré de 11 × 11. Tenu par un Aniimo Foudre.')
    add(f'<g class="obj gen"{tag("Crackle Generator")}><rect x="{x}" y="{y}" width="1" height="1" rx=".2"/></g>', 14, 10)

# ---------------- 5 · quarry under the mountain ----------------
rect(60, 15, 20, 15, 'url(#stone)', layer=1, rx=.4)
mines = [(x, y) for y in (25, 20, 15) for x in (60, 65, 70, 75)]
for k, (x, y) in enumerate(mines):
    if k < 7:
        phys('mine', x, y, 5, 5)
        T('Mine', FR.get('Mine', 'Mine'), 'Production', ic_fac('Mine'), '5 × 5', 'Mine de la carrière.')
        add(f'<g class="obj mine"{tag("Mine")}>' + shadow(x + 2.5, y + 2.5, 2.1) + blob(x + 2.5, y + 2.5, 2.35, 'rock', 8, .22, k) +
            blob(x + 2.1, y + 2.1, 1.1, 'rock-l', 6, .3, k + 9) + f'<use href="#i-{ic_fac("Mine")}" x="{x + 1.1}" y="{y + 1.1}" width="2.8" height="2.8" class="sign"/></g>', 14, 6)
    else:
        add(f'<rect x="{x + .4}" y="{y + .4}" width="4.2" height="4.2" rx=".6" class="slot"><title>Emplacement de mine pour les VR suivants</title></rect>', 16 if k < 9 else 18, 6)
deco('40700030', 61.5, 2, phase=16); deco('40700030', 70.5, 2, phase=16)
num(78.6, 16.6, 5)

# ---------------- 6 · rice terraces ----------------
for bx in (4, 20):
    rect(bx - .6, 37.4, 13.2, 13.2, 'url(#dike)', layer=1, rx=.5)
T('Sunlamp', FR.get('Sunlamp'), 'Climat et énergie', ic_fac('Sunlamp'), '1 × 1', 'Éclaire les cultures dans un carré de 9 × 9 (vue technique). Tenue par un Aniimo Lumière.')
T('Heat Furnace', FR.get('Heat Furnace'), 'Climat et énergie', ic_fac('Heat Furnace'), '1 × 1', 'Chauffe les cultures dans un carré de 9 × 9 (vue technique). Tenue par un Aniimo Feu.')
T('Cooling Unit', FR.get('Cooling Unit'), 'Climat et énergie', ic_fac('Cooling Unit'), '2 × 2', 'Rafraîchit dans un carré de 9 × 9 (vue technique). Tenue par un Aniimo Glace.')
DEVN = {'sun': 'Sunlamp', 'heat': 'Heat Furnace', 'cool': 'Cooling Unit'}
def paddy(bx, by, crops, mode, phase=14):
    k = 0
    for j in range(6):
        for i in range(6):
            if i in (2, 3) and j in (2, 3):
                continue
            x, y = bx + 2 * i, by + 2 * j
            c = crops[k] if k < len(crops) else None
            k += 1
            cls = {'grape': 'pd grape', 'quick_rice': 'pd rice', None: 'pd fallow'}[c]
            rows = '' if c is None else ''.join(f'<line x1="{x + .35}" y1="{y + .55 + r * .45}" x2="{x + 1.65}" y2="{y + .55 + r * .45}" class="rowl"/>' for r in range(3))
            T('Farmland', FR.get('Farmland', 'Ferme'), 'Production', ic_fac('Farmland'), '2 × 2', 'Champ des rizières.')
            crop = {'grape': 'Raisin, éclairé par la lampe', 'quick_rice': 'Riz (rapide)', None: 'emplacement libre pour les VR suivants'}[c]
            key = 'Farmland' if c else T('free-farm', 'Emplacement de champ libre', 'Production', None, '2 × 2', 'Prévu pour les champs des VR suivants.')
            add(f'<g class="obj"{tag(key, (FR.get("Farmland", "Ferme") + " · " + crop) if c else None)}><rect x="{x + .1}" y="{y + .1}" width="1.8" height="1.8" rx=".22" class="{cls}"/>{rows}</g>', phase, 4)
    add(f'<rect x="{bx + 4.2}" y="{by + 4.2}" width="3.6" height="3.6" rx=".5" class="pd-center"/>', phase, 4)
    if mode:
        add(f'<g class="obj dev {mode}"{tag(DEVN[mode])}><rect x="{bx + 5.5}" y="{by + 5.5}" width="1" height="1" rx=".2"/><rect x="{bx + 1.5}" y="{by + 1.5}" width="9" height="9" class="sq tech"/></g>', phase, 7)
    deco('40600066', bx + 4.5, by + 4.5, phase)
phys('rizière 1', 4, 38, 12, 12); phys('rizière 2', 20, 38, 12, 12); phys('verger 1', 46, 37, 16, 16); phys('verger 2', 64, 37, 16, 16)
phys('grand arbre', 37, 28, 6, 6)
paddy(4, 38, ['grape'] * 29 + ['quick_rice'], 'sun')
paddy(20, 38, [], None)
add('<text x="26" y="44.4" class="lbl soft2" font-size=".75" text-anchor="middle">en réserve</text>', 14, 9)
deco('40300002', .6, 37.6); deco('40300002', .6, 42); deco('40300002', .6, 46.4)
num(3.2, 37.2, 6)

# ---------------- 7 · orchards ----------------
def orchard(bx, by, trees, mode, phase=14):
    k = 0
    for j in range(4):
        for i in range(4):
            if i in (1, 2) and j in (1, 2):
                continue
            x, y = bx + 4 * i, by + 4 * j
            t = trees[k] if k < len(trees) else None
            k += 1
            cx, cy = x + 2, y + 2
            if t == 'coco':
                T('Woodland', FR.get('Woodland', 'Pépinière'), 'Production', ic_fac('Woodland'), '4 × 4', 'Pépinière des vergers.')
                add(f'<g class="obj wood"{tag("Woodland", FR.get("Woodland", "Pépinière") + " · Noix de coco, chauffée par la fournaise")}><rect x="{x + .15}" y="{y + .15}" width="3.7" height="3.7" rx=".5" class="bed"/>' + shadow(cx, cy, 1.5) + star(cx, cy, 1.75, .55, 7, 'palm') + star(cx, cy, .9, .3, 7, 'palm-l') + '</g>', phase, 4)
            elif t == 'lemon':
                T('Woodland', FR.get('Woodland', 'Pépinière'), 'Production', ic_fac('Woodland'), '4 × 4', 'Pépinière des vergers.')
                add(f'<g class="obj wood"{tag("Woodland", FR.get("Woodland", "Pépinière") + " · Citron (rapide)")}><rect x="{x + .15}" y="{y + .15}" width="3.7" height="3.7" rx=".5" class="bed"/>' + shadow(cx, cy, 1.4) + blob(cx, cy, 1.55, 'citrus', 8, .18, k) +
                    ''.join(f'<circle cx="{f(cx + .8 * math.cos(a))}" cy="{f(cy + .8 * math.sin(a))}" r=".2" class="lemon"/>' for a in (0.4, 2.2, 4.1)) + '</g>', phase, 4)
            else:
                T('free-wood', 'Emplacement de pépinière libre', 'Production', None, '4 × 4', 'Prévu pour les pépinières des VR suivants.')
                add(f'<rect x="{x + .4}" y="{y + .4}" width="3.2" height="3.2" rx="1" class="slot obj"{tag("free-wood")}/>', phase, 4)
    rect(bx + 4.3, by + 4.3, 7.4, 7.4, 'url(#gravel)', phase, 3, rx=1)
    if mode:
        add(f'<g class="obj dev {mode}"{tag(DEVN[mode])}><rect x="{bx + 7.5}" y="{by + 7.5}" width="1" height="1" rx=".2"/><rect x="{bx + 3.5}" y="{by + 3.5}" width="9" height="9" class="sq tech"/></g>', phase, 7)
orchard(46, 37, ['coco'] * 12, 'heat')
orchard(64, 37, ['lemon'] * 3, None)
deco('40600027', 53.5, 44.5); deco('40700016', 56.6, 47.6); deco('40700016', 51.4, 41.4)
deco('40600066', 70.2, 42.2); deco('40700016', 73.6, 47.6); deco('40700017', 69.6, 47.2)
num(79, 36, 7)

# ---------------- 8 · hatchery pavilion ----------------
rect(47.4, 54.6, 9.2, 4.8, 'url(#slabs)', layer=2, rx=.4)
for g in range(3):
    rect(42 + 2 * g, 56.1, 2, 2, 'url(#gravelpath)', layer=2, rx=.3)
    used[('40100010', 14)] = used.get(('40100010', 14), 0) + 1
for i in range(4):
    for j in range(2):
        x, y = 48 + 2 * i, 55 + 2 * j
        phys('éclorateur', x, y, 2, 2)
        T('Incubateur', FR.get('Incubateur', 'Éclorateur'), 'Production', ic_jp('10500001'), '2 × 2', 'Tes éclorateurs, regroupés en pavillon près de l\'entrée.')
        add(f'<g class="obj hatch"{tag("Incubateur")}>' + shadow(x + 1, y + 1, .85) + f'<circle cx="{x + 1}" cy="{y + 1}" r=".88" class="dome"/><circle cx="{x + .75}" cy="{y + .75}" r=".32" class="dome-l"/></g>', 14, 6)
num(57.8, 55, 8)

# ---------------- 9 · dry garden ----------------
rect(12, 52, 15, 7.5, 'url(#raked)', layer=2, rx=.6)
add('<g class="rakes">' + ''.join(f'<circle cx="20.5" cy="55.8" r="{r}"/>' for r in (1.1, 1.6, 2.1)) + '</g>', 14, 3)
deco('40700029', 2, 51)
deco('40600083', 20.25, 55.55); deco('40700017', 24.2, 53.4); deco('40700016', 14.2, 57.6)
num(12.4, 51.4, 9)

# ---------------- 10 · pavilions of the north ----------------
PAV = [('Nimbus Bed', 2, 2, 5), ('Starfall Hammock', 9, 2, 5), ('Tidewhisper Sandcastle', 27, 2, 5), ('Dewy House', 34, 3, 2)]
for n, x, y, s in PAV:
    phys(n, x, y, s, s)
    T(n, FR.get(n, n), 'Production', ic_fac(n), f'{s} × {s}', 'Bâtiment de matériaux, en pavillon au nord.')
    nlabel(x + s / 2, y + s + .75, SHORT.get(n, n), .6)
    add(f'<g class="obj pav"{tag(n)}><rect x="{x + .25}" y="{y + .3}" width="{s}" height="{s}" rx=".9" class="shd"/><rect x="{x}" y="{y}" width="{s}" height="{s}" rx=".9" class="eave"/>'
        f'<rect x="{x + .4}" y="{y + .4}" width="{s - .8}" height="{s - .8}" rx=".6" class="roof"/><use href="#i-{ic_fac(n)}" x="{x + s * .18}" y="{y + s * .18}" width="{s * .64}" height="{s * .64}" class="sign"/></g>', 14, 6)
phys('climatisation', 14.5, 5, 2, 2)
add(f'<g class="obj dev cool"{tag("Cooling Unit", FR.get("Cooling Unit") + " · réglée en Frais pour le Hamac")}><rect x="14.5" y="5" width="2" height="2" rx=".3"/><rect x="11" y="1.5" width="9" height="9" class="sq tech"/></g>', 14, 7)
rect(17.5, 1, 8, 8.2, 'url(#raked)', layer=2, rx=.6)
add('<g class="rakes">' + ''.join(f'<circle cx="21.5" cy="5" r="{r}"/>' for r in (1, 1.5, 2)) + '</g>', 14, 3)
deco('40600027', 21, 4.5); deco('40700017', 18.6, 2.4)
for x in (2, 4.6, 22.6, 25.2):
    deco('40700001', x, 9.9)
for x in (30, 33, 36):
    phys('puits', x, 8, 2, 2)
    T('Well', FR.get('Well', 'Puits'), 'Production', ic_fac('Well'), '2 × 2', 'Puits, près de la rue pour l\'électricité.')
    add(f'<g class="obj well"{tag("Well")}><circle cx="{x + 1}" cy="{9}" r=".95" class="wellr"/><circle cx="{x + 1}" cy="{9}" r=".55" class="wellw"/></g>', 14, 6)
num(1.3, 1.3, 10)

# ---------------- north-east, from RV16 / RV18: bamboo and cherry grove ----------------
for x in range(41, 59, 2):
    deco('40300002', x, 0.4, phase=16)
deco('40300004', 43, 3, phase=18); deco('40300004', 51, 3, phase=18)
deco('40300014', 41, 9.6, phase=16); deco('40300014', 58.4, 10.6, phase=16)
for x in range(60, 79, 3):
    deco('40300002', x, 57.6)
deco('40300014', 63.4, 54.2); deco('40300014', 72.6, 54.4)

# ---------------- places of the garden: tap to identify, names on demand ----------------
ZONES = [
    ('z-allee', 'Allée des lanternes', 'Entrée du jardin : dalles moussues bordées de lampes en pierre.', [(38, 37, 4, 23)], 14, (40, 46.2)),
    ('z-stream', 'Rivière sèche et pont', 'Lit de gravier ratissé et de galets qui évoque l\'eau, sorti du bassin rond et enjambé par le pont en pierre.', [(26, 52, 18, 3)], 14, (31.6, 56.9)),
    ('z-cour', 'Cour du grand arbre', 'Cour de gravier de 12 × 12 avec 4 grandes lampes et 4 haies coniques.', [(34, 25, 12, 12)], 14, (40, 36.3)),
    ('z-mousse', 'Jardin de mousse', 'Pas japonais, érables rouges, un pin et une lampe.', [(20, 25.5, 14, 11.5)], 14, (24.4, 25.3)),
    ('z-the', 'Jardin de thé', 'Clos de cordes, glycine, mortier, théière et pas japonais.', [(47, 26, 11, 10)], 14, (52.5, 29)),
    ('z-rue', 'Rue des artisans', 'Rue pavée : les ateliers ont leur façade dessus, les plus fréquentés près des kiosques 1 et 2.', [(1, 16.5, 59, 3), (38, 19.5, 4, 5.5)], 14, (30, 18.35)),
    ('z-carriere', 'Carrière', 'Bloc de 12 emplacements de mines 5 × 5 : 7 au VR 14, les autres pour la suite.', [(60, 15, 20, 15)], 14, (70, 29.3)),
    ('z-riz1', 'Rizière 1', '6 × 6 champs autour de la lampe : 29 champs de raisin et 1 de riz au VR 14.', [(3.4, 37.4, 13.2, 13.2)], 14, (10, 36.9)),
    ('z-riz2', 'Rizière 2', 'Même dessin, en réserve : elle se remplit à partir du VR 15.', [(19.4, 37.4, 13.2, 13.2)], 14, (26, 36.9)),
    ('z-verger1', 'Verger des cocotiers', '12 pépinières autour d\'un jardin de gravier, la fournaise au centre.', [(46, 37, 16, 16)], 14, (54, 52.4)),
    ('z-verger2', 'Verger 2', '3 citronniers au VR 14, il se remplit aux VR suivants.', [(64, 37, 16, 16)], 14, (72, 52.4)),
    ('z-sec', 'Jardin sec', 'Gravier ratissé, grande roche, souche moussue et mortier en pierre.', [(12, 52, 15, 7.5), (2, 51, 9, 9)], 14, (19.5, 59.3)),
    ('z-nord', 'Jardin ratissé du nord', 'Gravier ratissé entre les pavillons, avec une figurine en pierre.', [(17.5, 1, 8, 8.2)], 14, (21.5, 8.6)),
    ('z-eclo', 'Pavillon des éclosions', 'Tes 8 éclorateurs sur un parvis de dalles.', [(47.4, 54.6, 9.2, 4.8)], 14, (52, 54.2)),
    ('z-bosquet', 'Bosquet de bambous', 'Bambous dès le VR 16, deux cerisiers au VR 18.', [(40, 0, 20, 12)], 16, (50, 11.4)),
    ('z-montagne', 'Montagne', 'Deux roches « Pics majestueux » derrière la carrière.', [(60, 0, 20, 13)], 16, (70, 12.4)),
]
for key, fr, role, rects, ph, (lx, ly) in ZONES:
    T(key, fr, 'Lieux', None, '', role)
    for (x, y, w, h) in rects:
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="obj zone"{tag(key)}/>', ph, 2.5)
    nlabel(lx, ly, fr, .82, ph)
for k, (x, y) in KIOSK.items():
    nlabel(x + 1, y + 2.75, f'Stockage {k}', .5)
for x in (30, 33, 36):
    nlabel(x + 1, 10.75, 'Puits', .5)
nlabel(10, 43.3, 'Lampe', .5); nlabel(54, 44.3, 'Fournaise', .5); nlabel(15.5, 7.75, 'Clim', .5)
for x, y in GENS:
    nlabel(x + .5, y - .25, 'Générateur', .45)
for x, y, txt, sz, ph in NAMES:
    add(f'<text x="{f(x)}" y="{f(y)}" font-size="{sz}" text-anchor="middle" class="nm">{txt}</text>', ph, 13)

# ---------------- collision check ----------------
def ov(a, b):
    return min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']) > 1e-6 and min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']) > 1e-6
INSIDE_OK = {('rizière 1', "Lampe en pierre lumineuse\u00a0II"), ('rizière 2', "Lampe en pierre lumineuse\u00a0II"), ('verger 1', 'Figurine sculptée en pierre'), ('verger 1', 'Arbustes en fleurs'),
             ('verger 2', "Lampe en pierre lumineuse\u00a0II"), ('verger 2', 'Arbustes en fleurs'), ('verger 2', "Souche d'arbre recouverte de mousse"),  ('Sol en gravier', 'Pont en pierre'), ('Clôture en bois et corde', 'Liane à fleurs blanches')}
bad = []
for k, (n1, r1, p1) in enumerate(PHYS):
    for n2, r2, p2 in PHYS[k + 1:]:
        if ov(r1, r2) and (n1, n2) not in INSIDE_OK and (n2, n1) not in INSIDE_OK:
            bad.append((n1, r1, n2, r2))
    for cn, cr in CLEAR:
        if ov(r1, cr) and n1 not in ('Pont en pierre',) and not n1.startswith('stockage'):
            bad.append((n1, r1, cn, cr))
    if r1['x'] < -1e-6 or r1['y'] < -1e-6 or r1['x'] + r1['w'] > 80 + 1e-6 or r1['y'] + r1['h'] > 60 + 1e-6:
        bad.append((n1, r1, 'bord', None))
print('collisions', len(bad))
for b in bad:
    print('  ', b)

# ---------------- walking estimate with the concept ----------------
kc = {k: (x + 1, y + 1) for k, (x, y) in KIOSK.items()}
near = lambda cx, cy: min(math.dist((cx, cy), v) for v in kc.values())
tot = wsum = 0
for s in placed_shops:
    if s['wgt'] > 0:
        tot += s['wgt'] * near(s['x'] + s['w'] / 2, s['y'] + s['h'] / 2); wsum += s['wgt']
farm_cells = [(4 + 2 * i + 1, 38 + 2 * j + 1) for j in range(6) for i in range(6) if not (i in (2, 3) and j in (2, 3))][:30]
for c in farm_cells:
    tot += 2 * near(*c); wsum += 2
wood = [(46 + 4 * i + 2, 37 + 4 * j + 2) for j in range(4) for i in range(4) if not (i in (1, 2) and j in (1, 2))] + [(66, 39), (70, 39), (74, 39)]
for c in wood:
    tot += 2 * near(*c); wsum += 2
for k in range(7):
    x, y = mines[k]
    tot += 2 * near(x + 2.5, y + 2.5); wsum += 2
for c in ((31, 9), (34, 9)):
    tot += 2 * near(*c); wsum += 2
avg = tot / wsum
print('walking avg', round(avg, 2), 'reserve', reserve)

# ---------------- page ----------------
order = sorted(svg, key=lambda t: t[1])
body = '\n'.join(f'<g class="ph{p}">{m}</g>' if p != 14 else m for p, _, m in order)
shop_list = {}
for (i, ph), n in used.items():
    shop_list.setdefault(i, [0, 99]); shop_list[i][0] += n; shop_list[i][1] = min(shop_list[i][1], ph)
buy = []
for i, (n, ph) in sorted(shop_list.items(), key=lambda kv: (kv[1][1], -JP[kv[0]]['cf'] * kv[1][0])):
    j = JP[i]
    pr = int(''.join(c for c in (j['price'] or '0').split(' ')[0] if c.isdigit()) or 0)
    over = n > (j['max'] or 999)
    buy.append({'id': i, 'fr': j['fr'], 'n': n, 'ph': ph, 'cf': j['cf'], 'pr': pr, 'fp': j['fp'], 'ic': ic_jp(i), 'max': j['max'], 'load': j['load']})
    if over:
        print('OVER CAP', j['fr'], n, j['max'])
defs = ''.join(f'<symbol id="i-{k.replace(" ", "_")}" viewBox="0 0 1 1"><image href="{v}" width="1" height="1" preserveAspectRatio="xMidYMid meet"/></symbol>' for k, v in ICON.items())
body = body.replace('href="#i-', 'href="#i-').replace(' ', ' ')
for k in ICON:
    if ' ' in k:
        body = body.replace(f'#i-{k}"', f'#i-{k.replace(" ", "_")}"')
data = {'types': TYPES, 'avg': round(avg, 2), 'avgPlan': 4.66, 'reserve': [FR.get(r, r) for r in reserve], 'buy': buy}
tpl = open(os.path.join(S, 'concept_template.html')).read()
html = tpl.replace('/*DEFS*/', defs).replace('/*PLAN*/', body).replace('/*DATA*/', json.dumps(data, ensure_ascii=False))
open('/home/user/ClaudeHome/jardin-foyer-concept.html', 'w').write(html)
print('size', len(html), 'buy', [(b['fr'], b['n']) for b in buy])
