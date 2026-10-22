# Continue issue #5: captured early Sony checkpoint, target unaligned

Repository: DallasCarraher/Eco. Worktree:
`/Users/dallascarraher/Developer/Eco-startup-reference`, branch
`codex/issue-5-startup-reference`, draft PR #11. Preserve all existing work,
builds, translations, captures and ledgers. Read applicable AGENTS.md, then
docs/REFERENCE.md, docs/EXPERIMENTS.md and docs/work-items/05.md. PR #10 merged
as `7ef6532`; VU investigation and focused native/browser validation are complete.

Official PCSX2 2.8.2 is already downloaded and verified. The supplied BIOS is
suitable and its original hashes were rechecked unchanged. Paths, hashes and
settings are in private evidence; no download or BIOS search is needed. Keep
BIOS/disc/configuration/images ignored/local and preserve originals.

The user authorized a second bounded cycle after the first dump-configuration
failure. This continuation produced **14 validated, byte-identical 512x448 RGB
PNG framebuffers**, PCSX2 GS counters 180..330, showing Sony Computer
Entertainment America presents. Capture capability works, but Eco 480/510
remain **unaligned**. One no-input game process stopped cleanly after 8.272 s:
the early-output guard searched BMP only, so it falsely reported no images.
No restart was attempted. The original framebuffer_images() helper now recognizes
complete PNG/BMP files and ignores partial PNGs; five synthetic tests pass.
Use that helper for early monitoring, not an assumed extension.

Latest evidence: `local/reference-capture-20261022/`, especially
`cycle-result.json`, `identities.json`, `capture-settings.ini`, `reference.log`,
`framebuffers/` and `jobs/`. Exact argv, image SHA-256 hashes/timestamps, counters,
card identity, input semantics and settings/warnings are private. The contact
sheet is a labeled resized preview; preserve the raw PNGs. The raw supervisor
outcome remains capture_not_producing_images, explicitly annotated as false
negative. `next-session-template.py` is corrected but UNEXECUTED; new paths and
admission are mandatory. Earlier setup/inventory evidence stays historical.

Latest released ledger:
`/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/reference-capture-20261022-allocation.json`.
Cumulative **7,694.947 / 14,400 seconds**, remaining **6,705.053 seconds**.
Shared retained/sampled peak **4,008,191,481 bytes**; free **13,679,591,424 bytes**.
Shared cap remains 8 GiB. Remeasure and inspect newer allocations before reserving
under common serial.lock. Keep >=10 GiB free, <=900 s per subprocess, one process
group/diagnostic at a time. Account remained 96% weekly available; check before
and between stages and stop at 85% remaining. No overnight matrix or subagents.
No model/API calls inside replay programs; do not message other sessions.

The authorized cycle is closed. If the user authorizes another, the smallest
step is one longer bounded no-input pass in NEW isolated data/card/output with
format-aware monitoring and the existing finite dump range. Both HWDumpDirectory
and SWDumpDirectory must be configured. Create the -datapath parent; PCSX2 appends
PCSX2/. Run configuration preflight and native -testconfig before launch. Confirm
actual image output early and stop if absent. Do not reuse a card or save state.

The target is boot-idle/eco-00510 with 480 as context. Read-only archive:
`/Users/dallascarraher/Developer/Eco-issue-4/local/experiments/issue4-q-images-510/`.
Find a recognizable matching event in later reference images; do not assume equal
counters or wall times. Dumps are framebuffer textures before display composition;
record crop/aspect/interlace/backend differences separately from geometry. Keep
compatibility warnings and requested/effective settings explicit. Neither Eco
output nor emulator agreement proves PS2 hardware correctness. Do not introduce
tolerances, change expectations or suppress mismatches.

Commit original tooling/docs only, update PR #11 with exact commands/evidence,
remaining prerequisites, cumulative accounting and smallest next action. There is
an early Sony reference checkpoint but no aligned frame-510 handoff to #3 yet.
No runtime/GS/VU/input fix belongs in this track.
