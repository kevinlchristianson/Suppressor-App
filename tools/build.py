# Rebuild index.html from data/: python3 tools/build.py
import csv,json,re,sys
import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U=os.path.join(ROOT,'data'); OUT=os.path.join(U,'data.json')
def norm(s): return re.sub(r'[^a-z0-9]','',(s or '').lower())
MF={'eccomachine':'ECCO','ecco':'ECCO','wraithmetalworks':'Wraith Metalworks','qllc':'Q','q':'Q',
    'huxwrx':'HUXWRX','surefire':'SureFire','knightsarmamentco':"Knight's Armament",'knightsarmament':"Knight's Armament",
    'thunderbeastarms':'TBAC','tbac':'TBAC'}
def mf(m): return MF.get(norm(m),m)
# prices: Kevin's list wins
pl={}
for r in csv.DictReader(open(f'{U}/price_list.csv')):
    b=r['basis']; b='user' if b.startswith('user') else b
    pl[(norm(mf(r['mfgr'])),norm(r['model']))]=(float(r['price']),b)
cat=json.load(open(f'{U}/catalog.json'))
cm={}
for c in cat:
    for k in {norm(c['model']), norm(c['model']+' '+(c.get('variant') or ''))}:
        cm.setdefault((norm(mf(c['manufacturer'])),k),c)
# over-the-barrel cans: length added past the muzzle (inches)
OTB={('Dead Air','Nomad Ti OTB'):(4.6,'Dead Air spec'),
     ('Unknown Suppressors','OG 30'):(4.0,'Unknown Suppressors spec (8 in can, 4 in over the barrel)'),
     ('B&T','TiRe-X with OTB'):(4.1,'estimate: reviews say "a little over 4 in"'),
     ('B&T','TiRe-X Compact with OTB'):(None,'not published')}
# Outdoor Life recoil test: inches of recoil-sled travel (lower = less recoil), one rifle for every can.
# Summit can -> (Outdoor Life row used, Outdoor Life base name for its other setups, note).
# Only setups that match how the Summit tested the can: plain, flat cap or the can's own brake for stock cans,
# an aftermarket brake only for Summit "with Brake"/"with Recoil X" entries. Matched by name, weight and length.
OL=[r for r in list(csv.reader(open(f'{U}/recoil_outdoorlife.csv')))[2:] if r and r[0]]
OLD={r[0]:r for r in OL}
RC={('Abel','Theorem'):('Abel Theorem','Abel Theorem',''),
    ('Abel','Theorem with Brake'):('Abel Theorem (Recoil X Brake)','Abel Theorem','Summit does not name the brake; Recoil X is the closest weight'),
    ('Abel','Theorem S'):('Abel Theorem S','Abel Theorem S',''),
    ('Abel','Theorem-S'):('Abel Theorem S','Abel Theorem S',''),
    ('Abel','Theorem S with Brake'):('Abel Theorem S (Recoil X Brake)','Abel Theorem S','Summit does not name the brake; Recoil X is the closest weight'),
    ('Abel','Theorem L'):('Able Theorem L','Able Theorem L',''),
    ('Abel','Theorem L with Brake'):('Able Theorem L (Able Brake)','Able Theorem L',''),
    ('BOSS','Top Shot'):('BOSS Top Shot (Factory Brake)','BOSS Top Shot',''),
    ('Banish','BANISH 30 V2 Long'):('Banish 30 V2','Banish 30 V2',''),
    ('Banish','BANISH BACKCOUNTRY'):('Banish Backcountry','Banish Backcountry',''),
    ('Fletcher Rifle Works','Texas Flood with Recoil X'):('Fletcher Texas Flood (Recoil X Gen 2 Brake)','Fletcher Texas Flood',''),
    ('PTR','Vent 1'):('PTR Vent 1','PTR Vent 1',''),
    ('SilencerCo','Scythe-Ti Stock Brake'):('Silencerco Scythe Ti','Silencerco Scythe Ti',''),
    ('TBAC','Magnus K RR CB'):('Thunder Beast Magnus K RR (Factory Brake)','Thunder Beast Magnus K RR',''),
    ('TBAC','Ultra 5 CB'):('Thunder Beast Ultra 5 Gen 2','Thunder Beast Ultra 5',''),
    ('TBAC','Ultra 7 CB'):('Thunder Beast Ultra 7 Gen 1','Thunder Beast Ultra 7','Outdoor Life tested the Gen 1'),
    ('TBAC','Ultra 9 CB'):('Thunder Beast Ultra 9 Gen 2','Thunder Beast Ultra 9',''),
    ('Unknown Suppressors','RPRS'):('Unknown Reaper','Unknown Reaper','assumes RPRS is the Reaper (same weight and length)')}
fl=lambda v: float(v) if v else None
def setup(n,base): t=n[len(base):].strip(' ()'); return t or 'as tested'
used=set()
rows=[];bare=[];fills=[];flags=[]
for y,f in [(2025,'summit2025_all.csv'),(2026,'summit2026_all.csv')]:
    for r in list(csv.reader(open(f'{U}/{f}')))[2:]:
        if len(r)<27: continue
        num=lambda i: float(r[i]) if r[i].strip() else None
        q=round((num(7)+num(13))/2,2); e=num(19)
        imp=round((num(9)+num(15))/2,2) if r[9].strip() and r[15].strip() else None  # Im-dB (cols: PkPr,dB,dB(A),Im-Pa,Im-dB,Pk Leq)
        if r[1]=='Bare':
            bare.append({'y':y,'h':r[4],'q':q,'e':e,'n':r[2]}); continue
        m=mf(r[1]); s=r[2].strip()
        d={'y':y,'h':r[4],'b':r[3],'m':m,'s':s,'q':q,'i':imp,'e':e,'w':num(24),'l':num(25),'d':num(26),'p':None,'pb':None}
        k=(norm(m),norm(s))
        if k in pl: d['p'],d['pb']=pl[k]
        c=cm.get(k)
        if c:
            if d['p'] is None and c.get('msrp_usd'):
                d['p'],d['pb']=c['msrp_usd'],'catalog'; fills.append((m,s,c['msrp_usd']))
            elif d['p'] and c.get('msrp_usd') and abs(d['p']-c['msrp_usd'])/c['msrp_usd']>0.25:
                flags.append((m,s,d['p'],c['msrp_usd']))
            if c.get('status')=='discontinued': d['dc']=1
            mounts=(c.get('proprietary_mounts') or '').lower()
        if (m,s) in OTB:
            d['otb']=1; d['a'],d['as']=OTB[(m,s)]
        if (m,s) in RC:
            n,base,note=RC[(m,s)];o=OLD[n];used.add(n)
            d['rc']=fl(o[1]);d['rcs']=setup(n,base);d['rcn']=note
            d['rco']=[[setup(x[0],base),fl(x[1])] for x in OL if x[0]!=n and (x[0]==base or x[0].startswith(base+' ('))]
        rows.append(d)
ol=[{'n':r[0],'rc':fl(r[1]),'sd':fl(r[2]),'w':fl(r[3]),'l':fl(r[4]),'u':1 if r[0] in used else 0} for r in OL]
json.dump({'rows':rows,'bare':bare,'ol':ol},open(OUT,'w'),separators=(',',':'))
print(len(rows),'tests',len({(r['m'],r['s']) for r in rows}),'cans; priced',sum(1 for r in rows if r['p']),'catalog fills',len(set(fills)))
print('recoil: matched',len(RC),'Summit cans to',len(used),'Outdoor Life rows of',len(OL))
print('disagreements >25%:');[print(' ',x) for x in sorted(set(flags))]

# inject into the page
tpl=open(os.path.join(ROOT,'tools','template.html')).read()
page=tpl.replace('__DATA__',open(OUT).read().replace('</','<\\/'))
head,rest=page.split('</style>',1)
open(os.path.join(ROOT,'index.html'),'w').write('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'+head+'</style>\n</head>\n<body>\n'+rest+'\n</body>\n</html>\n')
print('wrote index.html')
