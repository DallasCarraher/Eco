# Issue 4 continuation: flag history across dispatch

The reduced dispatch-boundary bug is corrected: VU1 flag history now survives
compiled dispatch and interpreter fallback until the logical microprogram
invocation ends. Arithmetic flag writes are retained because an unrecorded
continuation can read them. No expected result or mismatch criterion changed.
This is not a hardware, visual-correctness or gameplay claim.

## Scope and implementation

The branch remains `codex/issue-4-vu-divergence`, in the isolated `Eco-issue-4`
checkout. Earlier builds, translations and experiment directories are retained.
New translations are in ignored `generated/issue4-flags`, with a dedicated
`build/issue4-flags`. Neither writable directory is shared with another task.

`FlagDispatch` initializes one thread-local `FlagPipe` at a logical VU1 root.
Generated native fragments use a `FlagFrame` referencing that context;
interpreter fallback joins it. VU0 uses its own local pipe. Each new root
starts from the current architectural flags, and the context guard restores
any enclosing host context on exit. It does not carry pending history across
separate microprogram invocations.

The Wasm JIT uses the same stable thread-local context address as generated
C++ in its worker. Its persistent-layout prologue retains flag rings and
loads the saved issue clock; both dispatch and end paths write that clock
back. Standalone/nonpersistent JIT layouts retain their initialization behavior.
The existing Q flush-at-dispatch policy is retained; Q and branch hazards are
not newly modeled or asserted correct.

Both code generators conservatively retain arithmetic flag producers. The
old local liveness analysis cannot establish that writes are dead across a
dynamic continuation; additionally, sticky status can retain earlier results.
The VU1 interpreter likewise retains producers even when the current code
memory contains no flag reader. A future optimization needs cross-dispatch
proof rather than entry-local reachability.

Sampled and whole-chain comparisons now snapshot and restore the shared pipe
alongside architectural registers/memory. Otherwise the dry execution would
change the live continuation's history. New first-discrepancy dumps include
the input pipe. The offline replay tool accepts this additional file, while
older root snapshots start with freshly seeded history as before.

## Synthetic and saved-call validation

The original status assertion remains `(0,2)`, including the four-issue-cycle
visibility delay. It now passes for native compiled-to-compiled, native
compiled-to-interpreter and Wasm compiled-to-compiled dispatch. Additional
original MAC and clip variants require `(0,128)` and `(0,1)` respectively,
using their four- and three-cycle history policies. These timing expectations
follow the original test derivation and Eco policy; there is no hardware test.

Each native variant runs 128 chains in plain, sampled and whole-chain-check
modes, followed by fresh-invocation, reset and VU0-isolation checks. The fallback
variant registers only its producer, so the production runtime must select
interpreter fallback. Whole-chain synthetic logs report zero mismatches in
all variants. Wasm variants run 128 two-module dispatch chains each and check
fresh invocation/reset separately. All checks pass without tolerances.

The existing eight native and eight Wasm VU regressions pass, as do all 21
experiment-runner tests. The changed `vu_jit_web.cpp` and `vu_micro.cpp` compile
with the local Emscripten compiler using SIMD/pthreads. This verifies those
translation units, not a full browser/game execution.

The original frame-192 root snapshot (`E8F821F8F25E63CE`, entry `0010`) was
replayed using the corrected generated VU files. Its complete final registers,
16 KiB memory and length-prefixed packet streams now agree exactly. Before
this correction the same snapshot had 92 differing memory words and packet
lengths 19,960/24,512. This establishes an effect on that saved execution;
image causation and residual mismatches are measured separately below.

## Input identities and exact commands

Before modifying translations, the 59 recorded VU inputs were copied into
`local/issue4-next/recorded-vu`. The prior generator produced 110 programs,
including 51 jump-target entries, and every emitted VU C++/table file matched
the previously verified archived generated input byte-for-byte. Input hashes
and that comparison are in `local/issue4-next/input-verification.json`.
The copied generated directory retains all EE translations; only VU files are
regenerated. The external wgpu installation is a read-only link dependency.

From the isolated checkout:

```sh
python3 scripts/repro_vu_dispatch_flags.py
python3 scripts/test_vu_codegen.py
python3 -m unittest discover -s scripts -p test_run_experiments.py -v
cmake -S . -B build/issue4-flags -DPS2_GENERATED="$PWD/generated/issue4-flags" \
  -DCMAKE_BUILD_TYPE=Release \
  -DPS2_WGPU_DIR=/Users/dallascarraher/Developer/Eco/third_party/wgpu-native
cmake --build build/issue4-flags --target vurecomp -j 4
build/issue4-flags/vurecomp local/issue4-next/recorded-vu generated/issue4-flags
cmake --build build/issue4-flags -j 4
python3 scripts/run_experiments.py --manifest experiments/jak1-vu-issue4.json \
  --iso '/Users/dallascarraher/Developer/Eco/Jak and Daxter - The Precursor Legacy (USA) (En,Fr,De,Es,It) (Rev 1).iso' \
  --runner build/issue4-flags/ps2run --elf games/jak1/disc/SCUS_971.24 \
  --generated generated/issue4-flags --output local/experiments/issue4-flags-validation-510
```

The last command uses the existing three-case manifest: CPU compiled,
CPU interpreted and whole-chain check, serially to 510 frames, capturing every
five frames. Preserve prior artifacts; use a new output directory to repeat.
The generated directory must first be a private copy of the verified complete
`generated/jak1` input; do not generate into the preserved baseline directory.

Offline replay uses the command in the first investigation report, substituting
`build/issue4-flags`, the table object path
`generated/issue4-flags/vu1_table.cpp.o`, and output executable
`local/issue4-next/replay`. The investigated input prefix remains:

```text
local/experiments/issue4-chains-510/boot-idle--vu-all--1--2a234941e76c/vu-first
```

Pass `compiled` or `interpreted` and a new ignored output prefix. Results and
comparisons are in `local/issue4-next/compiled-*.bin`, `interpreted-*.bin` and
`offline-comparison.json`. Old game-derived snapshots and captures stay local.
The former `--force-native-flags` intervention was removed from the synthetic
script once producer retention became normal behavior; its historical results
can be reproduced from commit `34dc944` in a separately isolated checkout.

## Bounded replay results and stopping point

The plain compiled/interpreted cases ran at clean revision
`a48d8ff54d1c81fb361e2e72b71e20b2c9f63a9e`, using the regenerated VU inventory
hash `a719caeff6d17300367f6d0a6433c2e1447a8e72f7ee0a900b7373273277fc30`.
Both reached 510 frames and 2,524,450,548 guest cycles (95.7 and 97.3 seconds).
All **102 captures match exactly**, with no tolerances. The corrected
interpreted captures are unchanged from the previous interpreted case; only
compiled frames 500, 505 and 510 changed from the previous compiled case.
Consequently this correction removes the measured CPU-backend image gap.
It does not establish that either resulting image is visually or PS2 correct.
GPU, Start-pulse, longer routes and gameplay were not remeasured.

The particular original sampled `7A23D81EC7B8D0D2` call 172 was not traced as a
unique cause. The evidence now supports a causal effect of correcting the
flag-retention/dispatch-history class on the observed images: the interpreter
images remain fixed while the compiled images converge. It does not identify
that individual early flags-only sample as the sole source of those pixels.

The whole-chain case **did not complete**. It exited via SIGABRT at its
existing 8,192-continuation diagnostic guard, after approximately 4 seconds.
No final chain counts are available; it must not be reported as zero mismatches
or as a passed 510-frame comparison. The 1 MiB packet and 8,192-segment caps
were not increased.

Commit `7bbcd10` adds only a bounded input snapshot and identifying fields at
that guard. A separate diagnostic-only probe retained the same guard and
stopped again, recording guest frame 192, root key `8A7C5336C2223702`, entry
`0020`, zero-based chain index 348, next PC `1280`, and issue clock 16/113120
(113,104 issued instructions before the guard). This is the invocation after
the originally reduced root 347. The probe preserves its before-registers,
code, memory and flag-pipe input. It does not establish the full invocation's
length or a new execution defect. The plain interpreter log has no VU
instruction-limit/nontermination messages through 510.

The same diagnostic-only manifest then ran the legacy sampled checker to 510
under unchanged limits. It completed in 135.6 seconds. The last **periodic**
observation was 116,000 sampled checks and zero mismatches. Final checked,
eligible and skipped counts remain unknown; escaping prefixes remain excluded
from the legacy mismatch comparison. Its 17 captured frames all exactly match
the corrected plain compiled case, supporting the comparison state-restore
change without claiming exhaustive coverage.

The two diagnostic probes and sampled check were not an enlarged overnight
matrix or retries with expanded budgets. The second probe added the missing
bounded reproducer for the observed guard, and the sampled case provided
explicitly partial coverage after whole-chain checking could not finish.
Game replay time in this continuation's two reports totals 337.2 seconds;
including the first cycle it totals about 921.7 seconds. No subprocess reached
900 seconds, and the total remains below four hours. Retained builds,
translations and local artifacts across both cycles total about 1.67 GiB,
below 2 GiB; free space remained at least about 28 GiB, above 10 GiB.
Original batch artifact hashes, the prior binary and baseline generated
inventory were reverified unchanged after the new runs.

## Artifacts and exact follow-up reproduction

All paths below are relative to the isolated checkout:

- `local/experiments/issue4-flags-validation-510/`: the clean-revision three-case
  report, successful plain comparisons and failed whole-chain comparison.
- `local/experiments/issue4-flags-check-validation-510/`: the guard snapshot
  probe and completed sampled-check report, at clean revision `7bbcd10`.
- `local/issue4-next/validation-analysis.json`: exact hash comparisons against
  both previous paths, preserved-input checks, sampled counts and guard metadata.
- `local/issue4-next/dispatch-expanded.txt`: all original status/MAC/clip,
  fallback, comparison-mode and invocation-boundary assertions passing.
- `local/issue4-next/codegen-tests.txt`, `runner-tests.txt`, `web-compile.txt`:
  existing regression and Emscripten translation-unit checks.
- `local/issue4-next/offline-comparison.json`: the original root 347's corrected
  complete registers/memory/packet equality, with outputs alongside it.

The diagnostic-only probe and legacy check can be repeated with a new output
path using:

```sh
python3 scripts/run_experiments.py --manifest local/issue4-next/check-validation.json \
  --iso '/Users/dallascarraher/Developer/Eco/Jak and Daxter - The Precursor Legacy (USA) (En,Fr,De,Es,It) (Rev 1).iso' \
  --runner build/issue4-flags/ps2run --elf games/jak1/disc/SCUS_971.24 \
  --generated generated/issue4-flags --output local/experiments/issue4-flags-check-repeat
```

This manifest uses 510 frames, 30-frame capture spacing and only whole-chain
and sampled variants. The whole-chain case is expected to hit its guard;
inspect statuses rather than the batch program's exit status.

The overlong-check input prefix is:

```text
local/experiments/issue4-flags-check-validation-510/boot-idle--vu-chain-check--1--f29ec88a2acf/vu-limit
```

The committed offline replay tool also retains its 8,192-continuation guard;
compiled replay of that prefix cannot provide a full result under that guard.
The next smallest investigation is a bounded checkpoint/streaming comparison
for this saved invocation that preserves in-flight flags and accounts for Q
and VI branch history. It must not reset the interpreter at arbitrary dispatch
boundaries and call resulting agreement comprehensive, as the first cycle
showed. Any proposed change to explicit diagnostic limits must be stated and
justified before use. No such work or limit increase is started in this cycle.

The scoped fix and its original synthetic assertions are validated; exhaustive
VU state agreement, independent rendering correctness and GPU replay remain
open. Stop here rather than extending into GS, browser parity or another issue.
