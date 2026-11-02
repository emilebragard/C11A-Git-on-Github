"""Steps 2-3: detect each site's platform, then scrape head coach name + email.

Usage:  python scripts/scrape.py <run_id>          e.g. ncaa-d1-mens-water-polo

Only fetches sites that allow it (robots.txt), ~1 request/second per site,
everything cached in cache/pages. Sites that return 403 (blocked) are marked
status=blocked so the Chrome step picks them up.
"""
import sys
from urllib.parse import urljoin
from common import *

PLATFORMS = [('sidearm', r'sidearm'), ('presto', r'prestosports|presto-sport|/landing/index'),
             ('wmt', r'wmt\.digital'), ('wordpress', r'wp-content'), ('drupal', r'drupal')]

def fingerprint(s):
    url = s.get('athletics_url')
    if not url: return 'no_url'
    h = fetch(url, min_len=500)
    if not h: return 'blocked' if is_blocked_host(url) else 'unreachable'
    return next((n for n, p in PLATFORMS if re.search(p, h, re.I)), 'other')

def candidates(base, home, sp):
    root = '{0.scheme}://{0.netloc}'.format(urlparse(base))
    slug, code = sp['sidearm_slug'], sp['presto_code']
    urls = [f'{root}/sports/{slug}/coaches', f'{root}/sports/{code}/coaches/index', f'{root}/sports/{code}/coaches']
    y = int(TODAY[:4]); m = int(TODAY[5:7]); start = y if m >= 7 else y - 1
    urls += [f'{root}/sports/{code}/{start}-{str(start + 1)[2:]}/coaches']
    if home:
        t = html(home); kw = sp['keywords']
        for a in t.css('a[href]'):
            h, txt = a.attributes.get('href') or '', a.text(strip=True)
            if re.search(r'coach|staff', h + txt, re.I) and re.search(kw, h + ' ' + txt, re.I): urls.append(urljoin(base, h))
        for a in t.css('a[href]'):
            h, txt = a.attributes.get('href') or '', a.text(strip=True)
            if re.search(kw, txt, re.I): urls.append(urljoin(base, h))  # the sport's own page
    urls += [f'{root}/staff-directory', f'{root}/information/directory/index']
    return list(dict.fromkeys(u for u in urls if u.startswith('http')))

def extract(page, sp, known_name=''):
    """Return (name, title, email) for the head coach on a coaches/staff page, or None."""
    t = html(page); kw = sp['keywords']
    other_kw = None
    sports_all = sports()
    for k, o in sports_all.items():  # the opposite-gender version of this sport, to filter it out
        if k != sp['sport_key'] and o['sidearm_slug'].replace('womens-', '').replace('mens-', '') == \
           sp['sidearm_slug'].replace('womens-', '').replace('mens-', ''): other_kw = o['keywords']
    best = None
    for node in t.css('tr, li, article, .sidearm-coaches-coach, .s-person-card, .staff-member, div.card, div.coach'):
        text = ' '.join(node.text(separator=' ').split())
        if len(text) > 500 or not re.search(r'coach', text, re.I): continue
        if other_kw and re.search(other_kw, text, re.I) and not re.search(kw, text, re.I): continue
        mail = node.css_first('a[href^="mailto:"]')
        email = mail.attributes['href'][7:].split('?')[0].strip().lower().strip('/. ') if mail else \
                (EMAIL_RE.search(text).group(0).lower() if EMAIL_RE.search(text) else '')
        is_head = re.search(r'\bhead\b(?![^.]{0,25}assistant)', text, re.I) and not re.search(r'assistant head|associate head', text, re.I)
        if known_name:
            f, l = name_parts(known_name)
            if l and l in text.lower():
                return (known_name, 'Head Coach', email)
            continue
        if not is_head: continue
        nm_el = node.css_first('h3, h4, .sidearm-coaches-coach-name, .s-person-details__personal-single-line, th a, td a, a')
        name = nm_el.text(strip=True) if nm_el else ''
        if not name or '@' in name or re.search(r'coach', name, re.I):
            m = re.search(r"([A-Z][a-zA-Z'\-]+(?: [A-Z]\.)? [A-Z][a-zA-Z'\-]+)", text); name = m.group(1) if m else ''
        if name and (not best or (email and not best[2])): best = (name, 'Head Coach', email)
    return best

def main():
    rid = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
    assoc, div, sport = parse_run_id(rid); sp = sports()[sport]
    schools = load_schools(); coaches = load_coaches()
    rows = [r for r in coaches if r['run_id'] == rid]
    for r in rows:
        s = schools.get((assoc, r['school']), {})
        if not s.get('platform') or s['platform'] in ('unreachable',):
            s['platform'] = fingerprint(s); s['checked'] = TODAY
    save_schools(schools)
    found = blocked = 0
    for i, r in enumerate(rows):
        if r['email'] and r['status'] not in ('pending', 'name_only'): continue
        s = schools.get((assoc, r['school']), {})
        if s.get('platform') in ('blocked', 'no_url', 'unreachable'):
            if s['platform'] == 'blocked': r['status'] = 'blocked'; blocked += 1
            elif r['status'] == 'pending': r['status'] = 'not_found'
            continue
        home = fetch(s['athletics_url'], min_len=500)
        hit, src = None, ''
        for u in candidates(s['athletics_url'], home, sp)[:10]:
            pg = fetch(u)
            if pg and (hit := extract(pg, sp, r['name'])): src = u; break
        if hit:
            name, title, email = hit
            r.update(name=r['name'] or name, title=r['title'] or title, source_url=src, last_checked=TODAY)
            if email and EMAIL_RE.fullmatch(email):
                r['email'], r['email_source'], r['status'] = email, 'scraped', 'scraped'; found += 1
            else: r['status'] = 'name_only'
        elif r['status'] == 'pending': r['status'] = 'not_found'
        if (i + 1) % 25 == 0: print(f'  ...{i + 1}/{len(rows)}')
    for r in rows: r['tier'] = tier(r)
    save_coaches(coaches)
    from collections import Counter
    print(f'{rid}: {found} emails scraped, {blocked} blocked sites. Status:', dict(Counter(r["status"] for r in rows)))
    print('platforms:', dict(Counter(schools.get((assoc, r["school"]), {}).get("platform", "?") for r in rows)))

if __name__ == '__main__':
    main()
