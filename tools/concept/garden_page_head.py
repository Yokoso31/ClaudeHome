"""The Japanese-garden homeland, level by level (RV14-20): the garden drawn once, production per level.

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


def shrink(raw, px=96, q=75):
    """Re-encode an embedded image small: the page shows icons at 30-60 px, so 64-96 px is plenty."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(raw)).convert('RGBA')
    im.thumbnail((px, px))
    out = io.BytesIO()
    im.save(out, 'WEBP', quality=q, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(out.getvalue()).decode()
def b64(path):
    return shrink(open(path, 'rb').read())


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
for (x, y, w, h) in ((26, 25.5, 8, 11.5), (46.5, 25.5, 8.5, 7.5), (0, 51, 28, 9), (56, 54, 24, 6)):
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
    T('jp40700003', j['fr'], 'Déco', ic_jp('40700003'), '2 × 2', f'Petit étang rond complet, avec son bord d\'herbe. 2 × 2 comme un champ, agrandissable jusqu\'à ×3 ; ici en taille de base · {j["price"]} · {j["cf"]} de confort')
    art = (shadow(cx, cy, 1) + f'<circle cx="{cx}" cy="{cy}" r="1.02" class="pond-rim"/><ellipse cx="{f(cx + .05)}" cy="{f(cy + .05)}" rx=".68" ry=".62" class="pond-w"/>'
           f'<circle cx="{f(cx - .1)}" cy="{f(cy - .05)}" r=".2" class="lily"/><circle cx="{f(cx + .3)}" cy="{f(cy + .25)}" r=".11" class="lily"/><circle cx="{f(cx - .35)}" cy="{f(cy + .2)}" r=".13" class="lily"/>'
           + blob(cx + .2, cy - .7, .26, 'pebble', 5, .3, int(x)) + blob(cx + .75, cy - .15, .16, 'pebble', 5, .3, int(y)) + blob(cx - .3, cy + .78, .14, 'pebble', 5, .3, 3)
           + f'<circle cx="{f(cx - .45)}" cy="{f(cy - .62)}" r=".14" class="whitef"/>')
    add(f'<g class="obj dc"{tag("jp40700003")}>{art}</g>', phase, 6)
pond(44, 52.2)            # the source of the dry stream
deco('40500003', 38.5, 50.5, rot=True, layer=7)
for x, y in ((23.9, 51.2), (43.8, 48.6), (30.6, 55.6)):
    deco('40300014', x, y)
deco('40700017', 46.6, 56.2); deco('40700016', 33.4, 51.2); deco('40700016', 35.6, 55.2)
num(31, 50.2, 2)

# ---------------- 3 · courtyard of the great tree ----------------
rect(34, 25, 12, 12, 'url(#gravel)', layer=2, rx=.6)
add('<circle cx="40" cy="31" r="5.3" class="ring"/><circle cx="40" cy="31" r="5.8" class="ring"/>', 14, 3)
T('bigtree', 'Grand arbre violet', 'Lieux', None, '8 × 8', 'Ton grand arbre actuel, déplacé au centre de la cour. De base il fait 5 × 5 comme le Lit de Cumulaine : avec « Taille », règle-le vers ×1,6 pour qu\'il remplisse la cour sans toucher les lampes ni les haies.')
add(f'<g class="obj bigtree"{tag("bigtree")}>' + shadow(40, 31, 4) +
    blob(40, 31, 4.3, 'wis', 12, .14, 3) + blob(38.6, 29.9, 2.3, 'wis-l', 8, .2, 4) + blob(41.8, 32.2, 2.2, 'wis-l', 8, .2, 5) + blob(40.6, 29.2, 1.4, 'wis-ll', 7, .2, 6) + '</g>', 14, 8)
for x, y in ((34.4, 25.4), (43.85, 25.4), (34.4, 35.1), (43.85, 35.1)):
    deco('40600065', x, y)
for x, y in ((39.5, 25.3), (39.5, 35.7), (34.3, 30.5), (44.7, 30.5)):
    deco('40700002', x, y)
num(46.4, 24.6, 3)

