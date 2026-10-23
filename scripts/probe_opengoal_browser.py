#!/usr/bin/env python3
"""Run an ignored generated fixture in a fresh headless Chrome process (no GPU).

The fixture must append output to #output. This is execution evidence only.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import threading
import time


class OutputParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.output = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'pre' and dict(attrs).get('id') == 'output':
            self.inside = True

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.output += data


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--attempt', default='browser-1')
    parser.add_argument('--chrome', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    attempt = root / args.attempt
    attempt.mkdir(exist_ok=False)
    profile = attempt / 'chrome-profile'
    if profile.exists():
        parser.error('fresh profile required')
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    command = [str(args.chrome), '--headless=new', '--no-first-run', '--disable-gpu',
               '--user-data-dir='+str(profile), '--dump-dom', '--virtual-time-budget=5000',
               f'http://127.0.0.1:{server.server_port}/index.html']
    started = time.monotonic()
    try:
        with (attempt/'browser-dom.html').open('w') as output, (attempt/'chrome.log').open('w') as log:
            result = subprocess.run(command, stdout=output, stderr=log, timeout=30)
        parsed = OutputParser()
        parsed.feed((attempt/'browser-dom.html').read_text())
        dom = parsed.output
        (attempt/'trace.txt').write_text(dom)
        passed = (result.returncode == 0 and 'RESULT 205 yields=3 ticks=44' in dom
                  and 'resume depth=3 tick=44' in dom and 'BROWSER_ERROR' not in dom)
        report = dict(status='pass' if passed else 'failed', exit_code=result.returncode,
                      browser=subprocess.check_output([str(args.chrome), '--version'], text=True).strip(),
                      backend='WebAssembly CPU; GPU disabled; no rendering tested',
                      wall_seconds=time.monotonic()-started)
        (attempt/'browser.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report))
        return 0 if passed else 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == '__main__':
    raise SystemExit(main())
