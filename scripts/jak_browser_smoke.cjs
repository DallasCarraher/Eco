// Run with Node and Playwright available in NODE_PATH. Uses a fresh headless
// Chrome profile; never attaches to the user's browser or personal tabs.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(require.resolve('playwright', {
  paths: [path.resolve(__dirname, '../tools/browser-smoke'), __dirname],
}));

(async () => {
  const url = process.argv[2] || 'http://127.0.0.1:8621/?nocard';
  if (!['localhost', '127.0.0.1'].includes(new URL(url).hostname)) {
    throw new Error('Smoke test expects a local fixture server');
  }
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const messages = [];
  const errors = [];
  const reportDir = path.resolve(__dirname, '../games/toolchain-smoke');
  try {
    const page = await browser.newPage();
    page.on('console', msg => messages.push(msg.text()));
    page.on('pageerror', error => errors.push(error.message));
    const response = await page.goto(url);
    if (response.status() !== 200) throw new Error(`HTTP ${response.status()}`);
    await page.waitForFunction(() => !document.getElementById('start').disabled, undefined, { timeout: 60000 });
    const features = await page.evaluate(() => ({
      isolated: crossOriginIsolated,
      jspi: typeof WebAssembly.Suspending === 'function',
      webgpu: !!navigator.gpu,
      gpuInfo: Module.gpuInfo,
    }));
    const stopped = page.waitForEvent('console', {
      predicate: msg => /^\[ee\] stopped after \d+ frames, \d+ cycles: Exit$/.test(msg.text()),
      timeout: 30000,
    });
    await page.locator('#start').click();
    await stopped;
    await page.waitForFunction(() => document.getElementById('status').textContent === 'Halted: Exit', undefined, { timeout: 5000 });
    if (errors.length) throw new Error(errors.join('\n'));
    const result = { status: 'pass', browser: browser.version(), features,
      assertion: 'Recompiled original MIPS fixture reached its Exit syscall in browser WASM.',
      gameplayVerified: false, messages };
    fs.writeFileSync(path.join(reportDir, 'browser.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    fs.writeFileSync(path.join(reportDir, 'browser.json'), JSON.stringify({
      status: 'fail', error: error.message, errors, messages,
    }, null, 2) + '\n');
    throw error;
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
