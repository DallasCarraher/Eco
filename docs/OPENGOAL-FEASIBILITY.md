# OpenGOAL feasibility: partial execution, rendering blocked

October 22–23, 2026. Eco base `dd90204145060ae89408df4cf4e5da1aca3f1378`;
OpenGOAL `c983c5f103d6b291849e8084a89df5de77f1cc67`, clean throughout.
Work is isolated in `Eco-opengoal-feasibility`, branch
`codex/opengoal-feasibility`. No Eco game replay or reference capture was resumed.

**The two required proofs are not complete. Do not choose a trilogy engine yet.**
A real recovered function now runs as mechanically generated C++ in native and
browser builds, retaining nested caller locals across browser event turns.
However, this uses explicit experimental runtime adapters, an original data
fixture, and no native OpenGOAL execution oracle. Representative rendering is
blocked at the missing browser renderer interface, and was not run.

## Implemented experiment and dependency boundary

`experiments/opengoal/ir_probe.cpp` links against the existing OpenGOAL compiler.
It calls `Compiler::compile_object_file` and exports every function's IR **before
register allocation**. This requires no upstream source changes. The appropriate
production emission point is between frontend lowering and `color_object_file`;
`Compiler::codegen_object_file` currently invokes the machine-code
`CodeGenerator`. Upstream's public README describes x86, but this actual revision
also implements ARM64. The native compiler built successfully on Apple Silicon.

`scripts/prepare_opengoal_path.py` extracts the unchanged real Jak 1
`actor-wait-for-period` definition from `levels/misty/misty-obs.gc` (line 1207).
Its SHA-256 is
`d600d9373cbfad9bef8a2f1d1f2fea8ff676acec57a98e0c13f33eade62aea43`.
GOAL remains authoritative: no handwritten C++ version of that function exists.
The experiment supplies a 64-bit test time type and two explicit macro adapters:

- `current-time`: the game's display counter access becomes a host clock service.
- `suspend`: the game's machine-stack hook becomes a host continuation service.

The real function calls these through macro expansion. Two original GOAL callers
in `experiments/opengoal/nested.gc` surround it. The outer caller loads a duration
from a real eight-byte little-endian file through another implemented service;
this is **original fixture data, not a game object/asset loader**. The inner caller
retains `77`, the outer retains `123`, and the inner adds `5` after the wait.

`scripts/opengoal_cpp.py` lowers the reachable IR graph to C++ switch blocks with
explicit virtual registers, program counters, caller return destinations and
owned continuation frames. It supports only the observed integer constants,
register copies, function-symbol lookup, false-symbol lookup, addition,
subtraction, signed less-than branches, jumps, calls and returns. It rejects
unknown opcodes, unresolved functions, assembly-family operations, invalid branch
targets and oversized register indices before writing output. This is an
experimental backend, not an implementation of the complete GOAL ABI.

The host uses 64-bit integer register slots, numeric function IDs and a synthetic
false-symbol token (`4096`). It does not treat native code addresses as WASM
function pointers. General GOAL pointers, type/method tables, tagged object layout,
relocations, static data, vectors/floats and dynamically loaded functions remain
unsupported. Upstream memory-access IR also derives from `IR_Asm`; the blanket
rejection must eventually distinguish ordinary memory operations from raw
machine-stack manipulation. `value-reset` needs no operation for this input's
entry arguments; register-specific resets in arbitrary code are not established.

## Proof A results

| Check | Result |
| --- | --- |
| Build existing native ARM64 OpenGOAL compiler | Pass; configure 31.584 s, build 138.198 s, four jobs |
| Compile unchanged selected GOAL definition through upstream frontend | Pass; private IR exported |
| Generate C++ and run natively | Pass for the adapted fixture |
| Compile same generated state-machine mechanism to WASM; execute in Chrome | Pass for the adapted fixture |
| Nested call/return and preserved caller locals | Three yields at depth three; return values false token, 82, then 205 |
| Browser pause/resume across event-loop turns | Three timer callbacks resume ticks 42, 43, 44 (starting at 41); complete trace equals native byte-for-byte |
| Original data loading | Eight-byte duration file loaded; no game object layout/loading demonstrated |
| Compare against native OpenGOAL execution of the path | **Untested**; compiler build is not execution of the original runtime |
| Original kernel stack-switch behavior | **Unsupported** by this backend; substituted by the explicit adapter |
| Full required proof A | **Incomplete** |

The original kernel's `suspend` macro in `gkernel-h.gc` selects the thread's
suspend hook. `thread-suspend`/`thread-resume` in `gkernel.gc` save native registers,
PC/SP, copy stack bytes and transfer control through architecture-specific
assembly. Ordinary C++ returns cannot preserve those semantics. This experiment
shows a continuation mechanism but does not prove kernel process relocation,
resume hooks or native OpenGOAL parity. An actual native runtime oracle remains
necessary; no success stub or interpreter was presented as that oracle.

Native boundary runs also pass at duration zero and eight. A nine-tick request
and a truncated input file fail with exit code 2. Ten original regression tests
cover unsupported/unsafe lowering and false browser completion signals.

Browser: Google Chrome **155.0.8059.86**, fresh headless profiles, WebAssembly CPU,
GPU disabled. Browser attempt 1 failed on a JS global-name collision with
Emscripten; attempt 2 stopped after one yield using animation-frame scheduling.
Both remain private and intact. A renamed page binding plus timer scheduling
passed on attempt 3. The final nonzero-clock check also passed, preserving start
time 41 across all resumptions and completing at tick 44; this avoids a zero
initial value masking lost local state. No expectations were weakened. The browser report parses
only the output element, so result strings in scripts cannot produce a pass.

## Proof B boundary and status

**Blocked; no representative samples drawn, no native OpenGOAL output captured,
no image comparison, no frame-time measurement.** No blank canvas or setup
triangle is counted as evidence.

At this revision `game/graphics/gfx.h` exposes only `GfxPipeline::OpenGL`;
`gfx.cpp::GetRenderer` dispatches only that renderer. There is no browser backend
consuming OpenGOAL's level/character rendering packets. Eco's PS2 GS/WebGPU route
is not an OpenGOAL packet consumer. The specific missing interface is the
OpenGOAL render-state/asset-loader to browser draw-packet consumer for Tfrag/Tie
geometry, Merc character animation and texture-animation output.

Desktop adaptations would also be required: the shipped shaders declare GLSL
`410 core`; `shaders/etie.vert` uses `sampler1D`, and geometry renderers use
`glMultiDrawElements` and configurable primitive-restart indices. These are
source inspection findings, not browser API compatibility test results. A WebGPU
route needs packet/asset adaptation and shader translation; simply linking the
existing renderer into Emscripten does not supply that route. A WebGL route would
need its own measured compatibility work.

Local upstream `iso_data/jak1` contains only its ignore file; no OpenGOAL build,
extracted FR3 samples or identified native OpenGOAL captures existed at admission.
The user's Eco disc/extraction remains available and untouched. The missing
renderer interface, rather than a missing user-owned disc, blocks this proof.
Building a replacement renderer and extracting an unrestricted asset corpus was
outside this small experiment. No new dependencies were downloaded.

## Measurements and accounting

Apple clang 21.0.0; CMake 4.4.4; Emscripten 6.0.11
(`a0014542110d6078c3a1a7941fa1ddb3a2281f16`). Native generated executable: 55 KiB
(rounded). Final browser payload: WASM **146,589 bytes**, JS **69,537 bytes**,
data **8 bytes**, uncompressed. WASM declares fixed memory of **16,908,288 bytes**
(258 pages). Native maximum RSS was **1,441,792 bytes** in one tiny measured run;
wall time rounded to 0.00 s. These are fixture costs, not game estimates.
Chrome process/server run took **0.579 s**; this includes launch and virtual-time
handling and is not a frame-time benchmark. CPU/GPU game performance is unknown.

The private plan preceded configure/build: at most 900 active seconds, initially
512 MiB retained / 1 GiB peak, one shared serial lock, at least 10 GiB free.
The retained estimate was revised within the same 1 GiB reservation after native
intermediates exceeded it; they were preserved. The native build monitor sampled
801,167,919 bytes at its last in-progress maximum; completed artifacts were larger.
The final census measured 848,587,569 bytes for this checkout’s private artifacts.

Admission used the latest released `reference-pose-20261022-allocation.json`:
7,979.183 / 14,400 seconds used, 6,420.817 remaining, shared cap 8 GiB. The common
`Eco-artifact-audit/local/artifact-audit-20261021/serial.lock` serialized the
compiler configure/build; no other game/GPU process was observed. Smaller private
compile/execution steps were serial too. Weekly account usage remained 86%
available at stage checks, above the inherited 85% stop threshold. See the latest
private `opengoal-feasibility-final-allocation.json`: this cycle conservatively debits
479.259 s (179.259 s measured stages plus 300 s for all other serial steps),
bringing use to 8,458.442 / 14,400 s and leaving 5,941.558 s. Shared retained
bytes total 5,160,406,077; final free space was 12,292,423,680 bytes. No prior files were pruned, reset or overwritten.

## Reproduction

Run from the experiment worktree; substitute local paths. Outputs below must be
new ignored directories. Reserve/check the shared allocation and lock before
running, as in the recorded private plan. Commands do not themselves allocate
another budget. The build helper targets this tested macOS/Ninja configuration.

```sh
cmake -S ../jak-project -B build/opengoal-feasibility -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=OFF -DBUILD_TESTING=OFF
cmake --build build/opengoal-feasibility --target goalc -j 4
python3 scripts/build_opengoal_ir_probe.py --build build/opengoal-feasibility \
  --output local/opengoal-repro/probe
python3 scripts/prepare_opengoal_path.py --opengoal ../jak-project \
  --output local/opengoal-repro/input
local/opengoal-repro/probe/ir-probe ../jak-project \
  local/opengoal-repro/input/path.gc local/opengoal-repro/ir.json
python3 scripts/opengoal_cpp.py local/opengoal-repro/ir.json local/opengoal-repro/main.cpp
clang++ -std=c++20 -O2 local/opengoal-repro/main.cpp -o local/opengoal-repro/native
local/opengoal-repro/native local/opengoal-repro/input/duration.dat
../Eco/tools/emsdk/upstream/emscripten/em++ -std=c++20 -O2 \
  local/opengoal-repro/main.cpp -o local/opengoal-repro/timers.js \
  -sENVIRONMENT=web -sEXIT_RUNTIME=1 -sINVOKE_RUN=0 \
  -sEXPORTED_RUNTIME_METHODS=callMain,FS \
  --preload-file local/opengoal-repro/input/duration.dat@/duration.dat
cp experiments/opengoal/index.html local/opengoal-repro/index.html
python3 scripts/probe_opengoal_browser.py --root local/opengoal-repro \
  --chrome '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
python3 -m unittest discover -s scripts -p test_opengoal_cpp.py -v
```

Private actual artifacts: `local/opengoal-feasibility/`, including plan, compiler
logs, IR, generated programs, duration files, failed browser attempts and final
`final/browser-1/trace.txt`. No ISO/BIOS, game-derived source/IR/C++/WASM, assets, captures,
RAM or saves are committed. This source-only test uses no disc identity.

## Recommendation and one next step

**Obtain one specifically named missing proof next: native OpenGOAL kernel
suspension parity for this nested wait.** Do not select OpenGOAL or restart Eco
pose investigation from this partial result. Build a bounded native runtime
oracle, retain the real display-counter and suspend-hook semantics, and compare
return order and live locals against the generated continuation trace. First
measure that runtime's build footprint; a prospective 900 s / 1 GiB reservation
is an estimate, not an additional authorization or a measured cost.

The experiment concentrates the execution work in a compiler backend and runtime
ABI, which is encouraging but insufficient. Reaching Sandover still requires a
general object/type/symbol loader and dispatch, kernel/process compatibility,
representative renderer/animation/texture evidence, browser controls/camera,
audio, persistent save storage and a fresh-start route. Proof B must also be
completed before an architecture decision. Eco remains preserved and its paused
reference findings remain valid; neither implementation has established the
playable milestone.
