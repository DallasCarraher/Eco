# Issue 4: production bounded comparison outcomes

The subsequent [focused handoff review](ISSUE4-VU-HANDOFF-REVIEW.md) adds enclosing
context, capture-policy and active-pipeline regressions and scopes the remaining
real-queue integration experiment.
The [real GIF queue follow-up](ISSUE4-VU-GIF-QUEUE.md) passes that native boundary
test and identifies browser worker execution as the remaining focused check.
The [bounded browser attempt](ISSUE4-VU-BROWSER.md) executes the fixture in a Wasm
worker but remains incomplete because required checked-outcome summaries are not
captured; its strict assertion fails and the PR remains a draft.

`PS2_VU_CHECK=all` now uses the validated checkpoint mechanism in the production
dispatcher. A finite invocation exceeding the default 8,192-continuation
comparison budget reports **budget_exhausted** rather than aborting. Complete
agreement, mismatch, exhausted budget and unsupported comparison are distinct.
Guest execution continues from its actual compiled state after checking stops;
the remainder is explicitly counted as unchecked, never as a fresh comparison
with another budget. A fresh invocation starts its own comparison.

The default stays **8,192**. Explicit `PS2_VU_CHECK_CONTINUATIONS=16384` selects
the authorized finite policy; only 8,192 and 16,384 are accepted. The harness
allows this setting only with `PS2_VU_CHECK=all`. Invalid manual configuration
reports unsupported coverage and cannot silently increase the budget.

## State and reporting

The implementation moved to internal `runtime/src/vu_checkpoint.hpp`; the script
header remains a compatible include. Separate owners retain raw registers,
memory, ordered packets and semantic flag/Q pipelines. Interpreter cursors keep
PC/NPC, pending end and VI branch history; compiled execution yields only at
existing function returns, with cumulative issue/continuation counts. No VU
arithmetic, branch timing, Q latency, generator expectations or tolerance changed.

Only the compiled side emits live GIF transfers, at its original kicks. The
reference stays dry. Context guards restore the host after each side, and only
compiled state becomes live afterward. An enclosing dry replay stays dry. Its
packet capture receives compiled bytes once; unchecked tails append normally.
Missing compiled functions stop comparison as unsupported, then follow the
existing normal fallback path under the preserved pipe. That fallback is not
claimed as compared. Mismatches likewise remain explicit when a tail is unchecked.

The new summary marker is distinct from historical reports:

```text
[vu-chain-outcomes] attempted N complete N mismatch N budget_exhausted N unsupported N unchecked_tail_dispatches N checkpoints N continuations N
```

The harness records `chain_comparison_outcomes` and
`chain_comparison_complete_for_attempted`. The latter requires nonzero attempts,
all complete, and zero unchecked tail dispatches. Failed exits, missing/duplicate
summaries and inconsistent totals leave counters unknown. Historical
`[vu-chain-summary]` logs still parse separately; legacy sampled checks remain
separate. This reports coverage of attempted invocations, not hardware correctness.

First mismatch and first incomplete captures are independent, so a budget stop
cannot consume the first-mismatch capture. Detailed logs are bounded per outcome
while totals retain every outcome. Captures include inputs, both endpoint images,
ordered packets, both pipes and interpreter cursor. `vu-chain-*.txt` metadata is
ignored alongside binary outputs; game-derived artifacts are not committed.

The one-million-instruction and 1 MiB packet capture limits remain. Compiled
fragments are indivisible: the instruction budget is checked on return, not at
internal polls. Existing packet overflow still aborts and is a process failure.
Use the bounded process-group monitor and 900-second ceiling. Durable crash-resume
and safe comparison through compiled fallback remain outside this implementation.

## Original evidence

`scripts/repro_vu_chain.py` builds original programs and calls the real production
dispatcher. The initial default-budget regression reproduces the old SIGABRT at
8,192 continuations (`local/vu-chain-integration/before/`). Accepted outcomes:

| Case | Attempted | Complete | Mismatch | Budget | Unsupported | Unchecked tail dispatches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Short finite input | 1 | 1 | 0 | 0 | 0 | 0 |
| 10,000 continuations, default budget | 1 | 0 | 0 | 1 | 0 | 1,808 |
| Same input, explicit 16,384 budget | 1 | 1 | 0 | 0 | 0 | 0 |
| Missing compiled continuation | 1 | 0 | 0 | 0 | 1 | 1 |
| Deliberately corrupted compiled VI | 1 | 0 | 1 | 0 | 0 | 0 |
| Budget stop, then fresh short input | 2 | 1 | 0 | 1 | 0 | 1,808 |
| Budget stop, then deliberate mismatch | 2 | 0 | 1 | 1 | 0 | 1,808 |
| Invalid manual policy | 1 | 0 | 0 | 0 | 1 | 3 |
| Simulated atomic fragment ending over budget | 1 | 0 | 0 | 1 | 0 | 0 |

Literal assertions cover counter, Q, end PC and packet values. Checked,
budget-stopped and unsupported final register/memory/packet files match plain
execution exactly. A test-only GIF seam records exactly two submissions, in
order, at cumulative captured lengths 20 then 40 bytes. Thus the dry reference
does not submit, and packets are not deferred into an end-of-comparison batch.
No GS/backend implementation was changed.

An integration edge case was reduced before fixing it: the helper cleared the
compiled end bit when a fragment exceeded its instruction budget, causing the
dispatcher to resume its end PC. The simulated-fragment fixture fails before
correction (`atomic-before/`) and passes after (`final/`). The helper preserves
the actual end while reporting exhausted coverage; no unchecked tail executes.

Intermediate failures remain preserved. One packet probe initially assumed a
compiler-localized VI was published to its host register mirror at every kick.
It now observes packet-delivery/capture lengths at the GIF boundary instead;
architectural end-state, Q and packet-value assertions stayed unchanged. A later
Python grouping typo incorrectly expected a tail for the atomic-end fixture;
it was corrected to the independently asserted no-restart behavior above.

## Commands and validation

All diagnostics ran serially under the common cross-checkout allocation. Below,
`ECO_INVESTIGATION` denotes the preserved investigation checkout, `ECO_PRIMARY`
the primary checkout. Exact resolved argv are archived under ignored
`local/vu-chain-integration/jobs/`, test `commands.json` and `chain-build.json`.
All output/build locations were new; original archives were read-only inputs.

```sh
python3 scripts/repro_vu_chain.py --output local/vu-chain-integration/final \
  --runtime "$ECO_INVESTIGATION/build/issue4-flags/libps2runtime.a" \
  --wgpu "$ECO_PRIMARY/third_party/wgpu-native/lib/libwgpu_native.a"
python3 scripts/repro_vu_checkpoint.py --output local/vu-chain-integration/checkpoint \
  --runtime "$ECO_INVESTIGATION/build/issue4-flags/libps2runtime.a" \
  --wgpu "$ECO_PRIMARY/third_party/wgpu-native/lib/libwgpu_native.a"
python3 -m unittest discover -s scripts -p test_run_experiments.py -v
python3 scripts/repro_vu_dispatch_flags.py
python3 scripts/repro_vu_dispatch_q.py
python3 scripts/test_vu_codegen.py
python3 -m unittest discover -s scripts -p test_run_vu_prefix.py -v
"$ECO_PRIMARY/tools/emsdk/upstream/emscripten/em++" -std=c++20 -O2 -msimd128 -pthread \
  -Iruntime/include -Iruntime/src -c runtime/src/vu_micro.cpp \
  -o local/vu-chain-integration/vu_micro_web.o
python3 local/vu-chain-integration/build-replay.py
local/vu-chain-integration/replay-chain \
  "$ECO_INVESTIGATION/local/experiments/issue4-flags-check-validation-510/boot-idle--vu-chain-check--1--f29ec88a2acf/vu-limit" \
  local/experiments/issue4-production-chain-16384 16384
python3 local/vu-chain-integration/verify.py
```

Choose fresh outputs for reproduction. The production regression passes, as do
checkpoint/Q/branch/end/budget tests, native/fallback/Wasm flag and Q checks,
eight native/eight Wasm codegen cases, **23** harness tests and **five** prefix
wrapper tests. The changed runtime compiles with Emscripten SIMD/pthreads; this
is translation-unit compilation, not full browser integration.

The single game-derived validation replays the frozen frame-192 input through
`run_chain`, the production invocation loop. Its archived initial pipe is loaded
inside its owning FlagDispatch, not rebuilt by starting from an endpoint PC.
GS submission is dry; the explicit production comparison policy is 16,384.
No game boot or matrix ran.

Result: **one complete comparison, zero mismatches/budget stops/unsupported cases,
zero unchecked tail dispatches**, **37 checkpoints / 9,363 continuations /
129,186 instructions**, final PC `0x0A00`. Final registers, memory, packets and
semantic pipe match both prior checkpointed paths and uninterrupted interpretation
exactly. Input identity stays key `8A7C5336C2223702`, entry `0020`, root index 348.
The parser reports complete coverage for this one attempt.

`verification.json` records hashes and counts; outputs are in
`local/experiments/issue4-production-chain-16384/`. The private adapter SHA-256 is
`3f539f4f06a1d514f0bd4a1550610ac477d59bbc0f318819af633c07cd431d24`.
Five snapshot files, archived runner/wrapper, generated inventory, eight link
objects and three archives were checked against sealed identities before reuse
and/or linking; link inputs remained unchanged after replay. Compiler argv,
measured diff and source hashes remain local. Preserved worktrees stay clean.

## Accounting and remaining scope

The serial slot is released. Its ledger is
`Eco-artifact-audit/local/artifact-audit-20261021/coverage-integration-allocation.json`.
It carries **7,271.564 seconds** forward and adds **105.210 seconds** including
builds, failed original regressions and verification conservatively:
**7,376.773 / 14,400 seconds** cumulative active debit. The saved-input case took
**0.421 s**; longest supervised subprocess **50.345 s**.

Shared retained bytes and sampled aggregate peak including temporary products:
**3,458,371,964 bytes (3.221 GiB)** under 8 GiB, about **149.5 MiB** added within
the 512 MiB retained / 1 GiB peak reservation. Sampled private temporary peak:
**8,426,718 bytes**; peaks between polls remain unmeasured. Free disk:
**29,636,190,208 bytes (27.60 GiB)**, above 10 GiB. No history or budget reset,
evidence deletion, translation rebuild or archived-output overwrite occurred.

Self-review covered context restoration, actual-end versus budget state, tail
accounting, first mismatch after incomplete coverage, packet delivery and parsing.
This is not independent review. Full native game execution, full browser build/run,
GPU behavior, performance and independent PS2/visual correctness remain unmeasured.
Neither path is an oracle. Next is review of the draft PR; any broader game-derived
diagnostic batch should be separately scoped after review, with explicit policy
and coverage reporting.

## PR #10 parser review follow-up

Review `5606020934` identified that a valid summary followed by a truncated
`[vu-chain-outcomes]` line could falsely report complete coverage. Parsing now
requires exactly one outcome-marker line as well as one valid summary. Original
regressions cover truncated, bare and trailing-text markers alone and before or
after a valid summary; both outcome counts and completion coverage stay unknown.

Commands from `Eco-vu-coverage`, serially supervised under the shared lock:

```sh
python3 scripts/test_run_experiments.py Experiments.test_malformed_chain_outcome_markers -v
python3 -m unittest discover -s scripts -p test_run_experiments.py -v
```

The first command reproduced six failing duplicate-marker cases before the fix;
the second passed all **24 tests** afterward. Logs remain ignored in
`local/vu-chain-review/jobs/01-before.log` and `02-after.log`. No build, saved
input reuse or game replay was needed; invocation coverage is unchanged.

The released allocation is
`Eco-artifact-audit/local/artifact-audit-20261021/coverage-review-allocation.json`.
It carries 7,376.773 seconds forward and adds **19.955 seconds**, totaling
**7,396.728 / 14,400 seconds**. Shared retained bytes: **3,458,391,581**;
sampled aggregate peak: **3,458,461,817**, under 8 GiB. Private temporary peak:
zero bytes; peaks between polls remain unmeasured. Free disk: **29,501,222,912
bytes**, above 10 GiB. The smallest next step remains human review of production
state restoration and packet handoff before any broader native/browser run.
