# Project rules: NJCAA D2 basketball coach scraper

## Budget (hard rules)
- Hard cap: $95 total cloud/Claude credits. Target: $35-45.
- Phase budgets (target / stop-and-ask limit):
  1. School list: $3-5 / $8
  2. Platform fingerprint: $3-5 / $8
  3. Pilot (10 schools, 2-3 parsers): $8-12 / $20
  4. Full scripted run: $1-3 / $5
  5. AI fallback on failures only: $3-8 / $15
  6. Email inference + QA: $3-5 / $10
- After each phase, report estimated spend and pause if over the stop limit.

## Token discipline
- Never print raw HTML into context. Scripts save HTML to `cache/` and print summaries only.
- Debug with `grep -m5 -C2`, never `cat` on HTML.
- Cap all script output (counts + first 5 failures).
- One session; no subagents. Exception (approved by user): Haiku helpers may run web-search batches for PrestoSports-blocked schools, hard stop at $15 for that pass.
- Cache every HTTP response; reruns must hit cache.

## Tooling limits
- No Firecrawl, ZeroBounce/NeverBounce, browser agents, or computer use.
- Playwright only if the pilot shows JS-only sites are common, and only for those.
- AI extraction: trimmed text (<2k tokens/page). <=30 failures: read in-session; more: Haiku Batch API.
- Email validation: free DNS MX checks; mark inferred emails `email_source=inferred`.

## Scope
- NJCAA Division II men's and women's basketball, head coaches first; assistants only if budget allows.
- Sport is a parameter, not hardcoded.
- Scrape politely: 1-2 req/s per domain, respect robots.txt.

## Output
`data/coaches.csv`: school, sport, name, title, email, email_source, phone, url, status
