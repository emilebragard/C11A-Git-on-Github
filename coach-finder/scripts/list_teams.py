"""Step 1: list every team for one association / division / sport.

Usage:  python scripts/list_teams.py NCAA D1 mens-water-polo
        python scripts/list_teams.py NJCAA D2 mens-basketball
        python scripts/list_teams.py NAIA ALL womens-soccer   (prints manual instructions)

Writes data/runs/<run_id>/teams.csv and adds new schools to data/schools.csv.
Creates a placeholder row per team in data/coaches.csv (status=pending), so
coverage is measurable from the start. Head coach names from the NCAA
directory are stored right away (status=name_only).
"""
import re, sys, json
from playwright.sync_api import sync_playwright
from common import *

DIV_NUM = {'D1': 'I', 'D2': 'II', 'D3': 'III'}

def ncaa(div, sp, pg):
    code = sp['ncaa_code']
    if not code: sys.exit(f"No NCAA code for {sp['sport_key']} in knowledge/sports.csv")
    pg.goto(f'https://web3.ncaa.org/directory/memberList?type=12&sportCode={code}&division={DIV_NUM[div]}',
            wait_until='networkidle', timeout=60000)
    pg.wait_for_timeout(1500)
    head = re.search(r'Division I+ (.+?) Institutions', pg.inner_text('body'))
    ncaa_label = head.group(1).strip() if head else sp['label']  # the directory's own sport name
    sel = pg.locator('select[name$="_length"]')
    if sel.count(): sel.first.select_option('100')  # show 100 rows per page
    teams = []
    while True:
        pg.wait_for_timeout(800)
        rows = pg.eval_on_selector_all('table tbody tr', """trs => trs.map(tr => {
            const a = tr.querySelector('a[href*="orgDetail"]'); const td = tr.querySelectorAll('td');
            return a ? [a.innerText.trim(), a.getAttribute('href'), td[1] ? td[1].innerText.trim() : ''] : null }).filter(Boolean)""")
        teams += rows
        nxt = pg.locator('a.paginate_button.next:not(.disabled), li.next:not(.disabled) a')
        if not nxt.count(): break
        before = rows[0][0] if rows else ''
        nxt.first.click(); pg.wait_for_timeout(800)
        first = pg.eval_on_selector('table tbody tr a[href*="orgDetail"]', 'a => a.innerText.trim()')
        if first == before: break
    out = []
    for name, href, conf in teams:
        oid = re.search(r'id=(\d+)', href).group(1)
        pg.goto(f'https://web3.ncaa.org/directory/orgDetail?id={oid}', wait_until='networkidle', timeout=60000)
        pg.wait_for_timeout(700)
        links = pg.eval_on_selector_all('a', 'as => as.map(a => a.href)')
        ext = [l for l in links if not re.search(r'ncaa\.org|amazonaws|facebook|twitter|instagram|youtube|tiktok|linkedin|x\.com', l)]
        # first external link is usually the college, second the athletics site
        athletics = ext[1] if len(ext) > 1 else (ext[0] if ext else '')
        college = ext[0] if ext else ''
        # "Sponsored Sports" table: one row per sport -> [sport, head coach, division, conference]
        rows = pg.eval_on_selector_all('table tr', "trs => trs.map(tr => [...tr.querySelectorAll('td')].map(td => td.innerText.trim()))")
        coach = next((r[1] for r in rows if len(r) > 1 and r[0].lower() == ncaa_label.lower()), '')
        out.append({'school': name, 'school_id': oid, 'conference': conf, 'athletics_url': athletics,
                    'college_url': college, 'head_coach_listed': coach})
        print(f'  {len(out)}/{len(teams)} {name[:40]} | coach: {coach or "-"}')
    return out

def njcaa(div, sp, pg):
    code = sp['njcaa_code']
    if not code: sys.exit(f"NJCAA has no {sp['label']} (no njcaa_code in knowledge/sports.csv)")
    pg.goto(f'https://www.njcaa.org/sports/{code}/teams', wait_until='networkidle', timeout=60000)
    label = {'D1': 'Division I', 'D2': 'Division II', 'D3': 'Division III'}[div]
    pg.locator('select', has=pg.locator('option', has_text=label)).first.select_option(label=label)
    pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(2000)
    reg = pg.locator('select[aria-label="Region"]')
    regions = [r for r in reg.locator('option').all_inner_texts() if r != 'All regions']
    teams = {}
    for r in regions:
        reg.select_option(label=r); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1500)
        for name, href in pg.eval_on_selector_all('.sports-team-directory a[href*="/statistics?"]',
                "as => as.filter(a => a.innerText.trim() !== 'Stats').map(a => [a.innerText.trim(), a.getAttribute('href')])"):
            tid = re.search(r'teams/(\d+)', href).group(1)
            teams.setdefault(tid, {'school': name, 'school_id': tid, 'conference': r})
    # athletics websites come from the NJCAA member directory (cached for 30 days)
    mfile = DATA / 'njcaa_members.json'
    if not mfile.exists() or time.time() - mfile.stat().st_mtime > 30 * 86400:
        pg.goto('https://www.njcaa.org/member_colleges/directory/members', wait_until='networkidle')
        for _ in range(30):
            btn = pg.get_by_role('button', name='Load more schools')
            if not btn.count(): break
            btn.click(); pg.wait_for_timeout(1200)
        members = pg.eval_on_selector_all('a', """as => as.filter(a => /ATHLETICS WEBSITE/i.test(a.innerText)).map(a => {
            let e = a; for (let i = 0; i < 6 && e; i++) { e = e.parentElement;
              const t = e.innerText.replace(/VISIT ATHLETICS WEBSITE\\s*↗?/gi, '').trim(); if (t.length > 3) return [t.split('\\n')[0], a.href]; }
            return ['', a.href]; })""")
        mfile.write_text(json.dumps(members))
    norm = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s.upper().replace('&', 'AND')).split())
    import difflib
    members = {norm(n): u for n, u in json.loads(mfile.read_text())}
    out = []
    for t in teams.values():
        k = norm(t['school']); hit = k if k in members else (difflib.get_close_matches(k, members, 1, 0.85) or [None])[0]
        out.append(t | {'athletics_url': members.get(hit, '') if hit else '', 'college_url': '', 'head_coach_listed': ''})
    return out

def main():
    if len(sys.argv) != 4: sys.exit(__doc__)
    assoc, div, sport = sys.argv[1].upper(), sys.argv[2].upper(), sys.argv[3]
    sp = sports().get(sport) or sys.exit(f'Unknown sport "{sport}". See knowledge/sports.csv for sport_key values.')
    rid = run_id(assoc, div, sport); rd = run_dir(rid)
    if assoc == 'NAIA':
        tpl = rd / 'teams.csv'
        if not tpl.exists():
            write_csv(tpl, [], ['school', 'school_id', 'conference', 'athletics_url', 'college_url', 'head_coach_listed'])
        sys.exit(f'NAIA has no scriptable team list. Fill {tpl} using knowledge/associations/naia.md '
                 '(Claude in Chrome works well for this), then rerun this command.')
    with sync_playwright() as p:
        b = browser(p); pg = b.new_page()
        teams = (ncaa if assoc == 'NCAA' else njcaa)(div, sp, pg)
        b.close()
    write_csv(rd / 'teams.csv', teams, ['school', 'school_id', 'conference', 'athletics_url', 'college_url', 'head_coach_listed'])
    finish(assoc, div, sport, rid, teams)

def finish(assoc, div, sport, rid, teams):
    schools = load_schools()
    for t in teams:
        s = schools.setdefault((assoc, t['school']), {'association': assoc, 'school': t['school']})
        s['school_id'] = s.get('school_id') or t.get('school_id', '')
        if t.get('athletics_url') and not s.get('athletics_url'): s['athletics_url'] = t['athletics_url']
        cu = t.get('college_url', '')
        if cu and not s.get('email_domain'):
            s['email_domain'] = re.sub(r'^www\.', '', urlparse(cu).netloc)
    save_schools(schools)
    coaches = load_coaches(); have = {(r['run_id'], r['school']) for r in coaches}
    for t in teams:
        if (rid, t['school']) in have: continue
        nm = t.get('head_coach_listed', '')
        coaches.append({'run_id': rid, 'association': assoc, 'division': div, 'sport': sport, 'school': t['school'],
                        'name': nm, 'title': 'Head Coach' if nm else '', 'status': 'name_only' if nm else 'pending',
                        'source_url': 'NCAA directory' if nm else '', 'last_checked': TODAY})
    save_coaches(coaches)
    no_url = [t['school'] for t in teams if not t.get('athletics_url')]
    print(f'{rid}: {len(teams)} teams, {sum(1 for t in teams if t.get("head_coach_listed"))} with coach names, '
          f'{len(no_url)} without athletics URL {no_url[:5]}')

if __name__ == '__main__':
    main()
