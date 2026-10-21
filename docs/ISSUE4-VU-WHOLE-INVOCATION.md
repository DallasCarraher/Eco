# Issue 4: saved whole invocation compared exactly

The saved frame-192 invocation, key `8A7C5336C2223702`, entry `0020`, root index
348, **completes with exact compiled/interpreter agreement** after **9,363
continuations and 129,186 issued instructions**, ending at PC `0x0A00`.
All **37 checkpoints** match. The first 32 reproduce the earlier 8,192-continuation
prefix exactly. A separate uninterrupted interpreter execution reaches the same
end and matches both checkpointed paths' final registers, memory, ordered packet
bytes and every semantic pipeline field.

This resolves whole-invocation comparison coverage for this saved input. It does
not establish agreement at every intermediate instruction, coverage of all VU
invocations, independent PS2 correctness, visual correctness or browser parity.
No execution discrepancy was observed, no tolerance or expected result changed,
and neither Eco path is an independent oracle.

## Authorized policy and implementation

The user authorized continuing the proposed finite **16,384-continuation offline
diagnostic** in this session. The implementation builds on the state-preserving
mechanism in `46de6df`, on branch `codex/issue-4-vu-coverage`, dedicated checkout
`/Users/dallascarraher/Developer/Eco-vu-coverage`.

`scripts/replay_vu_checkpoint.cpp` now accepts an explicit optional
`--continuations 16384`. Its default stays 8,192; only 8,192 and 16,384 are
accepted policies. The chosen limit is immutable within the compiled cursor and
is recorded in status.json. Chunk size remains a separate scheduling parameter.
The production whole-chain guard is still 8,192 and was not modified. The
one-million-instruction, 1 MiB packet, 900-second subprocess, serial-execution,
8 GiB shared-storage and 10 GiB free-space constraints remain.

Only the offline CLI policy and original regression were changed. Runtime,
generators and state-preservation semantics were not changed in this continuation.
This is in-process checkpointing, with compiled yields at existing function
returns and a fully restored interpreter cursor. Durable crash-resume and safe
compiled fallback support remain outside the implementation.

## Original validation before saved-input reuse

The expanded `scripts/repro_vu_checkpoint.py` passed before the saved replay:

* Its 10,000-continuation finite invocation completes identically under the new
  16,384 policy and uninterrupted execution, retaining the existing Q, branch,
  end-delay, flag, packet and instruction-count assertions.
* A longer original 20,000-iteration input stops exactly at 16,384 continuations,
  163,843 issued instructions, counter 3,616. Chunks of 1, 7 and 257 all stop at
  that same point. Repeated resumes with different chunk sizes issue nothing more.
* Original default-policy tests still stop at 8,192 and cannot resume past it.
* The actual CLI is compiled into an original fixture. Default and explicit
  8,192 produce partial results, while explicit 16,384 produces either complete
  or partial results as appropriate. Numeric limits, completion booleans, states
  and instruction/continuation counts are asserted from the resulting JSON.
* Unsupported ceilings including 8,193, 16,385, 32,768, negative values and
  `unlimited` are rejected before creating an output directory.

The existing fallback-exhaustion reporting regression also passes. It remains
incomplete at exactly one million aggregate instructions. No runtime/Wasm or
generator changes required repeating the broader suites passed in the
[preceding validation cycle](ISSUE4-VU-CHECKPOINT-VALIDATION.md).

## Identities, commands and local evidence

All diagnostics ran serially under the common audit flock, with a supervisor
monitoring process-group wall time, shared storage, temporary files and free disk.
All paths below are relative to the dedicated checkout unless absolute.
Existing artifacts were read-only. Every output/build path was new.

```sh
python3 scripts/repro_vu_checkpoint.py \
  --output local/vu-coverage-16384/synthetic \
  --runtime /Users/dallascarraher/Developer/Eco-issue-4/build/issue4-flags/libps2runtime.a \
  --wgpu /Users/dallascarraher/Developer/Eco/third_party/wgpu-native/lib/libwgpu_native.a
python3 local/vu-coverage-16384/build-replay.py
local/vu-coverage-16384/replay \
  /Users/dallascarraher/Developer/Eco-issue-4/local/experiments/issue4-flags-check-validation-510/boot-idle--vu-chain-check--1--f29ec88a2acf/vu-limit \
  local/experiments/issue4-checkpoint-16384-256 256 --continuations 16384
/Users/dallascarraher/Developer/Eco-issue-4/local/issue4-prefix/q-fixed/replay \
  /Users/dallascarraher/Developer/Eco-issue-4/local/experiments/issue4-flags-check-validation-510/boot-idle--vu-chain-check--1--f29ec88a2acf/vu-limit \
  interpreted local/experiments/issue4-checkpoint-16384-continuous/interpreted
python3 local/vu-coverage-16384/verify-v2.py
```

These are archived exact commands; choose new outputs and acquire the common
serial allocation before reproducing. The continuous output parent directory
was created first. The supervisor clears inherited PS2 settings and redirects
compiler temporary products into the private ignored storage.

Preflight and postflight verified the original five snapshot inputs, archived
runner/wrapper, corrected generated inventory and three link archives against
the sealed prefix report/build record. All eight read-only generated link
objects also match the storage audit inventory. No old build was rebuilt.
Input identities are unchanged from the [design report](ISSUE4-VU-COVERAGE.md).

`local/vu-coverage-16384/replay-build.json` preserves exact compiler argv and
input hashes. The new binary SHA-256 is
`5d57ba121ed33ab762d80b3dc448155cff51a4da12abe6f4c3db86d52a15877c`.
`source-v2.json` and `measurement-source-v2.diff` record source base
`46de6df34b54c3842aef6851b0502bbd93d61961` and measured dirty-source identities.
`synthetic/commands.json` and `inputs.json` record original test build identities.

`local/experiments/issue4-checkpoint-16384-256/` contains the complete comparison:

| Result | Observation |
| --- | --- |
| Process result | Exit 0, `complete_match`, `full_invocation_compared: true` |
| Continuations / issued instructions | 9,363 / 129,186 |
| End PC / interpreter NPC | `0x0A00` / `0x0A08` |
| Issue clock / pending Q | 129,202 / false |
| Compared checkpoints | 37 exact matches; first 32 identical to previous prefix |
| Exact final files per path | 608 register bytes, 16,384 memory bytes, 30,332 packet bytes, semantic pipeline text |

The extension covers **1,171 additional continuations and 16,082 additional
instructions** beyond the old prefix. The uninterrupted interpreter independently
reports an actual end at the same count and PC, not merely reaching a requested
instruction checkpoint. Its four final files equal each checkpointed path's
corresponding files exactly. It is still the same Eco interpreter, not an
independent implementation or hardware reference.

`local/vu-coverage-16384/verification-v2.json` is the authoritative postprocessing
record: complete status, all endpoint hashes, 32 reproduced prefix checkpoints,
eight uninterrupted-reference equality checks and unchanged link inputs. The
initial `verification.json` accidentally enumerated the old prefix directory
after a read-only preflight snippet reused its `out` variable. It is retained
as superseded evidence. The corrected helper executes preflight in an isolated
namespace and explicitly checks the new full-output directory. No replay output,
snapshot, expectation or archived report was overwritten by this correction.

## Shared accounting and stopping point

The common serial slot is released. Its authoritative ledger is:

```text
/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/coverage-16384-allocation.json
```

The ledger carries forward **7,260.824 seconds**, including historical reserves
and the preceding coverage cycle, and debits **10.740 seconds** for this cycle's
builds, synthetic tests, replay and verification: **7,271.564 / 14,400 seconds**
allocated cumulative active time. The segmented saved replay took **0.379 s**
and uninterrupted interpreter **0.192 s**; no subprocess approached 900 seconds.

Final shared retained bytes and sampled aggregate peak (including temporary
products) are **3,301,657,516 bytes (3.075 GiB)**, below the 8 GiB shared cap.
The separately sampled private temporary-file peak is **244,160 bytes**. Peaks
are polling observations, not exact reconstruction between polls. The reserved
256 MiB retained / 512 MiB peak envelope comfortably covers observed growth of
about 51 MiB. Free disk at release was **29,816,078,336 bytes (27.77 GiB)**,
above the 10 GiB floor. No previous time or storage history was reset, no evidence
was deleted, and preserved worktree status remained clean.

This bounded cycle is complete. The saved invocation's coverage question needs
no larger budget or further replay. The smallest next engineering step, if
requested, is an original integration regression for adopting explicit bounded
comparison outcomes in the production whole-chain checker; its current guard
and aggregate checking behavior have not changed. That should precede any
broader game-derived check batch. Independent PS2/visual reference work remains
a separate task; do not infer it from this exact path agreement.
