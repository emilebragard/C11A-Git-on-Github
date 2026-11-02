"""Phase 5: for teams the parser missed, gather trimmed text snippets
(<~600 chars per team) around basketball coach mentions for manual/AI review."""
import csv, re, sys, json
from urllib.parse import urljoin, urlparse
sys.path.insert(0, 'scraper')
from coaches import get, candidates, SPORTS, H

pilot = list(csv.DictReader(open('data/coaches_pilot.csv')))
failed = {(r['school'], r['sport']) for r in pilot if r['status'] == 'needs_review'}
schools = {r['school']: r for r in csv.DictReader(open('data/schools.csv'))}
out = {}
for school, sport in sorted(failed):
    r = schools[school]; base = r['final_url'] or r['athletics_url']
    home = open(r['home_cache']).read() if r['home_cache'] else ''
    pages = candidates(base, home, sport)[:8]
    # basketball page links (either gender) and their coach/staff/roster links
    for a in H(home).css('a[href]') if home else []:
        if re.search(r'basketball', a.text(strip=True) + a.attributes['href'], re.I):
            pages.append(urljoin(base, a.attributes['href']))
    pages = list(dict.fromkeys(pages))[:12]
    for u in list(pages):
        html = get(u) if urlparse(u).netloc.endswith(urlparse(base).netloc.split('.', 1)[-1]) else None
        if not html: continue
        for a in H(html).css('a[href]'):
            if re.search(r'coach|staff|roster|directory', a.text(strip=True) + a.attributes['href'], re.I) \
               and re.search(r'basketball|athlet', a.attributes['href'] + a.text(strip=True), re.I):
                pages.append(urljoin(u, a.attributes['href']))
    snips = []
    for u in list(dict.fromkeys(pages))[:20]:
        html = get(u)
        if not html: continue
        t = H(html)
        for n in t.css('script, style, nav, header, footer'): n.decompose()
        txt = ' '.join(t.body.text(separator=' ').split()) if t.body else ''
        mails = ' '.join(a.attributes['href'][7:] for a in t.css('a[href^="mailto:"]'))
        for m in re.finditer(r'basketball', txt, re.I):
            w = txt[max(0, m.start() - 150): m.end() + 150]
            if re.search(r'coach', w, re.I) and w not in snips:
                snips.append(f'[{u}] {w}')
        if mails and any('coach' in s.lower() for s in snips):
            snips.append(f'[{u}] MAILTO: {mails[:300]}')
    out[f'{school}|{sport}'] = snips[:4]
json.dump(out, open('data/fallback_snippets.json', 'w'), indent=1)
print('teams', len(out), 'with snippets', sum(1 for v in out.values() if v))
