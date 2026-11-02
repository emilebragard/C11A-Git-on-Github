"""Merge helper results (Chrome, search, verify) into data/coaches.csv.

Usage:  python scripts/merge.py <run_id>

Reads every CSV in data/runs/<run_id>/results/. File name decides the source:
chrome_*.csv -> status chrome_ok ; search_*.csv -> search_<confidence> ;
verify_*.csv -> uses the verdict column ; hunter_*.csv -> email verification
(school,email,hunter_status,score): valid -> tier A, invalid -> email removed. Never overwrites a better (tier A) email
with a weaker one. Example staff emails are saved for emails.py to learn formats.
Safe to run repeatedly.
"""
import sys, glob
from common import *

RANK = {'email_verified': 5, 'scraped': 5, 'chrome_ok': 5, 'college_site': 5, 'confirmed': 5, 'search_high': 4,
        'inferred_confirmed': 3, 'search_medium': 2, 'inferred_single': 1, 'search_low': 1}

def main():
    rid = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
    coaches = load_coaches(); by = {r['school']: r for r in coaches if r['run_id'] == rid}
    rd = run_dir(rid); examples = read_csv(rd / 'examples.csv'); stats = {}
    for f in sorted(glob.glob(str(rd / 'results' / '*.csv'))):
        kind = pathlib.Path(f).name.split('_')[0]
        for g in read_csv(f):
            r = by.get((g.get('school') or '').strip())
            if not r: continue
            if kind == 'hunter':  # email verification results (Hunter Email-Verifier)
                hs = (g.get('hunter_status') or '').strip().lower()
                if (g.get('email') or '').strip().lower() != r['email']: continue
                r['email_check'] = f"Hunter {hs} {g.get('score', '')} ({TODAY})".replace('  ', ' ')
                if hs == 'valid' and r['email_source'] != 'inferred': r['status'] = 'email_verified'
                elif hs == 'invalid':
                    r.update(email='', email_source='', status='name_only' if r['name'] else 'not_found')
                stats['hunter_' + hs] = stats.get('hunter_' + hs, 0) + 1
                r['tier'] = tier(r); continue
            dc = re.sub(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', '', g.get('dept_contact') or '').strip(' ,;')  # no phone numbers
            if dc: r['dept_contact'] = dc
            for pair in re.split(r';\s*', g.get('example_staff_emails') or ''):
                if '=' in pair:
                    nm, em = pair.rsplit('=', 1)
                    examples.append({'school': r['school'], 'name': nm.strip(), 'email': em.strip().lower()})
            name = (g.get('name') or '').strip(); email = (g.get('email') or '').strip().lower()
            if email and not EMAIL_RE.fullmatch(email): email = ''
            verdict = (g.get('verdict') or '').strip().lower()
            if kind == 'verify':
                if verdict == 'confirmed': r['status'] = 'confirmed'
                elif verdict == 'email_wrong' and email: r.update(email=email, email_source='verified', status='confirmed')
                elif verdict == 'replaced' and name:
                    r.update(name=name, email=email, email_source='web_search' if email else '',
                             status='confirmed' if email else 'name_only')
                else: continue
                stats[verdict] = stats.get(verdict, 0) + 1
            else:
                new = 'chrome_ok' if kind == 'chrome' else f"search_{(g.get('confidence') or 'low').strip().lower()}"
                if new not in RANK: new = 'search_low'
                if email and RANK[new] > RANK.get(r['status'], 0):
                    r.update(name=name or r['name'], email=email, email_source=kind, status=new)
                    stats[kind + '_email'] = stats.get(kind + '_email', 0) + 1
                elif name and not r['name']:
                    r.update(name=name, status='name_only'); stats[kind + '_name'] = stats.get(kind + '_name', 0) + 1
                else: continue
            if g.get('title'): r['title'] = g['title'].strip()
            if g.get('source_url'): r['source_url'] = g['source_url'].strip()
            r['last_checked'] = TODAY
    for r in by.values(): r['tier'] = tier(r)
    save_coaches(coaches)
    uniq = {(e['school'], e['email']): e for e in examples if EMAIL_RE.fullmatch(e['email'])}
    write_csv(rd / 'examples.csv', list(uniq.values()), ['school', 'name', 'email'])
    print(f'{rid} merged:', stats or 'nothing new', f'| example staff emails stored: {len(uniq)}')

if __name__ == '__main__':
    main()
