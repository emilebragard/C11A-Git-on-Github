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
- 2026-11-02: Hunter Email-Verifier on 16 search-found (tier D) basketball emails: 14 valid, 2 accept_all, 0 invalid, for 8 credits. Search-found emails are mostly real; Hunter turns them into tier A cheaply. Hunter's sources also show whether a page still lists the coach (`still_on_page`), which is a free hint about whether they're current.
- 2026-11-02: Second half of tier D (18 emails): 12 valid, 4 accept_all, 1 invalid, plus 1 typo domain fixed with Email-Finder. Across all 34 checked: 26 valid, 6 accept_all, 1 invalid. Search-found emails are ~97% deliverable.
- 2026-11-02: Typo in a source email's domain (denmarktecch.edu): don't fix it by hand and verify (that's building an email). Use Hunter Email-Finder with the name + correct domain.
