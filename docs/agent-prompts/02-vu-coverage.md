# Prompt: bounded VU whole-invocation coverage

**Historical handoff, completed for its saved-input objective:** PR #10 is merged.
Read the [current issue audit](../work-items/README.md) before assigning work.
The constraints and accounting below describe the original task, not a new run.

Repository: DallasCarraher/Eco
Primary checkout: /Users/dallascarraher/Developer/Eco
Preserved investigation checkout: /Users/dallascarraher/Developer/Eco-issue-4

Read applicable AGENTS.md, docs/ROADMAP.md, docs/EXPERIMENTS.md,
docs/OVERNIGHT.md, docs/work-items/04.md, docs/ISSUE4-VU-FLAGS.md and
docs/ISSUE4-VU-PREFIX.md before acting. Inspect working trees and preserve
existing work. Start from the merged issue-4 corrections (at least 22762de,
or their merged equivalent). Create a dedicated checkout and the branch named
below. Treat all existing investigation builds/generated/game-output folders
as read-only. Never share writable build/generated/game-output directories.
Do not reset, clean, rebase or delete another task's worktree.

All game inputs, assets, translations, traces and captures stay in ignored
local storage. Never commit ISO/BIOS/assets/game-derived code or images.
No model/API calls inside replay/comparison programs. Neither Eco path is an
independent correctness oracle. No tolerances, changed expectations or
suppressed mismatches. No browser/input/GS fixes or architecture expansion.

Budget is shared across these follow-ups, not a fresh allowance per session.
The last ledger was about 1.89 GiB retained under a 2 GiB cap, about 113 MiB
remaining, at least 27 GiB free, and under 20 minutes measured game subprocess
time (build/synthetic time separate). Re-measure before adding artifacts.
Keep >=10 GiB free, <=900 seconds per subprocess and <=4 hours cumulative
active experiments. Diagnostic cases are serial, including across sessions.
Run the storage-audit follow-up first. Until its storage/time allocation is
explicit and no other diagnostic is running, do read-only analysis only;
do not silently reset budgets or start concurrent runs. Do not delete or
rewrite evidence to make room. Record peak temporary as well as retained use.

Proceed autonomously within this scope, then stop after one bounded cycle.
Commit original source/test/documentation changes only; do not merge or message
other sessions unless the user authorizes it. Report branch/commits, exact
commands, identities, results, artifact locations, limits and smallest next
experiment. If blocked, preserve evidence and report the precise missing input.

Branch: codex/issue-4-vu-coverage

Objective: address the diagnostic coverage blocker for the saved long VU
invocation without merely raising the 8,192-continuation guard. Design bounded
checkpoints or resumable execution that preserve the complete interpreter and
compiled continuation state. Begin with offline analysis and original tests.

Read scripts/replay_vu_snapshot.cpp, scripts/run_vu_prefix.py,
scripts/repro_vu_dispatch_flags.py, scripts/repro_vu_dispatch_q.py and the
sampling/state-restore/escape/branch/flag/Q logic in runtime/src/vu_micro.cpp.

Saved input prefix (read-only):
/Users/dallascarraher/Developer/Eco-issue-4/local/experiments/issue4-flags-check-validation-510/boot-idle--vu-chain-check--1--f29ec88a2acf/vu-limit
It is frame 192, key 8A7C5336C2223702, entry 0020, root index 348.
After 8,192 continuations both corrected paths match exactly at PC 1280,
113,104 issued instructions. This is a partial observation, not a completed
invocation. Preserve PC/NPC, pending end, delay-slot/branch history, registers,
memory, flag rings, issue clock, pending Q and packet ordering; restarting the
interpreter at a PC alone previously masked a real discrepancy.

Verify snapshot/tool/generated hashes against the sealed reports before reuse.
Read local/experiments/issue4-prefix-q-fixed-8192/report.json and the local
issue4-prefix/q-fixed/build.json in the preserved checkout. Build privately;
never overwrite those objects or archived outputs.

First create an original finite synthetic program that exceeds the continuation
cap, and prove bounded resumed/checkpoint execution matches uninterrupted
execution, including branch-delay and pending-Q cases. Make incomplete/error/
timeout states explicit. Do not turn prefix equality into full-invocation
agreement. A segmented design must still impose a finite cumulative budget;
chunking cannot silently evade the existing stop rule. If processing beyond
the current aggregate guard requires a policy change, implement/test the
mechanism synthetically and report that decision before extending game replay.

Once storage/time are allocated, perform only the smallest offline saved-input
comparison justified by the tests. Keep exact register/memory/packet/pipeline
comparisons. Do not boot the game or rerun the matrix by default. If a concrete
new execution bug emerges, reduce it to an original regression before changing
semantics. Keep coverage engineering separate from a correctness claim.
