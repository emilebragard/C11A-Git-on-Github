"""Merge Haiku web-search batches into coaches.csv, replacing site_blocked
placeholder rows. Search rows are marked email_source=web_search and a
status that says to verify them."""
import csv, glob, re, collections
SPORT = {'men': 'mbkb', 'women': 'wbkb'}
found = {}
for f in sorted(glob.glob('data/search/batch_*.csv')):
    for r in csv.DictReader(open(f)):
        sp = SPORT.get(r.get('sport', '').strip().lower())
        if not sp: continue
        email = (r.get('email') or '').strip().lower()
        if email and not re.fullmatch(r'[\w.+-]+@[\w-]+(\.[\w-]+)+', email): email = ''
        found[(r['school'].strip(), sp)] = r | {'email': email}
F = ['school','sport','role','name','title','email','email_source','url','status']
rows = list(csv.DictReader(open('data/coaches_full.csv'))); F = [f for f in rows[0] if f != 'phone']
out, used = [], 0
for r in rows:
    k = (r['school'], r['sport'])
    if r['status'] == 'site_blocked' and k in found and found[k].get('name', '').strip():
        s = found[k]; used += 1
        conf = (s.get('confidence') or 'low').strip().lower()
        r.update(name=s['name'].strip(), title=(s.get('title') or 'Head Coach').strip(), email=s['email'],
                 email_source='web_search' if s['email'] else '',
                 url=(s.get('source_url') or r['url']).strip(),
                 status=f'search_{conf}_verify' if s['email'] else f'search_name_only_{conf}')
    out.append(r)
csv.DictWriter(open('data/coaches_full.csv', 'w'), fieldnames=F, extrasaction='ignore').writeheader()
w = csv.DictWriter(open('data/coaches_full.csv', 'a'), fieldnames=F, extrasaction='ignore'); w.writerows(out)
heads = [r for r in out if r['role'] == 'head']
print('search rows read', len(found), 'merged', used)
print('head-coach status:', collections.Counter(r['status'] for r in heads).most_common())
print('head coaches with any email:', sum(1 for r in heads if r['email']), 'of', len(heads))
