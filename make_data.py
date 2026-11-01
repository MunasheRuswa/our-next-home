import json, glob, sys, os
src = sys.argv[1]; out = sys.argv[2]
rows = []
for f in glob.glob(os.path.join(src, '*.json')):
    d = json.load(open(f)); d = d.get('data', d)
    if d.get('status') != 'active' or d.get('children') is False or not d.get('rent'): continue
    if not d.get('url'): continue
    agent = next((x['t'].split(':',1)[1].strip() for x in d.get('facts',[]) if x.get('t','').startswith('Agent:')), None)
    av = d.get('available')
    when = 'dec' if av and '2026-11-24' <= av <= '2026-12-08' else 'other'
    txt = ' '.join([d.get('title',''), d.get('type',''), d.get('outdoor') or '', d.get('parking') or '', ' '.join(x['t'] for x in d.get('facts',[]))]).lower()
    rows.append(dict(
        id=os.path.basename(f)[:-5], title=d['title'], suburb=d['suburb'], type=d.get('type'),
        rent=d['rent'], deposit=d.get('deposit'), beds=d.get('beds'), baths=d.get('baths'),
        size=d.get('size'), parking=d.get('parking'), outdoor=d.get('outdoor'),
        security=d.get('security') or [], available=av, when=when,
        agency=d.get('agency'), agent=agent, ref=d.get('ref'), source=d.get('source'), url=d['url'],
        unknowns=d.get('unknowns') or [],
        notes=[x['t'] for x in d.get('facts',[]) if not x.get('t','').startswith('Agent:')][:6],
        draw=dict(garden=('garden' in txt or 'courtyard' in txt), wall=('wall' in txt or 'secure' in txt or 'access' in txt),
                  garage=('garage' in txt), flat=bool(d.get('type')) and any(k in d['type'].lower() for k in ['apart','flat']),
                  duet=('duet' in txt or 'simplex' in txt), house=bool(d.get('type')) and 'house' in d['type'].lower() and 'town' not in d['type'].lower())
    ))
rows.sort(key=lambda r: (r['rent'], r['title']))
json.dump(dict(updated='2026-10-31', homes=rows), open(out,'w'), indent=1, ensure_ascii=False)
from collections import Counter
print(len(rows), Counter(r['when'] for r in rows), Counter(r['type'] for r in rows))
for r in rows:
    if r['when']=='dec': print(r['rent'], r['title'], r['draw'])
