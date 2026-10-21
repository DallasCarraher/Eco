# Eco

An experimental effort to run **Jak and Daxter: The Precursor Legacy** in a
browser using WebAssembly and WebGPU.

**Status: experimental Jak boot; no playable scene verified.** The supplied
USA Rev 1 disc boots through driver loading and into GOAL object initialization
in the native runner. Heap snapshot support is being developed to translate
the code that GOAL loads and relocates during startup. A small,
original MIPS test program has been translated to C++, compiled for native
Apple Silicon and WASM, and executed successfully in headless Chrome with
WebGPU available. It does not draw a scene or establish gameplay compatibility.
The original test program also runs in Chrome; Jak's browser behavior is a
separate milestone.

Eco builds on [PS2 Web Recomp](https://github.com/snuri00/ps2-web-recomp) by
snuri00, starting at commit `6526f4803d98e10de50bea3af104a4d26e9df033`.
Its source, history and MIT license are retained. See [upstream documentation](UPSTREAM.md)
for the engine design. [OpenGOAL](https://github.com/open-goal/jak-project)
is an architectural reference for Jak's GOAL loader and game behavior.

## Local setup (macOS / Apple Silicon)

```sh
brew install bash cmake ninja
/opt/homebrew/bin/bash scripts/setup.sh
```

Setup installs a project-local Emscripten SDK and downloads wgpu-native.
SDL2 is optional for the native window (`brew install sdl2`). The diagnostic
probe uses the headless runner. Upstream also supports Linux; Eco's helpers
currently target the tested macOS environment.

## Test your Jak 1 disc

Copy your own ISO here or keep it elsewhere. `.iso` and `.ISO` files are already
ignored, as are game folders, generated translations, SDKs, builds, logs and
saves. No game files are included.

Inspect the disc, then run the bounded native compatibility probe:

```sh
python3 scripts/jak_probe.py "/path/to/Jak and Daxter.iso"
python3 scripts/jak_probe.py "/path/to/Jak and Daxter.iso" --run
```

The probe checks `SYSTEM.CNF` and expected Jak 1 archive names. It links the ISO
rather than copying it, explores for 600 frames per round (up to two rounds),
and stops the process tree after 15 minutes. Results go in `games/jak1/`.
Use `--timeout SECONDS` to change the limit, or `--web` to include the WASM build.

The first baseline probe stops when Jak calls heap-loaded GOAL code. Eco's
experimental path captures missed pages, checks their instruction words, and
uses Jak 1's reciprocal type/symbol metadata to seed linked functions in batches:

```sh
python3 scripts/jak_probe.py "/path/to/Jak and Daxter.iso" --run --goal-functions --rounds 100
```

This is a fixed-address snapshot experiment, not a complete relocatable GOAL
loader. Code pages can change during linking; the probe sets
`PS2_WINDOW_FULL=1` to require full instruction matching. `--capture-heap`
captures only observed misses without discovering additional tagged functions.

For the supplied USA Rev 1 disc, an additional experiment precompiles V3 object
initialization routines from CGO/DGO archives. Supported patched immediates are
read from live memory; opcode/register bits and branch instructions still must
match. Templates relocate to their actual call site, including when an archive
uses a different heap. Other code segments still use captured pages; this is
not a complete relocatable GOAL loader or a verified configuration for other releases:

```sh
python3 scripts/jak_probe.py "/path/to/Jak and Daxter.iso" --run --toplevel-templates --rounds 60
```

**A completed build is not proof that the game works.** Check `probe.json`,
`pipeline.log`, `explore.log`, and captured frames. The runtime can halt while
the upstream pipeline still exits successfully.

Once a browser build exists:

```sh
python3 scripts/serve.py build/web-jak1 games/jak1/disc.iso
```

Open `http://127.0.0.1:8620/?PS2_WINDOW_FULL=1` in current Chrome or Edge for
heap experiments. The local server supplies
the isolation headers required for WASM threads and supports disc range reads.

## Verify the toolchain without game data

```sh
python3 scripts/jak_smoke.py --web --live-template
python3 scripts/serve.py build/web-toolchain-smoke games/toolchain-smoke/disc.iso 8621
```

The original smoke program tests live-patched LUI/ORI/ADDIU and signed SW/LW
immediates before executing the PS2 Exit syscall. Its synthetic ISO is
built with macOS `hdiutil`. Native execution is checked during the build;
browser execution is a separate Playwright check, run in another terminal:

```sh
npm install --prefix tools/browser-smoke --no-save --package-lock=false playwright
node scripts/jak_browser_smoke.cjs
```

This uses installed Google Chrome in a fresh headless profile and writes
`games/toolchain-smoke/browser.json`. It asserts the final Exit message from
WASM; it does not test rendering, sound, controls, or Jak gameplay.

## Current technical question

Jak loads GOAL objects from CGO/DGO archives and relocates code into its heap.
The inherited engine handles boot ELFs, SNR2 modules, and certain fixed code
windows. Eco adds observed heap snapshots and fixes dispatch selection when
multiple snapshots match a page but offer different entry points. Supporting
the full game still requires addressing every code-loading path, graphics,
audio, controls and saves, then verifying browser gameplay.

## Regression checks

```sh
python3 -m unittest discover -s scripts -p test_heap_windows.py -v
cmake --build build/tools --target dispatch_snapshot_test
build/tools/dispatch_snapshot_test
cmake --build build/tools --target analysis_boundary_test
build/tools/analysis_boundary_test
```

These tests use synthetic memory and original test code, with no disc required.
The browser smoke check also exercises a template relocated from offset zero
to a live heap address. `scripts/jak_browser_probe.cjs` records an actual local
Jak build's console, frame/primitive counters and canvas in `games/jak1/`,
without declaring the game playable. Build scripts default to four compiler
jobs; set `PS2_BUILD_JOBS` to override that limit.

Eco is unofficial and not affiliated with Sony or Naughty Dog. Do not commit or
publish disc images, extracted assets, or generated translations of game code.
The inherited engine is MIT licensed; see [LICENSE](LICENSE) and upstream notices.
