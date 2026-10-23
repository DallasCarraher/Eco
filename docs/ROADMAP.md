# Eco: next steps

Updated October 23, 2026 with the partial OpenGOAL experiment on merged
PR #12 base `dd90204`, preserving the reference checkpoint from PR #11.
See the [issue audit](work-items/README.md) for evidence and ticket status.

**Goal:** eventually run every Jak and Daxter game locally in a browser.
**First playable milestone:** start Jak 1, reach Sandover Village, move around,
control the camera, hear audio, save, and reload after restarting the browser.

## Recommendation

Complete native OpenGOAL kernel suspension parity for the generated nested-wait
prototype next. The initial native/browser traces match through an explicit
adapter, but both full feasibility proofs remain incomplete. Keep the Eco
startup-reference investigation paused and obtain the missing evidence before
choosing one main trilogy implementation.

Eco translates the original PS2 program and recreates console services.
OpenGOAL provides recovered game source and a PC runtime that we could adapt
to the browser. Neither has demonstrated playable browser Jak in this project.

## Already completed

- The automatic native experiment runner is implemented and merged. Reuse it.
- VU fixes (the PS2's vector-math processors) and focused native/browser checks
  are merged in PRs #9/#10. One saved long calculation now compares fully.
- PR #11 is merged. PCSX2 captures cover startup through the title screen.
  The static Sony checkpoint matches Eco exactly in RGB; a frozen replay
  identifies Eco frame 510 as the Naughty Dog intro (`ndi-intro`).
- The intro comparison narrowed a timing difference across five animation
  channels. Exact pose alignment remains unverified; details are in the report.

Correct graphics and playable browser gameplay remain unproven.

## Reference investigation — paused, with evidence preserved

Keep [#5](https://github.com/DallasCarraher/Eco/issues/5) and
[#3](https://github.com/DallasCarraher/Eco/issues/3) open. The
[reference report](REFERENCE.md) preserves captures, scene identification,
phase measurements and limits. PR #11's 15 synthetic tooling tests passed at
merge; they do not establish game correctness.

The next possible Eco diagnostic is streamed-audio position sampling. Resume
it only if a named architecture question or chosen implementation needs it.
Do not repeat setup/capture work or accept a nearest pose as exact. This open
question does not block the OpenGOAL experiment; no graphics gate is marked passed.

## 1. OpenGOAL browser experiment — partial evidence

The [bounded feasibility report](OPENGOAL-FEASIBILITY.md) records a real recovered
wait function lowered through OpenGOAL IR to generated C++, with matching native
and Chrome traces across three nested suspension/resumption events. This uses
explicit clock/suspend adapters and original loaded data. It does **not** verify
native OpenGOAL kernel parity or general game object loading. Representative
rendering is blocked at the missing OpenGOAL-to-browser renderer interface.
Neither required proof is complete; no architecture or gameplay gate passed.

Next: obtain **native OpenGOAL kernel suspension parity for the nested wait**,
within the latest remaining allocation. Retain the renderer proof as a separate
unfulfilled requirement before choosing the trilogy implementation. Preserve the
existing native compiler build and private failed/passing attempts.

Use the [experiment brief](agent-prompts/05-opengoal-feasibility.md).
No GitHub issue exists for it yet. The narrow prototype generates
C++ while retaining GOAL as the authoritative game source. Extend it only for
the named missing proof; do not hand-port the game or assume a complete backend.

Test a real object that loads data, calls other functions and the runtime,
pauses inside nested calls, and resumes correctly. Compare native/browser
state. Separately try drawing level geometry, an animated character, and
a texture effect.

**Finish with:** evidence for both examples or specific blockers, required
compiler/runtime/renderer changes, and basic size/memory/speed measurements.
Bound the work within the latest applicable cumulative allocation before
execution. A simple arithmetic function or blank canvas is insufficient.

## 2. Choose one main trilogy approach

Prefer OpenGOAL if the examples work and changes remain concentrated in the
compiler, runtime, and renderer. Continue Eco if its remaining faults are
understood and it has a credible general solution for loading relocated code.

**Finish with:** one decision based on remaining work to reach Sandover.
If uncertain, identify one missing proof and its cost. Preserve the other
implementation without developing two complete ports at once.

## 3. Make Jak 1 playable, then expand

For Eco: finish matching native/browser inputs (#2), resolve remaining graphics
faults with reference evidence (#3/#4/#5), address code-loading gaps (#6), and
validate gameplay (#7). If OpenGOAL is chosen, replace Eco-specific tasks while
keeping the same acceptance requirements.

**Finish with:** two fresh starts of the Sandover route, usable controls and
camera, correct visible behavior, audible sound, and save/reload across a browser
restart. This verifies the route, not the whole game.

Then measure performance (#8), test Jak 1's remaining levels and transitions,
and add Jak II/3. Evaluate Jak X, Daxter, and The Lost Frontier separately;
one browser interface can support different execution engines.

## Keep the work focused

Expand tooling only when a named next test requires it. Revisit Eco graphics,
audio-timing or VU diagnostics when the decision or a new failure requires them.
Defer broad optimization and other game ports.

Existing milestone names remain: M0 = repeatable native/browser tests;
M1 = correct startup graphics; M2 = reaching Sandover; M3 = gameplay/audio/saves;
M4 = performance. Only M0's native-runner portion is complete.

Use the [experiment details](EXPERIMENTS.md) and [runbook](OVERNIGHT.md) for
commands and limits. Preserve evidence and cumulative budgets; serialize shared
builds/measurements. Game-derived files stay local. This plan starts no experiment,
changes no GitHub issue state, and grants no new experiment budget.
