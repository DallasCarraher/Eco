# Mac mini overnight workflow

Yes: the expensive experiment loop can run without any model calls. A model is
useful to design the experiment and interpret results afterward; replay,
comparison, hashing and reporting should be normal programs.

## What exists today

The native runner, bounded `jak_probe.py`, renderer/VU switches and browser
probes exist. A single bounded exploration command works today:

```sh
cd /path/to/Eco
PS2_BUILD_JOBS=4 python3 scripts/jak_probe.py "/path/to/Jak.iso" \
  --run --toplevel-templates --rounds 10 --frames 600 --timeout 3600
```

This mutates the local generated build and `games/jak1` outputs. Run it in a
dedicated checkout, with no other build or probe using that checkout. Its
one-hour timeout bounds the build/exploration process tree, but it does not yet
provide the matrix runner's disk quotas, immutable case archives or resume
contract. It is not the recommended unattended graphics experiment. Repeated
exploration alone will not diagnose incorrect rendering.

## Run a frozen native experiment

The runner for work item 01 is implemented. Build before starting it, then keep
source, binary and generated code unchanged through the batch and any resume.
The documented budgets are four hours total active time, 15 minutes per case,
2 GiB aggregate output and at least 10 GiB free space. Execution is serial.

Validate the harness and original synthetic toolchain fixture first:

```sh
python3 -m unittest discover -s scripts -p test_run_experiments.py -v
python3 scripts/jak_smoke.py --web --live-template
```

The toolchain fixture writes only its own `toolchain-smoke` directories. Do not
run another task using those directories concurrently. Web compilation requires
the local Emscripten SDK; it does not execute a browser test.

Run the three-case Jak pilot:

```sh
python3 scripts/run_experiments.py --manifest experiments/jak1-startup.json \
  --iso "/path/to/Jak.iso" --runner build/native-jak1/ps2run \
  --elf games/jak1/disc/SCUS_971.24 --generated generated/jak1 \
  --output local/experiments/jak1-pilot --pilot
```

Inspect `summary.md` and `report.json`: the actual GPU backend, matching repeat
captures, missing captures and honest stop classifications matter even if all
cases halt. Each case has separate artifacts. A halt is not a gameplay result.
Use a new output directory for another pilot; existing directories are rejected.

After pilot review, the full matrix is the same command without `--pilot`, with
a new output directory. To run it on macOS independent of the agent and terminal
session (substitute the local ISO path):

```sh
mkdir -p local/experiments
nohup caffeinate -i python3 scripts/run_experiments.py \
  --manifest experiments/jak1-startup.json \
  --iso "/path/to/Jak.iso" --runner build/native-jak1/ps2run \
  --elf games/jak1/disc/SCUS_971.24 --generated generated/jak1 \
  --output "local/experiments/jak1-overnight-$(date +%Y%m%d-%H%M%S)" \
  > local/experiments/overnight-launch.log 2>&1 < /dev/null &
```

Save the output directory printed in the launch log. The launcher log is small;
case logs/captures and reports are inside the bounded run directory. No active
agent, model call, scheduler or network access is needed. `caffeinate` prevents
idle sleep while the command runs; the Mac must remain powered.

Resume a stopped run with **the same arguments and output directory**, adding
`--resume` (and preserving `--pilot` for a pilot). Resume verifies every input
and saved artifact hash before skipping sealed case reports. SIGINT/SIGTERM
cancel the active case, stop its process group, and preserve pending work.
Resume gives a cancelled case a new attempt directory. Recorded failures are
not automatically retried. Limits belong to the manifest; a changed manifest
requires a new run. See [the contract](EXPERIMENTS.md) for exact semantics,
cooperative resource locks, polling-limit overshoot and build provenance limits.

## Prepare the Mac mini once

1. Clone the private Eco repository into a dedicated local directory. Follow
   README toolchain setup. Verify architecture, free space and native graphics
   support. This machine has not yet been inspected or configured.
2. Place the user's ISO locally and verify its hash. Build translations on that
   machine or transfer the ignored local inputs deliberately, then rebuild for
   its architecture. Git does not include the disc, generated code, SDK or builds.
3. Install Chrome and the existing Playwright dependency if running browser
   cases. Run the original synthetic native/WASM smoke checks before Jak.
4. Run the small pilot; inspect reports and actual backend detection. A Mac
   without a usable GPU session may need a logged-in session for GPU cases.
5. Freeze the commit and binary. Run the bounded batch directly from a terminal.
   On macOS, use `caffeinate -i` as shown above if sleep would interrupt it. The machine must remain powered and awake for the run.

No scheduler, remote login or automation has been configured by this roadmap.
A one-shot overnight process is sufficient; recurring agent wakeups add no value
while a deterministic batch is still working.

## Agent handoff template

> Work on Eco issue <number> at commit <sha>. Read docs/ROADMAP.md and the linked
> issue contract. Use a codex/<issue>-<topic> branch and a dedicated checkout.
> Implement only that issue; run its synthetic checks and bounded local pilot.
> For measurement, freeze the build and launch one bounded batch. Do not keep
> requesting model analysis while the subprocess is running. If a limit or new
> failure stops it, preserve evidence and return a concise report with the first
> actionable divergence. Do not silently extend budgets, change acceptance
> criteria or launch a new architectural approach. Keep game-derived artifacts
> local. Provide revision, commands, checks, result paths and unresolved limits.

The batch should run independently of an active agent session. After it exits,
give its summary to an agent in a new turn. This avoids relying on a model to
stay active overnight, polling repeatedly or spending tokens rereading logs.

## Morning review

Read the summary first: cases completed/pending, time/output/disk stops, first
mismatch, missing code grouped by PC/RA, and actual backend. Open only the
relevant trace or capture. Select one reproducer for the next issue. Do not
paste entire logs or game data into GitHub issues. A report that says
"no reliable comparison: repeatability failed" is a useful result.
