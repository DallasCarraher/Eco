# Deterministic experiment contract

`experiments/jak1-startup.json` is a versioned specification for work item 01,
not an executable configuration yet. Implement and validate this contract
before treating it as an overnight job.

## Inputs and matrix

The manifest expands scenario × variant × repetition: 2 × 6 × 2 = 24 cases.
Each starts from a fresh process and fresh memory card, with no save state.
Run serially. The explicit Start pulse is guest frames 300 and 301; native and
browser implementations must verify those semantics at the pad sampling point.
Capture every 30 guest frames and on halt. Start with a three-case pilot
(repeated gpu-compiled boot-idle, then cpu-compiled boot-idle); expand only if
limits and reporting work. Run order must pair repeated cases early so that
an exhausted total budget still yields repeatability evidence.

The six environment combinations are supported by current native source:

| Variant | Purpose |
| --- | --- |
| gpu-compiled | Current default rendering and VU execution |
| cpu-compiled | Software GS output |
| gpu-interpreted | WebGPU with interpreter override |
| cpu-interpreted | Software GS with interpreter override |
| gs-mirror | `PS2_GS=both`, `PS2_GS_COMPARE=1`: software output plus GPU comparison |
| vu-sampled-check | `PS2_VU_CHECK=1`: existing sampled compiled/interpreter comparison |

`PS2_VU_CHECK` checks every 64th eligible compiled invocation; escaping calls
are not compared in the same way. A zero mismatch count is not comprehensive
coverage. Report checked, skipped and total eligible calls where available,
and mark unavailable counters unknown. GPU initialization can fall back to
software: record the actual backend and classify unavailable GPU cases as
unsupported, never as a successful GPU comparison.

Clear inherited `PS2_*` variables before applying case settings. Record the
allowlisted effective settings. Never copy an entire environment into a report.
`PS2_WINDOW_FULL=1` is mandatory for every heap snapshot experiment.

## Command mapping (existing native runner)

Build before the measurement batch. The harness invokes an argv array, with
absolute paths resolved from CLI parameters. This is the command shape:

```text
build/native-jak1/ps2run games/jak1/disc/SCUS_971.24
  --disc <local-iso> --frames 600
  --memcard <case-dir>/card.ps2 --misses <case-dir>/misses.txt
  --frames-dir <case-dir>/frames --frame-every 30
  [--press 300:start:2]
```

Do not use `port.sh` or `jak_probe.py --run` inside this fixed measurement
matrix: those can rebuild translations and overwrite shared exploration data.
They remain useful for a separately bounded coverage-generation stage.

## Output contract

Write under ignored `local/experiments/<unique-run-id>/`. Never reuse a case
directory. Keep a machine-readable manifest snapshot, run report and human
summary, plus per-case logs, frames, misses and memory cards. Write reports
atomically after every case so interruptions preserve completed results.

Run identity includes source commit, dirty diff hash (or refusal of dirty tree),
runner binary SHA-256, generated-code inventory hash, ISO SHA-256, manifest
hash, toolchain versions, OS/architecture, actual backend and hardware when
available. Hash the ISO once at preflight, not once per case. Record paths
locally, but redact home directories from summaries intended for GitHub.

Per-case fields include scenario, variant, repetition, argv, effective settings,
start/end timestamps, wall time, exit code/signal, last guest frame/cycle,
halt reason, observed backend, comparison counts, first missing PC/RA, output
sizes and frame hashes. `gameplay_verified` stays false in this matrix.

Use distinct result categories: `frame_limit_reached`, `runtime_halted`,
`timeout`, `process_failed`, `unsupported`, `output_limit`, `disk_limit`,
`cancelled`, and `incomplete`. Missing summaries and malformed output are
incomplete, even with exit code zero. Parse the explicit runtime stop line;
never infer completion from the process exit alone. A frame limit is a coverage
result, not visual correctness. Keep classification separate from pixel metrics.

Comparison report: first repeatability divergence, first cross-variant
mismatch, compared frame count, missing captures, pixel mismatch count and max
channel delta. Exact hashes identify equality; tolerances need reference-backed
justification. Do not silently bless existing distorted images as goldens.

## Limits and resume

Defaults: four hours total, 15 minutes per case, one process group at a time,
2 GiB total output and at least 10 GiB disk free. These are initial guardrails,
not measured runtime estimates. Check quotas during a case, not only afterward.
Stop its whole process group with TERM, then KILL after a grace period. On
SIGINT/SIGTERM, record cancellation and reap descendants. Do not delete earlier
runs automatically. A total budget stop leaves remaining cases pending.

Lock the output run and shared build resources; reject overlapping writers.
Resume only when source, binary, generated-code, ISO and manifest hashes match.
Skip only cases with complete, validated reports. Repeat runs are explicit
cases, not retries. Do not retry identical failures automatically.

Required harness tests use a fake subprocess, not copyrighted game data:
zero-exit halt, normal frame limit, missing summary, timeout with child process,
output quota, cancellation, unavailable GPU, lock contention, resume hash
mismatch, and paths containing spaces. Use a short synthetic smoke case before
running the local game pilot.
