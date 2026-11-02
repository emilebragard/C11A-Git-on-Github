"""Shared helpers for every coach-finder script.

Keeps the plain-spreadsheet "database" in data/ consistent:
  data/schools.csv       one row per school (website, platform, email domain)
  data/coaches.csv       one row per team (run_id + school), all sports
  data/coverage.csv      one row per run: how complete it is
  data/email_formats.csv learned email format per email domain
  data/runs/<run_id>/    per-run working files (team list, worklists, helper results)
"""
import csv, hashlib, json, os, pathlib, re, time, urllib.robotparser as rp
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, CACHE, KNOW = ROOT / 'data', ROOT / 'cache', ROOT / 'knowledge'
UA = 'Mozilla/5.0 (compatible; coach-finder research; polite crawler)'
PERSONAL = ('gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com', 'aol.com')
EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')

COACH_FIELDS = ['run_id', 'association', 'division', 'sport', 'school', 'name', 'title', 'email',
                'email_source', 'tier', 'status', 'source_url', 'dept_contact', 'last_checked']
SCHOOL_FIELDS = ['association', 'school', 'school_id', 'athletics_url', 'final_url', 'platform',
                 'email_domain', 'checked']
COVERAGE_FIELDS = ['run_id', 'association', 'division', 'sport', 'teams', 'with_email', 'tier_A',
                   'tier_B', 'tier_C', 'tier_D', 'name_only', 'nothing', 'pct_email', 'doc_link', 'last_run']

TODAY = time.strftime('%Y-%m-%d')

# ---------- spreadsheets ----------
def read_csv(path):
    path = pathlib.Path(path)
    return list(csv.DictReader(open(path, newline='', encoding='utf-8'))) if path.exists() else []

def write_csv(path, rows, fields):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, '') for k in fields})
    os.replace(tmp, path)  # atomic: a crash never leaves a half-written file

def sports():
    return {r['sport_key']: r for r in read_csv(KNOW / 'sports.csv')}

def run_id(association, division, sport):
    return f"{association.lower()}-{division.lower()}-{sport}"

def run_dir(rid):
    d = DATA / 'runs' / rid; d.mkdir(parents=True, exist_ok=True); return d

def parse_run_id(rid):
    assoc, div, sport = rid.split('-', 2)
    return assoc.upper(), div.upper(), sport

def load_coaches():
    return read_csv(DATA / 'coaches.csv')

def save_coaches(rows):
    rows.sort(key=lambda r: (r['run_id'], r['school']))
    write_csv(DATA / 'coaches.csv', rows, COACH_FIELDS)

def load_schools():
    return {(r['association'], r['school']): r for r in read_csv(DATA / 'schools.csv')}

def save_schools(d):
    write_csv(DATA / 'schools.csv', sorted(d.values(), key=lambda r: (r['association'], r['school'])), SCHOOL_FIELDS)

# ---------- polite, cached fetching ----------
_robots, _last_hit = {}, {}

def _allowed(url):
    host = '{0.scheme}://{0.netloc}'.format(urlparse(url))
    if host not in _robots:
        r = rp.RobotFileParser(host + '/robots.txt')
        try: r.read()
        except Exception: r = None
        _robots[host] = r
    return _robots[host] is None or _robots[host].can_fetch(UA, url)

def fetch(url, min_len=1500):
    """Return page HTML or None. Cached forever in cache/pages (delete to refresh).
    Respects robots.txt and waits ~0.7s between hits to the same site."""
    import httpx
    if url.startswith('http://'): url = 'https://' + url[7:]  # prefer HTTPS; nearly all sites support it
    f = CACHE / 'pages' / (hashlib.md5(url.encode()).hexdigest() + '.html')
    if f.exists():
        t = f.read_text(errors='ignore'); return t or None
    f.parent.mkdir(parents=True, exist_ok=True)
    host = urlparse(url).netloc
    if not _allowed(url):
        rb = _robots.get('{0.scheme}://{0.netloc}'.format(urlparse(url)))
        if rb is not None and rb.disallow_all:  # robots.txt itself answered 401/403: site blocks us
            (CACHE / 'blocked_hosts.txt').open('a').write(host + '\n')
        f.write_text(''); return None
    wait = 0.7 - (time.time() - _last_hit.get(host, 0))
    if wait > 0: time.sleep(wait)
    try:
        r = httpx.get(url, follow_redirects=True, timeout=20, headers={'User-Agent': UA})
        _last_hit[host] = time.time()
        txt = r.text if r.status_code == 200 and len(r.text) >= min_len else ''
        if r.status_code == 403: txt = ''; (CACHE / 'blocked_hosts.txt').open('a').write(host + '\n')
    except Exception:
        txt = ''
    f.write_text(txt); return txt or None

def is_blocked_host(url):
    p = CACHE / 'blocked_hosts.txt'
    return p.exists() and urlparse(url).netloc in p.read_text().split()

def html(text):
    from selectolax.lexbor import LexborHTMLParser
    return LexborHTMLParser(text)

def browser(playwright):
    """Launch Chromium; set CHROMIUM_PATH if Playwright can't find its own browser."""
    exe = os.environ.get('CHROMIUM_PATH')
    return playwright.chromium.launch(executable_path=exe) if exe else playwright.chromium.launch()

# ---------- names and email formats ----------
def name_parts(name):
    n = re.sub(r'\b(jr|sr|ii|iii|iv)\b\.?', '', name or '', flags=re.I).strip()
    if ',' in n: last, first = [x.strip() for x in n.split(',', 1)]
    else:
        w = n.split(); first, last = (w[0], w[-1]) if len(w) > 1 else ('', '')
    clean = lambda s: re.sub(r'[^a-z]', '', s.lower())
    return clean(first), clean(last)

FORMATS = {
    'first.last': lambda f, l: f'{f}.{l}', 'flast': lambda f, l: f'{f[0]}{l}',
    'firstl': lambda f, l: f'{f}{l[0]}', 'lastf': lambda f, l: f'{l}{f[0]}',
    'last.first': lambda f, l: f'{l}.{f}', 'firstlast': lambda f, l: f'{f}{l}',
    'f.last': lambda f, l: f'{f[0]}.{l}', 'first_last': lambda f, l: f'{f}_{l}',
    'last': lambda f, l: l,
}

def format_of(name, email):
    """Which known format turns `name` into this email's local part (or None)."""
    f, l = name_parts(name); local = email.split('@')[0].lower()
    if not (f and l) or re.search(r'\d', local): return None
    for k, fn in FORMATS.items():
        if k == 'last': continue  # too ambiguous to learn from
        if fn(f, l) == local: return k
    return None

def build_email(name, fmt, domain):
    f, l = name_parts(name)
    return f'{FORMATS[fmt](f, l)}@{domain}' if f and l and len(f) > 1 else ''

_mx = {}
def has_mx(domain):
    """True if the domain accepts email (DNS MX record). Tries normal DNS, then DNS-over-HTTPS."""
    if domain in _mx: return _mx[domain]
    ok = False
    try:
        import dns.resolver
        ok = bool(dns.resolver.resolve(domain, 'MX', lifetime=5))
    except Exception:
        try:
            import httpx
            j = httpx.get('https://dns.google/resolve', params={'name': domain, 'type': 'MX'}, timeout=10).json()
            ok = any(a.get('type') == 15 for a in j.get('Answer', []))
        except Exception: ok = False
    _mx[domain] = ok; return ok

# ---------- tiers ----------
TIER_A = {'scraped', 'chrome_ok', 'college_site', 'confirmed', 'search_high'}
TIER_D = {'search_medium', 'search_low'}

def tier(row):
    if not row.get('email'): return ''
    s = row.get('status', '')
    if s in TIER_A: return 'A'
    if s == 'inferred_confirmed': return 'B'
    if s == 'inferred_single': return 'C'
    if s in TIER_D: return 'D'
    return 'D'
