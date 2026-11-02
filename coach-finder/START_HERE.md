# Coach Finder: start here

A folder that finds college **head coaches' names and emails** for any NCAA, NJCAA, or NAIA sport, keeps everything in simple spreadsheets, and gets smarter every run.

## How to use it (2 minutes)

1. Open the **Claude desktop app → Code tab** and choose this folder. (Or run `claude` in this folder from a terminal.)
2. Say what you want, in plain words:
   - "We're missing D1 men's soccer."
   - "Do all NJCAA D2 sports."
   - "Refresh NCAA D1 women's water polo, it's from last year."
   - "What do we have so far?"
3. Claude explains the plan and rough cost, creates a **live Claude doc** for each sport, and fills it in as results come in. Everything is also saved in this folder as the backup.

That's it. Claude follows `PLAYBOOK.md`, so you don't have to.

## What's already in here

Open `data/coverage.csv` (any spreadsheet app) to see every sport done so far, how complete it is, and the link to its doc.

| Run | Teams | With email |
|---|---|---|
| NJCAA D2 Men's Basketball | 152 | 88% |
| NJCAA D2 Women's Basketball | 153 | 85% |
| NCAA D1 Men's Water Polo (test run, scripts only) | 30 | 27% (all 30 coach names) |

## One-time setup on a new computer (about 15 min)

1. **Claude desktop app** (claude.ai/download), signed in with a paid plan (Pro or higher).
2. **Python 3.11+** (python.org). On Windows, tick "Add Python to PATH" during install.
3. **Google Chrome** with the **Claude in Chrome** extension (from the Chrome Web Store, version 1.0.36+), signed in to the same Claude account.
4. **Connect Chrome to Claude Code:** in the Code tab, type `/chrome` and choose **Enabled by default**. Or start the terminal version with `claude --chrome`. If the Code tab doesn't offer `/chrome`, use the terminal version for runs.
5. **Claude Docs** (for the live docs) comes with your Claude account. In the Code tab, `/mcp` should list "claude.ai Claude Docs". If not, Claude still saves everything in `reports/`.
6. The first time, Claude installs the Python libraries itself (`requirements.txt`).
7. So runs don't stall while you're away: type `/permissions` and allow `Bash(python *)` and `Bash(pip *)`, or turn on auto mode. Keep the computer awake during long runs.

## How it finds coaches (why it's fast and thorough)

1. **Scripts first, free:** official lists from NCAA, NJCAA, and NAIA give every team. The NCAA directory even gives every head coach's name. Then scripts read each athletics site's coaches page.
2. **Claude in Chrome:** opens the sites that block scripts, in your own browser, and reads the coaches page like a person would.
3. **Search helpers:** cheap AI helpers search the web for anything still missing.
4. **Email formats:** if a school's emails look like `first.last@school.edu`, a coach's email can be built from their name, but only when real examples confirm the format.
5. **Verify:** uncertain coaches get re-checked, because coaches change jobs every year.

**Confidence levels in every doc:**
- **High:** taken from a school page, or confirmed current.
- **Good (format confirmed):** built from the school's email format, confirmed by 2+ real emails.
- **Guessed:** built from a format seen only once. Verify before a big send.
- **Unconfirmed:** found by web search; the coach may have changed. Verify first.

## What's in the folder

| Folder / file | What it is |
|---|---|
| `START_HERE.md` | This page |
| `PLAYBOOK.md` | Claude's step-by-step routine |
| `CLAUDE.md` | Rules Claude always follows (budget, politeness, no guessing) |
| `data/coaches.csv` | **The master list.** One row per team, every sport (the backup for all docs) |
| `data/coverage.csv` | What's done, % complete, doc links |
| `data/schools.csv` | Every school: athletics website, website platform, email domain |
| `data/email_formats.csv` | Each school's email format, learned from real emails |
| `data/runs/` | Working files per run (team lists, to-do lists, helper results) |
| `reports/` | A copy of each live doc, as a plain file |
| `exports/` | Clean lists to share: school, coach, title, email, confidence |
| `knowledge/` | What Claude knows about each association, website platform, and lessons from past runs |
| `scripts/` | The Python scripts (Claude runs these; you don't need to) |
| `cache/` | Saved web pages so reruns are fast. Safe to delete, and not worth sharing |

## Good to know

- **Costs:** a typical sport (200-350 teams) runs about $5-20 in AI usage. "All D2 sports" is ~20 runs, so Claude does them one at a time and reports as it goes.
- **Coaches change every year.** Re-run before each recruiting cycle. Claude only redoes what's stale.
- **Before emailing a list:** run tier Guessed/Unconfirmed emails through an email verifier, and follow CAN-SPAM (real sender, physical address, unsubscribe link).
- **Sharing this folder:** zip it without `cache/`. Anyone with Claude can pick up where you left off.
