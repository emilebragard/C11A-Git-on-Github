"""Apply verify_*.csv verdicts to medium/low search rows in coaches.csv.
confirmed -> search_confirmed; replaced -> new coach (email only if shown);
email_wrong -> corrected email; unclear -> unchanged."""
import csv, glob, re, collections
SPORT = {'men': 'mbkb', 'women': 'wbkb'}
EM = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')
v = {}
for f in sorted(glob.glob('data/search/verify_*.csv')):
    for r in csv.DictReader(open(f)):
        sp = SPORT.get((r.get('sport') or '').strip().lower())
        if sp: v[(r['school'].strip(), sp)] = r
rows = list(csv.DictReader(open('data/coaches_full.csv'))); c = collections.Counter()
for r in rows:
    g = v.get((r['school'], r['sport']))
    if r['role'] != 'head' or not g or r['status'] not in ('search_medium_verify', 'search_low_verify'): continue
    verdict = (g.get('verdict') or 'unclear').strip().lower(); c[verdict] += 1
    ne = (g.get('current_email') or '').strip().lower()
    if verdict == 'confirmed': r['status'] = 'search_confirmed'
    elif verdict == 'email_wrong' and EM.fullmatch(ne): r['email'] = ne; r['status'] = 'search_confirmed'
    elif verdict == 'replaced' and (g.get('current_name') or '').strip():
        r['name'] = g['current_name'].strip(); r['email'] = ne if EM.fullmatch(ne) else ''
        r['email_source'] = 'web_search' if r['email'] else ''
        r['status'] = 'search_confirmed' if r['email'] else 'search_name_only_medium'
    if g.get('source_url'): r['url'] = g['source_url'].strip()
csv.DictWriter(open('data/coaches_full.csv', 'w'), fieldnames=list(rows[0])).writeheader()
csv.DictWriter(open('data/coaches_full.csv', 'a'), fieldnames=list(rows[0])).writerows(rows)
heads = [r for r in rows if r['role'] == 'head']
print('verdicts', dict(c))
print('teams with head coach email:', len({(r['school'], r['sport']) for r in heads if r['email']}), 'of', len({(r['school'], r['sport']) for r in heads}))
