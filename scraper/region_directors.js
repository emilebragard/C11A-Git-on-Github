// Collect NJCAA region directors (name, title, bio URL, email if shown) for chosen regions.
const { chromium } = require('playwright');
const REGIONS = [1, 4, 10, 11, 12, 20];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('https://www.njcaa.org/about/region_directors', { waitUntil: 'networkidle' }); await p.waitForTimeout(2000);
  const people = await p.$$eval('a', as => as.filter(a => /\/region_directors\//i.test(a.href)).map(a => {
    const row = a.closest('tr') || a.parentElement.parentElement;
    return { name: a.innerText.trim(), title: row.innerText.replace(a.innerText, '').replace(/\s+/g, ' ').trim(), url: a.href };
  }).filter(x => x.name));
  const want = people.filter(x => REGIONS.some(r => new RegExp(`Region ${r} `).test(x.title)) && !/Assistant/.test(x.title));
  for (const x of want) {
    await p.goto(x.url, { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
    const t = (await p.innerText('body')).replace(/\s+/g, ' ');
    x.email = (await p.$$eval('a[href^="mailto:"]', as => as.map(a => a.href.slice(7)))).find(e => !/njcaa\.org$/.test(e))
           || (t.match(/[\w.+-]+@[\w-]+\.(?:edu|org|com)/) || [''])[0];
    x.school = (t.match(/(?:College|University)[^.]{0,0}/) ? (t.match(/[A-Z][\w.&' -]{3,60}(?:College|University)/) || [''])[0] : '');
  }
  require('fs').writeFileSync('data/region_directors.json', JSON.stringify(want, null, 1));
  console.log('total people', people.length, 'selected', want.length);
  want.forEach(x => console.log(x.title.slice(0, 28), '|', x.name, '|', x.email, '|', x.school.slice(0, 45)));
  await b.close();
})();
