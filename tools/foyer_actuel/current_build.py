"""Digitize the player's current homeland (RV14) from the 'Gestion du logis' screenshots."""
import json
T = {'11': (46.07, 1067, 20, 312, 45), '12': (48.5, 990, 20, 730, 30), '15': (46.1, 980, 60, 705, 30), '16': (46.3, 1035, 60, 438, 45)}
def snap(v): return round(v * 2) / 2
def card(img, px, py, n, w, h=None):
    s, PX, X0, PY, Y0 = T[img]; h = h or w
    return {'n': n, 'x': snap(X0 + (px + 2 - PX) / s), 'y': snap(Y0 + (py + 2 - PY) / s), 'w': w, 'h': h}
def cen(img, px, py, n, w, h=None):
    s, PX, X0, PY, Y0 = T[img]; h = h or w
    return {'n': n, 'x': snap(X0 + (px - PX) / s - w / 2), 'y': snap(Y0 + (py - PY) / s - h / 2), 'w': w, 'h': h}
it = []
c12 = [(772,51,'Aniipod Maker',4.5),(1015,51,'Dance Pad Polisher',2.5),(1149,51,'Joy Wheel Loom',4),(1356,51,'Carousel Mill',5.5),(1623,51,'Carousel Mill',5.5),
       (468,342,'Chimney Kiln',5.5),(736,391,'Joy Wheel Loom',4),(1210,415,'Phonolfactory Table',3.5),(1380,403,'Crafting Table',4),(1793,415,'Jukebox Dryer',2.5),
       (930,464,'Pickling Jar',2.5,2),(748,658,'Phonolfactory Table',3.5),(918,658,'Bouncy Brew Keg',3),(1063,670,'Crafting Table',4),(1501,682,'Bouncy Brew Keg',3),
       (1792,682,'Nimbus Bed',5),(1258,695,'Jukebox Dryer',2.5),(1391,719,'Dewy House',2),(1586,342,'Woodworking Bench',2,1.5),(1586,415,'Woodworking Bench',2,1.5),(1683,415,'Woodworking Bench',2,1.5)]
it += [card('12', *c) for c in c12]
stores = [card('12',1052,488,'Storage Unit',2), card('12',1647,537,'Storage Unit',2), card('15',788,487,'Storage Unit',2), card('16',1638,349,'Storage Unit',2), card('11',1553,441,'Storage Unit',2)]
gens = [cen('12',1110,340,'Crackle Generator',1)]
poles = [cen('12',x,y,'Crackle Power Pole',1.5) for x,y in [(1511,352),(1840,365),(867,620),(1390,645),(1706,680)]] + [cen('15',x,y,'Crackle Power Pole',1.5) for x,y in [(821,290),(256,347),(520,543)]]
it += [card('15',x,y,'Mine',5) for x,y in [(603,14),(937,26),(1306,14),(1675,26),(926,268),(1306,256),(1675,268)]]
it += [card('15',4,60,'Chimney Kiln',5.5), card('15',269,60,'Chimney Kiln',5.5), card('15',27,406,'Claw Game Cooker',3.5), card('15',211,406,'Claw Game Cooker',3.5),
       card('15',465,401,'Blazing Stove',2.5,1.75), cen('15',418,433,'Simmering Pot',1.5), cen('15',625,422,'Simmering Pot',1.5),
       card('15',926,510,'Tidewhisper Sandcastle',5), card('15',926,741,'Tidewhisper Sandcastle',5), card('15',637,649,'Starfall Hammock',5)]
it += [card('16',x,y,'Woodland',4) for x,y in [(1407,-21),(1407,164),(1592,164),(1777,164),(1407,441),(1592,441),(1777,441),(1407,626),(1777,626),(1407,812),(1592,812),(1777,812)]]
it += [card('15',x,752,'Woodland',4) for x in (1352,1537,1721)]
it += [card('16',x,y,'Well',2) for x,y in [(249,210),(527,210),(805,198)]]
it += [card('16',x,y,'Incubateur',2) for x in (539,643) for y in (499,592,684,777)]
it += [cen('16',1683,68,'Heat Furnace',1), cen('16',1683,717,'Heat Furnace',1), card('11',1830,441,'Cooling Unit',2)]
for x in (1645,1738,1830,1922):
    for y in (257,349,441,534,626):
        if (x, y) != (1830, 441): it.append(card('11',x,y,'Farmland',2))
it += [card('16',133,y,'Farmland',2) for y in (383,476,569,661,754)]
it += [card('11',x,833,'Farmland',2) for x in (1461,1553,1645,1738,1830,1922)]
ENV = {'Heat Furnace','Cooling Unit','Sunlamp'}
for i in it:
    i['kind'] = 'env' if i['n'] in ENV else 'piece'; i['item'] = ''
    if i['kind'] == 'env': i['group'] = None
def ov(a, b):
    w = min(a['x']+a['w'], b['x']+b['w']) - max(a['x'], b['x']); h = min(a['y']+a['h'], b['y']+b['h']) - max(a['y'], b['y'])
    return w > 1e-6 and h > 1e-6
allr = it + stores + gens + poles
bad = [(a['n'],a['x'],a['y'],b['n'],b['x'],b['y']) for k,a in enumerate(allr) for b in allr[k+1:] if ov(a,b)]
print('items', len(it), 'overlaps', len(bad)); [print(' ', b) for b in bad]
import collections; print(collections.Counter(i['n'] for i in it))
json.dump({'lvl': 14, 'items': it, 'stores': [{k: s[k] for k in 'xywh'} for s in stores], 'gens': [{k: g[k] for k in 'xywh'} for g in gens],
           'poles': [{k: p[k] for k in 'xywh'} for p in poles], 'hubIdx': None}, open('current_rv14.json', 'w'))
for i in sorted(allr, key=lambda i: (i['n'], i['y'], i['x'])): print(f"  {i['n']:24s} {i['x']:5} {i['y']:5} {i['w']}x{i['h']}")
