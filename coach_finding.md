# Coach Finding: Fast, Unattended, Code-Based

How to build a college coach contact list (name + email) for any NJCAA division and sport, using **Claude Code on your own computer** and the scripts in this repo.

This replaces the "ChatGPT in a browser tab" approach. That approach is slow because it does one page at a time, stops when you walk away, and keeps no files or code. Here, code does about 90% of the work on its own, and AI only handles the leftovers.

---

## 1. Why this is faster

| Old way (chat in a browser) | This way |
|---|---|
| AI reads every school site one at a time | A script fetches 150+ sites in minutes with **no AI cost** |
| Stops when you close the tab or step away | Scripts and Claude Code keep running while you're away (computer awake) |
| Results live in chat; you copy and paste | Results land in a CSV, cached and resumable |
| Starts from scratch every time | Rerun for a new sport by changing one setting |
| One AI does everything | Cheap helper AIs (Haiku) run searches in parallel, only on gaps |

**Last run (D2 men's + women's basketball):** 305 teams, **264 with a head coach email (87%)**, about $20 of AI usage, a few hours mostly unattended.

---

## 2. One-time setup (about 20 min)

1. **Install:**
   - Python 3.11+ (python.org)
   - Node.js 20+ (nodejs.org)
   - Git
   - **Claude Code**: the Claude desktop app (Code tab) or the CLI (`npm install -g @anthropic-ai/claude-code`)
2. **Get the repo and libraries.** In a terminal:
   ```bash
   git clone https://github.com/emilebragard/C11A-Git-on-Github.git
   ```
   ```bash
   cd C11A-Git-on-Github
   ```
   ```bash
   pip install -r requirements.txt
   ```
   ```bash
   npm install playwright && npx playwright install chromium
   ```
3. **Open the folder in Claude Code.** It reads `CLAUDE.md` automatically. That file holds the budget and scraping rules, so Claude follows them without being told.
4. **Allow common commands** so Claude doesn't stop and wait for you to click "approve" while you're away. In Claude Code, run `/permissions` and allow `Bash(python3 scraper/*)`, `Bash(node scraper/*)`, and `Bash(git *)`, or turn on auto mode. **This is the #1 reason things stall when you're away.**
5. **Keep the computer awake during long runs:**
   - **Mac:** run `caffeinate -i` in a spare terminal.
   - **Windows:** Settings → Power → Screen and sleep → Never (while plugged in).

---

## 3. Big advantage on your own computer: PrestoSports may not block you

About 70% of NJCAA athletics sites run on **PrestoSports**. PrestoSports blocks traffic from cloud servers, which is why the last run needed web search for those schools. **From a home or office internet connection, the sites usually load normally.** Test it first:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://cgccathletics.com/landing/index
```

- **`200`:** you're not blocked. Have Claude add a PrestoSports parser (prompt in section 6) and scrape those schools directly. That's faster, more current, and free compared with web search.
- **`403`:** you're blocked too. Use the web-search helpers (step 5 below), or Claude in Chrome in your own browser.

> Don't disguise the scraper as a browser or use proxy services to get around a block. If a site blocks you, switch to search or Chrome.

---

## 4. The pipeline (what runs, in order)

Every script prints a short summary and saves files to `data/` and `cache/`. **If something crashes, just rerun it.** Cached pages aren't downloaded again.

| # | Step | Command | AI? | Time |
|---|---|---|---|---|
| 1 | Team list per sport from njcaa.org | `node scraper/njcaa_teams.js mbkb data/mbkb_d2.json` (repeat per sport) | No | 1 min each |
| 2 | Athletics website for every member college | `node scraper/njcaa_members.js` | No | 1 min |
| 3 | Combine into one school list | `python3 scraper/build_schools.py mbkb wbkb` | No | seconds |
| 4 | Detect each site's platform (Sidearm, Presto, ...) | `python3 scraper/fingerprint.py` | No | 2-5 min |
| 5 | Scrape coach pages | `python3 scraper/coaches.py sidearm,presto,streamline,other,wordpress,drupal,other_tiny` | No | 5-15 min |
| 6 | Pull text snippets for pages the parser missed | `python3 scraper/fallback_snippets.py` | Claude reads short snippets | 5 min |
| 7 | Merge, infer emails, check domains | `python3 scraper/finalize.py` | No | 1 min |
| 8 | Search helpers for blocked or missing teams | `python3 scraper/make_worklists.py gap 3`, then the helper prompt (section 6) | Haiku | 10-20 min |
| 9 | Merge search results | `python3 scraper/merge_gaps.py` | No | seconds |
| 10 | Build emails from known school formats | `python3 scraper/infer_name_only.py` | No | seconds |
| 11 | Check the main college sites' staff directories | `python3 scraper/college_dirs.py` | No | 5-15 min |
| 12 | Re-check uncertain rows | `python3 scraper/make_worklists.py verify 2`, then the verify prompt, then `python3 scraper/merge_verify.py` | Haiku | 10 min |
| 13 | Write the clean deliverable | `python3 scraper/export.py` | No | seconds |

**Output:** `data/coaches.csv`, with columns school, sport, role, name, title, email, email_source, tier, dept_contact.

**Tiers:**
- **A_high:** from a school page or confirmed current. Safe to use.
- **B_inferred_confirmed:** built from the school's email format, with the format confirmed by 2+ staff emails.
- **C_inferred_single_example:** built from the format, based on one example. Run it through an email verifier first.
- **D_search_unconfirmed:** found by search, but the coach may have changed. Verify first.

Steps 1-2 and 6 (the NJCAA site) need Playwright because njcaa.org only renders in a browser.

---

## 5. Running it while you're away

**Option A, the simplest: let Claude Code drive.** Paste the "full run" prompt from section 6, confirm the permissions from setup step 4 are set, keep the computer awake, and leave. Claude runs each step, launches the helpers, merges, and commits. When you're back, it tells you where it stopped and why.

**Option B: run the scripts yourself in the background.** Steps 1-5, 7, 9-11, and 13 need no AI. Chain them in one terminal and leave it:

- **Mac/Linux:**
  ```bash
  (python3 scraper/fingerprint.py && python3 scraper/coaches.py sidearm,presto,streamline,other,wordpress,drupal,other_tiny && python3 scraper/finalize.py) > run.log 2>&1 &
  ```
- **Windows (PowerShell):** the same commands joined with `;`, run in a window you leave open.

Only steps 6, 8, and 12 need Claude.

**What makes a session stall while you're away:**
- A permission prompt waiting for a click. Fix with `/permissions` or auto mode.
- The computer going to sleep. Fix with caffeinate or the power settings.
- Too many search helpers at once, which hits the search rate limit. Keep it at **3 helpers max**.

---

## 6. Prompts to paste into Claude Code

**Full run, for a new sport or a refresh:**
> Read CLAUDE.md and coach_finding.md. Run the pipeline in section 4 for NJCAA Division II [SPORTS, e.g. baseball (bsb) and softball (sball)]. First add the sport slugs to `SPORTS` in scraper/coaches.py. Pilot on 10 schools before the full run and report the parse rate. Use Haiku helpers (max 3 at a time) only for gaps. Commit after each step. Stop and tell me if estimated spend passes $40.

**Add a PrestoSports parser** (only if section 3's test returned 200):
> PrestoSports sites aren't blocked from my connection. Fetch 3 PrestoSports coaches pages (e.g. `<site>/sports/mbkb/coaches/index`), look at the HTML structure with grep (don't print whole pages), and add a parser to scraper/coaches.py. Rerun coaches.py on the `blocked_403` schools.

**Search helpers.** Claude Code launches these when you ask for "Haiku subagents":
> Run `python3 scraper/make_worklists.py gap 3`, then launch 3 Haiku subagents, one per data/search/gap_N.txt. Each uses WebSearch one at a time (no parallel searches; on a rate-limit error wait 30s and retry), max 3 searches per school, and records only emails a source explicitly shows (never guessed). Output data/search/gap_N.csv with columns school,sport,name,title,email,source_url,confidence,example_staff_emails,athletics_contact,note. Then run `python3 scraper/merge_gaps.py`, `python3 scraper/infer_name_only.py`, and `python3 scraper/export.py`.

**Verify pass:**
> Run `python3 scraper/make_worklists.py verify 2` and launch 2 Haiku subagents to check whether each person is the current (this season) head coach. Verdicts: confirmed / replaced / email_wrong / unclear, written to data/search/verify_N.csv. Then run `python3 scraper/merge_verify.py` and `python3 scraper/export.py`.

---

## 7. Costs and rules of thumb

- **Scripts are free.** AI tokens only go to snippets, search, and verification.
- **Haiku for bulk work, the main model for building and debugging.** Haiku helpers handled about 500 searches for a few dollars.
- **Don't let Claude read raw HTML.** One page can be 100k tokens. Scripts print summaries; Claude uses `grep` to inspect pages. (This is in CLAUDE.md.)
- **One sport pair, about 150-300 teams: expect $10-25.** Most of it goes to the search step.
- **Be polite:** 1-2 requests per second per site, respect robots.txt, and don't hit contact forms.
- **Email outreach:** CAN-SPAM applies (real sender, physical address, working unsubscribe). Verify tier C/D emails before a big send; bounces hurt your sender reputation.
- **Coaches turn over every year.** Rerun before each recruiting cycle. The cache makes reruns fast, so delete `cache/` to force fresh pages.

---

## 8. Adding a new sport

1. Find the NJCAA sport code in the njcaa.org URL. For example, `njcaa.org/sports/bsb/teams` means `bsb` (baseball).
2. Add it to `SPORTS` in `scraper/coaches.py`, with the URL slug athletics sites use (e.g. `'bsb': ('baseball', r'baseball|\bbsb\b')`).
3. Run steps 1-13 with the new code(s). The member list and platform fingerprints are reused.

**Known limits:**
- `make_worklists.py` and `merge_gaps.py` label teams as men/women. That works for paired sports; one-gender sports like baseball and softball need a quick edit, so ask Claude to generalize it.
- About 7 schools aren't in NJCAA's member directory. Add their athletics URLs to `data/schools.csv` by hand.

---

## 9. Where to get help

- **Region directors** (names and emails are on njcaa.org under About → Region Directors) can share coach lists for a whole region. Drafts are in `data/region_director_emails.md`.
- **To pick up where the last run stopped:** open the repo in Claude Code and say "read coach_finding.md and continue". Everything it needs is in the files.
