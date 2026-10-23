# Continue issue #5: ndi-intro phase bracket measured, exact pose unverified

Repository DallasCarraher/Eco; worktree
`/Users/dallascarraher/Developer/Eco-startup-reference`, branch
`codex/issue-5-startup-reference`, draft PR #11. Preserve all builds, inputs,
translations, captures, states and ledgers. Read applicable AGENTS.md, README,
REFERENCE.md and the revised roadmap/work queue (roadmap-audit worktree if needed).
Never request Copilot review without explicit owner instruction. Do not repeat
merged VU/native/browser work or start an alternate port by default.

Eco frame510 is `ndi-intro` (Naughty Dog intro), established by a frozen CPU
replay that exactly reproduced archived frame480/510 PPM hashes. Saved RAM has
five coordinated channels: logo, camera-anim, volumes, Jak, Daxter. Their local
frame is **43.818359375 / 0x422f4600**, interpolation zero, speed .5, artist
base115 and step1. Original group names and exact bits are in target-pose.json.

Latest authorized reference probe: one fresh isolated PCSX2 startup process,
normal pacing/no guest input, private local PINE socket, read-only guest-memory
queries and two host state saves. No state load or guest RAM write. It stopped
cleanly after 23.196s and recorded 477 phase observations. In the same streamed
part, adjacent coherent phases are **43.583984375** and **44.052734375**. Eco's
phase lies halfway between them, ±0.234375. No exact phase was observed.
Saved-state RAM confirms phases39.013671875/44.052734375. Later state's five
channel records match Eco in group/speed/base/step/command/interpolation; ONLY
frame bits differ (+0.234375). **Do not call this exact-pose aligned.** This one
pass does not prove the same grid occurs on every possible reference run.

Latest private evidence `local/reference-pose-20261022/`: target-pose.json,
probe.json, phase-observations.json, phase-result.json, capture-settings.ini,
reference.log, jobs/, saved states under data/PCSX2/sstates/, extracted screenshots
and phase-comparison.png. The latter is labeled phase-bracketed context, not an
exact match. Eco512x448, PCSX2 state screenshot640x480 already aspect-corrected by
emulator; layout adds padding/labels only. No crop/scale/tolerance/pixel assertion.
All images/RAM/BIOS/disc/settings stay ignored/local. Original hashes rechecked.

Original reference_pose.py supplies bounded PINE reads and retail five-channel
pose input extraction; six synthetic tests pass (protocol/read bounds, linked
channels, invalid link, one-bit phase distinction). No native/browser rebuild
or VU investigation. PCSX2 2.8.2 is already verified; no download or BIOS search
needed. Earlier reference/marker/inventory evidence remains historical.

Latest released ledger:
`/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/reference-pose-20261022-allocation.json`.
Cumulative **7,979.183 /14,400 s**, remaining **6,420.817 s**. Shared retained/
sampled peak **4,153,755,479 bytes**, free **12,484,788,224 bytes**. Reservation
600s,192MiB retained/256MiB peak; active37.395s. Lock released/emulator stopped.
Remeasure and inspect newer allocations before admission; shared cap8GiB,
>=10GiB free, <=900s/subprocess, serial diagnostics, no budget reset. Weekly
remaining last89%; stop at85% remaining and check between stages. No subagents,
overnight matrix, model/API calls inside replay programs or session messages.

Next: inspect how streamed-audio position sampling produces the half-step phase
offset, using the saved RAM/state evidence. Retail loader uses current-str-pos,
not display counters. Do not make another blind startup capture, silently accept
a nearest pose, blend images, change timing or force guest phase to claim exact
alignment. Any new diagnostic needs a narrow hypothesis and renewed admission.
Keep GS/backend causal attribution unknown and do not claim hardware truth.
Update PR#11 and current summaries with exact evidence/commands and limits;
commit original tooling/docs only. OpenGOAL prototype is a later scoped task.
