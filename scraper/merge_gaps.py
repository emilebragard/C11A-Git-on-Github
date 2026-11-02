"""Merge gap_*.csv helper results into coaches.csv (head-coach rows only).
Order of preference: coach email shown in search > email built from the
school's format (learned from example staff emails) > name only.
Also stores the athletics department contact in dept_contact."""
import csv, glob, re, collections, sys
sys.path.insert(0, 'scraper')
from infer_name_only import parts, P, has_mx, PERSONAL  # reuse format logic
SPORT = {'men': 'mbkb', 'women': 'wbkb'}
EM = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')
res = {}
import os
for f in sorted(glob.glob(os.environ.get('GAP_GLOB', 'data/search/gap_*.csv'))):
    for r in csv.DictReader(open(f)):
        sp = SPORT.get((r.get('sport') or '').strip().lower())
        if sp: res[(r['school'].strip(), sp)] = r
def learn(examples):
    c = collections.Counter()
    for pair in re.split(r';\s*', examples or ''):
        if '=' not in pair: continue
        name, email = pair.rsplit('=', 1); email = email.strip().lower()
        if not EM.fullmatch(email) or email.endswith(PERSONAL): continue
        f, l = parts(name); local, dom = email.split('@', 1)
        if not (f and l) or re.search(r'\d', local): continue
        for p, fn in P.items():
            if fn(f, l) == local and len(local) > len(l): c[(p, dom)] += 1
    if not c: return None
    top = c.most_common(2)
    return None if len(top) > 1 and top[0][1] == top[1][1] else top[0][0]
rows = list(csv.DictReader(open('data/coaches_full.csv')))
F = list(rows[0]) + ([] if 'dept_contact' in rows[0] else ['dept_contact'])
stats = collections.Counter()
for r in rows:
    r.setdefault('dept_contact', '')
    g = res.get((r['school'], r['sport']))
    if r['role'] != 'head' or not g: continue
    if (g.get('athletics_contact') or '').strip(): r['dept_contact'] = g['athletics_contact'].strip()
    name = (g.get('name') or '').strip() or r['name']
    conf = (g.get('confidence') or 'low').strip().lower()
    email = (g.get('email') or '').strip().lower()
    if email and EM.fullmatch(email):
        r.update(name=name, email=email, email_source='web_search', status=f'search_{conf}_verify',
                 url=(g.get('source_url') or r['url']).strip(), title=(g.get('title') or r['title'] or 'Head Coach').strip())
        stats['coach_email_found'] += 1; continue
    pat = learn(g.get('example_staff_emails'))
    f, l = parts(name) if name else ('', '')
    if pat and f and l and len(f) > 1 and has_mx(pat[1]):
        r.update(name=name, email=f'{P[pat[0]](f, l)}@{pat[1]}', email_source='inferred', status='inferred_verify')
        stats['inferred_from_examples'] += 1; continue
    if name and not r['email']:
        r['name'] = name
        if r['status'] in ('not_found', 'site_blocked', 'no_url'): r['status'] = f'search_name_only_{conf}'
        stats['name_only'] += 1
    else: stats['nothing_new'] += 1
w = csv.DictWriter(open('data/coaches_full.csv', 'w'), fieldnames=F); w.writeheader(); w.writerows(rows)
heads = [r for r in rows if r['role'] == 'head']
print(dict(stats))
print('head-coach status:', collections.Counter(r['status'] for r in heads).most_common())
print('teams with head coach email:', len({(r['school'], r['sport']) for r in heads if r['email']}), 'of', len({(r['school'], r['sport']) for r in heads}))
