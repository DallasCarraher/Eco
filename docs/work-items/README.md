# Agent work queue

Pick one issue, read its scope and stop conditions, and work on a dedicated branch/checkout.
These are planning tickets; none is implemented by this documentation change.
Local copies preserve the initial contracts. GitHub is authoritative for later status and discussion.

| Issue | Local contract | Readiness |
| --- | --- | --- |
| [#1: Build a bounded, resumable native experiment runner for overnight batches](https://github.com/DallasCarraher/Eco/issues/1) | [01.md](01.md) | Ready; first priority |
| [#2: Make native and browser startup input replays and captures comparable](https://github.com/DallasCarraher/Eco/issues/2) | [02.md](02.md) | After #1 schema; can develop independently |
| [#3: Localize startup geometry corruption with software and WebGPU comparisons](https://github.com/DallasCarraher/Eco/issues/3) | [03.md](03.md) | After #1; reference from #5 |
| [#4: Isolate compiled VU versus interpreter differences affecting startup geometry](https://github.com/DallasCarraher/Eco/issues/4) | [04.md](04.md) | After #1; coordinate with #3 |
| [#5: Establish a PCSX2 reference capture protocol for Jak startup checkpoints](https://github.com/DallasCarraher/Eco/issues/5) | [05.md](05.md) | Ready for inventory/protocol; capture requires local prerequisites |
| [#6: Extend GOAL coverage from startup toward Sandover with relocation regressions](https://github.com/DallasCarraher/Eco/issues/6) | [06.md](06.md) | After #1/#2; visual signoff after M1 |
| [#7: Validate first playable Sandover route, controls, audio and save reload](https://github.com/DallasCarraher/Eco/issues/7) | [07.md](07.md) | After #2–#6 milestone gates |
| [#8: Measure browser loading, frame pacing and memory after correctness gates](https://github.com/DallasCarraher/Eco/issues/8) | [08.md](08.md) | After #7 |

Recommended first handoff: issue #1. The output is a tested runner and short pilot,
not an unattended full-game repair agent. After that, the Mac mini can execute
a frozen matrix with no model calls and return evidence for #3 and #4.

Develop independent tooling in separate checkouts if desired, but serialize GPU
measurements and builds on a machine. Do not share writable games/, generated/
or build/ directories between agents. Issue #5 can make progress on its protocol
even while other issues await the harness.

