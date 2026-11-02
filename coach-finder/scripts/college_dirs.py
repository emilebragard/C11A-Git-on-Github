"""Check each college's MAIN website (e.g. brown.edu, not the athletics site)
for staff directory pages. Finds coach emails directly, and collects other
staff emails so emails.py can learn the school's email format.

Usage:  python scripts/college_dirs.py <run_id>
Only looks at teams still missing an email or with a guessed (inferred) one.
"""
import sys, collections
from urllib.parse import urljoin
from common import *

PATHS = ['/directory', '/directory/', '/employee-directory', '/staff-directory', '/about/directory',
         '/faculty-staff-directory', '/athletics/staff', '/athletics/coaches', '/contact-us', '/athletics']
NAME = re.compile(r"([A-Z][a-zA-Z'\-]+(?:\s+[A-Z]\.)?\s+[A-Z][a-zA-Z'\-]+)")

def harvest(page, domain):
    t = html(page); out = []
    for a in t.css('a[href^="mailto:"]'):
        email = a.attributes['href'][7:].split('?')[0].strip().lower()
        if not (email.endswith('@' + domain) or email.endswith('.' + domain)): continue
        node, ctx = a, ''
        for _ in range(3):
            node = node.parent or node; ctx = ' '.join(node.text(separator=' ').split())
            if len(ctx) > 40: break
        txt = a.text(strip=True)
        nm = txt if NAME.fullmatch(txt or '') else (NAME.search(ctx).group(1) if NAME.search(ctx) else '')
        out.append({'name': nm, 'email': email})
    return out

def main():
    rid = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
    assoc, div, sport = parse_run_id(rid)
    schools = load_schools(); coaches = load_coaches(); rd = run_dir(rid)
    examples = read_csv(rd / 'examples.csv'); stats = collections.Counter()
    known_dom = {}
    for r in coaches:
        if r['email'].endswith('.edu') and r['email_source'] != 'inferred': known_dom.setdefault(r['school'], r['email'].split('@')[1])
    for r in [x for x in coaches if x['run_id'] == rid and (not x['email'] or x['email_source'] == 'inferred')]:
        s = schools.get((assoc, r['school']), {})
        dom = s.get('email_domain') or known_dom.get(r['school'])
        if not dom: stats['no_domain'] += 1; continue
        root = f'https://www.{dom}'
        home = fetch(root) or fetch(f'https://{dom}')
        urls = [urljoin(root, p) for p in PATHS]
        if home:
            for a in html(home).css('a[href]'):
                h = a.attributes.get('href') or ''
                if re.search(r'directory|athletic|staff|contact', h + a.text(strip=True), re.I):
                    u = urljoin(root, h)
                    if dom in urlparse(u).netloc: urls.insert(0, u)
        found = []
        for u in list(dict.fromkeys(urls))[:8]:
            pg = fetch(u)
            if pg: found += harvest(pg, dom)
        if not found: stats['no_emails_on_site'] += 1; continue
        examples += [{'school': r['school'], **e} for e in found if e['name']]
        f, l = name_parts(r['name'])
        hit = next((e['email'] for e in found if l and len(l) > 2 and l in e['email'].split('@')[0]
                    and (not f or f[0] in e['email'].split('@')[0])), None)
        if hit:
            r.update(email=hit, email_source='college_site', status='college_site', last_checked=TODAY); stats['coach_email_found'] += 1
        else: stats['staff_emails_only'] += 1
    for r in coaches:
        if r['run_id'] == rid: r['tier'] = tier(r)
    save_coaches(coaches)
    uniq = {(e['school'], e['email']): e for e in examples}
    write_csv(rd / 'examples.csv', list(uniq.values()), ['school', 'name', 'email'])
    print(f'{rid} college sites:', dict(stats), '| now run emails.py to use the staff emails')

if __name__ == '__main__':
    main()
