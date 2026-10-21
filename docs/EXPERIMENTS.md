# Deterministic experiment contract

`experiments/jak1-startup.json` is the versioned input to
`scripts/run_experiments.py`. The runner uses only the Python standard library
and local subprocesses: it does not build, generate translations, use the
network, or make model/API calls. Python 3.10+ and a POSIX host are required.

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

## Implemented CLI and report details

```sh
python3 scripts/run_experiments.py \
  --manifest experiments/jak1-startup.json \
  --iso "/path/to/Jak.iso" --runner build/native-jak1/ps2run \
  --elf games/jak1/disc/SCUS_971.24 --generated generated/jak1 \
  --output local/experiments/my-pilot --pilot
```

All six paths are required; they resolve absolutely before execution. The output
must be a new directory under this checkout's ignored `local/experiments/`.
`--pilot` selects exactly gpu-compiled boot-idle repetitions 1 and 2, then
cpu-compiled boot-idle repetition 1. Omit it for all 24 cases. Reuse exactly the
same arguments with `--resume` to continue; do not add/remove `--pilot` when
resuming. Limits come from the manifest, with positive integer values; changing
limits changes its hash and requires a new run. No automatic retries occur.

Each attempt gets a new UUID-suffixed directory. A nonexistent `card.ps2` path
asks the runtime for a fresh, unformatted card. The runtime may create no card
file if it never flushes a write. The runner's cwd is the attempt directory, so
incidental relative runtime files are isolated too. The argv uses absolute ELF,
ISO, capture, misses and card paths. Only the allowlisted PS2 settings in
the matrix can be configured; all inherited `PS2_*` values are removed.

Native input semantics were checked in `runtime/src/system.cpp`: vblank
increments `g_frames`, applies presses with `frame <= g_frames < frame+frames`,
and updates pad 0 before IOP vblank processing. `runtime/src/iop/sio2.cpp` samples
that state into active-low pad response bytes. Thus `300:start:2` holds Start
through guest frames 300 and 301 and releases it at 302. This source inspection
does not prove that the game polls during the pulse; browser parity is issue #2.

`manifest.json` preserves the exact input bytes. `report.json` contains input
identities, the case plan, all attempt results, pending case IDs, cumulative
active batch time, runtime outcomes and comparisons. Each attempt has
`case.json`, `runtime.log`, `frames/`, and any runtime-created card/misses files.
`summary.md` avoids raw paths and runtime messages and can be reviewed for
sharing. Full JSON and logs contain local paths and may contain game data;
keep them local. The runner never prunes earlier artifacts.

Resume validates the source commit, tracked diff and untracked source hashes,
runner-script hash, binary, complete generated inventory, ELF, ISO and manifest,
as well as plan selection, the manifest snapshot, every case report and every
listed artifact. Source dirty state is recorded, not rejected. Fully written,
validated terminal reports are sealed, including timeout, halt, unsupported,
process failure and an `incomplete` runtime result. These are observations,
not implicit retries. Cancelled attempts remain unsealed and get a fresh
attempt directory on resume; partial directories lacking a report are retained
but never reused. A crash between writing `case.json` and the run report can
leave an orphan attempt; it is retained and the case remains pending.

Locks under `local/experiments/.locks/` use POSIX flock and canonical resource
paths for the output, native build directory and generated directory. Locks
release on process exit; lock files may remain. All instances of this runner
in this checkout cooperate. Build/probe tools do not acquire these locks:
keep the checkout/build frozen and do not run those writers during measurement.
Fingerprints identify files present at preflight; an older already-built binary
is not thereby attested to have been compiled from the recorded source commit.
The report includes the local CMake cache hash and available toolchain versions.

An adapter line plus GPU submit statistics proves active WebGPU. An explicit
software-fallback line records CPU. A requested GPU/mirror case with no positive
GPU evidence is unsupported once an otherwise valid runtime summary is seen.
A CPU case is identified from its explicit setting, whose dispatch was checked
in native source; the runtime has no CPU-init banner. Hardware adapter text is
preserved when available. Exit failure, timeout and malformed summaries retain
their own categories even if GPU evidence is unavailable. A valid stop requires
one stop summary and a matching halt line; frame-limit stops must match the
requested count. Completion classification is separate from capture coverage.

VU counters are **last observed**, not final totals: the runtime prints sampled
counts periodically, shares a sampling counter with other checks and does not
report escaping/skipped totals. Final checked, skipped and eligible counts stay
unknown. GS mirror lines preserve the runtime's count of pixels over delta 2;
this existing diagnostic threshold is not an acceptance tolerance. Cross-case
PPM comparisons use exact SHA-256 equality and zero-tolerance RGB metrics.
They report differing pixel count, maximum channel delta, first unequal capture,
unpaired captures, expected-but-missing captures and runtime-outcome equality.
A reliable full comparison requires frame-limit completion, complete captures
and valid matching image dimensions. `repeatable` additionally requires identical
frame hashes and runtime outcomes on repeated cases. Cross-variant reports
record whether repeatability is established for both variants (unknown when
a pilot includes only one CPU case); complete capture coverage alone does not
establish repeatability or a reliable causal attribution. Comparing early-halt captures remains
useful but is explicitly partial. Agreement never establishes PS2 correctness.

The monitor checks elapsed time, aggregate run bytes and free disk every poll
(50 ms plus filesystem scan time). Captures and other native direct writes may
overshoot the byte/disk thresholds between polls; streamed logs are capped at
the remaining byte allowance. Small reports are still written after a quota
stop to preserve evidence. Reserve additional free space for this overhead.
Parsing is bounded to the first 1 MiB and last 7 MiB of logs over 8 MiB; omitted
middle diagnostics are explicitly flagged. Complete logs remain on disk.
Total time is cumulative active batch time across resume, excluding preflight
hashing, validation and time while the runner is stopped. ISO hashing occurs
once per invocation at preflight. A total-budget timeout leaves later cases
pending. A depleted cumulative budget cannot be extended via resume.

TERM goes to the entire process group, followed by KILL after a one-second
grace period even if its leader has exited; the leader is always waited for.
Linux uses a child subreaper and waits for adopted group descendants. macOS
reparents orphan descendants to launchd for reaping; tests verify none remain
running. Processes intentionally escaping the session/group are outside this
cooperative native-runtime contract. SIGINT/SIGTERM preserve a cancellation
report. SIGKILL/power loss cannot run cleanup; atomic completed reports survive,
but inspect for surviving processes before resuming after such a failure.

Exit status 0 means a bounded batch report was produced, even if game cases
failed. Cancellation returns 130; invalid inputs, identity/lock failures and
preflight errors return 2. Read `state`, `pending` and case statuses in the
report to assess results. No visual or gameplay success exit code is offered.

Synthetic regression suite:

```sh
python3 -m unittest discover -s scripts -p test_run_experiments.py -v
```

For issue 4, the separate [bounded VU diagnostic](ISSUE4-VU.md) adds opt-in
`PS2_VU_CHECK=all` complete-chain comparison and final chain counters, distinct
from the legacy sampled observations above. The three-case
`experiments/jak1-vu-issue4.json` manifest stops at 510 frames. This mode is
instrumentation, not an acceptance oracle or a replacement for the startup
matrix.

The [bounded production checker](ISSUE4-VU-CHAIN-INTEGRATION.md) now distinguishes
`complete_match`, `mismatch`, `budget_exhausted` and `unsupported`. The default
aggregate comparison budget is still 8,192 continuations; optional
`PS2_VU_CHECK_CONTINUATIONS=16384` selects that explicit finite policy. The harness
allows only `8192` or `16384`, and only with `PS2_VU_CHECK=all`. This does not grant
a fresh shared time/storage budget or schedule a replay.

Comparison stops on budget exhaustion or unsupported boundaries while the guest
continues normally from compiled state. Its remaining dispatches are explicitly
unchecked and cannot reset the comparison budget. New `[vu-chain-outcomes]`
summaries populate `chain_comparison_outcomes`; the independent runtime-stop
classification remains unchanged. `chain_comparison_complete_for_attempted` is
true only for nonzero attempts which all matched completely, with no unchecked
tail. It does not establish hardware correctness or coverage of other executions.
Historical `[vu-chain-summary]` logs still populate their separate legacy field.
Failed exits, missing/duplicate summaries and inconsistent outcome totals leave
new counters unknown, never zero. Compiled fragments require the existing
subprocess wall-time guard; packet overflow remains a process failure.
