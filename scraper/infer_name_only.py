"""Step 1: infer emails for search name-only head coaches from other emails
already known at the same school. Skips ambiguous formats (digits, single
bare last name). Prints a short summary."""
import csv, re, collections, httpx
PERSONAL = ('gmail.com','yahoo.com','hotmail.com','outlook.com','icloud.com')
def parts(name):
    n = re.sub(r'\b(jr|sr|ii|iii|iv)\b\.?', '', name, flags=re.I).strip()
    if ',' in n: last, first = [x.strip() for x in n.split(',', 1)]
    else:
        w = n.split(); first, last = (w[0], w[-1]) if len(w) > 1 else ('', '')
    clean = lambda s: re.sub(r'[^a-z]', '', s.lower())
    return clean(first), clean(last)
P = {'first.last': lambda f,l: f'{f}.{l}', 'flast': lambda f,l: f'{f[0]}{l}', 'firstl': lambda f,l: f'{f}{l[0]}',
     'lastf': lambda f,l: f'{l}{f[0]}', 'last.first': lambda f,l: f'{l}.{f}', 'firstlast': lambda f,l: f'{f}{l}',
     'f.last': lambda f,l: f'{f[0]}.{l}', 'first_last': lambda f,l: f'{f}_{l}'}
mx = {}
def has_mx(d):
    if d not in mx:
        try: mx[d] = any(a.get('type') == 15 for a in httpx.get('https://dns.google/resolve', params={'name': d, 'type': 'MX'}, timeout=10).json().get('Answer', []))
        except Exception: mx[d] = False
    return mx[d]

def main():
    rows = list(csv.DictReader(open('data/coaches.csv'))); F = list(rows[0])
    learned = collections.defaultdict(collections.Counter)
    for r in rows:
        e = r['email']
        if not e or '@' not in e or e.endswith(PERSONAL) or r['email_source'] == 'inferred': continue
        f, l = parts(r['name']); local, dom = e.split('@', 1)
        if not (f and l) or re.search(r'\d', local): continue
        for p, fn in P.items():
            if fn(f, l) == local and len(local) > len(l): learned[r['school']][(p, dom)] += 1
    done, skipped, examples = 0, collections.Counter(), []
    for r in rows:
        if not r['status'].startswith('search_name_only'): continue
        pats = learned.get(r['school'])
        if not pats: skipped['no_known_format'] += 1; continue
        (p, dom), n = pats.most_common(1)[0]
        if len(pats) > 1 and pats.most_common(2)[1][1] == n: skipped['conflicting_formats'] += 1; continue
        f, l = parts(r['name'])
        if not (f and l) or len(f) < 2: skipped['name_unusable'] += 1; continue
        if not has_mx(dom): skipped['no_mx'] += 1; continue
        r['email'] = f'{P[p](f, l)}@{dom}'; r['email_source'] = 'inferred'; r['status'] = 'inferred_verify'
        done += 1; examples.append((r['school'][:26], r['name'], r['email'], p))
    w = csv.DictWriter(open('data/coaches.csv', 'w'), fieldnames=F); w.writeheader(); w.writerows(rows)
    print('inferred', done, 'skipped', dict(skipped))
    for x in examples[:8]: print(' ', x)

if __name__ == '__main__':
    main()
