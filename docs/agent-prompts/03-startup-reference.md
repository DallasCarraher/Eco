# Prompt: independent startup reference comparison

**Historical handoff:** draft PR #11 now has the emulator/BIOS setup and early
startup images. Continue from that branch's current reference report and handoff;
the remaining task is later scene alignment. See the
[current issue audit](../work-items/README.md) before using this original prompt.

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

Also read docs/work-items/05.md. Branch: codex/issue-5-startup-reference

Objective: obtain a small, reproducible independent reference comparison for
startup frames near the previously observed image divergence. Treat reference
emulator output as identified evidence with configuration limits, not automatic
PS2 hardware truth. This task produces reference evidence; it does not fix GS,
VU, input handling or compatibility.

Existing Eco evidence is read-only under:
/Users/dallascarraher/Developer/Eco-issue-4/local/experiments/issue4-q-images-510/
Read report.json, summary.md and case logs. CPU compiled/interpreted reach 510
and their 98 available captures (25..510 every five frames) match exactly;
requested 5/10/15/20 are absent. Frames 480 and 510 exist. Both sets also match
the pre-Q-fix baseline. The flag-history correction removed the measured CPU
image gap; the specific early sampled flags mismatch is not uniquely causal.
Q correction fixed a state discrepancy without measured images changing.

Local user-owned disc:
/Users/dallascarraher/Developer/Eco/Jak and Daxter - The Precursor Legacy (USA) (En,Fr,De,Es,It) (Rev 1).iso

Inspect narrowly for an installed suitable reference emulator and user-provided
BIOS/configuration. Prefer its supported deterministic CLI/capture facilities;
read applicable app/computer-use skills before controlling an app. Do not
download BIOS or assets, purchase/install software, or change the user's
existing emulator configuration. Use a private configuration/output directory.
If BIOS or another required input is absent, ask for that exact missing input
and continue read-only alignment planning; never substitute an unverified image.

Record emulator version/build, disc/BIOS hashes privately, renderer/settings,
patches, speedhacks, resolution/interlacing/aspect, input route and capture
method. Use boot-idle, no Start pulse. Start with a tiny set near 480 and 510,
and align by observable scene and event timing; emulator frame numbers need
not share Eco's frame-count origin. Distinguish temporal, crop/resolution,
interlace and renderer differences from geometry/content differences. Preserve
original captures and document any separate analysis transforms; do not add
runtime comparison tolerances or alter expected outputs.

With allocated storage/time and serial ownership, make one bounded reference
capture pass. Describe observable differences and supporting alignment; do
not call either Eco path correct from agreement. If reference execution is
unavailable, deliver the precise blocker and smallest reproducible capture
procedure, without inventing results. Commit only documentation/original
capture tooling, keeping game-derived images and BIOS details private.
