# Lessons learned (newest at the bottom; add one dated line per lesson)

- 2026-11-02: "Women's basketball" contains "men's basketball". Match the men's version with a word boundary (`\bmen`). `knowledge/sports.csv` keywords already do this.
- 2026-11-02: Mixed staff directories list both genders' coaches. Filter by the sport's keywords and exclude the other gender's.
- 2026-11-02: Running 8 search helpers at once hit the web-search rate limit, and half came back empty. 3 at once with one-at-a-time searches worked with no limits hit.
- 2026-11-02: Email formats need 2+ real examples. A single example (e.g. "nee@" or "adobbs1@") is often ambiguous. Formats with digits can't be learned.
- 2026-11-02: Format guesses are sometimes wrong (guessed kchandler@, real was kdchandler@). The college-directory step and verification catch these.
- 2026-11-02: Verification found ~10% of search-found coaches had been replaced. Always run the verify pass on medium/low rows.
- 2026-11-02: Cloud servers are blocked by PrestoSports and many Sidearm sites (403, including robots.txt). On home or office internet, expect far fewer blocks. Chrome handles the rest.
- 2026-11-02: The NCAA Directory (web3.ncaa.org) lists every head coach's name per sport, so NCAA runs only need emails.
- 2026-11-02: Region and conference sites don't list coach emails, but NJCAA region directors will share lists by email.
