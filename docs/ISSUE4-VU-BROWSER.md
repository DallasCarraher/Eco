# Issue 4: bounded browser worker attempt

**Focused browser comparison validation now passes for the compiled fixture.**
The follow-up below fixes fixture environment timing and verifies both complete
and budget outcomes using the existing read-only Wasm build. No VU runtime
behavior or comparison expectation changed. The initial failed cycle remains
documented as history; PR #10 remains a draft.

## Initial observations (preserved history)

`scripts/repro_vu_browser.py` builds the real runtime privately, reuses the original
two-kick program generator and real GIF queue driver, and verifies native source
and fixture identities before reuse. `scripts/repro_vu_browser.cjs` serves only
the local fixture with cross-origin isolation and launches a fresh headless Chrome
profile. The fixture main executes via `PROXY_TO_PTHREAD`; explicit assertions
confirm it is neither the browser main thread nor the main runtime thread.
JIT is requested off; JIT behavior is outside this test's intended scope.

Final browser: **Chrome 155.0.8059.86**. All four requested modes (plain short,
plain long, complete and budget) exit **0**, with no reported page/abort errors,
confirmed cross-origin isolation, worker assertions and literal final Q/counter/
end/real-queue packet assertions. All 20 output comparisons against the prior
native fixture match exactly: registers, memory, captured packets, semantic pipe
and queue bytes for each mode. Read-only verification is recorded in
`local/vu-browser/output-verification.json`.

However, the successful page reports contain only the two fixture stdout messages;
they lack both `[vu-chain-result]` and `[vu-chain-outcomes]` evidence. The Python
driver fails on the complete mode's absent summary. This does **not** establish
that the requested `PS2_VU_CHECK` setting reached worker execution. Environment
propagation, stderr capture and exit/log ordering remain unresolved. The browser
collector records page console separately while running, but its successful
report currently retains only the fixture callback messages. No missing counters
are replaced with zeros, and no expected outcome is relaxed.

## Preserved attempts and commands

All four serial attempts are new ignored output directories under
`local/vu-browser/`; their supervisor records and logs remain in `jobs/`:

1. `validation`: failed shader generation because this repository's CMake commands
   assume top-level source paths. Private source links address that fixture layout.
2. `validation-fixed`: failed fixture compilation because its top-level CMake
   target had not selected C++20. The fixture now requires C++20 explicitly.
3. `validation-cxx20`: compiled, but Chrome rejected mixed legacy/new Wasm
   exception instructions. The fixture compile flags now match the runtime's
   existing `WASM_LEGACY_EXCEPTIONS=0` setting.
4. `validation-exceptions`: all four worker processes run and outputs match;
   strict summary validation fails. Execution attempts stopped at this boundary.

Final command, from `/Users/dallascarraher/Developer/Eco-vu-coverage`:

```sh
python3 scripts/repro_vu_browser.py --output local/vu-browser/validation-exceptions \
  --empp /Users/dallascarraher/Developer/Eco/tools/emsdk/upstream/emscripten/em++ \
  --playwright /Users/dallascarraher/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright \
  --native-reference local/vu-gif-queue/validation
```

Exit code **1**, due to the required summary assertion. Exact compilation,
configuration and browser argv are in each output's `commands.json`; source and
native-reference identities are in `inputs.json` and `native-inputs.json`.
Final browser evidence: `validation-exceptions/browser.json`. Native reference:
the [real queue fixture](ISSUE4-VU-GIF-QUEUE.md), with unchanged source hashes and
byte-identical regenerated original program/code.

## Initial limits and selected next experiment (history)

The user requested frequent weekly-usage checks and stopping at **85% remaining**.
The account tool reported **92% remaining** at admission and **91% remaining** at
each later check before stopping experiments. Percentages are account-wide and
coarse; they are not an exact token debit for this task. No subagents were used.

The released shared allocation is
`Eco-artifact-audit/local/artifact-audit-20261021/coverage-browser-allocation.json`.
It carries **7,414.859 seconds** forward and adds **58.979 seconds**, including all
failed builds and checks: **7,473.838 / 14,400 seconds** cumulative active debit.
The reservation was 900 seconds active, 256 MiB retained / 512 MiB peak, within
the existing shared 8 GiB cap. Longest supervised command: **23.473 seconds**.
New private retained bytes at release were approximately **268,398,498**, just
under 256 MiB; previous attempts were preserved. Shared retained bytes:
**3,766,500,741**; sampled aggregate peak: **3,773,284,751**; private temporary
peak: **6,805,962**. Between-poll peaks remain unmeasured. Free disk:
**24,868,061,184 bytes**, above 10 GiB. Emscripten also generated its small cached
`crt1_proxy_main.o` toolchain asset; the shared artifact scan covers checkout
local/build/generated trees, while the free-space gate covers the filesystem.

The smallest next experiment is **one complete-mode page**, retaining both page
console and fixture callbacks, plus explicit worker-side effective environment
and outcome-state evidence if logs remain absent. First inspect/reuse the existing
Wasm build read-only where possible; do not rebuild the runtime or repeat four
cases merely to diagnose the collector. Renew shared admission first: retained
space in this cycle's reservation is nearly full. Verify positive comparison
evidence before attempting the budget mode. This follow-up is not scheduled.

No game inputs, game boot, rendering validation, overnight matrix, concurrent
consumer/backpressure test, JIT validation or independent PS2 correctness result
was produced. Neither path is an oracle. Native queue success and worker guest
execution do not close the browser comparison/outcome coverage gap.

## Follow-up: environment timing fixed, both checked cases verified

The raw-console-only complete-mode probe reproduced missing outcome evidence.
Source inspection of the generated Emscripten loader showed cached environment
strings. The fixture had set `Module.ENV` in `onRuntimeInitialized`, after libc
initialization. Moving the diagnostic settings into **`preRun`** makes worker-side
`getenv` observe them. The same unchanged Wasm then emits both result and summary
markers. This is a fixture configuration fix, not a VU execution change.

The collector now retains raw page console alongside callback messages and can
select one mode against an existing build. A separate complete-mode probe and
budget-mode probe both pass in **Chrome 155.0.8059.86**, each in a fresh isolated
context and a confirmed Wasm pthread. Captured result lines report all five exact
comparison dimensions equal. Summary evidence:

| Mode | Attempted | Complete | Budget | Checkpoints | Compared continuations | Unchecked dispatches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Complete | 1 | 1 | 0 | 1 | 2 | 0 |
| Budget | 1 | 0 | 1 | 32 | 8,192 | 1,808 |

Both summaries have zero mismatches and unsupported outcomes. Every final output
(raw registers, 16 KiB memory, captured packets, semantic flag/Q pipe, and queued
payloads) matches both the corresponding checked native case and its plain native
control exactly. The fixture's literal counter/Q/end and two ordered, owned GIF
packet assertions also pass. The budget result remains incomplete comparison
coverage even though the guest finishes normally. JIT fallback is not exercised.

Commands, from the investigation checkout (create each output directory first):

```sh
node scripts/repro_vu_browser.cjs local/vu-browser-logs/complete-env \
  /Users/dallascarraher/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright \
  local/vu-browser/validation-exceptions/build complete
node scripts/repro_vu_browser.cjs local/vu-browser-logs/budget-env \
  /Users/dallascarraher/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright \
  local/vu-browser/validation-exceptions/build budget
python3 local/vu-browser-logs/verify.py
```

The final command asserts worker/isolation/exit evidence, exact full summary
counts, positive exact-result markers and all output equalities. All three exit
0. Evidence is in each probe's `browser.json`, the per-case output files,
`local/vu-browser-logs/verification.json`, and `jobs/`. Build hashes were sealed
before reuse in `build-hashes.json` and verified unchanged afterward. No rebuild
or archived-output overwrite occurred. The initial raw-console probe is retained
separately in `local/vu-browser-logs/complete/`. A console-only 404 for the missing
favicon is retained; neither checked page reports an abort or page exception.

The released allocation is
`Eco-artifact-audit/local/artifact-audit-20261021/coverage-browser-logs-allocation.json`.
It reserves 60 seconds active, 16 MiB retained / 128 MiB peak, carries
**7,473.838 seconds** forward and adds **3.480 seconds**:
**7,477.318 / 14,400 seconds** cumulative active debit. Shared retained bytes:
**3,766,574,950**; sampled aggregate peak: **3,773,338,410**; private temporary
peak: **6,805,690 bytes**. Between-poll peaks remain unmeasured. Free disk:
**24,741,810,176 bytes**, above 10 GiB. Weekly usage was checked at admission and
between stages and stayed above the user's stop threshold. No subagents were used.

The selected focused native/browser fixture cycle is complete. The earlier
missing-summary blocker is resolved; another repeat of this fixture is not the
next useful investigation. PR review can now assess the bounded mechanism with
native and browser worker evidence. Concurrent consumer/backpressure, JIT fallback,
full game execution, rendering and independent PS2 correctness remain separate,
unmeasured scopes rather than implied passes from this test.
