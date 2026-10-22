// Fresh headless Chrome profile, localhost-only fixture, no personal tabs.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {chromium} = require(process.argv[3]);
const output = path.resolve(process.argv[2]);
const build = path.resolve(process.argv[4] || path.join(output, 'build'));
const allowedModes = ['plain-short', 'plain-long', 'complete', 'budget'];
const modes = process.argv[5] ? [process.argv[5]] : allowedModes;
if (modes.some(mode => !allowedModes.includes(mode))) throw Error('Unknown fixture mode');
const html = mode => `<!doctype html><meta charset="utf-8"><title>Original VU fixture</title>
<script>
window.fixture = {messages: [], errors: [], done: false};
window.Module = {
  noInitialRun: true,
  // Emscripten caches libc's environment during initialization. Setting ENV in
  // onRuntimeInitialized is too late for worker-side getenv in this fixture.
  preRun: [() => {
    if (${JSON.stringify(mode)} === 'complete' || ${JSON.stringify(mode)} === 'budget') Module.ENV.PS2_VU_CHECK = 'all';
    Module.ENV.PS2_VU_JIT = '0';
  }],
  print: s => fixture.messages.push(s), printErr: s => fixture.messages.push(s),
  onAbort: s => { fixture.errors.push(String(s)); fixture.done = true; },
  onExit: code => {
    fixture.exit_code = code;
    try {
      fixture.files = {};
      for (const suffix of ['regs.bin','mem.bin','packets.bin','pipe.txt','queue.bin']) {
        const bytes = Module.FS.readFile('/final-' + suffix);
        fixture.files[suffix] = Array.from(bytes);
      }
    } catch(e) { fixture.errors.push(String(e)); }
    fixture.done = true;
  },
  onRuntimeInitialized: () => {
    Module.callMain(['/code.bin', ${JSON.stringify(mode)}, '/final']);
  }
};
</script><script src="/vu_worker.js"></script>`;
const server = http.createServer((req, res) => {
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
  const url = new URL(req.url, 'http://127.0.0.1');
  if (url.pathname === '/') {
    const mode = url.searchParams.get('mode');
    if (!modes.includes(mode)) { res.writeHead(400).end(); return; }
    res.setHeader('Content-Type', 'text/html'); res.end(html(mode)); return;
  }
  const name = path.basename(url.pathname);
  if (!/^vu_worker\.(js|wasm|data|worker\.js)$/.test(name)) { res.writeHead(404).end(); return; }
  const file = path.join(build, name);
  if (!fs.existsSync(file)) { res.writeHead(404).end(); return; }
  res.setHeader('Content-Type', name.endsWith('.js') ? 'application/javascript' : name.endsWith('.wasm') ? 'application/wasm' : 'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  const report = {browser: browser.version(), cases: {}, jit_enabled: false};
  try {
    for (const mode of modes) {
      const context = await browser.newContext();
      const page = await context.newPage();
      const errors = [], consoleMessages = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('console', msg => consoleMessages.push(msg.text()));
      try {
        await page.goto(`http://127.0.0.1:${server.address().port}/?mode=${mode}`);
        await page.waitForFunction(() => window.fixture?.done, undefined, {timeout: 60000});
        const result = await page.evaluate(() => ({...fixture, isolated: crossOriginIsolated}));
        result.console_messages = consoleMessages;
        result.errors.push(...errors);
        if (!result.isolated) result.errors.push('Cross-origin isolation missing');
        const dir = path.join(output, mode); fs.mkdirSync(dir);
        for (const [suffix, bytes] of Object.entries(result.files || {})) fs.writeFileSync(path.join(dir, 'final-' + suffix), Buffer.from(bytes));
        delete result.files;
        report.cases[mode] = result;
      } catch(e) {
        report.cases[mode] = {errors: [...errors, e.message], messages: consoleMessages};
        throw e;
      } finally {
        fs.writeFileSync(path.join(output, 'browser.json'), JSON.stringify(report, null, 2)+'\n');
        await context.close();
      }
    }
  } finally {
    await browser.close(); await new Promise(resolve => server.close(resolve));
  }
})().catch(e => { console.error(e); server.close(); process.exitCode = 1; });
