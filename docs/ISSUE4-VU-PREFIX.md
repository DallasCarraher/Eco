# Issue 4: bounded prefix comparison

This continuation investigates the saved invocation that exceeded whole-chain
checking's 8,192-continuation guard. It does not raise that guard or change VU
execution semantics. The existing native flags fix and its image results are
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
