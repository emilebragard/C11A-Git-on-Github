"""Option 1: crawl main college (.edu) sites, not the athletics host, for
staff directory pages. Harvest (name, email) pairs to (a) find coach emails
directly and (b) learn/confirm each school's email format.
Polite: robots.txt respected, cached, <=8 pages per school. Summary output."""
import csv, glob, re, collections, sys, json
from urllib.parse import urljoin, urlparse
sys.path.insert(0, 'scraper')
from coaches import get, H
from infer_name_only import parts, P, PERSONAL

rows = list(csv.DictReader(open('data/coaches.csv')))
schools = {r['school']: r for r in csv.DictReader(open('data/schools.csv'))}
heads = [r for r in rows if r['role'] == 'head']
targets = {r['school'] for r in heads if not r['email'] or r['email_source'] == 'inferred'}

# Known .edu domains per school from emails we already have or helper examples.
dom = collections.defaultdict(collections.Counter)
for r in rows:
    if r['email'].endswith('.edu'): dom[r['school']][r['email'].split('@')[1]] += 1
for f in glob.glob('data/search/gap_*.csv'):
    for r in csv.DictReader(open(f)):
        for d in re.findall(r'@([\w.-]+\.edu)', r.get('example_staff_emails') or ''): dom[r['school']][d] += 1
for s in targets:
    host = urlparse(schools.get(s, {}).get('athletics_url', '')).netloc
    if host.endswith('.edu'): dom[s][re.sub(r'^(www|athletics)\.', '', host)] += 1

DIR_PATHS = ['/directory', '/directory/', '/employee-directory', '/staff-directory', '/about/directory',
             '/faculty-staff-directory', '/athletics/staff', '/athletics/coaches', '/contact-us', '/athletics']
NAME = re.compile(r"([A-Z][a-zA-Z'\-]+(?:\s+[A-Z]\.)?\s+[A-Z][a-zA-Z'\-]+)")

def harvest(html, domain):
    """Return list of (name, email, context) found on a page for this domain."""
    t = H(html); out = []
    for a in t.css('a[href^="mailto:"]'):
        email = a.attributes['href'][7:].split('?')[0].strip().lower()
        if not email.endswith('@' + domain) and not email.endswith('.' + domain): continue
        node, ctx = a, ''
        for _ in range(3):
            node = node.parent or node
            ctx = ' '.join(node.text(separator=' ').split())
            if len(ctx) > 40: break
        txt = a.text(strip=True)
        name = txt if NAME.fullmatch(txt or '') else (NAME.search(ctx).group(1) if NAME.search(ctx) else '')
        out.append((name, email, ctx[:250]))
    return out

found = collections.defaultdict(list); pages_ok = collections.Counter()
for s in sorted(targets):
    for d, _ in dom[s].most_common(1):
        root = f'https://www.{d}'
        home = get(root) or get(f'https://{d}')
        urls = [urljoin(root, p) for p in DIR_PATHS]
        if home:
            for a in H(home).css('a[href]'):
                if re.search(r'directory|athletic|staff|contact', a.attributes['href'] + a.text(strip=True), re.I):
                    u = urljoin(root, a.attributes['href'])
                    if d in urlparse(u).netloc: urls.insert(0, u)
        for u in list(dict.fromkeys(urls))[:8]:
            html = get(u)
            if html: pages_ok[s] += 1; found[s] += harvest(html, d)
        found[s] = list({e: (n, e, c) for n, e, c in found[s]}.values())

def pattern_of(name, email):
    f, l = parts(name); local = email.split('@')[0]
    if not (f and l) or re.search(r'\d', local): return None
    return next((p for p, fn in P.items() if fn(f, l) == local and len(local) > len(l)), None)

direct = inferred_confirmed = new_inferred = 0
for r in heads:
    s = r['school']
    pairs = found.get(s, [])
    if not pairs: continue
    pats = collections.Counter((pattern_of(n, e), e.split('@')[1]) for n, e, _ in pairs if n and pattern_of(n, e))
    # (a) direct coach match: email near coach's last name, or name matches
    f, l = parts(r['name']) if r['name'] else ('', '')
    hit = None
    for n, e, c in pairs:
        if l and len(l) > 2 and l in e.split('@')[0] and (not f or f[0] in e.split('@')[0]):
            hit = e; break
        if not l and re.search(r'basketball', c, re.I) and re.search(r'head', c, re.I):
            hit = e; r['name'] = n; break
    if hit and r['email'] != hit:
        r['email'] = hit; r['email_source'] = 'college_site'; r['status'] = 'college_site_ok'; direct += 1; continue
    if hit and r['email'] == hit and r['email_source'] == 'inferred':
        r['email_source'] = 'college_site'; r['status'] = 'college_site_ok'; inferred_confirmed += 1; continue
    if not pats or not (f and l): continue
    (p, d), n = pats.most_common(1)[0]
    if p is None or n < 2: continue  # need 2+ examples to trust a format
    guess = f'{P[p](f, l)}@{d}'
    if r['email_source'] == 'inferred' and r['email'] == guess:
        r['status'] = 'inferred_confirmed_format'; inferred_confirmed += 1
    elif not r['email']:
        r['email'] = guess; r['email_source'] = 'inferred'; r['status'] = 'inferred_confirmed_format'; new_inferred += 1

w = csv.DictWriter(open('data/coaches.csv', 'w'), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump({s: v for s, v in found.items()}, open('data/college_site_emails.json', 'w'), indent=0)
print('target schools', len(targets), 'with a domain', sum(1 for s in targets if dom[s]),
      'with pages fetched', len(pages_ok), 'with staff emails', sum(1 for v in found.values() if v))
print('direct coach emails', direct, '| inferred confirmed', inferred_confirmed, '| new inferred (2+ examples)', new_inferred)
print('teams with head coach email:', len({(r['school'], r['sport']) for r in heads if r['email']}), 'of', len({(r['school'], r['sport']) for r in heads}))
