# Startup reference protocol: boot-idle scene near Eco frame 510

## Current result

The 2026-10-22 setup/reference cycle downloaded the official stable **PCSX2
2.8.2** macOS release into ignored local storage. GitHub's release-asset SHA-256
matched; deep/strict code-signature verification passed and Gatekeeper accepted
the notarized Developer ID. The x86-64 binary ran using existing Rosetta on this
arm64 macOS 26.6.2 host; bundle minimum OS is 11.0. Sources:
[official release](https://github.com/PCSX2/pcsx2/releases/tag/v2.8.2) and
[requirements](https://pcsx2.net/docs/setup/requirements/).

The supplied BIOS directory had one ROM candidate. Read-only ROM-directory
inspection, private hashes and PCSX2's successful BIOS load established local
suitability for this setup; the original files were preserved and their hashes
rechecked. No additional BIOS or game data was downloaded. A **new inventory**
verified the disc and all four Eco anchors, leaving the earlier inventory intact.
Executable help/version and isolated configuration initialization were verified.

**No independent image or visual alignment was obtained.** There was one paused
initialization (zero recorded play seconds), followed by one no-input game pass
with a 45-second supervisor limit and clean exit after TERM. App-control requests
timed out twice. The fallback built-in framebuffer dump produced zero files:
the setup configured only the hardware dump directory, but this build requires
both hardware and software dump directories. Its log explicitly disabled dumping.
This was a configuration error, not evidence about image correctness. The failed
settings and logs remain preserved. Both private directories are now configured;
original preflight tooling and PCSX2's `-testconfig` accept the correction. No
second game pass was attempted.

Private evidence root: `local/reference-setup-20261022/`:

- `provenance.json`, `release.json`: download, signature, compatibility and BIOS
  inspection evidence; input identities stay private.
- `inventory/inventory.json`: new selected-emulator/BIOS inventory.
- `jobs/*.json`, `jobs/*.done`, `jobs/*.log`: exact argv, exit codes, limits and
  timings, including the failed configuration initialization.
- `capture-settings.ini`, `after-capture.ini`, `corrected-capture-settings.ini`:
  preserved attempted settings and prepared correction. Actual renderer,
  game-fix/patch warnings and timing observations are in `capture-reference.log`.
- `initial-card.json`, `cycle-result.json`: new erased-card identity, artifact
  hashes, no-input setup and failed capture result. Card, BIOS working copies,
  configuration and captures stay ignored. Lossless PNG previews of the two Eco
  anchors are labeled previews; original PPMs remain unchanged.
- `preflight-failed/preflight.json`, `preflight-corrected/preflight.json`: expected
  rejection (exit 2) and corrected configuration acceptance (exit 0).

Worktree: `/Users/dallascarraher/Developer/Eco-startup-reference`, branch
`codex/issue-5-startup-reference`, based on merged #10 (`7ef6532`). Existing
checkouts/builds/translations/evidence remain unchanged. Neither Eco output nor
PCSX2 agreement would establish PS2 hardware correctness.

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

## One-event capture procedure for a separately admitted continuation

1. Renew shared admission and acquire the common cross-checkout serial lock.
   Inspect the installed build's help/version and verify its executable hash;
   no capabilities are established merely by these online instructions.
2. Create a **new private application-data directory**. Create the parent passed
   to `-datapath` first: PCSX2 2.8.2 appends `PCSX2/` and does not recursively
   create a missing parent. The first attempt otherwise shows a modal error.
   Identify the selected user BIOS and same disc by hash. Do not alter the user's global emulator
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

This is a protocol template; the executed variant is recorded below and privately.
Use private paths and the external bounded supervisor. Do not leave a game running
while waiting for model input. No runtime/browser/GS/input fix belongs in this track.

## Framebuffer configuration gate

`scripts/reference_capture_preflight.py` checks a private PCSX2 2.8.2 INI without
launching it. This is a narrow gate for the built-in framebuffer dump path; it
never verifies capture capability, input semantics, effective game overrides or
visual alignment. It requires both existing private dump directories, enabled
frame dumping and a finite frame range. PCSX2's own
[`GSOptions::LoadSave`](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/Pcsx2Config.cpp)
disables `DumpGSData` if either directory is empty, even for a hardware renderer.
The dump saves framebuffer textures before display composition, so it is not an
emulator screenshot or raw PS2 hardware output. Local executable behavior must
still confirm output creation early in a future pass.

Executed commands below use variables for private inputs. Exact expanded argv
and the attempted settings are retained in the private jobs and result manifest:

```sh
python3 scripts/reference_inventory.py --output "$PRIVATE/inventory" \
  --eco-report "$ECO_REPORT" --iso "$USER_ISO" \
  --emulator "$PCSX2_APP" --bios "$USER_BIOS"
"$PCSX2_EXE" -datapath "$PRIVATE/data" -help
"$PCSX2_EXE" -datapath "$PRIVATE/data" -version
"$PCSX2_EXE" -earlyconsolelog -datapath "$PRIVATE/data" -testconfig
# Actual game pass: external serial supervisor imposed a 45-second limit.
"$PCSX2_EXE" -earlyconsolelog -datapath "$PRIVATE/data" \
  -logfile "$PRIVATE/capture-reference.log" -fastboot -batch -nofullscreen \
  -- "$USER_ISO"
python3 -m unittest discover -s scripts -p test_reference_capture_preflight.py -v
python3 scripts/reference_capture_preflight.py --private-root "$PRIVATE" \
  --config "$PRIVATE/capture-settings.ini" --output "$PRIVATE/preflight-failed"
python3 scripts/reference_capture_preflight.py --private-root "$PRIVATE" \
  --config "$PRIVATE/corrected-capture-settings.ini" --output "$PRIVATE/preflight-corrected"
```

All three synthetic tests passed. The negative check reproduced the real missing
software-directory failure. Corrected native configuration initialization exited
0 with no dump-directory warning. That does not demonstrate a working capture.
The BIOS companions were copied only into the private setup so emulator writes
could not affect the supplied originals. Configuration snapshots describe the
controller bindings, card, renderer and compatibility choices; inspect them and
the effective log before treating a later capture as comparable.

## Shared accounting and continuation

Latest released ledger:
`Eco-artifact-audit/local/artifact-audit-20261021/reference-setup-allocation.json`.
Prior inventory debit: **7,493.570 s**. This cycle: **189.656 s**, including a
conservative recovery debit for the first configuration timeout and 5 s for
out-of-queue surface discovery/preview conversion. Cumulative: **7,683.226 /
14,400 s**, leaving **6,716.774 s**. Reservation was 1,500 s active, 768 MiB
retained / 1 GiB peak, under the common `serial.lock`; it is now released.

Shared retained/sampled peak: **3,994,692,762 bytes**; private temporary sampled
peak: zero; free disk: **13,663,531,008 bytes**. Between-poll peaks and external
system/Rosetta caches are unmeasured. The first timeout's TERM stopped PCSX2;
a subsequent group KILL returned EPERM, interrupting supervisor accounting.
A fresh process census verified no survivors before accounting recovery and
lock reacquisition. The later game timeout and shutdown completed normally.

The user-authorized shared cap is **8 GiB**, superseding older 2 GiB prose.
Remeasure before another allocation; keep >=10 GiB free, run serially, and limit
every subprocess to <=900 s. The cap and cumulative debit never reset by chat,
branch or issue. Weekly usage was checked at startup and between stages: 96%
remained throughout; stop at 85% remaining. No overnight matrix was run.

Smallest next step: a **separately authorized/admitted** short no-input capture
pass using both corrected private dump directories, with a fresh erased card
and a new output/data directory. Confirm that the first framebuffer files are
actually written; stop early if not. Recheck configuration/compatibility warnings
and record effective settings. Then align the scene visually using Eco 480 as
context for 510, without assuming matching counters. There is no event description,
reference frame identity or image hash to hand #3 yet. No missing software/BIOS
prerequisite remains; working capture and event alignment remain unverified.
