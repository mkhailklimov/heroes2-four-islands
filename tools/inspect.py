import sys
from mp2read import read, ICN, OBJ
m=read(sys.argv[1]); W=m['w']
def parts(i):
    t=m['tiles'][i]; ps=[]
    def add(on,idx,uid,lvl,q=None):
        if on>>2: ps.append((lvl,ICN.get(on>>2),on&3,idx,uid,q))
    add(t['on1'],t['bi1'],t['uid1'],'G',t['q1']&3); add(t['on2'],t['ti2'],t['uid2'],'T')
    a=t['next']
    while a:
        ad=m['addons'][a]; add(ad['on1']<<1,ad['bi1'],ad['uid1'],'g',ad['q']&3); add(ad['on2'],ad['ti2'],ad['uid2'],'t'); a=ad['next']
    return t,ps
x0,y0,x1,y1=map(int,sys.argv[2:6])
for y in range(y0,y1+1):
    for x in range(x0,x1+1):
        t,ps=parts(y*W+x)
        md=((t['q2']<<8)+t['q1'])>>3
        print((x,y),'terr',t['terr'],'fl',t['tflags'],OBJ.get(t['otype']),'md',md,'q1',t['q1'],ps)
