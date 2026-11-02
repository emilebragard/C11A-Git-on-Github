"""Make a to-do list for a Chrome pass, search helpers, or a verify pass.

Usage:  python scripts/worklist.py <run_id> chrome          one list for Claude in Chrome
        python scripts/worklist.py <run_id> search 3        3 lists, one per search helper
        python scripts/worklist.py <run_id> verify 2        2 lists of uncertain rows to re-check

Writes data/runs/<run_id>/worklists/<mode>_<n>.csv and prints how many rows.
Helpers write results to data/runs/<run_id>/results/<mode>_<n>.csv
(columns in PLAYBOOK.md "Result file format"), then run merge.py.
"""
import sys
from common import *

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    rid, mode = sys.argv[1], sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    assoc, div, sport = parse_run_id(rid); sp = sports()[sport]
    schools = load_schools(); rows = [r for r in load_coaches() if r['run_id'] == rid]
    if mode == 'chrome':  # everything without an email whose site exists (blocked ones first)
        todo = [r for r in rows if not r['email'] and schools.get((assoc, r['school']), {}).get('athletics_url')]
        todo.sort(key=lambda r: r['status'] != 'blocked')
    elif mode == 'search':  # still no email after Chrome
        todo = [r for r in rows if not r['email']]
    elif mode == 'verify':  # emails we are least sure about
        todo = [r for r in rows if r['status'] in ('search_medium', 'search_low', 'inferred_single')]
    else: sys.exit('mode must be chrome, search or verify')
    out = []
    for r in todo:
        s = schools.get((assoc, r['school']), {})
        root = s.get('athletics_url', '').rstrip('/').replace('/landing/index', '')
        out.append({'school': r['school'], 'task': 'VERIFY' if mode == 'verify' else ('EMAIL' if r['name'] else 'FIND'),
                    'known_name': r['name'], 'known_email': r['email'], 'athletics_url': s.get('athletics_url', ''),
                    'try_first': f"{root}/sports/{sp['sidearm_slug']}/coaches" if root else '',
                    'email_domain': s.get('email_domain', '')})
    d = run_dir(rid) / 'worklists'
    for i in range(n):
        write_csv(d / f'{mode}_{i + 1}.csv', out[i::n], ['school', 'task', 'known_name', 'known_email', 'athletics_url', 'try_first', 'email_domain'])
    print(f'{rid} {mode}: {len(out)} rows in {n} list(s) -> {d}')

if __name__ == '__main__':
    main()
