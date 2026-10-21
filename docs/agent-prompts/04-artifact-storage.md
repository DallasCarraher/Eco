# Prompt: evidence-preserving artifact storage audit

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

Branch: codex/issue-4-artifact-audit

Run this follow-up before coverage/reference agents create more artifacts.
Objective: establish an accurate shared storage/time ledger and a concrete,
reviewable preservation/cleanup plan. Do not run the game, rebuild, trace or
create a large duplicate archive during the audit.

Inventory read-only the original Eco and preserved Eco-issue-4 checkouts,
including local/, generated/, build/ and their filesystem links. Distinguish
logical bytes, allocated disk blocks, APFS clones/hardlinks/symlinks, temporary
peaks and actual free space. Keep the agreed 2 GiB logical experiment allowance
explicit; physical sharing is not an automatic waiver. Inspect active processes,
locks and worktree ownership without interrupting another task.

Protected completed original batch:
/Users/dallascarraher/Developer/Eco/local/experiments/jak1-overnight-20261020-224647/
Preserved issue-4 evidence includes all sealed local/experiments/issue4-* reports,
case logs and captures; especially the long-invocation vu-limit snapshot,
issue4-prefix-8192, issue4-prefix-q-fixed-8192 and issue4-q-images-510.
Read local/issue4-q-images/{preflight,build,comparison}.json and
local/issue4-prefix/final-validation.json in Eco-issue-4.

Verify hashes before classifying anything. Distinguish irreplaceable diagnostic
inputs/outputs and provenance from reproducible executables/objects and redundant
copies. Map which archives/generated sources are required to rebuild or replay
each report; identify active consumers before proposing removal. Never delete
or edit an immutable completed batch, ISO/BIOS/assets, source, uncommitted work,
worktree or artifact used by another task.

Produce a compact inventory and dependency map, exact candidate paths and byte
savings, preservation destination/capacity, restore commands and verification
steps. Prefer reclaiming reproducible build products only after retaining enough
provenance and inputs for reconstruction. An archive on the same volume may
consume additional peak space; hashing a manifest alone is not a backup.
Do not move, compress, truncate or delete existing artifacts during the audit.
If cleanup is useful, present the fully prepared plan and request approval for
those exact mutations; this prompt authorizes the audit and plan only.

Propose a single explicit storage/time allocation and serial run ownership for
coverage and reference follow-ups. Account for the existing retained artifacts
rather than granting each session a fresh 2 GiB/four-hour budget. Save the
small audit/ledger in ignored local storage, commit a game-data-free handoff
document if useful, and report what work can proceed safely now versus what
requires the user's cleanup/archive approval. No automatic budget increase.
