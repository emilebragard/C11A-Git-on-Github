# Sidearm Sports (most NCAA D1/D2 athletics sites, some NJCAA)

- **Spot it:** "sidearm" appears in the page HTML.
- **Coaches page:** `/sports/<sidearm_slug>/coaches`, e.g. `/sports/mens-water-polo/coaches`. Slugs are in `knowledge/sports.csv`.
- **Staff directory:** `/staff-directory`. Usually lists every coach **with an email link**, often the most reliable page.
- **Parsing:** names in `.sidearm-coaches-coach-name` or `.s-person-details__personal-single-line`; emails are `mailto:` links. In tests, about 90% of open Sidearm sites parsed on the first try.
- **Blocking:** many Sidearm sites (behind CloudFront) return 403 to cloud servers, including robots.txt. From home or office internet they usually load; in Chrome they always do.
