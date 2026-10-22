# Issue 4: resumable comparison design and admission blocker

**Follow-up:** the user subsequently allocated 8 GiB of shared experiment
storage. The [implementation and validation report](ISSUE4-VU-CHECKPOINT-VALIDATION.md)
supersedes the admission blocker and proposed-only status below. This original
read-only-cycle record is retained as history.

This bounded cycle performed source analysis and read-only identity validation.
It did **not** implement or execute resumable VU execution. Whole-invocation
coverage remains blocked. The design and original regression specification below
are proposals, not validated behavior. No runtime semantics, guards, expected
results or tolerances changed. Neither Eco path is a correctness oracle.

Branch: `codex/issue-4-vu-coverage`, dedicated checkout
`/Users/dallascarraher/Developer/Eco-vu-coverage`, starting at merged corrections
`adb3a2d9bd17d485a1f49d9d6e6e89ccf09244e3`. No applicable AGENTS.md was found
in this checkout, the two supplied checkouts or their ancestors. Read the complete
coverage prompt, roadmap, experiment contract, overnight runbook, work item 04,
flag and prefix reports, replay/wrapper and both dispatch regression scripts.
All preserved builds, generated sources and experiments remained read-only.

## Admission decision

The storage audit had already completed its approved duplicate-object cleanup.
Its authoritative ledger is
`/Users/dallascarraher/Developer/Eco-artifact-audit/local/artifact-audit-20261021/post-cleanup-allocation.json`.
Ledger SHA-256: `e673a547aaac48b1b79a6c70246b33af8d35741155bf9cd2cddbcbe06733d357`.
The audit's tracked explanation is `docs/ISSUE4-ARTIFACT-AUDIT.md` in that
checkout (audit branch `codex/issue-4-artifact-audit`).

Read-only remeasurement on 2026-10-21 found these unchanged logical totals:

| Scope (local + build + generated) | Bytes |
| --- | ---: |
| Primary Eco checkout | 1,263,308,478 |
| Preserved Eco-issue-4 | 1,818,887,986 |
| Audit checkout | 13,461,781 |
| New coverage checkout | 0 |
| Shared retained | 3,095,658,245 |
| Shared cap | 2,147,483,648 |
| Deficit | 948,174,597 |

Free disk at remeasurement: 30,074,527,744 bytes, above the 10 GiB floor.
Free volume space does not resolve the logical retention deficit. The ledger
explicitly allocates **zero new bytes and zero execution seconds** to coverage.
Its conditional 32 MiB retained / 48 MiB peak / 900-second coverage envelope
has not been released. Historical active-time debit stays 7,200 of 14,400 seconds;
the reserve for unledgered history is not reset. No game, build or synthetic
diagnostic subprocess ran here; new experiment retention and temporary artifact
peak were both zero. Source/Git storage is outside this experiment ledger.

The precise prerequisite is explicit cap-scope reconciliation, or a
capacity-verified independent archival destination and preservation plan that
actually fits the shared cap, followed by an admitted allocation. Do not delete
more evidence, reinterpret the investigation-only headroom as shared capacity,
or start builds in temporary directories to bypass this gate. The prompt requires
allocation before builds or replays, and the audit also withholds synthetic
executions that write products. Consequently the requested synthetic proof and
saved-input validation could not be performed in this cycle.

When admitted, hold the existing cross-checkout POSIX flock at
`Eco-artifact-audit/local/artifact-audit-20261021/serial.lock` throughout builds,
synthetics and replay. Recheck processes, free space and the central ledger;
reserve and record peak bytes and cumulative active time there before starting.
Every subprocess remains at most 900 seconds. Existing checkout-local harness
locks alone are insufficient. No lock ownership or execution slot was claimed
by this read-only cycle. A point-in-time process scan found no Eco diagnostic.

## Verified evidence

Read the sealed corrected-prefix report and private build record:

* `Eco-issue-4/local/experiments/issue4-prefix-q-fixed-8192/report.json`, SHA-256
  `db58d778f132f2bf5dde4202db2f0e079a75f9866287cf5ff6864baed7bc2912`.
* `Eco-issue-4/local/issue4-prefix/q-fixed/build.json`, SHA-256
  `1cbf20e17c344943ed6a7ceb96d4eecfe9fd44dab2b875fa2f6e9a32d2f90b06`.

Rehashed all five snapshot inputs against the report, its archived runner and
wrapper, all eight corrected generated files with sizes, and all three read-only
link archives against build.json: all match. Canonical generated-inventory digest
is `046609e735d1f044e5513c3cdebb77fa8555741525ad9a1446f3ce34b2c28d0a`.
Use the harness's compact sorted JSON encoding; an initial check here used
pretty JSON and therefore gave a different aggregate hash. Correct canonical
encoding matches; every individual file matched in both checks.

The snapshot remains frame 192, key `8A7C5336C2223702`, entry `0020`, root index
348 at the prompt's preserved `vu-limit` prefix. The archived endpoint files
still agree exactly for raw registers, 16 KiB memory, ordered length-prefixed
packets and semantic pipeline fields. The compiled status is incomplete at
8,192 continuations / 113,104 issued instructions. Both next PCs are `0x1280`
(4736 decimal); interpreter NPC is `0x1288`, pending end false. Compiled status
NPC=0 and ending=false are default report fields, **not captured compiled control
state**. They cannot establish equivalent branch/delay-slot state.

The replay tool, wrapper, interpreter, FlagPipe header and native generator in
the merged base are byte-identical to their preserved-checkout versions. This
does not establish exact historical build provenance beyond the recorded hashes.
The audit's four unrelated historical runner-path identity gaps remain open.
No saved input was executed. Endpoint equality is not intermediate equality or
a completed invocation, and it does not establish visual or PS2 correctness.

## State ownership findings

`runtime/src/vu_micro.cpp::run_fast` initializes PC from its address argument,
NPC to PC+8, `ending=false`, and an empty `BranchView` on every call.
`FastCheckpoint` exports these fields and branch history but has no restore
path. Its limit/steps are call-local. Repeating run_fast at checkpoint.pc would
discard a pending branch target, pending end and the previous VI values used
by conditional branches. The shared FlagPipe alone cannot restore these.

`FlagDispatch` seeds a fresh pipe at construction and restores the enclosing
pipe at destruction. A resumed chunk must install its saved pipe after entering
an active context; it must not seed it from raw flags again. Keep issue clock,
all MAC/status/clip ring slots/timestamps and ring heads, pending Q/value/ready
clock, and raw architectural Q independently. Pause must not flush Q or write
TPC. Only the existing real invocation-end path may do so.

The native generator keeps `pend`, `pendj`, `ending`, `jpc`, delayed VI
`bk/next_bk/bi`, localized VI values and normalized VF shadows inside generated
functions. A mid-function restart using an address and raw registers is not a
capture of those locals. Prefer existing function-return dispatch boundaries;
do not add arbitrary mid-fragment yields in the first implementation.
At a verified register-jump dispatch, the delay slot has run and the jump decision
has been consumed. Still prove with tests that no relevant local state is lost
before treating this as a resumable boundary. Unsupported-instruction escapes
and missing-function fallbacks are separate cases, not automatically safe jumps.

`replay_vu_snapshot.cpp` currently infers compiled completion solely from a
negative escape. A fallback run_fast that exhausts its instruction limit can
return without setting an escape and be misclassified as complete. This is a
source-level reporting risk, not a newly observed saved-input discrepancy. A
new driver needs an explicit fallback outcome. `run_vu_prefix.py` also cannot
infer interpreter instruction count from issue-clock delta without validating
that relation; future stalls or changed clock semantics must not silently alter
alignment. Track issued count separately and require both alignment measures.

XGKICK captures packet bytes at kick time. Saving only VU memory and regenerating
packets later loses ordering and can substitute later memory contents. Preserve
the exact length-prefixed stream and its cumulative byte/packet counts. Retain
the existing 1 MiB aggregate packet ceiling across chunks.

## Proposed first implementation

Keep this diagnostic-only and VU1-only initially. Keep production `run_fast`
behavior and the whole-chain guard unchanged until original tests validate a
shared stepping core. Use explicit owned state rather than serializing pointers
or C++ object padding:

| State | Required contents |
| --- | --- |
| Shared execution image | Exact register bytes, 16 KiB data, immutable code identity, TOP/ITOP, every semantic FlagPipe field |
| Interpreter cursor | Next PC, NPC, pending end, BranchView.live and all 16 prior VI values, cumulative issued count, complete/paused/error state |
| Compiled cursor | Root-issued bit, next dispatch PC, boundary kind, cumulative continuations and issued count, completion or fallback cursor |
| Invocation accounting | Immutable aggregate limits, used continuations/instructions/packets/bytes/time, chunk sequence, parent checkpoint identity |
| Provenance | Schema/ABI/endian identity, original snapshot hashes, source/tool/generated/build identities, checksums and lengths of every state payload |

Interpreter resume restores PC/NPC/end/BranchView before the next instruction,
without executing prologue initialization for a new invocation. UpperOut and
the temporary branch pointer need not persist at a fully committed instruction
boundary; reconstruct pointers to the owned registers/code/pipe. Rebuild decoded
and Q-analysis caches from unchanged code after code_changed; never serialize
cached function pointers. Assert code/TOP/ITOP identity on restore.

Maintain separate execution images for compiled and interpreted paths. Save the
compiled image before installing the interpreter image; restore all host capture,
dry-run and active-pipe context through RAII on every exit. Never replace either
path's state with the other to obtain alignment. Compiled chunks stop only after
a verified dispatch return or a real end. An interpreter chunk advances from its
own cursor to that chunk's cumulative issued count, preserving control state.
If it ends early, cannot reach that count, or disagrees in PC/clock/state/packets,
stop with explicit evidence. Compare each path's resumed control state with its
own uninterrupted control state; compiled locals and interpreter BranchView are
different representations, not bytewise comparable structs.

Completion requires both paths' explicit end outcomes at the same cumulative
issued count, exact registers/memory/packet order/pipeline and aligned end PC.
Report `matched_partial`, `complete_match`, `mismatch`, `aggregate_limit`,
`timeout`, `cancelled`, `invalid_checkpoint`, `unsupported_boundary`, and
`process_failed` distinctly. Missing/malformed output and abnormal exits cannot
be matches. Write checkpoints atomically to new ignored paths, verify complete
payloads before installation, reject stale/changed identities or limit increases,
and retain failed attempts. Preserve raw register bytes exactly while encoding
pipeline/control fields individually, excluding their C++ padding.

Chunk size is scheduling, not permission to reset budgets. Default aggregate
continuations stay 8,192; interpreter instructions stay at most 1,000,000;
packets stay at most 1 MiB; include every resumed process in the same immutable
active-time and output ledger. Reject a resume with depleted budget before
issuing anything. A compiled fragment itself may loop indefinitely: dispatch
checkpointing does not bound its issued count or provide an internal pause.
The subprocess wall timeout still bounds it and must report incomplete execution.
Do not claim an instruction-bounded compiled engine without generated polls and
full live-local capture, which would require a separate design and tests.

## Original regression specification (not executed)

Start with the existing original 10,000-iteration finite fixture in
`scripts/repro_vu_dispatch_flags.py`, which dispatches through JR and completes
in 60,002 interpreter instructions. Its 8,192-continuation endpoint is counter
1,808 at PC `0080`, issued count 49,154. Existing tests prove only that prefix
and independent uninterrupted interpreter completion, not resumed execution.

Add an original variant with these operations, using separate scratch VI/VF
registers and fixed initialized data so the counter loop remains finite:

1. In the root set VI10=10,000, VI9=`0080/8`, Q=1, VF1.x=1, VF2.x=2.
   Dispatch through JR VI9 with a SUB.x flag producer in its delay slot.
2. In the loop decrement VI10; put a conditional branch immediately after
   the decrement so it must read the prior VI value. Include a distinct taken
   path store and a terminal store to make lost branch history observable.
   Because this intentionally changes branch timing from the old fixture,
   derive its iteration count before encoding expected results; do not copy
   the old fixture's instruction-count assertion into this variant.
3. Before the next JR, issue DIV 1/2. At the consumer read MULq before Q is
   ready, then WAITQ and read MULq again. Require exact old/new Q results
   `(1, 1/2)` on the dispatch route under the existing latency policy. Include
   the alternate direct branch DIV 1/4 route from the original Q regression.
4. Add two distinguishable minimal EOP packets, kicked in order from fixed
   memory slots and subsequently overwrite one slot. Limit kicks to the first
   and final iteration so the existing cumulative packet ceiling is respected.
5. End through an E-bit instruction and its delay slot. Pause once between
   them and require exactly one remaining delay-slot issue on resume.

For the small Q/branch/end subcases, pause before and after each instruction.
For the long fixture use chunks of 1, 7 and 257 continuations, plus interpreter
splits immediately after VI writes, branches, DIV, flag writes and E. Compare
all resumed final images and each saved cursor with uninterrupted execution of
the **same path**. Require independent literal assertions for branch stores,
Q results, counter/end behavior and packet order in addition to path equality.
Exercise full compiled and compiled-to-interpreter fallback routes separately.
Destroy/recreate host contexts and round-trip checkpoint bytes between chunks;
otherwise accidental TLS retention could make a broken restore pass.

Negative cases: mutate NPC, end bit, prior VI, Q ready/pending/value, flag-ring
slot and packet order individually; none may pass as equality. Reject truncated
state, changed code/tool identity, repeated chunk sequence and increased limits.
With aggregate 8,192 the finite long fixture must remain incomplete even when
resumed repeatedly. With a clearly labeled **synthetic-only** finite allowance
of 10,001 continuations, prove resumed compiled execution equals uninterrupted
compiled execution and the uninterrupted interpreter. This synthetic allowance
must not be selectable for saved game replay. Also exercise timeout, fallback
instruction exhaustion, missing output and cancellation classifications.

## Validation commands and next experiment

Executed from the new checkout: read-only `git show`, `git status --short`,
`git worktree list`, `rg`, `sed`, `cat`, `find . -name AGENTS.md -print`,
`df -k .`, and `ps -axo pid,etime,command` inspections; Python standard-library
hashing, byte comparisons and os.walk/lstat measurements. Created the checkout
with this exact command from the primary checkout:

```sh
git worktree add -b codex/issue-4-vu-coverage /Users/dallascarraher/Developer/Eco-vu-coverage adb3a2d9bd17d485a1f49d9d6e6e89ccf09244e3
```

The identity check's core, run via `python3 - <<'PY'` with no file writes:

```python
import hashlib, json
from pathlib import Path
r = Path('/Users/dallascarraher/Developer/Eco-issue-4')
report = json.loads((r/'local/experiments/issue4-prefix-q-fixed-8192/report.json').read_text())
build = json.loads((r/'local/issue4-prefix/q-fixed/build.json').read_text())
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()
assert all(sha(Path(p)) == h for p, h in report['snapshot'].items())
assert sha(Path(report['cases'][0]['argv'][0])) == report['runner_sha256']
assert sha(r/'scripts/run_vu_prefix.py') == report['wrapper_sha256']
g = r/'local/issue4-prefix/q-fixed/generated'
inv = {str(p.relative_to(g)): {'sha256': sha(p), 'bytes': p.stat().st_size}
       for p in sorted(g.rglob('*')) if p.is_file()}
assert inv == report['generated_inventory']
assert hashlib.sha256(json.dumps(inv, sort_keys=True, separators=(',', ':'),
                                allow_nan=False).encode()).hexdigest() == report['generated_sha256']
assert all(sha(r/p) == h for p, h in build['read_only_archives'].items())
out = r/'local/experiments/issue4-prefix-q-fixed-8192'
for suffix in ('regs.bin', 'mem.bin', 'packets.bin', 'pipe.txt'):
    assert (out/('compiled-'+suffix)).read_bytes() == (out/('interpreted-'+suffix)).read_bytes()
```

No build/test/replay commands are reported as passing. No new ignored artifact
directory exists. Final source validation is `git diff --check`; preserved
checkout status checks must remain clean. No game boot, matrix or cross-session
message was started.

The smallest next experiment, **after storage admission**, is the small original
DIV/branch/E interpreter checkpoint round-trip, followed by the finite dispatch
fixture above in one private measured build. Estimate its build peak before
release; the existing regression scripts build a full private runtime and are
not known to fit 48 MiB. Only after these pass should a new saved-input pair
split the existing prefix into smaller chunks and reproduce exactly the same
8,192-continuation / 113,104-instruction endpoint. That validates preservation
without crossing the aggregate guard. Going beyond it needs a separately stated
finite aggregate policy decision before any game-derived execution; no such
decision or coverage extension was made here.
