# Continue issue #5: one independent startup reference event

Repository: DallasCarraher/Eco. Worktree:
`/Users/dallascarraher/Developer/Eco-startup-reference`, branch
`codex/issue-5-startup-reference`, based on merged PR #10 (`7ef6532`).
Reuse it and preserve its work. Do not reset, clean or modify other checkouts.

Read applicable AGENTS.md first, then docs/REFERENCE.md, docs/ROADMAP.md,
docs/EXPERIMENTS.md, docs/OVERNIGHT.md and docs/work-items/05.md. The reference
protocol and historical inventory are already prepared; do not repeat the VU
investigation. PR #10 completed bounded comparison and focused native/browser
fixture validation, not independent visual correctness. Neither Eco path nor a
reference emulator automatically establishes PS2 hardware truth.

Current status: capture has not started. Scoped PATH, Applications/user app/data
locations and Spotlight did not find PCSX2. No BIOS has been selected. The user
was asked for alternate local emulator and user-provided BIOS paths; incorporate
any reply before proceeding. Do not download firmware/assets, install software,
or modify global emulator settings. If paths remain unavailable, report those
exact missing prerequisites and keep the protocol; do not invent captures.

The read-only inventory command/tool is scripts/reference_inventory.py.
Evidence: local/reference-inventory/inventory/inventory.json (private). It verified
the existing user disc against the archived Eco report and four frame-480/510
captures. Add explicit --emulator and --bios with a NEW output directory once
provided. No emulator launch is part of that tool. BIOS/disc identities stay local.

Shared event: boot-idle/eco-00510, SCUS_971.24 USA Rev 1, no controller presses,
fresh-card scenario. Existing Eco evidence is read-only in
`/Users/dallascarraher/Developer/Eco-issue-4/local/experiments/issue4-q-images-510/`.
CPU compiled/interpreted frames 480 and 510 match each other and their sealed
hashes (listed in docs/REFERENCE.md). They are visual alignment anchors, not
hardware goldens or evidence of the earliest wrong frame. Align the actual scene;
reference frame numbers need not equal Eco frame numbers. No new image tolerance,
changed assertion or suppressed mismatch is allowed. Keep raw captures unchanged.

Objective: verify available reference prerequisites, record exact build/settings,
then perform at most one bounded no-input reference pass for this event if setup
and capture facilities are available. Use a fresh private application-data/card/
output directory and the actual installed build's supported facilities. Verify
help/version and capture method first; online CLI documentation is not proof of
local capabilities. Read applicable app/computer-use skills before UI control.
No browser/input/GS/VU fixes, compatibility expansion or alternate port architecture.

Shared budget does NOT reset per chat, branch or issue. User-authorized storage
cap is 8 GiB, superseding older 2 GiB prose. Latest released ledger:
`/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/reference-inventory-allocation.json`.
Cumulative active debit: 7,493.570 / 14,400 seconds. Historical retained bytes:
3,841,499,866; free bytes: 20,438,642,688. Remeasure and reserve storage/time under
that audit directory's common serial.lock before adding capture/build artifacts.
Diagnostics must be serial across sessions, <=900 s per subprocess, >=10 GiB free.
Do not overwrite preserved builds/generated outputs or delete evidence to fit.
Record retained and temporary peak storage. No overnight matrix. No model/API calls
inside replay/capture programs. Stop if weekly usage reaches 85% remaining;
check between stages and communicate frequently.

Coordinate event description and local artifact hashes with #3/#4; independent
reference setup/capture is tracked in #5. User authorized issue coordination,
but do not message other sessions. Commit only original source/tests/docs;
BIOS/disc/game-derived translations/captures stay ignored. Stop after one bounded
cycle. Report exact commands, identities, results or precise blocker, allocation,
coverage limits and the smallest next action. Preserve the existing evidence and
all outstanding state when handing off to another chat.
