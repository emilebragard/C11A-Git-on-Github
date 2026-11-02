"""Refresh coverage and write the human-readable outputs for one run.

Usage:  python scripts/report.py <run_id>              summary + files
        python scripts/report.py <run_id> --doc-table  also print the table for the Claude doc

Writes:
  data/coverage.csv          one line per run (how complete it is)
  reports/<run_id>.md        local copy of the Claude doc (the backup)
  exports/<run_id>.csv       clean list to share: school, coach, title, email, confidence
The Claude doc link (once created) is stored with: --doc-link <url>
"""
import sys, collections
from common import *

CONF = {'A': 'High', 'B': 'Good (format confirmed)', 'C': 'Guessed (verify)', 'D': 'Unconfirmed (verify)'}

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    rid = sys.argv[1]; assoc, div, sport = parse_run_id(rid); sp = sports()[sport]
    coaches = load_coaches(); rows = sorted([r for r in coaches if r['run_id'] == rid], key=lambda r: r['school'])
    for r in rows: r['tier'] = tier(r)
    save_coaches(coaches)
    c = collections.Counter(r['tier'] for r in rows)
    cov = {r['run_id']: r for r in read_csv(DATA / 'coverage.csv')}
    old = cov.get(rid, {})
    link = sys.argv[sys.argv.index('--doc-link') + 1] if '--doc-link' in sys.argv else old.get('doc_link', '')
    n = len(rows); we = sum(1 for r in rows if r['email'])
    cov[rid] = {'run_id': rid, 'association': assoc, 'division': div, 'sport': sport, 'teams': n, 'with_email': we,
                'tier_A': c['A'], 'tier_B': c['B'], 'tier_C': c['C'], 'tier_D': c['D'],
                'name_only': sum(1 for r in rows if not r['email'] and r['name']),
                'nothing': sum(1 for r in rows if not r['email'] and not r['name']),
                'pct_email': f'{100 * we / n:.0f}%' if n else '0%', 'doc_link': link, 'last_run': TODAY}
    write_csv(DATA / 'coverage.csv', sorted(cov.values(), key=lambda r: r['run_id']), COVERAGE_FIELDS)
    title = f"{assoc} {div} {sp['label']} Head Coaches"
    table = ['| School | Head coach | Email | Confidence |', '|---|---|---|---|']
    for r in rows:
        table.append(f"| {r['school']} | {r['name'] or '—'} | {r['email'] or '—'} | {CONF.get(r['tier'], 'Not found yet' if not r['name'] else 'Name only')} |")
    summary = (f"**{we} of {n} teams have a head coach email ({cov[rid]['pct_email']}).** "
               f"High: {c['A']} · Format confirmed: {c['B']} · Guessed: {c['C']} · Unconfirmed: {c['D']} · "
               f"Name only: {cov[rid]['name_only']} · Not found: {cov[rid]['nothing']}. Last updated {TODAY}.")
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports' / f'{rid}.md').write_text(f"# {title}\n\n{summary}\n\n" + '\n'.join(table) + '\n'
        + (f"\nLive doc: {link}\n" if link else ''), encoding='utf-8')
    write_csv(ROOT / 'exports' / f'{rid}.csv', [{'school': r['school'], 'head_coach': r['name'], 'title': r['title'],
              'email': r['email'], 'confidence': CONF.get(r['tier'], ''), 'dept_contact': r['dept_contact']} for r in rows],
              ['school', 'head_coach', 'title', 'email', 'confidence', 'dept_contact'])
    print(title); print(summary.replace('**', ''))
    print('status:', dict(collections.Counter(r['status'] for r in rows)))
    if '--doc-table' in sys.argv: print('\n'.join(table))

if __name__ == '__main__':
    main()
