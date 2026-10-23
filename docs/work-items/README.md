# Issue audit and work queue

Audited October 22, 2026. Start with the plain-language [roadmap](../ROADMAP.md).
This page reconciles the original tickets with completed work; the numbered
files retain the detailed contracts and investigation history.

## Findings

All eight GitHub issues are still open. That does not mean all their work remains:
the native runner and major VU work are merged. The former queue incorrectly
recommended building the runner first. Several reports and prompts also describe
earlier blockers that later work resolved; read their current summaries first.

GitHub issue bodies, comments, and PRs differ in freshness. In particular, #5's
latest comment still describes missing emulator/BIOS prerequisites, while the
newer draft PR #11 records an installed emulator, supplied BIOS, and captured
images. The remaining reference task is scene alignment.

## Existing issues

| Issue / contract | Evidence-based status | Recommended next action |
| --- | --- | --- |
| [#1: Native experiment runner](https://github.com/DallasCarraher/Eco/issues/1) · [contract](01.md) | Implemented and merged via #9; pilot and synthetic acceptance evidence recorded. | Treat as completed infrastructure. Recommend closing the ticket with its existing evidence; no rebuild needed for this audit. |
| [#2: Comparable native/browser inputs](https://github.com/DallasCarraher/Eco/issues/2) · [contract](02.md) | No completed game-input parity evidence found. The VU browser fixture does not satisfy this ticket. | Keep queued for the selected browser implementation, before claiming comparable game runs. |
| [#3: Startup graphics](https://github.com/DallasCarraher/Eco/issues/3) · [contract](03.md) | Reference alignment is still missing; prior software/GPU differences do not identify the correct output. | Next after #5: inspect one aligned scene and isolate a reproducible graphics fault or record the remaining uncertainty. |
| [#4: VU differences](https://github.com/DallasCarraher/Eco/issues/4) · [contract](04.md) | Specific pipeline fixes, saved-invocation coverage, and focused native/browser fixtures are merged in #9/#10. Broader correctness is unproven. | Keep the remaining investigation open; resume only when #3/#5 or another concrete failure points to VU behavior. |
| [#5: Independent reference](https://github.com/DallasCarraher/Eco/issues/5) · [contract](05.md) | Draft #11 has early startup images; Eco's target scene is not aligned. | **Immediate priority:** continue the existing capture work and hand an aligned scene to #3. |
| [#6: Reach Sandover / code loading](https://github.com/DallasCarraher/Eco/issues/6) · [contract](06.md) | No completed first-level route evidence found. Historical missing addresses need reproduction against a named build. | Defer expansion until the architecture decision. If Eco continues, prioritize general object loading/relocation over accumulating snapshots. |
| [#7: Gameplay, sound, saves](https://github.com/DallasCarraher/Eco/issues/7) · [contract](07.md) | No accepted playable browser route found. | Keep as the product milestone for either architecture. |
| [#8: Performance](https://github.com/DallasCarraher/Eco/issues/8) · [contract](08.md) | No completed route benchmark found; depends on #7. | Defer broad optimization. Small feasibility measurements remain part of the OpenGOAL trial. |

These are recommendations. This audit did not close, edit, or comment on GitHub
issues, and absence of completion evidence is not proof that nobody has started.

## PRs and evidence

- [#9](https://github.com/DallasCarraher/Eco/pull/9): merged. Includes runner
  prerequisites and VU flag/Q fixes. See [runner acceptance](01.md#implementation-evidence)
  and [post-fix images](../ISSUE4-VU-PREFIX.md#post-q-fix-image-validation).
- [#10](https://github.com/DallasCarraher/Eco/pull/10): merged at `7ef6532`.
  [One saved invocation completes](../ISSUE4-VU-WHOLE-INVOCATION.md);
  [focused browser checks pass](../ISSUE4-VU-BROWSER.md). These are not a full
  game/browser rendering test. #4's latest comment explicitly keeps it open.
- [#11](https://github.com/DallasCarraher/Eco/pull/11): open draft at `ff34092`.
  Fourteen early Sony-screen captures exist; later scene alignment remains.
  Its [reference report](https://github.com/DallasCarraher/Eco/blob/ff34092f51961615ff053df26eae02f1478d50ca/docs/REFERENCE.md)
  is branch work, not merged-main evidence.

## Next handoffs

1. Continue #5 from draft #11's latest reference setup. Deliver the aligned
   scene, or a precise remaining capture/alignment blocker, to #3.
2. Complete one focused #3 comparison. Use #4 only for a reproduced VU fault.
3. Run the proposed two-part OpenGOAL feasibility trial in roadmap step 2.
   No ticket exists for it yet. It is a small experiment, not a full port.
4. Record the architecture decision, then order #2/#6/#7 for the chosen path.

Existing `docs/agent-prompts/` files are historical handoffs, not a fresh queue
or new budget allocation. The VU coverage prompt's saved-input objective is
complete. For reference work, use #11's newer handoff rather than restarting
from main's original prerequisite inventory. Existing storage accounting remains
in force; choose the latest ledger when scheduling an actual experiment.
