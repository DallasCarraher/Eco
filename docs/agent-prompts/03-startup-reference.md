# Continue issue #5 after the bounded setup/reference cycle

Repository: DallasCarraher/Eco. Worktree:
`/Users/dallascarraher/Developer/Eco-startup-reference`, branch
`codex/issue-5-startup-reference`, draft PR #11. Preserve its work and all other
checkouts, builds, translations, captures and ledgers. Read applicable AGENTS.md,
then docs/REFERENCE.md, docs/EXPERIMENTS.md and docs/work-items/05.md. PR #10 merged
as `7ef6532`; the VU investigation and focused native/browser validation are done.

The user authorized an official PCSX2 macOS download and supplied BIOS material.
PCSX2 2.8.2 is now downloaded in ignored local storage; release digest, signature,
notarization, existing Rosetta execution and BIOS suitability were verified.
Input hashes and configuration details remain private. No additional firmware or
game assets may be downloaded. The original BIOS files were preserved and their
hashes rechecked. Use the private evidence to resolve paths; no missing-path
question is needed.

Current result: **zero independent images, no event alignment**. One paused
initialization recorded zero play seconds. One actual no-input game pass then
ran under a 45-second supervisor limit and exited cleanly after TERM. CUA app
selection timed out twice. Built-in framebuffer dumping was disabled because
only HWDumpDirectory was configured; PCSX2 2.8.2 requires SWDumpDirectory too.
Both are now configured privately. The new original preflight rejects the failed
settings and accepts the correction; its three synthetic tests passed. Native
`-testconfig` accepts the correction. Capture capability is still unverified.
Do not treat this as successful reference capture or quietly repeat the pass.

Private evidence: `local/reference-setup-20261022/`, especially
`cycle-result.json`, `provenance.json`, `inventory/inventory.json`, `jobs/`,
`capture-reference.log`, `capture-settings.ini`, `corrected-capture-settings.ini`
and both preflight reports. Earlier `local/reference-inventory/inventory/`
remains historical evidence. Exact argv, settings and hashes are local.

The shared latest released ledger is:
`/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/reference-setup-allocation.json`.
Cumulative active debit: **7,683.226 / 14,400 seconds**. Retained/sampled peak:
**3,994,692,762 bytes**; free: **13,663,531,008 bytes**. Shared cap remains 8 GiB,
not a new allowance. Remeasure all scoped experiment trees and inspect for newer
allocations before acquiring common serial.lock. Keep >=10 GiB free, <=900 s per
subprocess, one process group/diagnostic at a time. Check account usage before
and between stages; stop at 85% weekly remaining (last observed 96%). No overnight
matrix, subagents, model/API calls inside replay programs or session messages.

The completed one-pass cycle is closed. If the user authorizes another cycle,
the smallest step is a separately admitted short pass with a new private data,
erased-card and capture directory. Create the -datapath parent first; PCSX2
appends PCSX2/. Configure BOTH private dump directories, run the configuration
preflight and native -testconfig, then confirm output appears early in the actual
pass and stop if not. No second download or BIOS search is needed. Dumped
framebuffers precede display composition; record those limits. Review effective
game-fix/patch warnings and settings before interpreting a future image.

Align to boot-idle/eco-00510 with Eco 480 as context, not matching counters.
Read-only Eco archive:
`/Users/dallascarraher/Developer/Eco-issue-4/local/experiments/issue4-q-images-510/`.
The new inventory verified the local disc and four CPU anchors. Distorted Eco
geometry makes visual alignment uncertain; do not invent a recognizable event.
Neither Eco agreement nor emulator agreement proves PS2 hardware correctness.
Do not change expectations, add tolerances or suppress mismatches.

Commit original tooling/docs only. BIOS, disc, configuration and game-derived
images stay ignored/local. Update PR #11 with exact commands, evidence, budget,
remaining prerequisites and smallest next action. No image/event handoff to #3
exists yet, and no runtime/GS/VU/input fixes belong in this track.
