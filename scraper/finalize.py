"""Phase 6: merge pilot + manual fallback, infer missing head-coach emails
from each school's observed pattern, MX-check domains, write coaches.csv."""
import csv, re, collections, httpx
pilot = [r for r in csv.DictReader(open('data/coaches_pilot.csv')) if r['name']]
manual = list(csv.DictReader(open('data/fallback_manual.csv')))
schools = {r['school']: r for r in csv.DictReader(open('data/schools.csv'))}
rows = []
for r in pilot:
    rows.append({k: r[k] for k in ['school','sport','name','title','email','phone','url']} | {'email_source': 'scraped' if r['email'] else '', 'status': ''})
done = {(r['school'], r['sport']) for r in pilot if r['status'] != 'needs_review'}
for r in manual:
    if (r['school'], r['sport']) not in done:
        rows.append(r | {'email_source': 'scraped' if r['email'] else '', 'status': ''})

def parts(name):
    n = re.sub(r'\b(jr|sr|ii|iii)\b\.?', '', name, flags=re.I)
    if ',' in n: last, first = [x.strip() for x in n.split(',', 1)]
    else: w = n.split(); first, last = (w[0], w[-1]) if len(w) > 1 else ('', '')
    return re.sub(r'[^a-z]', '', first.lower()), re.sub(r'[^a-z]', '', last.lower())
PATTERNS = {'first.last': lambda f,l: f'{f}.{l}', 'flast': lambda f,l: f'{f[0]}{l}', 'firstl': lambda f,l: f'{f}{l[0]}',
            'lastf': lambda f,l: f'{l}{f[0]}', 'last.first': lambda f,l: f'{l}.{f}', 'firstlast': lambda f,l: f'{f}{l}', 'f.last': lambda f,l: f'{f[0]}.{l}'}
# learn pattern + domain per school from scraped emails on school domains
learned = collections.defaultdict(collections.Counter)
for r in rows:
    if r['email'] and not r['email'].endswith(('gmail.com','yahoo.com','hotmail.com')):
        f, l = parts(r['name']); local, dom = r['email'].split('@')
        if not (f and l): continue
        for p, fn in PATTERNS.items():
            if fn(f, l) == local: learned[r['school']][(p, dom)] += 1
inferred = 0
for r in rows:
    if not r['email'] and learned[r['school']]:
        (p, dom), _ = learned[r['school']].most_common(1)[0]; f, l = parts(r['name'])
        if f and l: r['email'] = f'{PATTERNS[p](f, l)}@{dom}'; r['email_source'] = 'inferred'; inferred += 1
mx = {}
def has_mx(d):
    if d not in mx:
        try:  # DNS-over-HTTPS (direct DNS is blocked in this sandbox)
            j = httpx.get('https://dns.google/resolve', params={'name': d, 'type': 'MX'}, timeout=10).json()
            mx[d] = any(a.get('type') == 15 for a in j.get('Answer', []))
        except Exception: mx[d] = False
    return mx[d]
for r in rows:
    head = re.search(r'head', r['title'], re.I) and not re.search(r'assistant|associate', r['title'], re.I)
    r['role'] = 'head' if head else 'assistant'
    if not r['email']: r['status'] = 'no_email'
    elif not has_mx(r['email'].split('@')[1]): r['status'] = 'bad_domain'
    elif r['email_source'] == 'inferred': r['status'] = 'inferred_unverified'
    elif r['email'].endswith(('gmail.com','yahoo.com','hotmail.com')): r['status'] = 'ok_personal_email'
    else: r['status'] = 'ok'
# QA: dedupe on school+sport+name
seen, out = set(), []
for r in rows:
    k = (r['school'], r['sport'], r['name'].lower())
    if k not in seen: seen.add(k); out.append(r)
# add missing teams as placeholder rows
have = {(r['school'], r['sport']) for r in out if r['role'] == 'head'}
F = ['school','sport','role','name','title','email','email_source','url','status']
for s in schools.values():
    for sp in ['mbkb','wbkb']:
        if s[sp + '_id'] and (s['school'], sp) not in have:
            why = 'site_blocked' if s['platform'] == 'blocked_403' else 'no_url' if s['platform'] == 'no_url' else 'not_found'
            out.append({'school': s['school'], 'sport': sp, 'role': 'head', 'name': '', 'title': '', 'email': '', 'email_source': '', 'phone': '', 'url': s['athletics_url'], 'status': why})
out.sort(key=lambda r: (r['school'], r['sport'], r['role'] != 'head'))
w = csv.DictWriter(open('data/coaches.csv', 'w'), fieldnames=F, extrasaction='ignore'); w.writeheader(); w.writerows(out)
heads = [r for r in out if r['role'] == 'head']
print('rows', len(out), 'inferred', inferred, 'domains checked', len(mx), 'bad', [d for d, v in mx.items() if not v])
print('head-coach rows by status:', collections.Counter(r['status'] for r in heads).most_common())
print('total teams', sum(bool(s['mbkb_id']) + bool(s['wbkb_id']) for s in schools.values()))
