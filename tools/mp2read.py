import struct, json, sys, collections
E=json.load(open(__file__.rsplit('/',1)[0]+'/mp2_enums.json'))
ICN={v:k for k,v in E['icn'].items()}; OBJ={v:k for k,v in E['obj'].items()}
def read(path):
    b=open(path,'rb').read()
    hdr=b[:428]
    w,h=struct.unpack_from('<II',b,420)
    p=428; tiles=[]
    for i in range(w*h):
        t=struct.unpack_from('<HBBBBBBBBHII',b,p); p+=20
        tiles.append(dict(zip(['terr','on1','bi1','q1','q2','on2','ti2','tflags','otype','next','uid1','uid2'],t)))
    n=struct.unpack_from('<I',b,p)[0]; p+=4
    addons=[]
    for i in range(n):
        a=struct.unpack_from('<HBBBBBII',b,p); p+=15
        addons.append(dict(zip(['next','on1','bi1','q','on2','ti2','uid1','uid2'],a)))
    castles=[]
    for i in range(72):
        x,y,t=b[p],b[p+1],b[p+2]; p+=3
        if (x,y)!=(255,255): castles.append((x,y,t))
    caps=[]
    for i in range(144):
        x,y,t=b[p],b[p+1],b[p+2]; p+=3
        if (x,y)!=(255,255): caps.append((x,y,t))
    obel=b[p]; p+=1
    cntpos=p; cnt=None
    while True:
        l,hh=b[p],b[p+1]; p+=2
        if l==0 and hh==0: break
        cnt=256*hh+l-1
    blocks=[]
    for i in range(cnt or 0):
        sz=struct.unpack_from('<H',b,p)[0]; p+=2
        blocks.append(b[p:p+sz]); p+=sz
    tail=b[p:]
    return dict(b=b,hdr=hdr,w=w,h=h,tiles=tiles,addons=addons,castles=castles,caps=caps,obel=obel,cntbytes=b[cntpos:cntpos+(p-cntpos)][:8],blocks=blocks,tail=tail)
if __name__=='__main__':
    m=read(sys.argv[1])
    print('size',m['w'],m['h'],'addons',len(m['addons']),'castles',m['castles'],'caps',m['caps'],'obel',m['obel'])
    print('blocks',[len(x) for x in m['blocks']],'tail',m['tail'].hex())
    c=collections.Counter(OBJ.get(t['otype'],t['otype']) for t in m['tiles'])
    print(c.most_common(60))
    print('hdr',m['hdr'][:58].hex())
