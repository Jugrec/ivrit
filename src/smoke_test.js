// Smoke test before every publish:  node build/smoke_test.js <site_url> <progress_export.json>
// Opens every section from the home screen with a real learner state and fails on any page error;
// then checks: full-spelling answers (לימודים), the memory-hook box, the offline spelling check, the day plan.
const { chromium } = require('playwright'); const fs = require('fs');
const URL = process.argv[2] || 'http://localhost:8766/', FILE = process.argv[3];
(async () => {
  const b = await chromium.launch(); let fail = 0; const bad = (m) => { fail++; console.log('FAIL', m); };
  const base = JSON.parse(fs.readFileSync(FILE, 'utf8')).state; const day = Math.floor(Date.now() / 86400000);
  delete base.day; base.lesDay = day - 1;
  base.cards['w:wr_limudim'] = { s: 1, d: 5, reps: 3, lapses: 3, last: Date.now() - 86400000, due: Date.now() + 86400000 };
  const open = async () => { const p = await b.newPage({ viewport: { width: 400, height: 900 } });
    await p.addInitScript(s => { if (!localStorage.getItem('ivrit-state')) localStorage.setItem('ivrit-state', s); }, JSON.stringify(base));
    // a fake Hebrew voice (headless Chromium has none); everything spoken is collected in window.__said
    await p.addInitScript(() => { window.__said = []; const v = [{ lang: 'he-IL', name: 'Test' }];
      window.SpeechSynthesisUtterance = function (t) { this.text = t; };
      Object.defineProperty(window, 'speechSynthesis', { value: { getVoices: () => v, speak: (u) => window.__said.push(u.text), cancel() {}, addEventListener() {}, set onvoiceschanged(f) {} }, configurable: true }); });
    p.on('pageerror', e => bad('page error: ' + e.message)); await p.goto(URL); await p.waitForTimeout(2200); return p; };
  const view = (p) => p.evaluate(() => { const v = [...document.querySelectorAll('[id^="v-"]')].find(x => !x.hidden && x.offsetParent); return v ? v.id : null; });
  // 1. every button of the home screen opens something without errors
  let p = await open();
  const note = await p.evaluate(() => document.getElementById('planNote').textContent);
  if (!/контрольный тест/.test(note) || /урок \d/.test(note)) bad('plan (consolidation day expected): ' + note); else console.log('ok plan:', note);
  const ids = await p.evaluate(() => [...document.querySelectorAll('#v-home button[id]')].filter(x => x.offsetParent).map(x => x.id));
  await p.close();
  const seen = {};
  for (const id of ids) { p = await open(); try { await p.click('#' + id, { timeout: 2000 }); await p.waitForTimeout(500); seen[id] = await view(p); } catch (e) { seen[id] = 'not clickable'; } await p.close(); }
  console.log('home buttons:', JSON.stringify(seen));
  // 2. hard words: the hook box, and the full spelling לימודים is accepted
  p = await open();
  await p.evaluate(() => { const x = [...document.querySelectorAll('button')].find(b => /Мои слова/.test(b.innerText)); if (x) x.click(); }); await p.waitForTimeout(500);
  const lee = await p.evaluate(() => ({ n: document.querySelectorAll('#leechList details').length, inputs: document.querySelectorAll('#leechList input').length, hidden: document.getElementById('leechPanel').hidden }));
  if (lee.hidden || !lee.n || lee.inputs !== lee.n) bad('leech panel ' + JSON.stringify(lee)); else console.log('ok leeches:', lee.n);
  await p.click('#leechGo'); await p.waitForTimeout(500);
  let typed = null;
  for (let i = 0; i < 40 && typed === null; i++) {
    if (await view(p) !== 'v-run') break;
    const st = await p.evaluate(() => ({ prompt: document.querySelector('#v-run .prompt') ? document.querySelector('#v-run .prompt').innerText : '', type: !document.getElementById('answer').hidden && !!document.getElementById('answer').offsetParent, opts: document.querySelectorAll('#qopts button').length }));
    if (st.type && /учёба/.test(st.prompt)) { await p.fill('#answer', 'לימודים'); await p.click('#b-check'); await p.waitForTimeout(300); typed = await p.evaluate(() => document.getElementById('answer').classList.contains('right')); }
    else if (st.type) { await p.fill('#answer', 'אבג'); await p.click('#b-check'); await p.waitForTimeout(300);
      const hook = await p.evaluate(() => !!document.querySelector('#qfb input')); if (!hook) bad('no hook box after a missed hard word: ' + st.prompt); }
    else if (st.opts) { await p.click('#qopts button >> nth=0'); await p.click('#b-check'); await p.waitForTimeout(300); }
    else { await p.click('#b-skip').catch(() => {}); }
    await p.click('#b-check'); await p.waitForTimeout(350);
  }
  if (typed !== true) bad('לימודים accepted: ' + typed); else console.log('ok full spelling accepted');
  await p.close();
  // 3. offline writing: the spelling check flags בשבה
  p = await open();
  await p.click('#b-writing'); await p.waitForTimeout(500);
  await p.evaluate(() => { const x = [...document.querySelectorAll('#v-writing .li, #v-writing button')].find(e => e.offsetParent && !/Назад|главн/.test(e.innerText)); if (x) x.click(); }); await p.waitForTimeout(500);
  if (await view(p) === 'v-write') { await p.fill('#wrIn', 'היום יום שני. בבוקר אני קמה בשבה.'); await p.click('#wrCheck'); await p.waitForTimeout(1200);
    const t = await p.evaluate(() => document.getElementById('wrResult').innerText);
    if (!/בשבה/.test(t) || /קמה ·|· קמה/.test(t)) bad('spell check: ' + t.slice(0, 300)); else console.log('ok spell check'); }
  else bad('writing task did not open: ' + await view(p));
  await p.close();
  // 4. listening: 8 heard sentences, spoken without nikud, all three exercise kinds can be answered
  p = await open();
  if (await p.evaluate(() => document.getElementById('b-listen').hidden)) bad('listening button hidden'); else {
    await p.click('#b-listen'); await p.waitForTimeout(600); const kinds = {};
    for (let i = 0; i < 12 && await view(p) === 'v-run'; i++) {
      const st = await p.evaluate(() => ({ prompt: document.getElementById('qprompt').innerText, word: !document.getElementById('qword').hidden, listen: !document.getElementById('qlisten').hidden,
        type: !document.getElementById('qtype').hidden, order: !document.getElementById('qorder').hidden }));
      if (st.word || !st.listen) bad('listening shows the text or has no play button: ' + JSON.stringify(st));
      if (st.type) { kinds.type = 1; await p.fill('#answer', 'אבג'); } else if (st.order) { kinds.order = 1; for (const t of await p.$$('#qpool button')) await t.click(); } else { kinds.choice = 1; await p.click('#qopts button >> nth=0'); }
      await p.click('#b-check'); await p.waitForTimeout(300); await p.click('#b-check'); await p.waitForTimeout(400);
    }
    const said = await p.evaluate(() => window.__said);
    if (await view(p) !== 'v-summary') bad('listening did not reach the summary: ' + await view(p));
    if (said.length < 8 || said.some(t => /[\u0591-\u05C7]/.test(t) || !/\s/.test(t.trim()))) bad('spoken text: ' + JSON.stringify(said.slice(0, 3)));
    else console.log('ok listening:', said.length, 'phrases,', Object.keys(kinds).join('/'), '| e.g.', said[0]);
  }
  await p.close();
  await b.close();
  console.log(fail ? 'FAILED: ' + fail : 'ALL OK'); process.exit(fail ? 1 : 0);
})();
