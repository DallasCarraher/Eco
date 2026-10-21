# Issue 4: VU dispatch-boundary investigation

This bounded cycle found a specific flag-liveness/latency discrepancy affecting
VU registers, memory and emitted GIF packets. No execution fix is applied.
Agreement between Eco paths does not establish PS2 or visual correctness.
The frame-510 image cause remains unproven.

## Frozen starting evidence

The original checkout was clean at `17a598b6f412c2a6ac6026a6ee6d1b1f8ed335c1`.
Work uses branch `codex/issue-4-vu-divergence` in a separate `Eco-issue-4`
checkout, copied generated inputs and a dedicated `build/issue4` build.
The completed `local/experiments/jak1-overnight-20261020-224647` batch in the
original checkout was read without modification. Before copying inputs,
SHA-256 checks matched its recorded binary, generated inventory, ISO, ELF and
manifest. This verifies input identity, not original binary build provenance.

CPU-backend captures at frame 480 are exactly equal. At frame 510 the
interpreted capture contains pale horizontal streaks absent from the compiled
capture, within rows 218–279. Exactly 9,994 pixels differ, with maximum channel
delta 191 at this frame. The archived 223 maximum covers the full comparison,
not specifically frame 510. Neither capture is asserted correct. The separate
CPU/GPU delta (first sampled at frame 210, maximum 3) is not investigated here.

## What the original sampled comparison establishes

`PS2_VU_CHECK=1` increments a sampling counter before checking every 64th
eligible compiled invocation. That counter can also be incremented by the JIT
check. Its printed `call` value is a zero-based sampled-check index, not a guest
VU invocation number. Summary counts are periodic, not comprehensive totals.

The compiled function runs with real kick side effects, while a capture hook
records its escape instead of executing the continuation. The checker saves
compiled registers/data memory, restores the input, executes `run_fast` dry,
compares only if there was no escape, then restores the compiled result and
resumes its continuation. Raw register `memcmp` can include state omitted from
the human log (ACC, TPC, padding). The `flags` field combines MAC/status/clip.
The dry run suppresses GIF submission; the original checker does not compare
packet contents or flag-pipeline history. An escaping prefix and a full
interpreter invocation are not comparable endpoints.

The early sampled `7A23D81EC7B8D0D2`, entry `0040`, call 172 establishes a
flags-only final-register disagreement for that sampled nonescaping call.
Its generated function has no MAC/status reads or writes. Interpreter flag
usage is scanned over all VU code memory; generated flag liveness is scoped to
reachable instructions. This explains why that diagnostic can flag elided
writes. It does **not** establish that this particular call causes frame 510.

## Located execution discrepancy

The opt-in `PS2_VU_CHECK=all` diagnostic compares each eligible compiled-root
**complete dispatch chain** with an uninterrupted interpreter invocation from
identical registers and 16 KiB memory. Compiled continuations still dispatch
through their normal compiled lookups, with interpreter fallback when absent.
Both packet sequences are collected; only the compiled sequence is submitted.
The final compiled state is restored. Neither implementation is an oracle.

A preliminary comparison that split the interpreter at register jumps found
only flag differences through 510. That experiment artificially reset the
interpreter pipeline too, masking the relevant cross-boundary discrepancy.
Its 17 captures still matched the archived compiled frames exactly. An earlier
expensive full-interpreter/per-prefix check was deliberately cancelled and
retained. These exploratory reports are not exhaustive evidence of agreement.

The first complete-chain discrepancy occurs at guest frame 192, root key
`E8F821F8F25E63CE`, entry `0010`, zero-based chain index 347. Packets occupy
19,960/24,512 bytes in the diagnostic's length-prefixed representation.
The saved call reproduces compiled/interpreted registers, memory and packets
byte-for-byte offline. Their final VU data memory differs at 92 words.

A bounded offline instruction-prefix trace locates the first VI disagreement
at the FSAND at micro PC `1358`: VI2 is 0 compiled versus 2 interpreted after
that instruction. The preceding register-jump fragment at `16A0`/`16A8` has
flag-producing upper operations, but no local flag reader, so generated code
elides their flag updates. The reader at `1358` is in the continuation.
An earlier Q-register difference at a dispatch boundary is transient and is
not claimed to cause this VI difference. Trace prefixes ignore flags only to
locate subsequent VI/memory changes; original mismatch checks remain exact.

The trace was capped at 10,000 instructions per implementation (both stopped
at the cap), and the decisive VI difference is within the common prefix at
instruction index 434. It is not a full instruction trace or hardware proof.

## Original synthetic regression and why there is no narrow fix

Run `python3 scripts/repro_vu_dispatch_flags.py`. It requires CMake, clang++
with C++20 `std::format`, and Node supporting Wasm SIMD/tail calls. Everything
is built in private temporary directories, with no game input. Exit 1 honestly
reports the unresolved regression; it is not marked expected-failure or given
a tolerance to make the suite pass.

The original seven instruction pairs jump via VI9 to a separate generated
fragment. The jump's delay slot computes `SUB.x` of 1 minus 2; two NOPs and two
FSANDs read status bit 1 in the target, followed by an end delay slot. Expected
reads are `(0, 2)`, using a four-issue-cycle flag visibility delay across an
ordinary JR, without a microprogram end/reset. Native and Wasm generated
dispatch both return `(0, 0)`; continuous Eco interpretation returns `(0, 2)`.
The expectation is explicit and is not inferred solely from path agreement.
Sony's *VU User's Manual* v6.0 sections 3.3, 3.4.4 and the FSAND/JR references
describe arithmetic status flags, staged flag writeback, logical status reads
and jump delay slots; a [public transcription](https://studylib.net/doc/25815876/vuusersmanual.158394566)
was consulted. The exact timing assertion also matches Eco's existing
`FlagPipe::mac_slot` policy, but has not been verified on hardware.

`python3 scripts/repro_vu_dispatch_flags.py --force-native-flags` forces
native producer flag stores and changes `(0, 0)` to
`(2, 2)`, still failing `(0, 2)`. Each generated function currently constructs
and initializes its own FlagPipe, exposing the latest raw flags at the next
entry rather than retaining their delayed history. Therefore changing liveness
alone is insufficient. A justified fix needs a flag-history handoff contract
across native/Wasm dispatch and interpreter fallback, with microprogram
start/end distinguished from a host dispatch boundary. This cycle stops with
the useful original reproducer instead of landing an incomplete correction.

## Diagnostic limits and reproduction

`all` compares compiled-chain roots; it is not exhaustive hardware execution
coverage. Initial interpreter-only roots are outside this diagnostic. Final
chain/continuation/fallback/mismatch counts are separately reported on normal
process exit. Legacy sampled totals remain unknown. Signals/abort can prevent
the final line; partial observations stay partial.

The packet collector aborts above 1 MiB per chain and the compiled continuation
loop aborts above 8,192 segments. Snapshot output is fixed-size input/output
state plus bounded packet streams, once for the first discrepancy beyond
flags. A supplementary first-mismatch flags snapshot is also bounded. The
experiment runner enforces 900 seconds per subprocess, four hours active time,
2 GiB case output and 10 GiB free space. Keep all game-derived files ignored;
new build/copy/diagnostic outputs must also fit the overall user budget.

Use an isolated checkout, copy verified generated inputs and ELF into its
ignored `generated/jak1` and `games/jak1/disc/SCUS_971.24`, then:

```sh
cmake -S . -B build/issue4 -DPS2_GENERATED="$PWD/generated/jak1" -DCMAKE_BUILD_TYPE=Release \
  -DPS2_WGPU_DIR=/Users/dallascarraher/Developer/Eco/third_party/wgpu-native
cmake --build build/issue4 -j 4
python3 scripts/run_experiments.py --manifest experiments/jak1-vu-issue4.json \
  --iso '/Users/dallascarraher/Developer/Eco/Jak and Daxter - The Precursor Legacy (USA) (En,Fr,De,Es,It) (Rev 1).iso' \
  --runner build/issue4/ps2run --elf games/jak1/disc/SCUS_971.24 \
  --generated generated/jak1 --output local/experiments/issue4-validation-510
```

The wgpu installation above is used as a read-only external dependency; no
writable build/generated/game-output directory is shared. The validation
manifest runs only CPU compiled, CPU interpreted and whole-chain check, serially
to 510, capturing every five frames, one repetition. Existing archived repeats
provide prior repeatability evidence; this three-case run alone does not.

For offline replay on this macOS host (same ABI as snapshot), compile:

```sh
clang++ -std=c++20 -O2 -I. -Iruntime/include -Iruntime/src scripts/replay_vu_snapshot.cpp \
  build/issue4/CMakeFiles/ps2game.dir/generated/jak1/vu1_table.cpp.o \
  build/issue4/libps2game.a build/issue4/libps2runtime.a \
  /Users/dallascarraher/Developer/Eco/third_party/wgpu-native/lib/libwgpu_native.a \
  -framework Metal -framework QuartzCore -framework Foundation -framework CoreFoundation \
  -framework IOKit -framework IOSurface -lobjc -o local/issue4/replay
```

Pass `<case-dir>/vu-first` (without a suffix), `compiled` or `interpreted`, and
a new ignored output prefix. The tool writes registers, memory and packets;
compare those with the saved `vu-first-*-memory.bin`, `vu-first-*.bin` and
`vu-first-*-packets.bin`. Its output is native-ABI diagnostic data, not a
portable save state. Keep generated table/code files from the recorded identity.

## Final validation and continuation decision

Frozen measurement revision: `34dc9441a14bc2410b95fcaca187b3e3c0717fc2`, clean.
All three cases completed 510 frames, each at 2,524,450,548 guest cycles:

| Case | Seconds | Result |
| --- | ---: | --- |
| CPU compiled | 87.5 | 510-frame limit |
| CPU interpreted | 97.2 | 510-frame limit |
| CPU whole-chain check | 89.5 | 510-frame limit |

Final normal-exit chain counters: 21,852 compiled-root chains; 3,637,453
continuations; zero interpreter fallbacks; 7,153 exact mismatches, including
3,974 with a discrepancy beyond flags. These are the diagnostic's defined
chain scope, not totals of all VU execution or hardware validation. They cannot
be equated with the archived 62 sampled nonescaping mismatches. Legacy sampled
final/eligible/skipped counts remain unknown.

All 102 whole-chain-check capture hashes exactly match the plain compiled case.
For each plain path, all 17 overlapping archived capture hashes match as well.
Frame 495 is equal between paths; frame 500 differs at 9,900 pixels (maximum
channel delta 122); frame 510 still differs at 9,994 pixels (maximum 191).
Frame 500 is the first unequal five-frame checkpoint, not a proof that earlier
unsampled frames are equal. No rendering correction is claimed.

The saved trace also demonstrates a control-flow consequence: after FSAND
produces differing VI2 at index 434, the IBNE on VI2 at micro PC `1370` sends
the paths to `1380`/`1390` after its delay slot, at index 438. Thus this is a
concrete VU execution/state divergence, rather than a GS backend effect or a
comparison of unmatched endpoints. The counterfactual flag-store experiment
still shows that liveness alone is insufficient. No source execution fix was
landed, and the particular sampled `7A23...` flags mismatch has not been
causally tied to the frame-500/510 images.

Validation: all 21 runner tests passed; all eight existing native and eight
existing Wasm VU regressions passed. The new synthetic reproducer deliberately
returns exit 1 with native/Wasm `(0,0)` against `(0,2)`. Its forced-native-flags
variant returns exit 1 with native `(2,2)` and Wasm `(0,0)`. No expected output,
tolerance or mismatch reporting was changed to hide these failures. The
committed offline replay tool reproduces the saved registers, memory and
packet streams for both paths exactly.

Artifacts are under the isolated checkout's ignored storage:

- `local/experiments/issue4-validation-510/`: final manifest snapshot, full
  identities, reports, logs, 102 captures per case and first-discrepancy dumps.
- `local/experiments/issue4-chains-510/boot-idle--vu-all--1--2a234941e76c/`:
  original complete-chain snapshot used for offline tracing and replay.
- `local/experiments/issue4-segments-510/`: exploratory split-boundary result.
- `local/experiments/issue4-all-510/`: deliberately cancelled expensive probe.
- `local/issue4/`: identity verification, validation analysis, bounded trace
  prefixes and trace analysis, synthetic/test/build logs, preview images and
  local trace construction scripts. `reproduce-trace.sh` records the exact
  local trace command; `make_trace.py` adds bounded hooks to private copies of
  the generated VU files. No such files are committed.

Exact offline replay of the investigated snapshot, after the compilation
command above (the two output prefixes must be new):

```sh
local/issue4/replay \
  local/experiments/issue4-chains-510/boot-idle--vu-all--1--2a234941e76c/vu-first \
  compiled local/issue4/replayed-compiled
local/issue4/replay \
  local/experiments/issue4-chains-510/boot-idle--vu-all--1--2a234941e76c/vu-first \
  interpreted local/issue4/replayed-interpreted
python3 -m unittest discover -s scripts -p test_run_experiments.py -v
python3 scripts/test_vu_codegen.py
python3 scripts/repro_vu_dispatch_flags.py
python3 scripts/repro_vu_dispatch_flags.py --force-native-flags
```

The last two commands are expected to exit 1 until corrected. The measurement
output directory in the earlier command already exists locally: choose a new
ignored directory to repeat, and preserve prior reports.

Recorded game replay time across the exploratory and validation reports is
584.5 seconds, including 132.1 seconds for the cancelled probe. No case reached
its 900-second limit. Build, copied generated inputs and local artifacts total
about 913 MiB at the end (plus small previews in the original checkout), below
2 GiB; free disk stayed about 30 GiB, above 10 GiB. Synthetic builds were
private temporary directories and were removed. All original-batch listed
artifact hashes were reverified after validation; the original tracked tree
was not modified.

Further investigation is justified, but is not started in this cycle. The
smallest next experiment is to keep one flag-history context across the two
synthetic native/Wasm dispatch fragments while retaining the producer writes,
then require `(0,2)` in both and add an interpreter-fallback boundary variant.
The precise blocker to a liveness-only fix is lost in-flight flag history at
host dispatch. Once that handoff contract is tested, repeat the three-case
510-frame comparison to measure effects on the saved call and images. Q and
branch history across dispatch remain separate uncertainties; the transient Q
difference is not fixed or asserted harmless. Do not treat removal of this
one discrepancy as visual, hardware or gameplay signoff.
