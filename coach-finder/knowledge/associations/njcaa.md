# NJCAA (junior colleges: Divisions I, II, III)

**Sources** (njcaa.org is a JavaScript app, so scripts use Playwright, a scripted browser):

| What | Where |
|---|---|
| Teams per sport | `https://www.njcaa.org/sports/<njcaa_code>/teams`. Pick the Division dropdown, then loop the **Region** dropdown (only one region shows at a time) |
| Athletics websites | `https://www.njcaa.org/member_colleges/directory/members`. Click "Load more schools" until gone; each card has "Visit athletics website" (~505 schools). Cached in `data/njcaa_members.json` for 30 days |
| Region directors (name + email) | `https://www.njcaa.org/about/region_directors`, with each director's email on their bio page |
| Sport codes | `njcaa_code` in `knowledge/sports.csv` (e.g. mbkb, wsoc, wvball, mswimdive, beachvball) |

**Quirks:**
- The NJCAA has **no coach names** in its directories. Names and emails come from athletics sites.
- About 7 schools per sport aren't in the member directory under the same name (e.g. "CCBC Catonsville", "Johnson County"). Add their URLs to `data/schools.csv` by hand, or find them in Chrome.
- **~70% of NJCAA athletics sites are PrestoSports** (`/landing/index` URLs). They block cloud servers and often block scripts, so plan on the Chrome pass doing most of the work. See `platforms/prestosports.md`.
- Region and conference sites (also PrestoSports) don't publish coach directories.
- NJCAA has no water polo, ice hockey, or field hockey.

**Gap-filling:** region directors will often share coach lists for their region. Email them (names above) for the last stubborn schools.

**History:** D2 men's and women's basketball (Nov 2026) reached 88% and 85% with an email, using scripts, then web search, then format inference, then verification. The Chrome pass wasn't available then; it should push this higher.
