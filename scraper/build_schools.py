"""Build data/schools.csv from NJCAA team lists + member directory.
Usage: python3 scraper/build_schools.py mbkb wbkb
Needs data/<sport>_d2.json (njcaa_teams.js) and data/members.json (njcaa_members.js)."""
import csv, json, re, sys, difflib
sports = sys.argv[1:] or ['mbkb', 'wbkb']
def norm(s): return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s.upper().replace('&', 'AND')).split())
members = {norm(x['name']): x['url'] for x in json.load(open('data/members.json'))}
schools = {}
for sp in sports:
    for t in json.load(open(f'data/{sp}_d2.json')):
        r = schools.setdefault(t['school'], {'school': t['school'], 'region': t['region'], 'tenant': t['tenant']})
        r[sp + '_id'] = t['team_id']
rows = sorted(schools.values(), key=lambda r: (r['region'], r['school']))
missing = []
for r in rows:
    for sp in sports: r.setdefault(sp + '_id', '')
    k = norm(r['school']); hit = k if k in members else (difflib.get_close_matches(k, members, 1, 0.85) or [None])[0]
    r['athletics_url'] = members.get(hit, '') if hit else ''
    if not hit: missing.append(r['school'])
F = ['school', 'region', 'tenant'] + [sp + '_id' for sp in sports] + ['athletics_url']
w = csv.DictWriter(open('data/schools.csv', 'w'), fieldnames=F); w.writeheader(); w.writerows(rows)
print('schools', len(rows), '| no athletics URL (add by hand):', missing)
