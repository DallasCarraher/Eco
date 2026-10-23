# Working in Eco

This file contains repository-wide guidance for coding agents. Follow the user's
current task and explicit preferences; use this guidance to fill in routine
implementation decisions. More specific instructions may exist in subdirectories.

## GitHub Copilot reviews: owner-controlled

**Never automatically request a GitHub Copilot review. Copilot reviews cost
money, and the repository owner decides when to request them.**

- Creating, updating, reopening, marking a PR ready, or pushing commits does
  not authorize a Copilot review.
- Do not add Copilot as a reviewer, trigger it through comments or CLI/API calls,
  or request another Copilot review unless the user explicitly asks for that
  review on that PR. A generic request to review code is not that authorization.
- Do not enable automatic Copilot reviews through repository settings, rulesets,
  workflows, or other automation. Do not add review-triggering automation to PRs.
- Complete ordinary local review and relevant checks without prompting the user
  to purchase a review. If existing auto-review configuration is encountered,
  report it; this instruction file does not itself change GitHub settings.

## Goal and direction

The eventual goal is every Jak and Daxter game running locally in a browser.
The first playable milestone is Jak 1: start a game, reach Sandover Village,
use movement and camera controls, hear sound, save, and reload after restarting
the browser.

Eco currently translates PS2 machine code to C++ and WebAssembly, with a PS2
runtime and WebGPU graphics. The alternative under consideration is generated
C++ from OpenGOAL's recovered GOAL source, plus a browser-adapted runtime.
The project has not committed to a full OpenGOAL port.

When selecting the next work, follow this order:

1. Compare one matching startup scene in Eco and an independent reference.
2. Test a bounded OpenGOAL prototype covering real function calls, data loading,
   pause/resume behavior, and representative rendering.
3. Choose one main trilogy implementation from the evidence.
4. Deliver the playable Jak 1 milestone, then expand compatibility and games.

Keep GOAL as the authoritative source in an OpenGOAL experiment; generate C++
mechanically rather than maintaining a handwritten translation of the game.
A shared browser interface may use different execution engines for other games.
Avoid developing two complete trilogy ports at once.

## Start with current evidence

- Read [README.md](README.md), [the roadmap](docs/ROADMAP.md), and
  [the issue audit/work queue](docs/work-items/README.md). Read only the detailed
  issue contract and reports relevant to the assigned task.
- Inspect the working tree, branch, and related worktrees before editing.
  Check current issue comments and PR state when they affect the task. Distinguish
  merged work, draft work, historical results, and proposed experiments.
- The October 22, 2026 audit found that the native experiment runner and VU
  fixes/checking work were already merged through PRs #9/#10. Older checkouts
  still describe them as unimplemented. Verify revisions before repeating work.
- The revised roadmap was prepared in the `codex/roadmap-audit` worktree. If it
  has not reached the current branch, locate it with `git worktree list` and
  read it there. Do not overwrite or merge another task's changes automatically.
- Historical prompts and earlier report sections are context, not a fresh task
  assignment or budget. Follow later evidence and the user's current scope.

## Repository map

- `recomp/`: PS2 CPU/vector-unit analysis and code generation.
- `runtime/`: dispatch, memory, console services, vector units, graphics, audio.
- `host/`, `web/`: native/browser entry points and browser shell.
- `scripts/`: extraction, builds, probes, comparisons, and regression checks.
- `experiments/`, `docs/`: experiment inputs, plans, contracts, and reports.
- `games/`, `generated/`, `build/`, `local/`: ignored local inputs and outputs;
  they may contain valuable evidence and are not disposable by default.

Use C++20 and existing local style. Prefer focused fixes to unrelated refactors.
Preserve upstream attribution, licenses, and notices.

## Development and validation

- Work autonomously on authorized, reversible steps. Ask only for genuinely
  missing information, exhausted explicit limits, or actions outside scope.
  Explain the specific blocker rather than requesting routine reconfirmation.
- Reuse a suitable task checkout or isolate work when needed. Do not reset,
  clean, rebase, delete, or overwrite another task's work or captured evidence.
  Give each writer its own build/generated/output directories; serialize shared
  builds and GPU measurements.
- Use the existing harness and focused replayers. Add tooling only when a named
  test requires it. Keep expensive replay/comparison loops in ordinary programs,
  without model calls or unbounded logging.
- Consult [EXPERIMENTS.md](docs/EXPERIMENTS.md) and
  [OVERNIGHT.md](docs/OVERNIGHT.md) before game runs. Respect the latest applicable
  cumulative time/storage allocation; a new issue, session, or worktree does not
  reset it. Prefer one bounded comparison over an unnecessary full matrix.
- Run checks appropriate to the change. For execution changes, reduce the fault
  to original synthetic inputs where possible, then validate the relevant
  native/WASM paths. Documentation-only changes need link/diff checks, not game
  builds. Do not repeatedly rerun passing suites without new evidence.
- Never disable instruction validation, suppress mismatches, or loosen expected
  results simply to make a run pass. Keep `PS2_WINDOW_FULL=1` for heap snapshots.
  Prefer general object-loading/relocation fixes over accumulating fixed snapshots.

## Evidence and completion claims

A successful build, zero exit code, later halt address, or increased frame count
does not establish gameplay. Agreement between Eco's compiled and interpreted
paths does not establish independent PS2 correctness.

Record the tested revision/build, disc identity, scenario, actual backend,
outcome, and remaining gaps. Align reference scenes by visible events, not equal
frame counters. Keep raw captures separate from labeled/cropped presentation
images. Distinguish synthetic browser fixtures from actual browser game runs.

Never commit or publish ISO/BIOS files, extracted game assets, game-derived
translations/WASM, memory dumps, captures, or saves. Keep those files ignored and
local. Use original synthetic fixtures for committed regressions.

Keep progress updates brief and understandable. End with what changed, what was
verified, the practical limitations, and one next step. Update relevant current
status summaries when completing work so later agents do not restart it.
PR descriptions should state the problem, resulting behavior, validation, and
remaining limits. Never describe a self-review as independent approval.
