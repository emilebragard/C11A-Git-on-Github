"""Pilot: find basketball coach pages on open sites and extract coaches.
Generic strategy: candidate URLs (platform paths + homepage links), then
parse mailto links / staff table rows. Prints summary only."""
import csv, hashlib, pathlib, re, sys, time, urllib.robotparser as rp
from urllib.parse import urljoin, urlparse
import httpx
from selectolax.lexbor import LexborHTMLParser as H

CACHE = pathlib.Path('cache/pages'); CACHE.mkdir(parents=True, exist_ok=True)
UA = 'Mozilla/5.0 (research; coach directory)'
SPORTS = {'mbkb': ('mens-basketball', r"\bmen'?s basketball|\bmbb\b|mbkb"),
          'wbkb': ('womens-basketball', r"women'?s basketball|\bwbb\b|wbkb")}
client = httpx.Client(follow_redirects=True, timeout=20, headers={'User-Agent': UA})
robots = {}

def allowed(url):
    host = urlparse(url).scheme + '://' + urlparse(url).netloc
    if host not in robots:
        r = rp.RobotFileParser(host + '/robots.txt')
        try: r.read()
        except Exception: r = None
        robots[host] = r
    return robots[host] is None or robots[host].can_fetch(UA, url)

def get(url):
    f = CACHE / (hashlib.md5(url.encode()).hexdigest() + '.html')
    if f.exists(): return f.read_text(errors='ignore') or None
    if not allowed(url): f.write_text(''); return None
    try:
        r = client.get(url); time.sleep(0.6)
        txt = r.text if r.status_code == 200 and len(r.text) > 2000 else ''
    except Exception: txt = ''
    f.write_text(txt); return txt or None

PHONE = re.compile(r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}')
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+')
TITLE = re.compile(r'(head|assistant|associate)?\s*(men\'?s|women\'?s)?\s*(basketball)?\s*coach', re.I)

def extract(html, sport):
    """Return coach dicts from a coaches/staff page."""
    t = H(html); out = []
    sp_re = SPORTS[sport][1]
    # rows: table rows or list items or cards that contain a coach title
    for node in t.css('tr, li, .sidearm-coaches-coach, .s-person-card, article, .staff-member, div.card'):
        text = ' '.join(node.text(separator=' ').split())
        if len(text) > 400 or not re.search(r'coach', text, re.I): continue
        mail = node.css_first('a[href^="mailto:"]')
        email = mail.attributes['href'][7:].split('?')[0].strip() if mail else (EMAIL.search(text).group(0) if EMAIL.search(text) else '')
        m = re.search(r"((?:head|assistant|associate|interim)\b(?:[\s\-–—]+(?:men'?s|women'?s|basketball|coach|of))*)", text, re.I)
        if m and not re.search('coach', m.group(1), re.I): m = None
        if not m: continue
        title = m.group(1).strip()
        name_el = node.css_first('h3, h4, .sidearm-coaches-coach-name, .s-person-details__personal-single-line, th a, td a, a')
        name = name_el.text(strip=True) if name_el else ''
        if not name or '@' in name or re.search(r'coach', name, re.I): name = text[:m.start()].strip()[:40]
        out.append({'name': name, 'title': title, 'email': email.lower().strip('/. '), 'phone': (PHONE.search(text).group(0) if PHONE.search(text) else ''), 'context': text})
    # keep only basketball-relevant rows on mixed staff directories
    if any(re.search(sp_re, c['context'], re.I) for c in out):
        other = SPORTS['wbkb' if sport == 'mbkb' else 'mbkb'][1]
        out = [c for c in out if re.search(sp_re, c['context'] + c['title'], re.I)
               and not (re.search(other, c['title'], re.I))]
    seen, uniq = set(), []
    for c in out:
        k = (c['name'], c['title'])
        if k not in seen: seen.add(k); uniq.append(c)
    return uniq

def candidates(base, home_html, sport):
    slug, sp_re = SPORTS[sport]
    root = urlparse(base).scheme + '://' + urlparse(base).netloc
    code = sport  # PrestoSports uses mbkb/wbkb codes with season folders
    urls = [f'{root}/sports/{slug}/coaches', f'{root}/sports/{code}/coaches',
            f'{root}/sports/{code}/2025-26/coaches', f'{root}/sports/{code}/2026-27/coaches']
    if home_html:
        for a in H(home_html).css('a[href]'):
            h, txt = a.attributes['href'], a.text(strip=True)
            if re.search(r'coach|staff', h + txt, re.I) and re.search(sp_re + r'|bkb|basketball', h + txt, re.I):
                urls.append(urljoin(base, h))
        for a in H(home_html).css('a[href]'):
            if re.search(r'staff.?directory', a.attributes['href'] + a.text(strip=True), re.I):
                urls.append(urljoin(base, a.attributes['href']))
    urls.append(f'{root}/staff-directory')
    return list(dict.fromkeys(urls))

def run(rows, sport):
    results = []
    for r in rows:
        if not r[sport + '_id']: continue
        base = r['final_url'] or r['athletics_url']
        home = open(r['home_cache']).read() if r['home_cache'] else ''
        found, src = [], ''
        tried = 0
        for u in candidates(base, home, sport)[:8]:
            html = get(u); tried += 1
            if html and (found := extract(html, sport)): src = u; break
        if not found and home:  # second hop: sport page -> its coach/staff link
            sp = next((urljoin(base, a.attributes['href']) for a in H(home).css('a[href]')
                       if re.search(SPORTS[sport][1], a.text(strip=True), re.I)), None)
            page = get(sp) if sp else None
            if page:
                found = extract(page, sport); src = sp if found else ''
                for u in ([] if found else candidates(sp, page, sport)[4:8]):
                    html = get(u)
                    if html and (found := extract(html, sport)): src = u; break
        results.append((r, found, src))
    return results

if __name__ == '__main__':
    plats = sys.argv[1].split(',')
    rows = [r for r in csv.DictReader(open('data/schools.csv')) if r['platform'] in plats]
    allrows = []
    for sport in SPORTS:
        res = run(rows, sport)
        for r, found, src in res:
            head = [c for c in found if re.search(r'head', c['title'], re.I)]
            status = 'ok' if head and head[0]['email'] else 'no_email' if head else 'needs_review'
            for c in (found or [{'name': '', 'title': '', 'email': ''}]):
                allrows.append({'school': r['school'], 'sport': sport, 'name': c['name'], 'title': c['title'],
                                'email': c['email'], 'email_source': 'scraped' if c['email'] else '', 'phone': c.get('phone', ''),
                                'url': src, 'status': status, 'platform': r['platform']})
    out = 'data/coaches_pilot.csv'
    w = csv.DictWriter(open(out, 'w'), fieldnames=list(allrows[0])); w.writeheader(); w.writerows(allrows)
    from collections import Counter
    st = Counter((x['school'], x['sport'], x['status']) for x in allrows)
    print('team status:', Counter(k[2] for k in st))
    by = Counter((x['platform'], x['status']) for x in {(a['school'], a['sport']): a for a in allrows}.values())
    print('by platform:', sorted(by.items()))
