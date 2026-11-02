# NAIA (~250 schools, one division)

**Status: not yet run.** The first NAIA run will need to build the team list, which isn't scripted yet. Use run IDs like `naia-all-womens-soccer` (division = `ALL`).

**What we know (checked 2026-11-02):**
- `https://www.naia.org/schools/index` lists member info but **no per-school athletics links** (it points to a map at `naia.college-tour.com`).
- NAIA stats (`naiastats.prestosports.com`) blocks cloud servers. From home or office internet, or in Chrome, its sport pages list teams.
- Conference websites list their member schools with links to each athletics site.

**Suggested first-run approach (Claude):**
1. Run `python scripts/list_teams.py NAIA ALL <sport>`. It creates an empty `teams.csv` template and tells you where.
2. In **Chrome**, open the NAIA sport's page (naia.org → Sports → <sport> → teams or standings) or the school map. Fill `teams.csv` with school, conference, and athletics_url.
3. Rerun `list_teams.py`. Then continue the normal PLAYBOOK from step 2.
4. Write down what worked in this file and in `knowledge/lessons.md`, and if possible add an `naia()` function to `scripts/list_teams.py`.

**Expected platforms:** a mix of Sidearm, PrestoSports, and plain college sites, similar to NCAA D2/D3.
