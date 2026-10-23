# Continue issue #5: full startup captured, Eco 480/510 identity unresolved

Repository DallasCarraher/Eco; worktree
`/Users/dallascarraher/Developer/Eco-startup-reference`, branch
`codex/issue-5-startup-reference`, draft PR #11. Preserve all builds,
translations, captures, inputs and ledgers. Read applicable AGENTS.md, then
REFERENCE.md, EXPERIMENTS.md and work-items/05.md under docs/. PR #10 completed
VU investigation and native/browser fixture checks; do not repeat them.

The latest authorized 45-second no-input pass completed and PCSX2 shut down
cleanly after supervisor TERM. Raw category timeout, exit 0, wall 45.414 s.
The PNG/BMP early-output helper worked. There were **152 validated RGB PNGs,
124 unique, reference GS counters 180..2385**, covering Sony, Naughty Dog,
scenic transition, title-logo reveal and title/Press Start. One game process,
fresh private data/BIOS working copies/erased card, no guest input or state.
Input hashes and original BIOS hashes were rechecked. No further download,
build, native/browser fixture run or VU investigation occurred.

**Exact early alignment:** Eco CPU-compiled archive frames 25/100 match reference
GS330 Sony presents with zero differing RGB pixels and maximum delta zero,
without tolerance. This static scene is not a frame-counter mapping or evidence
of PS2 hardware correctness.

**Eco 480/510 remain unaligned.** Archive context becomes severely distorted
after Sony and provides no recognizable matching pose/landmark for the target.
Do not guess from colors, counters or wall time. The remaining prerequisite is
identifying the animation/draw event in the existing Eco 480/510 evidence.
Do not collect another blind timed capture for later coverage; this sequence
already reaches the title screen. Smallest next step is correlating a named
animation/draw event against these existing images. If metadata is insufficient,
propose a narrow event-marker diagnostic separately before replaying. No runtime
expectation/tolerance changes or suppressed mismatches are allowed.

Latest private root `local/reference-later-20261022/`: cycle-result.json,
identities.json, capture-settings.ini, reference.log, framebuffers/,
sony-anchor-comparison.json and jobs/. It contains image/input hashes, timestamps,
settings, observed warnings and expanded commands/outcomes. The overview/contact
sheets/Eco context are labeled resized previews; originals remain unchanged.
All BIOS/disc/configuration/game images stay ignored and local. Prior setup and
capture directories remain historical evidence. Official PCSX2 2.8.2 and the
user BIOS are already verified; no path question, BIOS search or download needed.

Latest released ledger:
`/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/reference-later-20261022-allocation.json`.
Cumulative **7,744.883 / 14,400 s**, remaining **6,655.117 s**. Retained/sampled
peak **4,036,741,093 bytes**; free **12,568,244,224 bytes**. Shared cap remains
8 GiB; inspect newer allocations and remeasure before admission under common
serial.lock. Keep >=10 GiB free, <=900 s per subprocess, serial diagnostics.
Lock released and emulator stopped. Weekly usage last 94% remaining; check before
and between stages and stop at 85% remaining. No overnight matrix, subagents,
model/API calls inside replay tools, or messages to other sessions.

Commit original tooling/docs only; update PR #11 with exact evidence, remaining
limits and smallest next action. The Sony event is independently aligned; no
exact frame-510 handoff exists yet. First-level/gameplay/repeatability are not
covered. Source/configuration changes require separately scoped justification.
