"""Evolve the player's homeland level by level, trying a few ways per level and keeping the best:
the climate blocks on the player's spots (pinned firmly or not) or left to the planner.
Each try is scored: nothing unplaced, every crop in its climate, then fewest steps, then walking."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evo_steps import pair, order_steps, climate

S = os.path.dirname(os.path.abspath(__file__))
prev = sys.argv[1] if len(sys.argv) > 1 else 'cur3_h60.json'
levels = [int(a) for a in sys.argv[2:]] or [15, 16, 17, 18, 19, 20]
TRIES = [('fit', {}), ('fit-firm', {'PINFREEZE': '1'}), ('engine', {'NOFIT': '1'})]
report = {}
for L in levels:
    P = json.load(open(os.path.join(S, prev)))
    lay = json.load(open(os.path.join(S, f'ev_lay_in_rv{L}.json')))
    best = None
    for name, env in TRIES:
        e = dict(os.environ, **env)
        tag = f'ev3_{name}'
        subprocess.run(['python3', '-I', 'field_plan.py', str(L), prev, f'ev_lay_in_rv{L}.json', f'{tag}_lay_in_rv{L}.json', f'pins_{name}_rv{L}.json'], cwd=S, env=e, check=True, capture_output=True)
        subprocess.run(['cp', f'ev_data_rv{L}.json', f'{tag}_data_rv{L}.json'], cwd=S, check=True)
        r = subprocess.run(['node', 'plan_multi.mjs', str(L), '5', '1', '2', '12', '4', '1.5'], cwd=os.path.join(S, 'multi'),
                           env=dict(e, PREFIX=f'{tag}_', PREV=f'../pins_{name}_rv{L}.json', NOSTEAL='1', MOVEC='150', OUT=f'try_{name}_rv{L}.json'), capture_output=True, text=True, timeout=1200)
        out = json.load(open(os.path.join(S, f'try_{name}_rv{L}.json')))
        steps = order_steps(pair(P, out), P, out)
        probs = climate(out, lay)[0]
        miss = sum(p['want'] - p['have'] for p in probs)
        n = sum(1 for s in steps if s['t'] in ('move', 'new', 'store', 'stash', 'remplace'))
        key = (len(out['metrics']['unplaced']), miss, n, out['metrics']['avg'])
        print(L, name, 'unplaced', key[0], 'climate miss', miss, 'steps', n, 'avg', key[3], 'powered', out['powered'], '/', out['targets'], flush=True)
        if best is None or key < best[0]:
            best = (key, name, out, steps)
    key, name, out, steps = best
    json.dump(out, open(os.path.join(S, f'ev3_rv{L}.json'), 'w'))
    report[L] = {'pick': name, 'unplaced': key[0], 'miss': key[1], 'steps': key[2], 'avg': key[3]}
    print(L, '=> keep', name, report[L], flush=True)
    prev = f'ev3_rv{L}.json'
json.dump(report, open(os.path.join(S, 'chain_report.json'), 'w'))
