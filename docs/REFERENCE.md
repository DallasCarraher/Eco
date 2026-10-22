# Startup reference protocol: boot-idle scene near Eco frame 510

## Current result

The read-only prerequisite cycle on 2026-10-22 verified the local disc against
the archived Eco report and all four CPU frame-480/510 capture hashes. It found
no PCSX2 candidate on PATH, in scoped standard app/data locations or via a
Spotlight filename query. No BIOS was selected. This is a scoped inventory,
not proof that the user has no emulator or BIOS elsewhere. **Reference execution
and capture are blocked on their local paths.** The user has been asked for them.
Nothing was installed, launched or reconfigured; no independent capture exists.

Worktree: `/Users/dallascarraher/Developer/Eco-startup-reference`, branch
`codex/issue-5-startup-reference`, based on merged #10 (`7ef6532`). Existing
checkouts/builds/translations/evidence remain unchanged.

## Verified Eco anchor

Use `boot-idle/eco-00510`, SCUS_971.24 USA Rev 1, no controller presses, fresh-card
scenario. Archive: `Eco-issue-4/local/experiments/issue4-q-images-510/`, measured
from source `da6352fa70669c9b3a0c6e420ed79d65322a2b27`. CPU compiled and interpreted
captures match each other and their recorded hashes:

| Eco frame | Capture SHA-256, both CPU paths |
| --- | --- |
| 480 | `7240b9940ca6ba6017d7bbf18ae366a5d12404718bd2335143d2452770dbc77a` |
| 510 | `dea10cb896ab35570b90055b66f367813ae03ac888a1bc5f44e34eda847540be` |

These are alignment anchors, not golden images or proof of the first wrong frame.
The archived 98 available captures cover 25..510 every five frames; 5/10/15/20
are absent. New-build repeatability and independent visual correctness were not
established by that archive. See [the historical validation](ISSUE4-VU-PREFIX.md#post-q-fix-image-validation).

## Inventory reproduction

`scripts/reference_inventory.py` reads metadata and hashes inputs; it never starts
the emulator. It writes private JSON to a new ignored directory. Example from
this worktree, under the shared serial allocation:

```sh
python3 scripts/reference_inventory.py --output local/reference-inventory/inventory \
  --eco-report /Users/dallascarraher/Developer/Eco-issue-4/local/experiments/issue4-q-images-510/report.json \
  --iso '/Users/dallascarraher/Developer/Eco/Jak and Daxter - The Precursor Legacy (USA) (En,Fr,De,Es,It) (Rev 1).iso'
```

That command exited 0: inventory succeeded; capture was not attempted. Do not
overwrite its output. For a later inventory use a new directory and add explicit
`--emulator /path/to/PCSX2.app` (or executable) and `--bios /path/to/user-bios.bin`.
The tool hashes selected files privately; bundle version metadata alone does not
verify CLI version or capture support. Disc mismatch or changed anchor bytes fail
the inventory. BIOS details, disc hashes, paths, configuration and screenshots
stay in ignored local storage. Do not acquire firmware or disc images elsewhere.

## One-event capture procedure, after prerequisites are available

1. Renew shared admission and acquire the common cross-checkout serial lock.
   Inspect the installed build's help/version and verify its executable hash;
   no capabilities are established merely by these online instructions.
2. Create a **new private application-data directory**. Identify the selected
   user BIOS and same disc by hash. Do not alter the user's global emulator
   configuration, reuse an unrelated save state/card or automatically copy a
   personal configuration. Record any setup work inside the private directory.
3. Record build/version, BIOS identity, renderer/backend, resolution, interlacing,
   aspect/output size, patches/cheats, game fixes, speedhacks, boot method, pacing,
   controller bindings/disconnections and memory-card initial state. Match the
   Eco fresh-card scenario where supported; otherwise record the mismatch before
   interpreting images. Keep normal timing and no Start pulse. Eco's direct ELF
   launch and reference fast boot need not have equivalent initial state.
4. Establish a capture mechanism supported by that build. Record whether it
   captures raw GS output, an emulator screenshot or a composed desktop window.
   No frame-limit or screenshot CLI option has been verified. Read the relevant
   computer-use skill before any UI capture/setup. Confirm the shutdown and
   process-group timeout mechanism before launching a game.
5. Make one bounded no-input pass, stopping at the visual event corresponding to
   the Eco anchor. Capture only the minimum nearby views needed for alignment,
   with timestamps and separate Eco/reference counters. Use frame 480 as context.
   Label the scene only after inspecting both sides. Do not assume reference
   frame 510 or guessed seconds represent the same event. Stop if alignment fails.
6. Preserve originals and hashes. Describe temporal, crop/scale, interlace and
   renderer differences separately from geometry/content. Any presentation
   transform produces a new labeled artifact. Do not add comparison tolerances,
   suppress pixel mismatches, change Eco expectations or call emulator output
   PS2 hardware truth. A repeatability claim needs a separately bounded repeat.
7. Hand #3 the aligned event description, local artifact hashes, settings and
   uncertainty. A software/GPU difference suggests a GS stream reduction; a
   shared independently demonstrated defect suggests tracing common inputs.
   Neither inference exonerates VU or proves the other backend correct.

The [official PCSX2 CLI documentation](https://github.com/PCSX2/pcsx2-net-www/blob/main/docs/advanced/cli.md)
lists `-datapath`, `-logfile`, `-fastboot`, `-batch`, `-version` and `-help`.
`-portable` overrides `-datapath`; do not combine them for isolation. `-gamecfg`
alone is not application-data isolation. `-batch` exits on shutdown; it is not a
time limit. After local help/setup verification, the launch shape is:

```sh
"$PCSX2_EXE" -datapath "$REFERENCE_DATA" -logfile "$REFERENCE_LOG" \
  -fastboot -batch -nofullscreen -- "$USER_ISO"
```

This is a protocol template, not an executed command or unattended capture tool.
Use private paths and the external bounded supervisor. Do not leave a game running
while waiting for model input. No runtime/browser/GS/input fix belongs in this track.

## Shared accounting and continuation

Released inventory ledger:
`Eco-artifact-audit/local/artifact-audit-20261021/reference-inventory-allocation.json`.
It carries **7,492.477 s** and adds **1.093 s**, totaling **7,493.570 / 14,400 s**.
Shared retained/sampled peak: **3,841,499,866 bytes**; private temporary peak: zero;
free disk: **20,438,642,688 bytes**. Between-poll peaks remain unmeasured. Reservation:
60 s active, 16 MiB retained / 128 MiB peak. Private inventory/logs are under
`local/reference-inventory/`. These values are historical, not a new capture slot.

The user-authorized shared cap is **8 GiB**, superseding older 2 GiB prose. Time
does not reset with a chat, branch or issue. Preserve all evidence, remeasure
before adding artifacts, keep >=10 GiB free, run serially, and limit every
subprocess to <=900 s. Weekly account usage must remain above the user's
85%-remaining stop threshold; check between stages. Do not run the overnight matrix.

Smallest next action: obtain the two prerequisite paths, verify the selected build
and BIOS privately, and establish its isolated capture facility. A compact
[continuation prompt](agent-prompts/03-startup-reference.md) supports a fresh chat;
that transition must carry this evidence and ledger forward rather than restart work.
