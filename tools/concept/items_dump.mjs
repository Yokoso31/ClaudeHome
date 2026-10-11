import fs from 'fs';
const M = await import('./aniimax-mirror/pkg/aniimax.js');
const buf = fs.readFileSync('./aniimax-mirror/pkg/aniimax_bg.wasm');
if (M.initSync) M.initSync({module: buf}); else await M.default({module_or_path: buf});
const s = M.get_all_items();
fs.writeFileSync('all_items.json', typeof s === 'string' ? s : JSON.stringify(s));
console.log(String(typeof s === 'string' ? s : JSON.stringify(s)).slice(0, 1500));
