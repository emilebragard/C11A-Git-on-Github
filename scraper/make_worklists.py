"""Write search worklists for AI helpers from data/coaches_full.csv.
Usage: python3 scraper/make_worklists.py gap 3      -> data/search/gap_1..3.txt
       python3 scraper/make_worklists.py verify 2   -> data/search/verify_1..2.txt
gap: head-coach teams with no email (FIND) or a name but no email (FORMAT).
verify: medium/low-confidence search rows to re-check."""
import csv, sys, collections, os
mode, n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3
os.makedirs('data/search', exist_ok=True)
rows = [r for r in csv.DictReader(open('data/coaches_full.csv')) if r['role'] == 'head']
urls = {r['school']: r['athletics_url'] for r in csv.DictReader(open('data/schools.csv'))}
label = lambda sp: 'men' if sp == 'mbkb' else 'women'
if mode == 'gap':
    items = collections.OrderedDict()
    for r in rows:
        if r['email']: continue
        task = f"{label(r['sport'])}:{'FORMAT' if r['name'] else 'FIND'}" + (f"={r['name']}" if r['name'] else '')
        items.setdefault(r['school'], []).append(task)
    it = list(items.items())
    for i in range(n):
        with open(f'data/search/gap_{i+1}.txt', 'w') as f:
            for s, t in it[i::n]: f.write(f"{s} | {'; '.join(t)} | {urls.get(s, '')}\n")
    print('gap schools', len(it))
elif mode == 'verify':
    v = [r for r in rows if r['status'] in ('search_medium_verify', 'search_low_verify')]
    for i in range(n):
        with open(f'data/search/verify_{i+1}.txt', 'w') as f:
            for r in v[i::n]: f.write(f"{r['school']} | {label(r['sport'])} | {r['name']} | {r['email']}\n")
    print('verify rows', len(v))
