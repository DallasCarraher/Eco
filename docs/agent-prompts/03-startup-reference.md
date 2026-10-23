# Continue issue #5: frame 510 is ndi-intro; exact pose remains unaligned

Repository DallasCarraher/Eco, worktree
`/Users/dallascarraher/Developer/Eco-startup-reference`, branch
`codex/issue-5-startup-reference`, draft PR #11. Preserve all inputs, builds,
translations, captures and ledgers. Read applicable AGENTS.md, README.md,
docs/REFERENCE.md and the revised roadmap/work queue (use the roadmap-audit
worktree if absent here). Never request Copilot review without explicit owner
instruction. PRs #9/#10 completed VU work and focused native/browser checks;
do not repeat them.

New result: a frozen CPU diagnostic reproduced BOTH archived frame-480/510 PPM
hashes exactly. Terminal frame-510 RAM identifies active logo state `ndi`,
anim `ndi-intro`, spool index 3/parts 4, and active art stream `ndi-intro`.
Thus the named event is the **Naughty Dog intro**, not the later title logo.
Frame 480 is image-identical context, without a separate state snapshot.

**Exact pose alignment is still unverified.** The existing PCSX2 capture includes
this sequence; GS900/1200 are labeled context, not claimed equivalent poses.
Native targets differ: Eco 512x448, selected PCSX2 intro targets 512x224 before
display composition. The comparison uses native-size RGB tiles with padding and
labels only. No counter offset, cross-pose pixel comparison/tolerance or PS2
hardware-correctness claim is permitted. The earlier Sony match (Eco25/100 vs
reference330) remains exact but cannot be extrapolated.

Current private evidence `local/reference-marker-20261022/`: result.json,
markers-510/markers.json, replay-identity.json, validated-replay/,
sequence-comparison.png and jobs/. Raw RAM/images, settings, hashes and paths
stay ignored/local. Original decoder scripts/reference_event_markers.py has
four passing synthetic tests and validates retail symbol/type and active-tree
links; GOAL's false terminator is nonzero. First historical frame600 RAM was
used for decoder development only. The first new CPU replay lacked a pre-created
capture directory; the corrected repeat passed exact hashes. Both RAM dumps and
failed postprocessor logs remain preserved. Two CPU replays, no PCSX2 launch,
rebuild, GPU comparison or VU reinvestigation occurred.

Existing independent capture remains local/reference-later-20261022/: 152 PNGs,
124 unique, GS180..2385, Sony through title/Press Start. Official PCSX2 2.8.2,
provided BIOS and disc are already verified. No new download/BIOS search needed.

Latest released ledger:
`/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/reference-marker-20261022-allocation.json`.
Cumulative **7,941.788 / 14,400 s**, remaining **6,458.212 s**. Shared retained/
sampled peak **4,113,836,817 bytes**, free **11,905,126,400 bytes**. Marker active
reservation was 300 s, 64 MiB retained/128 MiB peak; retained growth 77,080,143 bytes
exceeded retained estimate after preserving both RAM dumps but stayed inside
peak/shared cap. Prior read-only reservation added no queued subprocess debit.
Lock released and no game running. Recheck newer allocations/usage/storage before
any new admission. Shared cap 8 GiB, >=10 GiB free, <=900 s/subprocess, serial
diagnostics, no budget reset. Weekly remaining last 91%; stop at 85%. No subagents,
overnight matrix, API/model calls in replay tools or messages to other sessions.

Next is independently identifying the animation phase/camera pose inside
`ndi-intro` to choose a truly matching reference image. Do not make another blind
startup pass or treat semantic sequence identity as same-pose alignment. The
current comparison supplies a reproducible checkpoint for #3, but no GS/backend
cause is established. Any further phase-marker diagnostic must be narrowly scoped
and admitted under the same ledger. No expectations/tolerances/mismatch changes.
Commit original tooling/docs only and update PR #11 with evidence and limits.
