# PLAYBOOK: how Claude runs a coach-finding request

Claude: follow this whenever someone asks for coaches ("we're missing D1 soccer", "do all D2 sports", "refresh NJCAA basketball"). Read `CLAUDE.md` for the rules first.

## 0. Understand the request

1. Turn the request into one or more **runs**. A run is one association + division + sport, e.g. `ncaa-d1-mens-soccer`.
   - The `sport_key` values are in `knowledge/sports.csv`.
   - "Soccer" with no gender means both `mens-soccer` and `womens-soccer`, so 2 runs.
   - "All D2 sports" means one run per sport that division offers: for NCAA, the sports with an `ncaa_code`; for NJCAA, those with an `njcaa_code`.
2. Read `data/coverage.csv`. If a run already exists, this is a **refresh**: only redo rows older than 6 months or below tier A, unless asked otherwise.
3. Read `knowledge/associations/<association>.md` and `knowledge/lessons.md`.
4. Tell the person the plan in 2-3 lines: runs, rough team count, rough cost. Many runs (e.g. "all D2 sports") → do them one at a time, smallest first, and report after each.

## 1. Set up (once per computer)

- Python 3.11+. Install the libraries: `pip install -r requirements.txt` then `python -m playwright install chromium`.
- **Chrome connection.** Check that Claude in Chrome is connected (`/chrome`). If it isn't, tell the person how to connect it (START_HERE.md) and continue with the steps that don't need it. Never skip the Chrome step silently.

## 2. The run, step by step

Run the scripts from the folder root. Each prints a short summary; never print web pages into the conversation.

| Step | Command | Who | Unattended? |
|---|---|---|---|
| 1. Team list | `python scripts/list_teams.py NCAA D1 mens-soccer` | script | yes |
| 2. Create the live doc | see section 3 | Claude | yes |
| 3. Scrape athletics sites | `python scripts/scrape.py <run_id>` | script | yes |
| 4. College staff directories | `python scripts/college_dirs.py <run_id>` | script | yes |
| 5. Build emails from formats | `python scripts/emails.py <run_id>` | script | yes |
| 6. **Chrome pass** | `python scripts/worklist.py <run_id> chrome` → section 4 | Claude in Chrome | mostly; pauses on CAPTCHAs/logins |
| 7. Search pass | `python scripts/worklist.py <run_id> search 3` → section 5 | 3 `coach-searcher` helpers | yes |
| 8. Formats again | `python scripts/emails.py <run_id>` (uses staff emails found in 6-7) | script | yes |
| 9. Verify pass | `python scripts/worklist.py <run_id> verify 2` → section 5 | 2 `coach-verifier` helpers | yes |
| 10. Hunter pass (if connected) | section 5b | Claude + Hunter connector | yes |
| 11. Report | `python scripts/report.py <run_id> --doc-table` → update the doc | Claude | yes |

After steps 3, 5, 6, 7, 9, and 10: run `python scripts/merge.py <run_id>` (only after 6, 7, 9, 10), then `python scripts/report.py <run_id> --doc-table`, then **update the live doc**. Data reaches `data/coaches.csv` (the backup) before it reaches the doc.

**Skip rules:**
- NCAA: step 1 already gives every head coach's name, so most work is finding emails.
- Step 6 can be skipped only if nothing is blocked and few teams are missing.
- Stop early once 95%+ of teams have a tier A/B email.

## 3. The live Claude doc (one per run)

- **Title:** `<ASSOCIATION> <DIVISION> <Sport label> Head Coaches` (e.g. "NCAA D1 Men's Soccer Head Coaches").
- **Create** it right after step 1 with: a one-line summary, a "How to read this" line (High / Format confirmed / Guessed / Unconfirmed), and the table from `report.py --doc-table`.
- **Save the link:** `python scripts/report.py <run_id> --doc-link <url>`. It's stored in `data/coverage.csv` so the next session can find and update the same doc.
- **Update** after each step listed above: replace the summary line and table with the latest `report.py --doc-table` output. Don't append duplicate tables.
- **If Claude Docs isn't available,** say so once. `reports/<run_id>.md` is the same content and is always written; share that or `exports/<run_id>.csv` instead.

## 4. Chrome pass (Claude in Chrome)

Chrome reads sites the way a person does, so it works on sites that block scripts. Most PrestoSports, and many Sidearm sites when you're on a cloud server or flagged network, block scripts.

1. Open `data/runs/<run_id>/worklists/chrome_1.csv`. Do blocked rows first; they're already sorted.
2. For each school:
   1. Open `try_first`. If it's a 404, open `athletics_url` and find the sport's **Coaches** or **Staff** page.
   2. Read the page **text**; don't take screenshots unless the text is empty.
   3. Find the head coach (name, title, email).
   4. If the email is hidden behind a "contact" button or form, don't submit anything. Record the name, and note 2-3 other staff emails on the staff directory page (helps format learning).
3. Every 5 schools, append rows to `data/runs/<run_id>/results/chrome_1.csv` (format below), then run `merge.py` and `report.py`, and update the doc. Progress is never lost.
4. CAPTCHA, login wall, or "are you a robot" page: skip the school, note `captcha` in `note`, move on. Never try to get around it.
5. Pace: one page at a time, a few seconds per page. It's fine for this to take an hour for 300 schools.

## 5. Helper agents (search and verify)

Defined in `.claude/agents/`. Both run on Haiku, which is cheap.
- **`coach-searcher`:** give it one worklist file (`search_N.csv`) and its output path (`results/search_N.csv`). Run **at most 3 at once**. More hits the web-search rate limit and they return half empty.
- **`coach-verifier`:** give it `verify_N.csv` and `results/verify_N.csv`. Run at most 2 at once.
- After they finish, run `merge.py`, `emails.py`, `report.py`, and update the doc.

## 5b. Hunter pass (optional; only if the Hunter connector is connected)

Hunter checks whether a mailbox exists (Email-Verifier) and finds a person's email from their name and domain (Email-Finder).
- **Credits:** Verifier = 0.5 credit and Finder = 1 credit (only charged when found). Run `Get-Usage` first; the free plan has 50 credits/month. Say how many credits you'll use, and ask first if it's more than 20.
- **Verify only emails a page or search showed** (tier D first, then search_high). **Never send pattern-built (inferred, tier B/C) emails to the Verifier;** Hunter's rules forbid verifying guessed addresses. For those rows, and for name-only rows, use **Email-Finder** with the coach's full name + the school's email domain instead.
- Skip shared/role inboxes (e.g. `mens_basketball@`, `cardinalsmbasketball@`); Hunter can't judge them.
- Write Verifier results to `data/runs/<run_id>/results/hunter_<n>.csv` with columns `school,email,hunter_status,score`. Valid → tier A and recorded in `email_check`; invalid → email removed; accept_all → recorded, tier unchanged.
- Write Email-Finder hits in the normal result format to `results/search_hunter_<n>.csv`, with confidence `high` if score ≥ 90, otherwise `medium`, and note `Hunter Email-Finder score N`. If Finder returns an email different from an inferred one, Finder wins.
- Hunter saves verified addresses as leads in the Hunter account (All people). That's expected; mention it once.

## 6. Result file format (Chrome, search, and verify all use it)

`school,name,title,email,source_url,confidence,example_staff_emails,dept_contact,verdict,note`

| Column | What goes in it |
|---|---|
| school | Exactly as written in the worklist |
| confidence | high = current school page; medium = this season's source; low = older/conflicting. Chrome rows from the school's own page = high. |
| example_staff_emails | `Full Name=email; Full Name=email` (other staff at the same school, for format learning) |
| verdict | Verify only: confirmed / replaced / email_wrong / unclear |
| email | **Only an email a page explicitly shows. Never construct one.** |

## 7. Finish a run

1. Run `python scripts/report.py <run_id> --doc-table` and do a final doc update.
2. Tell the person:
   - % of teams with email and the tier breakdown
   - what's left and why (blocked, CAPTCHAs, no email published)
   - rough cost
3. Add anything new you learned to `knowledge/lessons.md` (one line each, dated) and, if relevant, `knowledge/platforms/*.md` or `knowledge/associations/*.md`. That's how the folder gets smarter.
4. Remaining gaps: suggest emailing region/conference contacts (`knowledge/associations/*.md` says where) or calling the athletics office (`dept_contact`).
