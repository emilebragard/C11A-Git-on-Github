// Collect NJCAA Division II teams for a sport by looping over regions.
// Usage: node njcaa_teams.js <sport> <out.json>. Prints counts only.
const { chromium } = require('playwright');
(async () => {
  const [sport, out] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto(`https://www.njcaa.org/sports/${sport}/teams`, { waitUntil: 'networkidle', timeout: 60000 });
  await p.locator('select', { has: p.locator('option', { hasText: 'Division II' }) }).first().selectOption({ label: 'Division II' });
  await p.waitForLoadState('networkidle'); await p.waitForTimeout(2000);
  const reg = p.locator('select[aria-label="Region"]');
  const regions = (await reg.locator('option').allInnerTexts()).filter(r => r !== 'All regions');
  const teams = {};
  for (const r of regions) {
    await reg.selectOption({ label: r });
    await p.waitForLoadState('networkidle'); await p.waitForTimeout(1500);
    const rows = await p.$$eval('.sports-team-directory a[href*="/statistics?"]', as =>
      as.filter(a => a.innerText.trim() !== 'Stats').map(a => [a.innerText.trim(), a.getAttribute('href')]));
    for (const [name, href] of rows) {
      const id = href.match(/teams\/(\d+)/)[1];
      teams[id] ??= { team_id: id, school: name, region: r, sport, tenant: (href.match(/tenant=(\d+)/)||[])[1] };
    }
    console.log(r, rows.length);
  }
  require('fs').writeFileSync(out, JSON.stringify(Object.values(teams), null, 1));
  console.log(sport, 'total unique', Object.keys(teams).length);
  await b.close();
})();
