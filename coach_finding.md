# Coach Finding: Fast, Unattended, Code-Based

How to build a college coach contact list (name + email) for any NJCAA division and sport, using the **Claude desktop app's Code tab** on your own computer.

This replaces the "ChatGPT in a browser tab" approach. That approach is slow because it does one page at a time, stops when you walk away, and keeps no files or code. Here, Claude writes small scripts that do about 90% of the work on their own, and AI only handles the leftovers.

> **Use the Code tab, not the Chat tab.** Chat can't run scripts on your computer, keep files between steps, or launch helper agents, which is the same limit as ChatGPT in a browser. The Code tab can do all three, and no terminal is needed.

---

## 1. Why this is faster

| Old way (chat in a browser) | This way |
|---|---|
| AI reads every school site one at a time | A script fetches 150+ sites in minutes with **no AI cost** |
| Stops when you close the tab or step away | Keeps running while you're away (computer awake) |
| Results live in chat; you copy and paste | Results land in a CSV, saved and resumable |
| Starts from scratch every time | Rerun for a new sport by changing one setting |
| One AI does everything | Cheap helper AIs (Haiku) run searches in parallel, only on gaps |

**Reference result (D2 men's + women's basketball):** 305 teams, **264 with a head coach email (87%)**, about $20 of AI usage, a few hours mostly unattended.

---

## 2. One-time setup (about 10 min)

**What you need:**
1. **The Claude desktop app** (claude.ai/download).
2. **Python 3.11 or newer.** This is the only other install.
   - **Mac:** download it from python.org, or run `brew install python` if you have Homebrew.
   - **Windows:** download it from python.org and **tick "Add Python to PATH"** during install.
   - Not sure if you have it? In the Code tab, ask Claude "Is Python 3 installed?" and it will check.

You don't need Git, Node.js, or anything else. Claude installs the Python libraries it needs (httpx, selectolax, playwright) the first time.

**Then:**
1. Make an empty folder, e.g. `Documents/coach-finder`.
2. Save this file (`coach_finding.md`) into it.
3. In the desktop app, open the **Code** tab and choose that folder.
4. **Allow common commands** so Claude doesn't stop and wait for you to click "approve" while you're away. Type `/permissions` and allow `Bash(python *)`, `Bash(python3 *)`, and `Bash(pip *)`, or turn on auto mode. **This is the #1 reason things stall when you're away.**
5. **Keep the computer awake during long runs:**
   - **Mac:** System Settings → Lock Screen → never turn off display while on power, or run `caffeinate -i`.
   - **Windows:** Settings → Power → Screen and sleep → Never (while plugged in).

---

## 3. First prompt: have Claude build it

Paste this into the Code tab:

> Read coach_finding.md in this folder. Create a CLAUDE.md with the rules from its section 7, then build the scripts described in section 5 in Python, in a `scraper/` folder. Install the Python libraries you need, and the Playwright Chromium browser. Then run the pipeline for NJCAA Division [II] [men's and women's basketball]. Pilot on 10 schools first and report the parse rate before the full run. Only create or change files inside this folder. Stop and tell me if estimated spend passes $40.

Claude writes the scripts, tests them, and runs them. Next time (a new sport, or next season), the scripts already exist, so just say: "Read coach_finding.md and rerun the pipeline for [sport]."

---

## 4. Check first: is PrestoSports blocked for you?

About 70% of NJCAA athletics sites run on **PrestoSports**, which blocks traffic from cloud servers. **From a home or office internet connection, the sites usually load normally,** which makes everything easier. Ask Claude to run this check early:

> Fetch https://cgccathletics.com/landing/index with Python and tell me the HTTP status code.

- **`200`:** you're not blocked. Claude can scrape PrestoSports coach pages directly. That's faster, more current, and free compared with web search.
- **`403`:** you're blocked. Use the web-search helpers (step 8 in section 5), or Claude in Chrome in your own browser.

> Don't disguise the scraper as a browser or use proxy services to get around a block. If a site blocks you, switch to search or Chrome.

---

## 5. The pipeline (build spec for Claude)

Each script should save results to `data/`, cache every downloaded page in `cache/` (so a rerun or crash never re-downloads), and print a short summary only.

| # | Script | What it does | AI? |
|---|---|---|---|
| 1 | `njcaa_teams.py <sport_code>` | Gets every team for the sport and division from njcaa.org | No |
| 2 | `njcaa_members.py` | Gets every member college's athletics website URL | No |
| 3 | `build_schools.py` | Merges 1 and 2 into `data/schools.csv` (school, region, teams, athletics_url) | No |
| 4 | `fingerprint.py` | Fetches each athletics homepage once and tags the platform | No |
| 5 | `coaches.py` | Scrapes each team's coaches page and extracts name, title, and email | No |
| 6 | `fallback_snippets.py` | For pages the parser missed, saves ~600 characters of text around "coach" for Claude to read | Claude reads short text |
| 7 | `finalize.py` | Merges everything, builds missing emails from the school's format, checks email domains | No |
| 8 | Search helpers | Haiku helpers web-search teams that are blocked or still missing an email | Haiku |
| 9 | `college_dirs.py` | Checks the main college website (e.g. school.edu) staff directory for coach emails and email formats | No |
| 10 | Verify helpers | Haiku helpers check that uncertain coaches are still the current coach | Haiku |
| 11 | `export.py` | Writes the clean deliverable `data/coaches.csv` | No |

### What Claude needs to know about the sources

- **njcaa.org is a JavaScript app.** Plain downloads return an empty page, so steps 1-2 need Playwright (a scripted browser).
  - **Team directory:** `https://www.njcaa.org/sports/<code>/teams`. It has dropdowns for Division and Region, and only one region shows at a time, so select the division, then loop through every region.
  - **Sport codes** (from the URL): `mbkb` men's basketball, `wbkb` women's basketball, `bsb` baseball, `sball` softball, and so on.
  - **Member directory:** `https://www.njcaa.org/member_colleges/directory/members`. Click "Load more schools" until it's gone; each card has a "Visit athletics website" link.
  - **Region directors** (name + email on each bio page): `https://www.njcaa.org/about/region_directors`.
- **Athletics site platforms and where coaches live:**
  - **Sidearm:** `/sports/mens-basketball/coaches`. Clean tables with email links; parses about 90% of the time.
  - **PrestoSports:** `/sports/mbkb/coaches/index`, or the season folder `/sports/mbkb/2025-26/coaches`. Also `/information/directory/index`.
  - **Plain college sites:** follow homepage links containing "basketball", then "coach" or "staff". Coaches are often listed on the team page itself.
- **Parser gotchas from the last run:**
  - "Women's basketball" contains "men's basketball". Use word boundaries (`\bmen`).
  - Strip trailing junk from titles and emails.
  - Mixed staff directories list both teams, so filter by sport.
- **Email formats:** learn each school's format from known staff emails (first.last, flast, lastf, firstl, f.last). Only build an email from a format seen in **2+ examples**. Skip formats with numbers (adobbs1@).
- **Domain check:** look up the domain's mail (MX) record. Plain DNS lookups work on a normal computer; DNS-over-HTTPS (`https://dns.google/resolve`) also works.

### Search helper instructions (steps 8 and 10)

Ask Claude to launch **Haiku subagents**, **3 at a time maximum**. More than that hits the web-search rate limit and they come back half empty. Each helper:
- gets a text file of ~15-30 schools and writes a CSV
- runs searches **one at a time**; on a rate-limit error, waits 30 seconds and retries
- uses up to 3 searches per school, e.g. "<School> basketball head coach email", "<School> staff directory", "\"Coach Name\" \"@school.edu\"", "<School> named head basketball coach"
- records **only emails a source explicitly shows, never guessed ones**, plus 2-3 other staff emails at the school so the format can be learned
- rates each result: high (current school page), medium (this season's source), low (older or conflicting)

---

## 6. Output

`data/coaches.csv`, with columns school, sport, role, name, title, email, email_source, tier, dept_contact.

| Tier | Meaning | Use? |
|---|---|---|
| A_high | From a school page, or confirmed current | Yes |
| B_inferred_confirmed | Built from the school's email format, confirmed by 2+ staff emails | Usually fine |
| C_inferred_single_example | Built from the format, based on one example | Run through an email verifier first |
| D_search_unconfirmed | Found by search; the coach may have changed | Verify first |

---

## 7. Rules for CLAUDE.md (Claude copies these in during setup)

- **Budget:** stop and ask if estimated spend passes $40. Report spend after each step.
- **Token discipline:** never print raw HTML into the conversation. Scripts save pages to `cache/` and print summaries only; inspect pages with `grep`, not by dumping them. Cap script output at counts plus the first 5 failures.
- **Use AI only where code fails:** scripts for bulk work, Claude reading short snippets for parser misses, Haiku helpers for search.
- **Be polite:** 1-2 requests per second per site, respect robots.txt, no contact forms.
- **No disguising the scraper** and no proxy services. If a site blocks you, use search or Chrome.
- **Never guess emails in search;** inferred emails come only from the format logic and are labeled `inferred`.
- **Sport is a setting, not hardcoded.**

---

## 8. Running it while you're away

- Give Claude the full task in one prompt (section 3) and leave. It runs each step, launches helpers, merges results, and saves files. When you're back, it tells you where it stopped and why.
- **What makes a session stall:**
  - A permission prompt waiting for a click. Fix with `/permissions` or auto mode.
  - The computer going to sleep.
  - Too many search helpers at once.
- Most steps need no AI. If you'd rather, ask Claude for a single command that runs steps 1-7 and 9 in a row, and leave that running.

---

## 9. Costs, outreach, and upkeep

- **Scripts are free.** AI tokens only go to snippets, search, and verification.
- **One sport pair, about 150-300 teams: expect $10-25.** Most of it goes to search, which drops sharply if PrestoSports isn't blocked for you.
- **Email outreach:** CAN-SPAM applies (real sender, physical address, working unsubscribe). Verify tier C/D emails before a big send; bounces hurt your sender reputation.
- **Coaches turn over every year.** Rerun before each recruiting cycle, and delete `cache/` to force fresh pages.
- **For the last few schools** that publish nothing, email the region directors for a coach list or call the athletics department.
