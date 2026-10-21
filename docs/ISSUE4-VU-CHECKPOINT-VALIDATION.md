# Issue 4: bounded checkpoint implementation and validation

The new diagnostic compares separately owned compiled/interpreter states in
bounded chunks. An original finite synthetic invocation completes exactly after
10,000 continuations / 100,003 instructions, with resumed chunks of 1, 7 and
257 continuations matching uninterrupted execution. The saved invocation matches
at all 32 checkpoints of 256 continuations, ending at the unchanged aggregate
guard: PC `0x1280`, 113,104 instructions, 8,192 continuations. Its final outputs
also match the archived corrected prefix byte-for-byte.

**The saved invocation remains incomplete.** Chunking does not bypass its
aggregate guard. Neither path is an independent correctness oracle; this result
does not establish PS2, visual or browser correctness. No game boot, overnight
matrix, tolerance or expectation change was used.

## Allocation and preservation

This continues branch `codex/issue-4-vu-coverage` in
`/Users/dallascarraher/Developer/Eco-vu-coverage`, based on merged corrections
`adb3a2d9bd17d485a1f49d9d6e6e89ccf09244e3`. The earlier design-only commit is
`58eb2fa`. Its zero-allocation stop was superseded by the user's explicit
allocation of 8 GB, recorded as **8 GiB shared**, including retained artifacts.
It is not a fresh time budget. The historical 7,200-second conservative debit,
four-hour total ceiling, 900-second subprocess ceiling, serial diagnostics and
10 GiB free-space floor remain.

The common cross-checkout serial flock was held by the slot supervisor for
builds, synthetics and replay. It reserved 512 MiB retained / 1 GiB peak and at
most 900 active seconds for this cycle. Existing reports and ledger files were
not overwritten. Current allocation and process start/PID are recorded at:

```text
/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/coverage-8g-allocation.json
/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/coverage-8g-reservation.json
```

All new private products are under this checkout's ignored `local/vu-coverage/`
and `local/experiments/issue4-checkpoint-prefix-256/`. The preserved checkouts,
builds, translations and sealed outputs were read-only inputs. No evidence was
deleted. Existing regressions' temporary builds were directed into the new
checkout's `local/vu-coverage/tmp/`, included in storage monitoring.

## Mechanism and limits

`run_fast` now restores an opt-in FastCheckpoint cursor's next PC, NPC, pending
end, branch-history-live bit and all previous VI values. Its steps and checkpoint
limit are invocation-cumulative; the one-million-instruction ceiling does not
reset on resume. Pausing does not flush Q, rewrite TPC or seed flag history.
Completion, pause, instruction exhaustion and invalid resume are distinct.
Normal production execution without this diagnostic cursor retains its original
entry/exit behavior. A cursor alone is not a save state: its exact register,
memory and active pipeline image must accompany it.

`scripts/vu_checkpoint.hpp` owns separate raw register bytes, 16 KiB memory,
semantic FlagPipe state and exact ordered packet bytes for each path. Each chunk
installs its own image and restores the enclosing host registers, memory, active
pipe, capture pointers and dry-run state afterward. Code and TOP/ITOP remain
immutable within the comparison session. This is **in-process resumption**;
there is no durable cross-process checkpoint format or crash-resume CLI.

Compiled execution yields only at existing generated function-return boundaries.
The compiled cursor preserves the root-issued bit, next dispatch PC, cumulative
continuations and issue count. It does not interrupt a fragment or reconstruct
its live locals from a PC. Therefore a fragment that never returns is bounded by
the external subprocess timeout, not by an internal instruction poll. Missing
compiled functions are explicitly unsupported in this new comparison path;
it does not silently substitute a newly initialized interpreter fallback.
The generated code's existing escape semantics are not changed or certified.

`scripts/replay_vu_checkpoint.cpp` interleaves the paths, resuming the interpreter
from its own cursor to each compiled cumulative issue count. It compares raw
register bytes, every memory byte, ordered length-prefixed packets, every
semantic pipeline field, PC, issue count and completion state at each endpoint.
Pipeline struct padding is excluded; no semantic fields are normalized away.
The compiled issue count is measured from the existing issue clock; the
interpreter's separate instruction count must align exactly, so a changed
clock/stall policy fails alignment instead of silently becoming a new limit.

The saved-input CLI exposes only chunk size 1..8,192. Its aggregate limit is
fixed at 8,192, independently of chunk size. Interpreter aggregate ceiling stays
1,000,000 and existing cumulative packet capture ceiling stays 1 MiB. A real
matching end returns 0; matching partial execution returns 4; mismatch or
unsupported/instruction-limit execution returns 1; invalid input/output failure
returns 2. Read status.json and the exit together. Missing/truncated output or a
timeout is incomplete/process failure, never agreement. Existing packet overflow
still aborts and is a process failure, not a matching prefix.

The supervisor's job record explicitly records timeout/storage/peak stops and
process exit; it caps and monitors the entire subprocess group. For reproduction
use the shared serial allocation and an external bounded process-group monitor,
not an unbounded direct invocation of the diagnostic binary.

## Original tests and reporting correction

`scripts/repro_vu_checkpoint.py` generates a new finite original program with
JR dispatch, delayed flags from a SUB in the root delay slot, a decrement/branch
loop, DIV/WAITQ/MULq and two distinguishable EOP packets. It asserts literal
old/new pending Q values, counter zero, exact instruction/continuation counts
and packet order. It compares uninterrupted compiled and interpreter execution
with segmented execution. Separate original subcases pause every instruction,
including immediately after a VI write, after a branch and between E and its
delay slot. Removing VI history or changing NPC makes the branch checks fail.
Pipeline Q and flag mutations and packet reordering fail exact comparison;
overwriting kicked memory does not rewrite already captured packet bytes.
Recreated host contexts prevent accidental TLS retention from supplying state.

An infinite branch fixture exhausts the cumulative interpreter instruction budget
and cannot progress by calling resume again. The finite fixture at the default
8,192-continuation guard stays incomplete on repeated chunks; its counter is
1,808. Only the **original synthetic fixture** constructs a separate fixed
10,001-continuation budget to prove finite completion. This is an explicit
synthetic test policy; it is not exposed by the saved-input CLI and grants no
permission to extend game-derived replay.

A second original fixture registers only the compiled root and dispatches into
an infinite interpreter fallback. It confirms a real diagnostic reporting bug:
the old replay tool called the fallback, saw no captured escape, and reported
`complete=true` after run_fast exhausted its instruction ceiling. The fixture
fails against the old tool. `replay_vu_snapshot.cpp` now inspects an explicit
fallback checkpoint, reports `instruction_limit` / `complete=false`, and subtracts
the root's issued instructions from fallback's remaining budget. The corrected
fixture stops at exactly 1,000,000 aggregate instructions (999,997 in fallback).
No VU arithmetic, branch or Q semantics were changed to make this assertion pass.

The before-fix tool reports 1,000,003 issued instructions and completion. That
archived original-regression failure is retained at `local/vu-coverage/fallback-before/`
and `jobs/11-reporting-before.log`. It is not a game-derived mismatch.

## Commands and evidence

All commands below ran from the dedicated checkout through the serial slot
supervisor, with each subprocess capped at 900 seconds. The supervisor itself
and exact argv, wall times, outcomes and logs are preserved under
`local/vu-coverage/{session.py,jobs/}`. Failures during fixture preparation are
retained too: the first XGKICK encoding used the wrong index; a job then had an
incorrect argument position; the first fallback fixture redefined a weak symbol
in the same translation unit. These fixture/build errors were corrected without
changing the expected packet, Q, completion or equality assertions.

Accepted original regression:

```sh
python3 scripts/repro_vu_checkpoint.py \
  --output local/vu-coverage/synthetic-release \
  --runtime /Users/dallascarraher/Developer/Eco-issue-4/build/issue4-flags/libps2runtime.a \
  --wgpu /Users/dallascarraher/Developer/Eco/third_party/wgpu-native/lib/libwgpu_native.a
```

Use a new output directory for every run. Each output contains commands.json,
input hashes, original generator/driver files and binaries. It links read-only
archives; it does not rebuild the preserved runtime. Existing regressions passed:

```sh
python3 scripts/repro_vu_dispatch_flags.py
python3 scripts/repro_vu_dispatch_q.py
python3 scripts/test_vu_codegen.py
python3 -m unittest discover -s scripts -p test_run_vu_prefix.py -v
```

Those runs used TMPDIR pointing to the private ignored tmp directory. Logs are
`local/vu-coverage/validation-{0,1,2,3}.log`, with commands/results in validation.json.
This includes native/fallback/Wasm flag and Q handoffs, eight native/eight Wasm
codegen cases and five wrapper tests (including timeout and malformed output).
It is not a full browser or production crash-resume integration test.

Private saved-input build and comparison:

```sh
python3 local/vu-coverage/build-replay.py
local/vu-coverage/replay \
  /Users/dallascarraher/Developer/Eco-issue-4/local/experiments/issue4-flags-check-validation-510/boot-idle--vu-chain-check--1--f29ec88a2acf/vu-limit \
  local/experiments/issue4-checkpoint-prefix-256 256
python3 local/vu-coverage/verify-final.py
```

`replay-build.json` records exact compiler argv and every input hash, including
the eight read-only generated objects verified against the audit inventory.
Preflight reran all five sealed snapshot hashes, the archived runner/wrapper,
all eight generated files and canonical inventory, and all three link archives.
Identities agree with the [design report](ISSUE4-VU-COVERAGE.md). The new runner
SHA-256 is `1ceae655dff5f2bea5c6cc33b1bf8e8c710a8cb4a8b380ad1e520b15168cbb60`.
Inputs were rehashed unchanged after linking/replay.

The game-derived subprocess returned **4**, `state=matched_partial` and
`full_invocation_compared=false`. `checkpoints.jsonl` records all 32 exact endpoint
comparisons. `verification.json` verifies that all eight final files (compiled
and interpreted registers/memory/packets/semantic pipeline) equal their respective
archived corrected-prefix files. PC/NPC at the interpreter endpoint are
`0x1280/0x1288`, pending end false. These are additional checkpoint observations
inside the same prefix, not instruction-by-instruction or full-invocation proof.

Final storage/time accounting and the slot's released state are in the central
allocation ledger. The cycle debited **60.824 active seconds**, including builds,
synthetics and verification conservatively; the one saved-input subprocess took
**0.379 seconds**. Longest supervised subprocess was **24.285 seconds**. With
the historical debit, allocated active usage is **7,260.824 / 14,400 seconds**.
Final shared retention and observed peak including temporary products were
**3,248,431,325 bytes (3.025 GiB)**, an increase of **152,773,080 bytes** from
admission, below the 512 MiB retained / 1 GiB peak reservation. About **27.87 GiB**
remained free (29,923,127,296 bytes), above the 10 GiB floor. Temporary products
were included in polling; their separate transient-only maximum was not isolated.
The aggregate sampled peak ended at final retention; this does not imply that
temporary builds used no space.

The peak is sampled across all scoped local/build/generated
trees, including synthetic scratch; short peaks between polls cannot be measured
exactly, so the 1 GiB reservation is retained as a conservative upper envelope.
No history was reset and no preserved experiment output was rewritten.

## Next decision

The preservation mechanism is now synthetically validated and reproduces the
saved prefix through 32 exact checkpoints. The next smallest game experiment
would resume past continuation 8,192 under a separately approved finite aggregate
limit while retaining all existing instruction/packet/time/storage limits.
That requires an explicit aggregate-policy decision first; changing only chunk
size cannot do it. No such extension was performed in this cycle. A further
mechanism limitation is durable cross-process resume and safe compiled fallback;
neither is claimed here. Stop this bounded cycle rather than booting the game
or broadening to the overnight matrix.
