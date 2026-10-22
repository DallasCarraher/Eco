# Issue 4: real GIF queue integration

The original two-kick fixture now passes through the real `gif::transfer` and
render ring with the VU producer role. Four native cases pass: plain short,
checked complete, plain long, and checked budget exhaustion. No runtime defect
was found and no runtime semantics were changed. The new original regression is
`scripts/repro_vu_gif_queue.py`.

## Evidence

The fixture directly compiles the current `runtime/src/gs/gif.cpp` and
`runtime/src/gs/queue.cpp`, along with the included current VU dispatcher and
original generated programs. It does not substitute the GIF boundary. A 4 KiB
render ring receives two path-1 `kGif` records, each one qword, with literal
payloads in the expected order. The consumer drains only after VU memory is
overwritten, stack scratch is overwritten and the comparison capture is poisoned
and freed. Exact payload assertions still pass, exercising queue storage ownership
after producer scratch lifetimes end. No extra records remain.

Final raw registers, 16 KiB memory, captured packets, semantic flag/Q pipe fields
and queued payloads match the corresponding plain case exactly. Literal end-PC,
Q and loop-counter assertions also pass. Both compared paths start from an
active pipe seeded with a pending Q and nonzero issue clock.

| Checked case | Complete | Budget | Compared continuations | Checkpoints | Unchecked tail dispatches |
| --- | ---: | ---: | ---: | ---: | ---: |
| Short finite input | 1 | 0 | 2 | 1 | 0 |
| 10,000-continuation input | 0 | 1 | 8,192 | 32 | 1,808 |

The budget case remains incomplete coverage even though normal guest execution
finishes. Neither comparison path is an independent correctness oracle.

## Reproduction and identities

From `/Users/dallascarraher/Developer/Eco-vu-coverage`, under the renewed shared
serial allocation:

```sh
python3 scripts/repro_vu_gif_queue.py --output local/vu-gif-queue/validation \
  --runtime /Users/dallascarraher/Developer/Eco-issue-4/build/issue4-flags/libps2runtime.a \
  --wgpu /Users/dallascarraher/Developer/Eco/third_party/wgpu-native/lib/libwgpu_native.a
```

Exit code **0**. The exact compile and per-case argv/environment overrides are
recorded in `local/vu-gif-queue/validation/commands.json`. Source and archive hashes
are in `inputs.json`; per-case logs, final images and `results.json` are retained
in the same new ignored directory. Supervisor log:
`local/vu-gif-queue/jobs/01-real-queue.log`.

Both read-only archive hashes were checked against the prior handoff record
before reuse and are unchanged:

- Runtime: `5d4c495109a0a064725d903b2c2a44bfffce5a24586ed23fd05a69c2206d1def`.
- wgpu: `7d8b688a6b55f0728c847e1c3b028d07ccb1009d8cea4833a6186a5775384248`.

No game-derived input, preserved translation or previous output was reused or
overwritten. The linked archives were not rebuilt. Only original fixture outputs
and new private executables were created.

## Shared budget and remaining scope

The released central allocation is
`Eco-artifact-audit/local/artifact-audit-20261021/coverage-gif-queue-allocation.json`.
It reserved **60 seconds active, 16 MiB retained / 128 MiB peak** under the existing
8 GiB/four-hour allowance. It carries **7,406.027 seconds** forward and adds
**8.832 seconds**, including compilation: **7,414.859 / 14,400 seconds** cumulative
active debit. About **6,985.141 seconds** remain; no budget reset occurred.

Shared retained and sampled aggregate peak: **3,498,092,807 bytes**, below 8 GiB.
New private directory retained approximately **12.08 MiB**, below 16 MiB. Sampled
private temporary peak: **155,776 bytes**; peaks between polls remain unmeasured.
Free disk at release: **24,785,342,464 bytes**, above 10 GiB. The command took
8.832 seconds, below both its allocation and the 900-second subprocess ceiling.

The focused native dispatcher/state/outcome and real queue boundary checks are
now covered; repeating them alone would not close another gap. Results and
coverage limits are recorded here. The remaining focused integration check is
the same original complete/budget fixture executing in a browser VU worker,
comparing exact state, semantic pipe, queue bytes and outcome counts. That needs
a separate bounded private Wasm build and renewed shared admission; the current
slot is released. It has not been run or scheduled.

This test drains the ring synchronously after producer completion. It does not
exercise concurrent consumer scheduling/backpressure, actual GS rendering,
browser worker/JIT behavior, full native/browser game execution or independent
PS2/visual correctness. No game boot or overnight matrix was run. PR readiness
should state these limits; native queue success is not browser integration proof.
