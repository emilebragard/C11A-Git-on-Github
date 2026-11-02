"""Fetch each school's athletics homepage once, cache it, tag the platform.
Prints a platform count summary only."""
import csv, hashlib, pathlib, re, sys, time, httpx
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
CACHE = pathlib.Path('cache/home'); CACHE.mkdir(parents=True, exist_ok=True)
MARKERS = [
  ('sidearm', r'sidearm'), ('presto', r'prestosports|presto-sport'),
  ('wmt', r'wmt\.digital|wmt-'), ('ardor', r'ardorsportshub'),
  ('streamline', r'streamlinetechnologies|landing/index'),
  ('wordpress', r'wp-content'), ('drupal', r'drupal'),
]
def fetch(r):
    url = r['athletics_url']
    if not url: return r, '', 0, 'no_url'
    f = CACHE / (hashlib.md5(url.encode()).hexdigest() + '.html')
    if not f.exists():
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=20,
                             headers={'User-Agent': 'Mozilla/5.0 (research; coach directory)'})
            f.write_text(resp.text); r['final_url'] = str(resp.url)
            time.sleep(0.5)
        except Exception as e:
            return r, '', 0, 'error:' + type(e).__name__
    html = f.read_text(errors='ignore')
    plat = next((n for n, p in MARKERS if re.search(p, html, re.I)), 'other')
    if len(html) < 2000: plat += '_tiny'
    return r, str(f), len(html), plat
rows = list(csv.DictReader(open('data/schools.csv')))
with ThreadPoolExecutor(8) as ex: res = list(ex.map(fetch, rows))
for r, f, n, plat in res: r['platform'] = plat; r['home_cache'] = f; r.setdefault('final_url', '')
w = csv.DictWriter(open('data/schools.csv', 'w'), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
c = Counter(r['platform'] for r in rows); print(c.most_common())
print('errors:', [(r['school'], r['platform']) for r in rows if r['platform'].startswith('error')][:8])
