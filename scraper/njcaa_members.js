// Collect every NJCAA member college name + athletics URL from the directory.
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('https://www.njcaa.org/member_colleges/directory/members', { waitUntil: 'networkidle' });
  for (let i = 0; i < 20; i++) {
    const btn = p.getByRole('button', { name: 'Load more schools' });
    if (!(await btn.count())) break;
    await btn.click(); await p.waitForTimeout(1200);
  }
  const rows = await p.$$eval('a', as => as.filter(a => /ATHLETICS WEBSITE/.test(a.innerText)).map(a => {
    let e = a; while (e && !/COLLEGE|UNIVERSITY|INSTITUTE|SCHOOL|ACADEMY|CENTER|TECH/i.test(e.innerText.replace(/VISIT ATHLETICS WEBSITE/g,''))) e = e.parentElement;
    const name = e.innerText.replace(/VISIT ATHLETICS WEBSITE\s*↗?/g,'').trim().split('\n')[0];
    return { name, url: a.href };
  }));
  require('fs').writeFileSync('data/members.json', JSON.stringify(rows, null, 1));
  console.log('members', rows.length, rows.slice(0, 3), rows.slice(-2));
  await b.close();
})();
