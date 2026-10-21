# Eco roadmap: evidence before expansion

## Goal and current evidence

Run Jak and Daxter: The Precursor Legacy in a browser, with correct rendering,
controls, audio and saves. The first playable milestone is Sandover Village.

Baseline implementation: `8295c34a38f69090a0bea502a744e1ee503f6b48`.
The local USA Rev 1 image boots as `SCUS_971.24`. Native exploration reached a
600-frame limit. The latest saved Chrome probe reached 891 frames and 2,659,668
primitives, then halted at `0x0068AA28` (return address `0x006896BC`). Geometry is
wrong. These are observations of particular runs, not performance scores or
proof of gameplay. Native and browser inputs currently differ.

## Execution model

An agent designs or fixes a small piece of code, runs synthetic checks, and
hands a frozen experiment to a normal program. That program does the expensive
work without model calls: replay inputs, run comparisons, hash outputs, group
failures, enforce limits, and write a report. An agent reviews the completed
report once and selects the next bounded investigation.

Deterministic means reproducible inputs and recorded outputs. Timing, GPU
rounding and uninitialized state can still make results differ; repeat runs
must measure this before images are used as regression assertions. The existing
VU interpreter is a comparison implementation, not an independent hardware
oracle. Agreement between two Eco paths does not establish PS2 correctness.

## Milestones and gates

| Milestone | Required evidence | Work items |
| --- | --- | --- |
| M0: Repeatable, unattended experiments | Isolated outputs; verified revision/build/disc identities; bounded execution; two repeated startup scenarios; honest failure classification | 01 harness, 02 browser parity |
| M1: Correct startup rendering | First bad frame localized; software/GPU and compiled/interpreted differences explained; Sony/title/intro checkpoints reviewed against a working reference; regression for each fix | 03 GS isolation, 04 VU isolation, 05 reference |
| M2: Reach the first playable area | No missing code on the chosen route; safe relocation/invalidation tests; title-to-Sandover input replay | 06 GOAL coverage, depends on M0 and M1 for visual signoff |
| M3: Verified browser gameplay | Movement, camera, collision, audio and save/reload checklist passes in Chrome | 07 gameplay |
| M4: Practical browser delivery | Measured frame times, loading and memory budgets on named devices; no correctness regressions | 08 performance |

M0 is the immediate priority. Native GS/VU investigations can proceed after the
native harness, while browser parity and reference capture are developed
separately. Reference capture can start immediately if PCSX2 and a user-provided
BIOS are available. Shared builds and game output directories must have one
writer. Do not run concurrent agents against the same generated build.

## Decision points

- If CPU images are correct and GPU images are wrong, isolate GS/WebGPU state,
  transfers and shaders using a captured packet stream.
- If interpreted VU execution changes the bad geometry, isolate the first state
  divergence and reduce it to a synthetic instruction test.
- If both paths agree on wrong output, inspect their shared inputs, DMA/VIF
  decoding and GS state, using reference evidence. Agreement is not exoneration.
- Missing function coverage is tracked separately from graphics correctness.
  Do not treat a later halt address or larger frame count as a rendering fix.
- After one bounded GS/VU/reference investigation cycle, write a continuation
  decision: concrete bugs and reproductions found, remaining gaps, and whether
  further runtime work or a separately scoped OpenGOAL WASM feasibility study
  is justified. Do not start a second port architecture by default.

Ghidra/REA can help analyze a specific unidentified routine after traces narrow
the fault. OpenGOAL already provides useful names, types and recovered logic.
Neither replaces behavioral comparisons or regression tests.

## Materials and ownership

- [Overnight runbook](OVERNIGHT.md): machine setup, budgets, handoff and stop rules.
- [Experiment contract](EXPERIMENTS.md): manifest and result semantics.
- [Startup matrix](../experiments/jak1-startup.json): data-only specification;
  **no runner consumes it yet**. Work item 01 implements that runner.
- [Work items](work-items/README.md): GitHub links, dependencies and agent scopes.

Every issue should end with a reproducible command, a small source diff when
needed, meaningful validation, and a concise evidence summary. Game-derived
captures stay in ignored local storage; commit original synthetic regressions
and diagnostic tooling. The roadmap does not schedule a job or grant another
machine access. No unattended job is started by this planning change.
