import numpy as np, json, sys
from PIL import Image
from scipy import ndimage as nd
I='/tmp/claude-0/-home-user-ClaudeHome/dad66101-28c5-5c34-ae52-cc7280e1b77f/images/'
res={}
for f in ['11','12','13','14','15','16']:
    a=np.asarray(Image.open(I+f+'.webp').convert('RGB')).astype(int)
    m=(a.min(2)>205)&((a.max(2)-a.min(2))<45)
    m=nd.binary_opening(m,iterations=2)
    m=nd.binary_fill_holes(m)
    lab,n=nd.label(m)
    out=[]
    for k,sl in enumerate(nd.find_objects(lab)):
        h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start
        if w>45 and h>45 and w<420 and h<420:
            out.append((sl[1].start,sl[0].start,w,h))
    res[f]=out
    print(f,len(out))
    for o in sorted(out,key=lambda o:(o[1]//30,o[0])): print('  ',o)
json.dump(res,open('cards.json','w'))
