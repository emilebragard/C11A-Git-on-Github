// Render a JS page, save HTML to a file, print a short summary only.
const { chromium } = require('playwright');
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
  await p.waitForTimeout(3000);
  require('fs').writeFileSync(out, await p.content());
  const links = await p.$$eval('a', as => as.map(a => [a.innerText.trim(), a.href]));
  console.log(url, 'links:', links.length);
  console.log((await p.innerText('body')).replace(/\s+/g,' ').slice(0, 600));
  await b.close();
})();
