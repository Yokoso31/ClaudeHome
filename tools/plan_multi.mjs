// Lays a homeland out around several Storage Units with walkways, then powers it and finds room for decor.
// Usage: node plan_multi.mjs <rv> [stores=5] [gap=1] [gens=2] [poles=12]
import fs from 'fs';
import path from 'path';
import { layOut } from './layout_multi.mjs';

const dir = path.dirname(new URL(import.meta.url).pathname);
const root = path.join(dir, '..');
const lvl = process.argv[2];
const K = +(process.argv[3] || 5);
const GAP = +(process.argv[4] || 1);
const GENS = +(process.argv[5] || 2);
const POLES = +(process.argv[6] || 12);
const HUBN = +(process.argv[7] || 0);
const GAPE = +(process.argv[8] || GAP);
const PREVFILE = process.env.PREV || null;
const MOVEC = +(process.env.MOVEC || 60);
const prevL = PREVFILE ? JSON.parse(fs.readFileSync(PREVFILE)) : null;

const PFX = process.env.PREFIX || '';
const inp = JSON.parse(fs.readFileSync(path.join(root, `${PFX}lay_in_rv${lvl}.json`)));
const cells = inp.cells;
const pieces = inp.pieces;
const ref = JSON.parse(fs.readFileSync(path.join(root, PFX ? `${PFX}data_rv${lvl}.json` : (fs.existsSync(path.join(root, `ax2_data_rv${lvl}.json`)) ? `ax2_data_rv${lvl}.json` : `ax_data_rv${lvl}.json`))));

const EMODE = new Set(['Aniipod Maker', 'Blazing Stove', 'Bouncy Brew Keg', 'Carousel Mill', 'Chimney Kiln', 'Claw Game Cooker', 'Crafting Table', 'Dance Pad Polisher', 'Joy Wheel Loom', 'Jukebox Dryer', 'Mine', 'Phonolfactory Table', 'Pickling Jar', 'Simmering Pot', 'Well', 'Woodworking Bench']);
const ov = (a, b) => { const w = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x); const h = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y); return w > 1e-6 && h > 1e-6 ? w * h : 0; };
const insideCells = r => cells.reduce((s, c) => s + ov(r, c), 0) >= r.w * r.h - 1e-6;
const center = m => ({ x: m.x + m.w / 2, y: m.y + m.h / 2 });

// ---------- stores: weighted k-means seeded from the single-store reference layout ----------
const pts = ref.pieces.filter(p => p.kind === 'piece' && p.name !== 'Storage Unit').map(p => {
  const m = /([\d.]+) trips/.exec(p.stats || ''); return { x: p.x + p.w / 2, y: p.y + p.h / 2, w: m ? +m[1] : 0 };
}).filter(p => p.w > 0);
const su = ref.pieces.find(p => p.name === 'Storage Unit');
let stores = [{ x: su.x + su.w / 2, y: su.y + su.h / 2 }];
while (stores.length < K) {
  let best = null, bd = -1;
  for (const p of pts) { const d = Math.min(...stores.map(s => Math.hypot(p.x - s.x, p.y - s.y))); const sc = p.w * d * d; if (sc > bd) { bd = sc; best = p; } }
  stores.push({ x: best.x, y: best.y });
}
for (let it = 0; it < 10; it++) {
  const acc = stores.map(() => ({ x: 0, y: 0, w: 0 }));
  pts.forEach(p => { let k = 0, bd = Infinity; stores.forEach((s, j) => { const d = Math.hypot(p.x - s.x, p.y - s.y); if (d < bd) { bd = d; k = j; } }); acc[k].x += p.x * p.w; acc[k].y += p.y * p.w; acc[k].w += p.w; });
  stores = stores.map((s, j) => (acc[j].w ? { x: acc[j].x / acc[j].w, y: acc[j].y / acc[j].w } : s));
}

function fixStores(list) {
  const out = [];
  for (const s of list) {
    let best = null;
    for (let r = 0; r < 12 && !best; r++) {
      for (let dx = -r; dx <= r && !best; dx++) for (let dy = -r; dy <= r && !best; dy++) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) !== r) continue;
        const c = { x: Math.round(s.x) + dx, y: Math.round(s.y) + dy };
        const rect = { x: c.x - 1, y: c.y - 1, w: 2, h: 2 };
        if (!insideCells(rect)) continue;
        if (out.some(o => Math.abs(o.x - c.x) < 2 + 2 * GAP + 4 && Math.abs(o.y - c.y) < 2 + 2 * GAP + 4)) continue;
        best = c;
      }
    }
    if (best) out.push(best);
  }
  return out;
}

function evaluate(out) {
  let cost = 0, w = 0;
  const near = s => { let k = 0, bd = Infinity; stores.forEach((t, j) => { const d = Math.hypot(s.x - t.x, s.y - t.y); if (d < bd) { bd = d; k = j; } }); return [k, bd]; };
  out.pieces.forEach(p => p.members.forEach(m => { if (!m.weight) return; const [, d] = near(center(m)); cost += m.weight * d; w += m.weight; }));
  return { cost, w, avg: w ? cost / w : 0 };
}

let best = null;
let hubIdx = null;
if (prevL) {
  stores = prevL.stores.map(r => ({ x: r.x + r.w / 2, y: r.y + r.h / 2 }));
  hubIdx = prevL.hubIdx || null;
  const prevMap = {};
  prevL.items.filter(i => i.kind === 'piece').forEach(i => { const k = i.n + '|' + i.w + 'x' + i.h; (prevMap[k] = prevMap[k] || []).push({ x: i.x + i.w / 2, y: i.y + i.h / 2 }); });
  const prevEnv = prevL.items.filter(i => i.kind === 'env').map(i => ({ x: i.x + i.w / 2, y: i.y + i.h / 2 }));
  const hubs = hubIdx ? hubIdx.map(k => stores[k]).filter(Boolean) : null;
  const pool = prevL.items.filter(i => i.kind === 'piece' || (i.kind === 'env' && i.group == null)).map(i => ({ ...i, used: false }));
  const pins = {};
  pieces.map((p, i) => ({ p, i })).filter(o => !o.p.cluster).sort((a, b) => (b.p.members[0].weight || 0) - (a.p.members[0].weight || 0)).forEach(({ p, i }) => {
    const m = p.members[0];
    const fit = q => !q.used && q.n === m.facility && ((q.w === m.w && q.h === m.h) || (q.w === m.h && q.h === m.w));
    const q = pool.find(q => fit(q) && (q.item || '') === (m.item || m.crop || '')) || pool.find(fit);
    if (q) { q.used = true; pins[i] = { x: q.x, y: q.y, w: q.w, h: q.h }; }
  });
  const out0 = layOut(pieces, { cells, storages: stores, gap: GAP, passes: 4, hubs, hubSet: [...EMODE], gapE: GAPE, prev: prevMap, prevEnv, moveCost: MOVEC, pins });
  best = { out: out0, ev: evaluate(out0), stores: stores.map(s => ({ ...s })) };
}
for (let iter = 0; !prevL && iter < (HUBN ? 7 : 5); iter++) {
  stores = fixStores(stores);
  const t0 = Date.now();
  const hubs = HUBN && hubIdx ? hubIdx.map(k => stores[k]).filter(Boolean) : null;
  const out = layOut(pieces, { cells, storages: stores, gap: GAP, passes: 4, hubs, hubSet: [...EMODE], gapE: GAPE });
  if (HUBN && !hubIdx) {
    const ew = stores.map(() => 0);
    out.pieces.forEach(p => p.members.forEach(m => { if (!m.weight || !EMODE.has(m.facility)) return; const c = center(m); let k = 0, bd = Infinity; stores.forEach((s, j) => { const d = Math.hypot(c.x - s.x, c.y - s.y); if (d < bd) { bd = d; k = j; } }); ew[k] += m.weight + 50; }));
    hubIdx = ew.map((w, k) => [w, k]).sort((a, b) => b[0] - a[0]).slice(0, HUBN).map(x => x[1]);
    console.error('hubs', hubIdx);
  }
  const ev = evaluate(out);
  console.error(`iter ${iter}: stores ${stores.length} unplaced ${out.unplaced.length} avg ${ev.avg.toFixed(2)} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  if (HUBN && iter === 0) { stores = stores; continue; }
  if (!best || out.unplaced.length < best.out.unplaced.length || (out.unplaced.length === best.out.unplaced.length && ev.cost < best.ev.cost)) best = { out, ev, stores: stores.map(s => ({ ...s })) };
  // move each store to the weighted center of what it serves
  const acc = stores.map(() => ({ x: 0, y: 0, w: 0 }));
  out.pieces.forEach(p => p.members.forEach(m => { if (!m.weight) return; const c = center(m); let k = 0, bd = Infinity; stores.forEach((s, j) => { const d = Math.hypot(c.x - s.x, c.y - s.y); if (d < bd) { bd = d; k = j; } }); acc[k].x += c.x * m.weight; acc[k].y += c.y * m.weight; acc[k].w += m.weight; }));
  const next = stores.map((s, j) => (acc[j].w ? { x: acc[j].x / acc[j].w, y: acc[j].y / acc[j].w } : s));
  if (next.every((s, j) => Math.hypot(s.x - stores[j].x, s.y - stores[j].y) < 0.6)) break;
  stores = next;
}
stores = best.stores;
const out = best.out;

// ---------- flatten ----------
const items = [];
const squares = [];
out.pieces.forEach((p, i) => {
  if (p.cluster) {
    p.members.forEach((m, j) => {
      if (m.building) {
        items.push({ kind: 'env', n: m.facility, mode: m.mode, x: m.x, y: m.y, w: m.w, h: m.h, group: i });
        squares.push({ x: m.x + m.w / 2 - 4.5, y: m.y + m.h / 2 - 4.5, w: 9, h: 9, n: m.facility, mode: m.mode, group: i });
      } else items.push({ kind: 'piece', n: m.facility, item: m.crop || m.item || '', x: m.x, y: m.y, w: m.w, h: m.h, weight: m.weight || 0, group: i });
    });
  } else p.members.forEach(m => items.push({ kind: m.facility === 'Sunlamp' || m.facility === 'Heat Furnace' || m.facility === 'Cooling Unit' ? 'env' : 'piece', n: m.facility, item: m.item || m.crop || '', mode: m.mode, x: m.x, y: m.y, w: m.w, h: m.h, weight: m.weight || 0, idle: !m.weight }));
});
items.forEach(it => {
  if (it.kind !== 'piece') return;
  const c = center(it); let k = 0, bd = Infinity; stores.forEach((s, j) => { const d = Math.hypot(c.x - s.x, c.y - s.y); if (d < bd) { bd = d; k = j; } });
  it.store = k; it.dist = +bd.toFixed(2);
});
const storeRects = stores.map(s => ({ x: s.x - 1, y: s.y - 1, w: 2, h: 2 }));

// ---------- power ----------
const occupied = [...items.map(i => ({ x: i.x, y: i.y, w: i.w, h: i.h })), ...storeRects];
const freeRect = r => insideCells(r) && !occupied.some(o => ov(r, o));
const targets = items.filter(i => i.kind === 'piece' && EMODE.has(i.n));
const area = (p, size) => ({ x: p.x + p.w / 2 - size / 2, y: p.y + p.h / 2 - size / 2, w: size, h: size });
const gens = [], poles = [], areas = [];
const powered = new Set();
const val = t => (t.weight > 0 ? 100 + t.weight : 1); // active machines first
const gain = a => targets.reduce((s, t, k) => s + (!powered.has(k) && ov(a, t) > 0 ? val(t) : 0), 0);
const mark = a => targets.forEach((t, k) => { if (ov(a, t) > 0) powered.add(k); });
const cand = (size, step) => { const out = []; for (let x = 0; x <= 80 - size; x += step) for (let y = 0; y <= 60 - size; y += step) out.push({ x, y, w: size, h: size }); return out; };
const genCand = cand(1, 1).filter(freeRect), poleCandAll = cand(1.5, 0.5).filter(freeRect);
// generators: best pair among the strongest single spots
const singles = genCand.map(c => ({ c, v: gain(area(c, 11)) })).filter(o => o.v > 0).sort((a, b) => b.v - a.v).slice(0, 80);
const covers = o => new Set(targets.map((t, k) => (ov(area(o.c, 11), t) > 0 ? k : -1)).filter(k => k >= 0));
let pair = null, pv = -1;
const sets = singles.map(covers);
for (let i = 0; i < singles.length; i++) for (let j = GENS > 1 ? i + 1 : i; j < (GENS > 1 ? singles.length : i + 1); j++) {
  if (GENS > 1 && ov(singles[i].c, singles[j].c) > 0) continue;
  const u = new Set([...sets[i], ...(GENS > 1 ? sets[j] : [])]);
  const v = [...u].reduce((s2, k) => s2 + val(targets[k]), 0);
  if (v > pv) { pv = v; pair = GENS > 1 ? [singles[i].c, singles[j].c] : [singles[i].c]; }
}
if (prevL && !process.env.POWER_FRESH && prevL.gens.every(freeRect)) pair = prevL.gens.map(g => ({ x: g.x, y: g.y, w: g.w, h: g.h }));
(pair || []).forEach(g => { gens.push(g); occupied.push(g); const a = area(g, 11); areas.push({ ...a, src: 'gen' }); mark(a); });
if (prevL && !process.env.POWER_FRESH) {
  let added = true;
  const pending = prevL.poles.map(p => ({ x: p.x, y: p.y, w: p.w, h: p.h }));
  while (added) { added = false;
    for (let k = 0; k < pending.length; k++) { const c = pending[k]; if (!c || !freeRect(c)) continue; const pa = area(c, 7);
      if (!areas.some(a => ov(pa, a) > 0)) continue;
      poles.push(c); occupied.push(c); areas.push({ ...pa, src: 'pole' }); mark(pa); pending[k] = null; added = true; } }
}
const connected = pa => areas.some(a => ov(pa, a) > 0);
const distTo = (a, t) => { const dx = Math.max(0, t.x - (a.x + a.w), a.x - (t.x + t.w)); const dy = Math.max(0, t.y - (a.y + a.h), a.y - (t.y + t.h)); return Math.hypot(dx, dy); };
const activeGain = pa => targets.reduce((s2, t, k) => s2 + (!powered.has(k) && t.weight > 0 && ov(pa, t) > 0 ? 100 + t.weight : 0), 0);
for (let p = poles.length; p < POLES; p++) {
  const left = targets.filter((t, k) => !powered.has(k) && t.weight > 0);
  const cands = poleCandAll.filter(c => freeRect(c) && connected(area(c, 7)));
  if (!cands.length) break;
  let pick = null;
  if (left.length) {
    let bv = 0;
    for (const c of cands) { const v = activeGain(area(c, 7)) + gain(area(c, 7)) * 1e-3; if (v > bv) { bv = v; pick = c; } }
    if (bv < 100) {
      pick = null;
      const cur = Math.min(...left.map(t => Math.min(...areas.map(a => distTo(a, t)))));
      let bd = cur - 0.25;
      for (const c of cands) { const d = Math.min(...left.map(t => distTo(area(c, 7), t))); if (d < bd) { bd = d; pick = c; } }
    }
  } else {
    let bv = 0;
    for (const c of cands) { const v = gain(area(c, 7)); if (v > bv) { bv = v; pick = c; } }
  }
  if (!pick) break;
  poles.push(pick); occupied.push(pick); const a = area(pick, 7); areas.push({ ...a, src: 'pole' }); mark(a);
}
const unpowered = targets.filter((t, k) => !powered.has(k)).map(t => ({ n: t.n, idle: !t.weight }));

// ---------- room for decor ----------
const W = 80, H = 60, open = new Uint8Array(W * H), occ = new Uint8Array(W * H);
cells.forEach(c => { for (let y = c.y; y < c.y + c.h; y++) for (let x = c.x; x < c.x + c.w; x++) open[y * W + x] = 1; });
occupied.forEach(r => { for (let y = Math.floor(r.y); y < Math.ceil(r.y + r.h - 1e-6); y++) for (let x = Math.floor(r.x); x < Math.ceil(r.x + r.w - 1e-6); x++) if (x >= 0 && y >= 0 && x < W && y < H) occ[y * W + x] = 1; });
const freeT = (x, y) => x >= 0 && y >= 0 && x < W && y < H && open[y * W + x] && !occ[y * W + x];
// production footprint: bounding box of the working pieces, grown by 2
let bx0 = 1e9, by0 = 1e9, bx1 = -1e9, by1 = -1e9;
items.concat(storeRects.map(r => ({ ...r }))).forEach(r => { bx0 = Math.min(bx0, r.x); by0 = Math.min(by0, r.y); bx1 = Math.max(bx1, r.x + r.w); by1 = Math.max(by1, r.y + r.h); });
// walkways: free tiles touching a piece
const walk = [];
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
  if (!freeT(x, y)) continue;
  let near = false;
  for (let dy = -1; dy <= 1 && !near; dy++) for (let dx = -1; dx <= 1 && !near; dx++) { const xx = x + dx, yy = y + dy; if (xx >= 0 && yy >= 0 && xx < W && yy < H && occ[yy * W + xx]) near = true; }
  if (near) walk.push([x, y]);
}
const walkSet = new Set(walk.map(([x, y]) => y * W + x));
// plazas: largest empty rectangles (not on walkways) within the production footprint, greedily
const used = new Uint8Array(W * H);
const zoneFree = (x, y) => freeT(x, y) && !walkSet.has(y * W + x) && !used[y * W + x];
function largestRect(x0, y0, x1, y1) {
  let best = null; const hgt = new Array(W).fill(0);
  for (let y = y0; y < y1; y++) {
    for (let x = x0; x < x1; x++) hgt[x] = zoneFree(x, y) ? hgt[x] + 1 : 0;
    const st = [];
    for (let x = x0; x <= x1; x++) {
      const h = x < x1 ? hgt[x] : 0; let start = x;
      while (st.length && st[st.length - 1][1] >= h) { const [sx, sh] = st.pop(); const w = x - sx; const area = w * sh; if (sh >= 3 && w >= 3 && (!best || area > best.area)) best = { x: sx, y: y - sh + 1, w, h: sh, area }; start = sx; }
      st.push([start, h]);
    }
  }
  return best;
}
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const fx0 = clamp(Math.floor(bx0) - 4, 0, W), fy0 = clamp(Math.floor(by0) - 4, 0, H), fx1 = clamp(Math.ceil(bx1) + 4, 0, W), fy1 = clamp(Math.ceil(by1) + 4, 0, H);
const plazas = [];
for (let k = 0; k < 6; k++) {
  const r = largestRect(fx0, fy0, fx1, fy1);
  if (!r || r.area < 12) break;
  plazas.push(r);
  for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) used[y * W + x] = 1;
}
let freeCount = 0; for (let i = 0; i < W * H; i++) if (open[i] && !occ[i]) freeCount++;

// ---------- what changes since the previous level ----------
let diff = null;
if (prevL) {
  const same = (a, b) => Math.abs(a.x - b.x) < 0.05 && Math.abs(a.y - b.y) < 0.05 && a.n === b.n && ((a.w === b.w && a.h === b.h) || (a.w === b.h && a.h === b.w));
  const prevItems = prevL.items.map(i => ({ ...i, used: false }));
  const cnt = {}; prevL.items.forEach(i => { cnt[i.n] = (cnt[i.n] || 0) + 1; });
  const now = {}; items.forEach(i => { now[i.n] = (now[i.n] || 0) + 1; });
  items.forEach(it => {
    const m = prevItems.find(p => !p.used && same(p, it));
    if (m) { m.used = true; it.st0 = (it.kind === 'env' ? (m.mode !== it.mode ? 'reglage' : 'ok') : ((m.item || '') !== (it.item || '') ? 'replant' : 'ok')); it.was = m.item || m.mode || ''; }
    else if (it.kind === 'env') {
      const m2 = prevItems.find(p => !p.used && p.kind === 'env' && Math.abs(p.x + p.w / 2 - it.x - it.w / 2) < 0.05 && Math.abs(p.y + p.h / 2 - it.y - it.h / 2) < 0.05);
      if (m2) { m2.used = true; it.st0 = 'remplace'; it.was = m2.n; } else it.st0 = 'move';
    } else it.st0 = 'move';
  });
  // among the off-spot pieces of a type, the extra count is new, the rest moved
  const extra = {}; Object.keys(now).forEach(n => { extra[n] = Math.max(0, now[n] - (cnt[n] || 0)); });
  items.filter(i => i.st0 === 'move').sort((a, b) => (b.weight || 0) - (a.weight || 0)).forEach(i => { if (extra[i.n] > 0) { i.st0 = 'new'; extra[i.n]--; } });
  const sum = {}; items.forEach(i => { sum[i.st0] = (sum[i.st0] || 0) + 1; });
  const keptP = poles.filter(p => prevL.poles.some(q => Math.abs(q.x - p.x) < 0.05 && Math.abs(q.y - p.y) < 0.05)).length;
  diff = { sum, polesKept: keptP, polesNew: poles.length - keptP, removed: prevItems.filter(p => !p.used && p.kind === 'piece' && !(now[p.n] >= (cnt[p.n] || 0))).length };
}
const refAvg = (() => { const m = /([\d.]+) tiles each/.exec(ref.summary || ''); return m ? +m[1] : null; })();
const res = {
  lvl: +lvl, K: stores.length, gap: GAP, gapE: GAPE, hubs: HUBN, hubIdx, diff, evolved: !!prevL,
  stores: storeRects, items, squares, gens, poles, areas, unpowered, powered: powered.size, targets: targets.length,
  walk, plazas, freeCount, plots: ref.plots,
  metrics: { weight: best.ev.w, avg: +best.ev.avg.toFixed(2), refAvg, unplaced: out.unplaced.map(i => pieces[i].cluster ? 'cluster' : pieces[i].members[0].facility) },
};
fs.writeFileSync(path.join(root, prevL ? `${PFX}evo_rv${lvl}${process.env.POWER_FRESH ? '_pf' : ''}.json` : `${PFX}multi_rv${lvl}_k${K}_g${GAP}_h${HUBN}_e${GAPE}.json`), JSON.stringify(res));
console.log(JSON.stringify({ diff: diff && diff.sum, lvl, stores: stores.length, avg: res.metrics.avg, refAvg, unplaced: res.metrics.unplaced, powered: `${powered.size}/${targets.length}`, activeUnpowered: unpowered.filter(u=>!u.idle).length, gens: gens.length, poles: poles.length, plazas: plazas.map(p => p.w + 'x' + p.h), free: freeCount }));
