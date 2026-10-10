#!/bin/bash
# Lay out the roster-based plans: optimal per level (3 hub settings) then the evolving chain, then decor.
S=/tmp/claude-0/-home-user-ClaudeHome/dad66101-28c5-5c34-ae52-cc7280e1b77f/scratchpad; cd $S
export PREFIX=my_
for l in 14 15 16 17 18 19 20; do for h in 2 3 4; do timeout 900 node multi/plan_multi.mjs $l 5 1 2 12 $h 1.5 2>/dev/null | cut -c1-200; done; done
# base for the chain: best RV14 opt variant
B=$(python3 -c "
import json,glob
c=[]
for f in glob.glob('my_multi_rv14_k5_g1_h*_e1.5.json'):
    d=json.load(open(f)); c.append((sum(1 for u in d['unpowered'] if not u['idle']), d['metrics']['avg'], f))
print(sorted(c)[0][2])")
H=$(echo $B | sed 's/.*_h\([0-9]\)_.*/\1/')
echo "base $B hubs $H"
for l in 15 16 17 18 19 20; do p=$((l-1)); prev=$S/my_evo_rv$p.json; [ $l = 15 ] && prev=$S/$B
  a=$(PREV=$prev MOVEC=150 timeout 1500 node multi/plan_multi.mjs $l 5 1 2 12 $H 1.5 2>/dev/null)
  b=$(POWER_FRESH=1 PREV=$prev MOVEC=150 timeout 1500 node multi/plan_multi.mjs $l 5 1 2 12 $H 1.5 2>/dev/null)
  python3 - "$a" "$b" $l <<'PY'
import sys,json,shutil
a=json.loads(sys.argv[1]); b=json.loads(sys.argv[2]); l=sys.argv[3]
pick='b' if b['activeUnpowered']<a['activeUnpowered'] else 'a'
if pick=='b': shutil.copy(f'my_evo_rv{l}_pf.json', f'my_evo_rv{l}.json')
d=a if pick=='a' else b
print('evo',l,'avg',d['avg'],'power',d['powered'],'actifs non alim',d['activeUnpowered'],'diff',d['diff'])
PY
done
BASE14=$S/$B python3 multi/compose.py | tail -14
