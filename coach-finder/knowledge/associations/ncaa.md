# NCAA (Divisions I, II, III)

**Best source: the official NCAA Directory.** It's free and public, and it gives every team **plus the current head coach's name** and the school's websites. Scripts read it fine (`scripts/list_teams.py NCAA D1 <sport>`). Verified 2026-11-02.

| What | Where |
|---|---|
| Every school sponsoring a sport | `https://web3.ncaa.org/directory/memberList?type=12&sportCode=<ncaa_code>&division=I` (or `II`, `III`) |
| One school's page | `https://web3.ncaa.org/directory/orgDetail?id=<id>` |
| Sport codes | `ncaa_code` column in `knowledge/sports.csv` (e.g. MBB, WSO, MWP, WSV = beach volleyball, WBW = bowling) |

**On each school's page:**
- The "Sponsored Sports" table lists sport, **head coach**, division, and conference for the current academic year.
- External links: the first is usually the college website (that gives the **email domain**, e.g. brown.edu), the second the athletics website.

**Quirks:**
- The directory uses its own sport names (e.g. "Men's Track, Outdoor"). The script reads the name from the page heading, so this is handled.
- The list table shows 10 rows per page by default; the script switches to 100 and pages through.
- Websites are often listed as `http://`. Scripts upgrade to `https://`.
- **Don't use stats.ncaa.org:** it blocks scripts (403).
- D1 has roughly 30-365 teams per sport. A full D1 sport costs mostly time, not money.

**Where emails come from:** D1 athletics sites are mostly Sidearm (see `platforms/sidearm.md`). Their staff directories usually show emails. Many block cloud servers but load fine from home or office internet, and always load in Chrome.

**Conferences** (for gap-filling): the conference column links to the conference's directory page, which links to the conference website. Conference sites rarely list coach emails.
