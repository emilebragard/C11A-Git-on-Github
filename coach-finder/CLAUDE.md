# coach-finder: rules for Claude

This folder is a reusable system for finding college head coaches' names and emails. For any request, follow `PLAYBOOK.md`. People start at `START_HERE.md`.

## Rules
- **Data first, then the doc.** Every finding goes into `data/coaches.csv` (the master backup) through the scripts before it goes into the live Claude doc.
- **Never guess emails in search or Chrome.** Only record emails a page shows. Built emails come only from `scripts/emails.py` and are labeled inferred (tier B/C).
- **Token discipline:** never print raw HTML or whole pages into the conversation. Scripts print summaries; inspect pages with `grep`. Chrome: read page text, and screenshots only if the text is empty.
- **Polite:** about 1 request per second per site, respect robots.txt, never submit contact forms.
- **No getting around blocks:** don't disguise scripts as browsers, use proxies, or solve CAPTCHAs. Blocked by scripts → Chrome. Blocked in Chrome → search.
- **Helpers:** use the `coach-searcher` (max 3 at once) and `coach-verifier` (max 2) agents for search work. Don't create other helpers per school.
- **Budget:** give a rough cost estimate before starting; stop and ask if one run looks like it will pass $25, or a multi-sport request $100.
- **Head coaches only** unless the person asks for assistants.
- **Keep the database tidy:** don't add columns or files outside the structure in START_HERE.md without saying so. Update `knowledge/lessons.md` at the end of each run.
- No phone numbers in outputs.
