# Issue audit and work queue

Updated October 22, 2026 after PR #11 merged. Start with the
plain-language [roadmap](../ROADMAP.md).
This page reconciles the original tickets with completed work; the numbered
files retain the detailed contracts and investigation history.

## Findings

All eight GitHub issues are still open. That does not mean all their work remains:
the native runner and major VU work are merged. The former queue incorrectly
recommended building the runner first. Several reports and prompts also describe
earlier blockers that later work resolved; read their current summaries first.

GitHub issue bodies and comments can lag the merged evidence. PR #11 now records
a complete startup reference, an exact static Sony match, `ndi-intro` sequence
identification, and a measured animation-phase bracket. Exact pose alignment
remains unresolved. The owner chose to pause that investigation and test a
bounded OpenGOAL prototype next; neither the pause nor merge marks graphics
correctness complete. Emulator/BIOS setup is no longer a missing prerequisite.

## Existing issues

| Issue / contract | Evidence-based status | Recommended next action |
| --- | --- | --- |
| [#1: Native experiment runner](https://github.com/DallasCarraher/Eco/issues/1) · [contract](01.md) | Implemented and merged via #9; pilot and synthetic acceptance evidence recorded. | Treat as completed infrastructure. Recommend closing the ticket with its existing evidence; no rebuild needed for this audit. |
| [#2: Comparable native/browser inputs](https://github.com/DallasCarraher/Eco/issues/2) · [contract](02.md) | No completed game-input parity evidence found. The VU browser fixture does not satisfy this ticket. | Keep queued for the selected browser implementation, before claiming comparable game runs. |
| [#3: Startup graphics](https://github.com/DallasCarraher/Eco/issues/3) · [contract](03.md) | Static Sony match and later sequence identity are established. Exact intro pose and GS/backend cause remain unverified. | Keep open; pause investigation during the OpenGOAL trial. Resume for a concrete decision question or the selected implementation. |
| [#4: VU differences](https://github.com/DallasCarraher/Eco/issues/4) · [contract](04.md) | Specific pipeline fixes, saved-invocation coverage, and focused native/browser fixtures are merged in #9/#10. Broader correctness is unproven. | Keep the remaining investigation open; resume only when #3/#5 or another concrete failure points to VU behavior. |
| [#5: Independent reference](https://github.com/DallasCarraher/Eco/issues/5) · [contract](05.md) | Merged #11 covers startup through title, exact Sony RGB match, `ndi-intro` identity and a ±0.234375 phase bracket; exact pose unverified. | Keep open and preserve evidence. Audio-position sampling is a possible follow-up, not a prerequisite for the OpenGOAL trial. |
| [#6: Reach Sandover / code loading](https://github.com/DallasCarraher/Eco/issues/6) · [contract](06.md) | No completed first-level route evidence found. Historical missing addresses need reproduction against a named build. | Defer expansion until the architecture decision. If Eco continues, prioritize general object loading/relocation over accumulating snapshots. |
| [#7: Gameplay, sound, saves](https://github.com/DallasCarraher/Eco/issues/7) · [contract](07.md) | No accepted playable browser route found. | Keep as the product milestone for either architecture. |
| [#8: Performance](https://github.com/DallasCarraher/Eco/issues/8) · [contract](08.md) | No completed route benchmark found; depends on #7. | Defer broad optimization. Small feasibility measurements remain part of the OpenGOAL trial. |

Issue states remain unchanged. The owner approved this task order and PR #11's
merge; absence of completion evidence is not proof that nobody has started.

## PRs and evidence

- [#9](https://github.com/DallasCarraher/Eco/pull/9): merged. Includes runner
  prerequisites and VU flag/Q fixes. See [runner acceptance](01.md#implementation-evidence)
  and [post-fix images](../ISSUE4-VU-PREFIX.md#post-q-fix-image-validation).
- [#10](https://github.com/DallasCarraher/Eco/pull/10): merged at `7ef6532`.
  [One saved invocation completes](../ISSUE4-VU-WHOLE-INVOCATION.md);
  [focused browser checks pass](../ISSUE4-VU-BROWSER.md). These are not a full
  game/browser rendering test. #4's latest comment explicitly keeps it open.
- [#11](https://github.com/DallasCarraher/Eco/pull/11): merged at `71016a2`,
  reviewed head `cdd1ccb`. The [reference report](../REFERENCE.md) records
  152 valid startup images (124 unique), an exact Sony match, image-bound
  `ndi-intro` identification and the unresolved phase difference. All 15
  original synthetic reference-tool tests and the diff check passed at merge;
  no new game run was made for review. This is merged diagnostic evidence,
  not graphics or gameplay acceptance. No GitHub checks were reported.

## Next handoffs

1. Run the [two-part OpenGOAL feasibility trial](../agent-prompts/05-opengoal-feasibility.md):
   real generated execution with nested pause/resume, plus representative browser
   rendering. No ticket exists yet. Read the brief and latest cumulative budget
   before execution; this documentation update starts no experiment.
2. Record an architecture decision using the trial and existing Eco evidence.
   If uncertain, name one missing proof and its bounded cost.
3. Order #2/#6/#7 for the chosen path, replacing Eco-specific tasks if needed.
   Resume #3/#4/#5 only where that decision or a concrete fault requires them.

Prompts 02–04 are historical handoffs, not a fresh queue or budget allocation.
The VU coverage prompt's saved-input objective is complete; the reference prompt
is paused. Prompt 05 is the new feasibility brief. Existing storage/accounting
constraints remain in force; inspect the latest ledger when scheduling work.
The last reference release recorded 7,979.183 / 14,400 seconds used and
6,420.817 seconds remaining under the shared 8 GiB cap. These are historical
balances, not a new allocation; other work may have consumed more since then.
