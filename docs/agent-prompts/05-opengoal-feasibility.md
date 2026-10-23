# Next task: bounded OpenGOAL browser feasibility experiment

## Purpose and starting point

Determine whether mechanically generated C++ from OpenGOAL's recovered GOAL
source, compiled to WebAssembly with a browser-adapted runtime, offers a credible
route to playable Jak 1. This experiment informs the trilogy architecture
decision; it does not commit the project to a full port.

Read root [AGENTS.md](../../AGENTS.md), the [roadmap](../ROADMAP.md) and
[issue audit](../work-items/README.md). PRs #9/#10 and #11 are merged. The
[reference investigation](../REFERENCE.md) is paused with its exact pose mismatch
unresolved. Do not resume capture or audio-timing work to start this trial.

Inspect current checkouts and the existing local OpenGOAL source before adding
dependencies. Record the selected upstream revision and reuse suitable local
inputs. Work on a `codex/` branch with isolated build/generated/output directories.
Keep upstream attribution and licenses. Treat GOAL as the authoritative game
source: generate C++ through a small compiler/backend experiment, not a parallel
handwritten game implementation. Identify the emission point and unsupported
constructs from the actual compiler; an existing portable backend is not assumed.

## Proof A: real execution across native and browser

Select the smallest real Jak 1 object/function path that exercises loaded data,
calls between functions, a runtime service, and suspension inside nested calls
followed by a correct resume. Record its dependency boundary before implementing.
Add original synthetic fixtures for the mechanism where useful, but an
arithmetic-only demo does not establish game feasibility.

Generate the same selected GOAL source mechanically, compile the output for
native and WASM, and run both. Compare observable state and call/resume order
with the existing native OpenGOAL behavior for that path, not solely between
two builds of the new generator. Verify that locals and control flow survive
the pause and that execution returns through the callers correctly. Record
data layout, symbol/function dispatch, pointer representation and runtime-call
assumptions that the example depends on. Unsupported constructs must be explicit;
do not replace meaningful behavior with success stubs.

## Proof B: representative browser rendering

Use one small existing level-geometry sample, an animated character and one
representative texture effect from locally supplied data. Exercise the intended
browser rendering route and compare it with identified native output. Record
the actual browser/backend and any adaptation needed in the renderer, shaders
or asset loading. Keep raw captures private and label differences in pose,
camera, resolution and timing. A blank canvas or unrelated triangle is only
setup evidence. If this proof is blocked, name the missing interface or feature
and leave it unverified.

The two proofs may be separate small programs; a complete game boot is not
required. Prefer existing loaders and runtime pieces where they serve the test.
Do not build a general replacement renderer, rewrite all game functions, or
expand into another game's support during this experiment.

## Limits and delivery

Before builds or runs, read [EXPERIMENTS.md](../EXPERIMENTS.md) and
[OVERNIGHT.md](../OVERNIGHT.md), inspect the latest shared allocation, and record
a finite effort/time/storage plan within the applicable remaining limits.
The old reference ledger is a starting locator, not a reset or current balance.
Use serial ownership for shared resources and bounded ordinary programs for
repeated measurements; no model calls inside experiment loops. Stop at the
allocation limit or a fundamental blocker. Ask only when required resources or
budget are genuinely missing; this brief grants no additional allocation.

Deliver reproducible commands, source/build/browser identities, pass/fail or
not-tested results for both proofs, and basic payload/build-time/memory/frame-time
measurements where available. Separate measured facts from estimates. List the
required compiler, runtime, data-loading and renderer changes, then recommend
OpenGOAL, Eco, or one narrowly scoped missing proof by the remaining work to
reach Sandover with controls, audio and persistent saves. Do not mark gameplay
or whole-game compatibility verified by these examples.

Commit only original tooling, original synthetic fixtures and documentation.
Do not copy recovered game source into Eco commits. Keep game-derived C++/WASM,
assets, RAM, captures and saves ignored and local. End with the decision evidence
and one next step; preserve the alternative implementation without developing
two complete trilogy ports.
Do not request GitHub Copilot reviews unless the owner explicitly authorizes
a review for that PR.
