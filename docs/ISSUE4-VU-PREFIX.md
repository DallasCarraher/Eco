# Issue 4: bounded prefix comparison

This continuation investigates the saved invocation that exceeded whole-chain
checking's 8,192-continuation guard. It does not raise that guard. The
initial diagnostic change preserves execution semantics; the subsequent Q
correction is described below. The existing native flags fix and its image results are
recorded in [the preceding report](ISSUE4-VU-FLAGS.md).

## Method and limits

The snapshot is the frame-192 root `8A7C5336C2223702`, entry `0020`, saved at
zero-based chain index 348. Snapshot files, the preserved runner and generated
inventory were rechecked against the previous sealed report before reuse.
Existing builds/translations are read-only inputs to a new standalone replayer;
no game boot, asset generation, ISO read, API/model call or matrix rerun occurs.

The compiled prefix runs the root and at most 8,192 continuations, saving its
next dispatch PC, raw registers, memory, packets and flag/Q pipe. An optional
smaller prefix is allowed; a larger one is rejected. It records a partial
status and exits 4 at the continuation guard instead of discarding the state.
The original full-chain runtime diagnostic still aborts at its existing guard.

The interpreter starts from the same original snapshot and executes continuously
to the compiled prefix's issue-clock delta, capped below its existing one-million
instruction ceiling. Its checkpoint occurs before the next instruction, with
no Q flush, TPC rewrite, pipeline reset or branch-history reset. Next PC, next
sequential PC, pending end state and branch history are recorded. This is not
an interpreter split/restart at each compiled dispatch; the first cycle showed
that such resets could mask real flag differences.

Both paths' raw registers, 16 KiB memory, length-prefixed packet streams, next
PC and issue clock are compared exactly. Pipe fields are serialized individually
for comparison, including Q fields; C++ padding is not a semantic pipe field.
Raw register snapshot comparisons remain exact. During fixture development a
normal struct assignment left trailing padding unspecified; changing the
fixture to `memcpy` restored exact snapshot bytes without changing any expected
VU result or adding a tolerance.

Matching prefix endpoints do not prove equality at every intermediate
instruction, equality of the remaining invocation, PS2 correctness or visual
correctness. A matching next PC and clock are necessary alignment checks;
repeated loops can revisit PCs. Pipeline or raw-Q differences must be reported,
not normalized away to force agreement. The interpreter checkpoint is an
observation, not a resumable standalone interpreter state: restarting from its
PC alone would discard branch/delay-slot context.

`scripts/run_vu_prefix.py` runs both subprocesses serially, clears inherited
`PS2_*` settings, hashes the inputs/tool/generated inventory, writes reports
atomically, caps each case at 900 seconds, caps its output at 8 MiB, requires
10 GiB free space and uses the fixed harness' process-group cleanup. Exit 0
means the compared endpoints match; inspect `full_invocation_compared` before
claiming a complete invocation. Partial checkpoints remain explicit. Invalid
reports, mismatches, timeout and cancellation do not become agreement.
The user's cumulative four-hour/2-GiB budget remains in force across all cycles.

## Original synthetic checks

`python3 scripts/repro_vu_dispatch_flags.py` retains all preceding status/MAC/
clip, fallback and fresh-invocation assertions. It adds an original finite loop
with 10,000 decrements and register-jump dispatches. Its compiled prefix stops
after 8,192 continuations; the uninterrupted interpreter matches that exact
49,154-instruction prefix, with counter 1,808 and next PC `0080`. The interpreter
then independently completes all 10,000 iterations within its unchanged budget
(60,002 instructions). This tests that reaching the diagnostic guard need not
mean nontermination, without continuing compiled replay past that guard.

A separate checkpoint immediately after DIV asserts that Q remains pending
and the prior architectural Q value remains intact. Branch-history and pending
end fields are checked at the loop checkpoint. No synthetic expected outputs
are changed. The wrapper's fake-subprocess tests cover partial-vs-complete
classification, visible mismatch failure, timeout cleanup, malformed status
and rejection of an existing output directory.

## Reproduction

From `/Users/dallascarraher/Developer/Eco-issue-4`, compile the isolated tool
against the preserved generated table and read-only archives:

```sh
mkdir -p local/issue4-prefix
clang++ -std=c++20 -O2 -I. -Iruntime/include -Iruntime/src scripts/replay_vu_snapshot.cpp \
  build/issue4-flags/CMakeFiles/ps2game.dir/generated/issue4-flags/vu1_table.cpp.o \
  build/issue4-flags/libps2game.a build/issue4-flags/libps2runtime.a \
  /Users/dallascarraher/Developer/Eco/third_party/wgpu-native/lib/libwgpu_native.a \
  -framework Metal -framework QuartzCore -framework Foundation -framework CoreFoundation \
  -framework IOKit -framework IOSurface -lobjc -o local/issue4-prefix/replay
python3 scripts/run_vu_prefix.py \
  --snapshot local/experiments/issue4-flags-check-validation-510/boot-idle--vu-chain-check--1--f29ec88a2acf/vu-limit \
  --runner local/issue4-prefix/replay --generated generated/issue4-flags \
  --output local/experiments/issue4-prefix-8192
```

Use a new output directory for repetition. `--continuations N` permits a
smaller positive prefix only, up to 8,192. Keep all game-derived inputs,
outputs and checkpoint files in ignored local storage. No existing build or
completed experiment directory is overwritten.

```sh
python3 scripts/repro_vu_dispatch_flags.py
python3 -m unittest discover -s scripts -p test_run_vu_prefix.py -v
python3 -m unittest discover -s scripts -p test_run_experiments.py -v
python3 scripts/test_vu_codegen.py
```

## Observed Q discrepancy and original regression

At diagnostic revision `9e14662`, both saved-prefix paths stop at next PC
`1280`, after 113,104 issued instructions and 8,192 compiled continuations.
Memory, packets and MAC/status/clip history match exactly. Raw register word
140 (Q) differs: compiled `C4824B1E`, interpreted `BE0F0ABF`. Both pipes hold
new Q `C4824B1E`, ready at clock 113,123; the checkpoint clock is 113,120.
Compiled dispatch has already published it and cleared `q_pending`, while
continuous interpretation retains old Q and the pending update. This is a
real endpoint state difference, not a padding mismatch. No VF, memory or
packet difference was observed at this checkpoint.

The original `scripts/repro_vu_dispatch_q.py` isolates the ownership error
without game inputs. DIV of 1 by 2 schedules Q; a register jump dispatches to
a consumer before readiness. MULq must retain old Q=1 under Eco's existing
seven-cycle DIV policy; after WAITQ, MULq must read Q=1/2. Exact power-of-two
results avoid rounding ambiguities. An alternate direct-branch path issues
DIV of 1 by 4 and tests its results too; it makes the shared reader's incoming
timing explicitly dynamic. This tests pipeline continuity under the existing
latency policy, not independent hardware validation of that policy.

Before correction, native compiled and fallback execution produce `(1/2,1/2)`
instead of `(1,1/2)` on the dispatch route. The boundary assertion also fails:
Q=1/2, pending=false, clock=21, ready=24. The persistent Wasm translator,
with a host callback that preserves the pipe, produces `(1,1)` because its
consumer prologue clears the pending update. The alternate route passes.
The complete failing output is `local/issue4-prefix/q-before.txt`.

Commit `227037f` preserves pending Q on active native dispatch and in the
persistent Wasm prologue/import. Native Q consumers honor an incoming pending
update even when their own compiled fragment contains no Q producer. Normal
invocation completion still flushes Q, and standalone calls retain their local
pipe behavior. It changes neither Q latency nor shared static timing analysis.
Both synthetic routes now pass for native compiled, interpreter fallback,
continuous interpreter and Node/Wasm. The boundary retains old Q and a pending
update at clock 21/ready 24. Expected results are unchanged.

All preceding native/Wasm dispatch status/MAC/clip tests, reset/fresh-invocation
checks, finite-loop/checkpoint assertions, eight native and eight Wasm codegen
regressions, and five prefix-wrapper tests pass after this correction. Logs
are `local/issue4-prefix/{q-after,flags-q,codegen-q,wrapper-q}.txt`.

The Wasm synthetic isolates generated-module prologue ownership; it is not a
browser or production-import integration replay. No browser parity or GS
changes are part of this investigation.

## Corrected prefix result and stopping point

The corrected measurement at clean revision `bf411f9` stops at the same PC
`1280`, issue delta 113,104, and unchanged 8,192-continuation budget. Registers,
memory, packets and every serialized pipe field now match exactly. The
continuous interpreter's four compared output files are unchanged from the
pre-Q-fix prefix. Compiled Q now retains `BE0F0ABF`, pending=true, ready at
113,123 with current clock 113,120. No tolerance or expected output changed.
Compiled/interpreted subprocess times are 0.3534/0.0639 seconds; the preceding
pair took 0.3353/0.0615 seconds. Both reports explicitly record
`full_invocation_compared: false`; exit 0 from the wrapper means exact endpoint
agreement, not completion of the invocation.

Artifacts in this isolated checkout:

- `local/experiments/issue4-prefix-8192/`: pre-fix mismatch, identities, exact
  commands, partial statuses, registers, pipe, memory and packet outputs.
- `local/experiments/issue4-prefix-q-fixed-8192/`: corrected exact prefix.
- `local/issue4-prefix/q-fixed/`: private VU-only generated code, objects and
  standalone binary. `build.json` records every exact build argv and SHA-256
  of each read-only archive; `local/issue4-prefix/build-q.txt` is its build log.
- `local/issue4-prefix/final-validation.json`: unchanged snapshot hashes,
  preserved generated inventory and baseline replayer hashes, interpreter
  output identity, final comparison and disk accounting.

The new standalone tool links newly generated VU objects before the preserved
EE/runtime archives; `replay_vu_snapshot.cpp` directly includes the current
interpreter. No preserved build or generated directory was rebuilt. The
original checkout is clean, and the completed overnight batch was never a
write target. Final retained build/generated/local size is 1,809,095,082 bytes
(about 1.69 GiB); free disk is about 28.1 GiB. This cycle adds less than one
second of measured game-derived prefix subprocess time, remaining well below
the cumulative four-hour limit. No subprocess limit was expanded.

Exact validation commands (run from the isolated checkout; always choose a
new experiment output directory):

```sh
python3 scripts/repro_vu_dispatch_q.py
python3 scripts/repro_vu_dispatch_flags.py
python3 scripts/test_vu_codegen.py
python3 -m unittest discover -s scripts -p test_run_vu_prefix.py -v
python3 scripts/run_vu_prefix.py \
  --snapshot local/experiments/issue4-flags-check-validation-510/boot-idle--vu-chain-check--1--f29ec88a2acf/vu-limit \
  --runner local/issue4-prefix/q-fixed/replay \
  --generated local/issue4-prefix/q-fixed/generated \
  --output local/experiments/issue4-prefix-q-fixed-repeat
```

This closes one further bounded investigation/validation cycle. It establishes
a Q pipeline handoff bug and removes the observed state discrepancy in the
saved prefix. It does not prove the full invocation or any image changed as a
result of this Q fix. The previous flag-history fix removed the measured CPU
frame-500/505/510 image gap; the individual sampled call-172 flags mismatch
still has not been uniquely linked to those pixels. Graphics-backend effects
remain separate and unmeasured here. No visual/PS2 correctness or gameplay
compatibility conclusion follows from path agreement.

A further focused validation is justified before broadening claims: build a
new private runner with this Q correction, then use `scripts/run_experiments.py`
for just boot-idle CPU compiled/interpreted through frame 510 with the existing
capture checkpoints. This would measure whether pending-Q preservation changes
any observed image while checking the earlier image agreement still holds.
It needs a disk-budget check before making another full build. The precise
remaining whole-chain coverage blocker is the invocation exceeding 8,192
continuations; this prefix experiment does not remove it. Do not increase the
guard or claim exhaustive agreement from this report.

## Post-Q-fix image validation

The next user-authorized continuation ran only boot-idle CPU compiled and CPU
interpreted through frame 510, serially with five-frame capture checkpoints.
The measurement used clean source `da6352fa70669c9b3a0c6e420ed79d65322a2b27`.
No execution correction was added in this continuation. The committed
`experiments/jak1-vu-q-validation.json` is byte-identical to the ignored manifest
used for measurement; it excludes the known guard-blocked whole-chain case.

A private runner in `local/issue4-q-images/` links the previously corrected VU
objects and freshly compiled interpreter/JIT/host objects before the preserved
read-only EE/runtime archives. It does not duplicate or rebuild a full game
archive. The harness generated inventory covers the corrected VU sources;
`local/issue4-q-images/build.json` additionally records exact build argv,
archive/object hashes and the final binary hash. Preflight rechecked those
archive hashes and the baseline full generated inventory before reuse. ISO and
ELF identities match the preceding flag-fix image experiment. Game-derived code
and all outputs remain ignored; the completed overnight batch is unchanged.

| CPU case | Frames | Guest cycles | Seconds | Captures |
| --- | --- | --- | --- | --- |
| Compiled | 510 | 2,524,450,548 | 93.386 | 98 |
| Interpreted | 510 | 2,524,450,548 | 95.044 | 98 |

All 98 available captures match byte-for-byte between the new paths. Each new
path also matches its corresponding pre-Q-fix capture set from
`local/experiments/issue4-flags-validation-510/`: zero differing pixels and
maximum channel delta zero in each comparison. Frame 480 and 510 captures are
present. Thus the Q correction has no measured CPU image effect on this route,
while retaining the earlier flag correction's measured image convergence.
This does not establish state equality between every intermediate instruction.

**Coverage correction:** earlier prose incorrectly reported 102 captures in the
first-cycle and flag-fix validations. Their sealed reports actually contain 98,
covering frames 25 through 510 every five frames. Requested frames 5, 10, 15
and 20 are absent from both paths, including this new batch. Those historical
prose counts are corrected; no archived report, capture, expected result or
comparison rule changed. The harness preserves `reliable: false` for incomplete
requested coverage even though every available image agrees. There is only one
new run per variant, so new-build repeatability remains unestablished. This
ordinary two-case batch does not measure VU-check coverage or final counters.

Evidence and exact measurement command, from the isolated checkout:

```sh
python3 local/issue4-q-images/build.py
python3 scripts/run_experiments.py \
  --manifest local/issue4-q-images/manifest.json \
  --iso '/Users/dallascarraher/Developer/Eco/Jak and Daxter - The Precursor Legacy (USA) (En,Fr,De,Es,It) (Rev 1).iso' \
  --runner local/issue4-q-images/ps2run \
  --elf games/jak1/disc/SCUS_971.24 \
  --generated local/issue4-prefix/q-fixed/generated \
  --output local/experiments/issue4-q-images-510
python3 local/issue4-q-images/compare.py
```

These are archived commands, not instructions to overwrite the completed
runner/output. A repeat needs new build/output locations and a fresh cumulative
budget check. The committed manifest can replace the ignored manifest path.
`build.py`, `build.json`, `build.txt`, `preflight.json`, `harness.txt` and
`comparison.json` are in `local/issue4-q-images/`. The comparison program verified
431 sealed files across both old and new reports, and checked exact bytes for
all common captures. The new batch's own report, immutable case directories,
logs and captures are in `local/experiments/issue4-q-images-510/`.

Measured game subprocess time added here is 188.429 seconds; no case approaches
900 seconds. Cumulative measured game replay remains below 20 minutes, excluding
short builds/synthetics, well below four hours. Retained build/generated/local
artifacts total 2,028,410,978 bytes (about 1.89 GiB) after validation, with about
27.9 GiB free. Only about 113 MiB remains under the 2 GiB cap, less than another
two-case capture batch; do not rerun it under the current retained-output budget.

This validation cycle is complete. The Q state discrepancy is fixed and its
original synthetic regression passes; its observed saved prefix is exact, and
no image change was measured through frame 510. The original sampled flags-only
call remains unproven as the unique image cause. Full-chain coverage is still
blocked by the unchanged 8,192-continuation guard. GPU/backend effects, browser
integration and independent PS2/visual correctness remain outside this result.
No further broad replay is justified by a newly observed image discrepancy.
A separately authorized investigation of bounded whole-invocation coverage or
an independent reference comparison would address the remaining uncertainty.
