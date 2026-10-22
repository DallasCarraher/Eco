# PR #10: focused state and packet handoff review

Reviewed branch `codex/issue-4-vu-coverage` at `71c42af`, on 2026-10-22.
No confirmed production defect was found in the reviewed restoration and handoff
paths. The finding was a validation gap: enclosing diagnostic context, dry/null/
prefilled capture policies, and the final active pipeline after an unchecked tail
were not directly asserted by the production regression. This follow-up adds
those assertions to `scripts/repro_vu_chain.py`; runtime semantics are unchanged.
This is an agent review of its earlier implementation, not independent approval.

## Review evidence

| Path reviewed | Evidence and conclusion |
| --- | --- |
| `Image::save/install`, `Context` | Raw registers, 16 KiB memory and flag/Q pipe are swapped separately from packet ownership. Guards restore active/dry flags and packet/escape/interpreter-cursor pointers. New sentinel tests verify normal exit and exception unwinding with active and inactive enclosing pipes, preserving a nonempty outer capture. |
| `Compiled::advance`, `Interpreter::advance` | Each return boundary saves its owned image before restoring the host. The interpreter resumes PC/NPC, pending end and VI history from its cursor. Existing checkpoint regressions cover branch delay, pending Q and cumulative guards; they were inspected, not rerun in this cycle. |
| `Comparison::run`, `check_chain` | Only the compiled side is live. Reference packets remain private. The compiled image is installed after both contexts restore, then its captured prefix is appended once to the enclosing capture. New dry, null and prefilled capture cases pass. |
| `check_chain`, `run_chain`, `run_entry` | A partial result queues its actual compiled continuation under the same pipe and counts the tail unchecked. A real end is not resumed. New active-pipe cases compare semantic final pipe fields after both complete execution and budget exhaustion against plain execution, including a seeded pending Q. |
| `xgkick`, `gif::transfer`, `queue::Ring::post` | Source review shows immediate compiled delivery and queue payload copying. The executable test still substitutes the GIF boundary: actual queue routing, asynchronous consumption and browser execution remain untested here. |

The final run passes **23 original subprocess cases**: eight plain controls and
15 checked outcomes. Four host-context combinations are also asserted in each
process. All original outcome expectations remain; six new checked cases cover
dry completion, dry exhaustion, no enclosing capture, prefilled capture, active
pipe completion and active pipe exhaustion. The two new exhaustion cases each
report 8,192 compared continuations and 1,808 unchecked tail dispatches. Final
registers, memory and packets match their plain controls exactly; active cases
also match every serialized semantic flag/Q pipe field. Dry cases submit no GIF
packets; live cases submit exactly the two literal packets in order.

## Commands, identities and allocation

From `/Users/dallascarraher/Developer/Eco-vu-coverage`, under the shared serial
lock, the same command was run twice with distinct new output directories:

```sh
python3 scripts/repro_vu_chain.py --output local/vu-handoff-review/handoff \
  --runtime /Users/dallascarraher/Developer/Eco-issue-4/build/issue4-flags/libps2runtime.a \
  --wgpu /Users/dallascarraher/Developer/Eco/third_party/wgpu-native/lib/libwgpu_native.a
python3 scripts/repro_vu_chain.py --output local/vu-handoff-review/active-pipe \
  --runtime /Users/dallascarraher/Developer/Eco-issue-4/build/issue4-flags/libps2runtime.a \
  --wgpu /Users/dallascarraher/Developer/Eco/third_party/wgpu-native/lib/libwgpu_native.a
```

The first run passed before adding active-pipe cases; the second passed the final
23-case fixture. Exact build argv, source/archive hashes, synthetic outputs and
per-case logs are retained under those ignored directories; supervisor logs are
in `local/vu-handoff-review/jobs/`. Read-only archive identities match the earlier
integration records:

- Runtime SHA-256: `5d4c495109a0a064725d903b2c2a44bfffce5a24586ed23fd05a69c2206d1def`.
- wgpu SHA-256: `7d8b688a6b55f0728c847e1c3b028d07ccb1009d8cea4833a6186a5775384248`.

The released central ledger is
`Eco-artifact-audit/local/artifact-audit-20261021/coverage-handoff-review-allocation.json`.
It carries **7,396.728 seconds** forward and adds **9.298 seconds**:
**7,406.027 / 14,400 seconds** cumulative active debit. Longest supervised command:
**4.836 seconds**. Retained and sampled aggregate peak: **3,485,426,735 bytes**,
under the shared 8 GiB cap. Sampled private temporary peak: **244,160 bytes**;
between-poll peaks remain unmeasured. Free disk at release: **25,927,430,144
bytes**, above 10 GiB. No saved game inputs were reused and no game boot, browser
run, matrix, preserved build mutation or evidence overwrite occurred.

## Smallest remaining integration experiment

This proposed native experiment is now complete; see the
[real GIF queue results](ISSUE4-VU-GIF-QUEUE.md). The recipe below records the
scope selected before that run.

Use the same original two-kick fixture with the **real `gif::transfer` and render
queue**, removing the test GIF substitution. Start a small render ring, select
the VU producer role, and run plain versus checked short and 10,000-continuation
cases in separate processes. Drain the ring after dispatch. Assert exactly two
`kGif` records with path 1, one qword each and the literal ordered payloads; mutate
the original VU memory before draining to verify queued bytes own their storage.
Compare final registers, memory and semantic pipe fields, and assert complete
versus budget/unchecked-tail outcomes. No renderer, GPU, ISO or game translation
is needed. This exercises the next actual boundary missing from the GIF seam.

A proposed reservation is **60 seconds active, 16 MiB retained / 128 MiB peak**,
serially under the existing shared lock, with the usual 900-second subprocess
ceiling and 10 GiB free-space gate. This is a proposed limit, not a measured
runtime estimate or a new allocation. About **6,993.973 seconds** remain in the
four-hour budget; storage must be remeasured before admission. If it passes,
browser worker/JIT integration is the next separate gap. Neither native test
agreement nor this review establishes PS2 hardware or visual correctness.
