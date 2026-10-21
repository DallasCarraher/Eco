// Inspect an actual local Jak build in a fresh headless Chrome profile.
// This records evidence; it never labels a successful boot as playable.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(require.resolve('playwright', {
  paths: [path.resolve(__dirname, '../tools/browser-smoke'), __dirname],
}));

(async () => {
  const url = process.argv[2] || 'http://127.0.0.1:8620/?PS2_WINDOW_FULL=1';
  if (!['localhost', '127.0.0.1'].includes(new URL(url).hostname)) {
    throw new Error('Expected a local game server');
  }
  const out = path.resolve(__dirname, '../games/jak1');
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const messages = [], errors = [];
  let dropped = 0;
  let report = { gameplayVerified: false };
  try {
    const page = await browser.newPage();
    let halt;
    const stopped = new Promise(resolve => { halt = resolve; });
    page.on('console', msg => {
      if (messages.length < 10000 || msg.text().startsWith('[ee]')) messages.push(msg.text());
      else ++dropped;
      if (msg.text().startsWith('[ee] stopped after')) halt('halted');
    });
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url);
    await page.waitForFunction(() => !document.getElementById('start').disabled, undefined, { timeout: 60000 });
    await page.locator('#start').click();
    const bootCapture = page.waitForFunction(() => Module._ps2web_frames() >= 30, undefined, { timeout: 30000 })
      .then(() => page.locator('#canvas').screenshot({ path: path.join(out, 'browser-boot.png') }))
      .catch(() => null);
    const result = await Promise.race([stopped, page.waitForTimeout(30000).then(() => 'observation_limit')]);
    if (result === 'halted') {
      await page.waitForFunction(() => document.getElementById('status').textContent.startsWith('Halted:'), undefined, { timeout: 5000 });
    }
    const state = await page.evaluate(() => ({ frames: Module._ps2web_frames(),
      primitives: Module._ps2web_primitives(), gpu: Module.gpuInfo,
      isolated: crossOriginIsolated, status: document.getElementById('status').textContent }));
    await page.locator('#canvas').screenshot({ path: path.join(out, 'browser.png') });
    await bootCapture;
    report = { ...report, result, browser: browser.version(), state, errors, consoleMessagesDropped: dropped };
  } catch (error) {
    report = { ...report, result: 'browser_error', error: error.message, errors };
    process.exitCode = 1;
  } finally {
    fs.writeFileSync(path.join(out, 'browser.log'), messages.join('\n') + '\n');
    fs.writeFileSync(path.join(out, 'browser.json'), JSON.stringify(report, null, 2) + '\n');
    await browser.close();
    console.log(JSON.stringify(report, null, 2));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
