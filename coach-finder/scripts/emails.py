"""Learn each school's email format, then build emails for coaches with a name but no email.

Usage:  python scripts/emails.py <run_id>

Learns from every known email in the whole database (all sports help each
other) plus example staff emails collected by helpers. Updates
data/email_formats.csv. A built email is:
  inferred_confirmed  format seen in 2+ real emails at that school  (tier B)
  inferred_single     format seen in only 1 real email              (tier C)
Only builds emails for domains that accept mail (MX check).
"""
import sys, glob, collections
from common import *

def main():
    rid = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
    coaches = load_coaches()
    pairs = [(r['school'], r['name'], r['email']) for r in coaches
             if r['email'] and r['email_source'] not in ('inferred',) and r['name']]
    for f in glob.glob(str(DATA / 'runs' / '*' / 'examples.csv')):
        pairs += [(e['school'], e['name'], e['email']) for e in read_csv(f)]
    learned = collections.defaultdict(collections.Counter)
    for school, name, email in pairs:
        if email.endswith(PERSONAL) or '@' not in email: continue
        fmt = format_of(name, email)
        if fmt: learned[school][(fmt, email.split('@')[1])] += 1
    fmts = []
    for school, c in learned.items():
        (fmt, dom), n = c.most_common(1)[0]
        tie = len(c) > 1 and c.most_common(2)[1][1] == n
        fmts.append({'school': school, 'domain': dom, 'format': fmt, 'examples': n, 'ambiguous': 'yes' if tie else ''})
    write_csv(DATA / 'email_formats.csv', sorted(fmts, key=lambda x: x['school']), ['school', 'domain', 'format', 'examples', 'ambiguous'])
    best = {f['school']: f for f in fmts if not f['ambiguous']}
    built = collections.Counter()
    for r in coaches:
        if r['run_id'] != rid or r['email'] or not r['name']: continue
        f = best.get(r['school'])
        if not f: built['no_format_known'] += 1; continue
        e = build_email(r['name'], f['format'], f['domain'])
        if not e or not has_mx(f['domain']): built['skipped'] += 1; continue
        st = 'inferred_confirmed' if int(f['examples']) >= 2 else 'inferred_single'
        r.update(email=e, email_source='inferred', status=st, last_checked=TODAY); built[st] += 1
    for r in coaches:
        if r['run_id'] == rid: r['tier'] = tier(r)
    save_coaches(coaches)
    print(f'{rid}: formats known for {len(best)} schools |', dict(built))

if __name__ == '__main__':
    main()
