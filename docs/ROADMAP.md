# Eco: next steps

Audited October 22, 2026 against issues #1–#8, PRs #9–#11, merged code
`7ef6532`, and draft reference work `ff34092`.
See the [issue audit](work-items/README.md) for evidence and ticket status.

**Goal:** eventually run every Jak and Daxter game locally in a browser.
**First playable milestone:** start Jak 1, reach Sandover Village, move around,
hear audio, save, and reload.

## Recommendation

Finish one focused graphics comparison, then test a small OpenGOAL browser
prototype. Use those results to choose one main approach for the trilogy
before investing in more extensive development.

Eco translates the original PS2 program and recreates console services.
OpenGOAL provides recovered game source and a PC runtime that we could adapt
to the browser. Neither has demonstrated playable browser Jak in this project.

## Already completed

- The automatic native experiment runner is implemented and merged. Reuse it.
- VU fixes (the PS2's vector-math processors) and focused native/browser checks
  are merged in PRs #9/#10. One saved long calculation now compares fully.
- Draft PR #11 has captured the Sony startup screen in PCSX2, an independent
  PS2 emulator. The later target scene still needs matching to Eco.

Correct graphics and playable browser gameplay remain unproven.

## 1. Compare the same scene — next task

Continue [#5](https://github.com/DallasCarraher/Eco/issues/5) from
[draft PR #11](https://github.com/DallasCarraher/Eco/pull/11), then
[#3](https://github.com/DallasCarraher/Eco/issues/3).

Use the existing reference setup and corrected image detection to capture
the event corresponding to Eco frame 510, with frame 480 as context. Match
the visible scene; the programs' frame numbers are not interchangeable.

**Finish with:** side-by-side images and an explanation of any defect.
Compare Eco's software/GPU output to narrow its cause. Limit this to one
focused investigation, ending with a reproducible problem or a precise blocker.

## 2. Test a small OpenGOAL browser example

New proposed task; no GitHub issue yet. Generate C++ through OpenGOAL's
compiler while retaining GOAL as the game source.

Test a real object that loads data, calls other functions and the runtime,
pauses inside nested calls, and resumes correctly. Compare native/browser
state. Separately try drawing level geometry, an animated character, and
a texture effect.

**Finish with:** working examples or specific blockers, required source
changes, and basic size/memory/speed measurements. Set a finite effort budget
before starting. A simple arithmetic function or blank canvas is insufficient.

## 3. Choose one main trilogy approach

Prefer OpenGOAL if the examples work and changes remain concentrated in the
compiler, runtime, and renderer. Continue Eco if its remaining faults are
understood and it has a credible general solution for loading relocated code.

**Finish with:** one decision based on remaining work to reach Sandover.
If uncertain, identify one missing proof and its cost. Preserve the other
implementation without developing two complete ports at once.

## 4. Make Jak 1 playable, then expand

For Eco: finish matching native/browser inputs (#2), address code-loading gaps
(#6), and validate gameplay (#7). If OpenGOAL is chosen, replace Eco-specific
tasks while keeping the same acceptance requirements.

**Finish with:** two fresh starts of the Sandover route, usable controls and
camera, correct visible behavior, audible sound, and save/reload across a browser
restart. This verifies the route, not the whole game.

Then measure performance (#8), test Jak 1's remaining levels and transitions,
and add Jak II/3. Evaluate Jak X, Daxter, and The Lost Frontier separately;
one browser interface can support different execution engines.

## Keep the work focused

Expand tooling only when a named next test requires it. Revisit VU diagnostics
when a new failure points there. Defer broad optimization and other game ports.

Existing milestone names remain: M0 = repeatable native/browser tests;
M1 = correct startup graphics; M2 = reaching Sandover; M3 = gameplay/audio/saves;
M4 = performance. Only M0's native-runner portion is complete.

Use the [experiment details](EXPERIMENTS.md) and [runbook](OVERNIGHT.md) for
commands and limits. Preserve evidence and cumulative budgets; serialize shared
builds/measurements. Game-derived files stay local. This plan starts no experiment,
changes no GitHub issue state, and grants no new experiment budget.
