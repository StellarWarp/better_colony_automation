# Native Parallel Construction Automation

This document records the investigation and native patch implementation for
making Stellaris colony automation use more than one planet construction slot.

An initial persistent test exposed an ASLR bug in the first helper and was
immediately rolled back. The corrected RIP-relative helper has now been
applied and independently byte-verified. Runtime behavior at the monthly
automation boundary remains to be tested.

## Scope And Version

The concrete addresses and binary hashes in this document are the regression
baseline captured from:

| Property | Value |
| --- | --- |
| Product | Stellaris |
| Version | 4.4.6 |
| PE image base | `0x140000000` |
| Executable MD5 | `8B1BCA722491CF6DDEB66C5CD1CA0ADE` |
| Executable SHA-256 | `BC451C72D9654C8901F1BB0BEE1DD78D76F415465C2FBF746E9F98ADE333173A` |

Static addresses in this document use the preferred PE image base. For a
running process:

```text
runtime_address = runtime_module_base + (static_address - 0x140000000)
```

They are not the primary compatibility check. The patch locator must recover
addresses and field offsets from native code features on every scan. Never
reuse runtime object addresses or a previous process ID after restarting the
game.

## Problem

Stellaris 4.4 introduced parallel planet construction capacity through the
modifier:

```text
planet_building_capacity_add
```

Native construction progression and the planet UI recognize the additional
capacity. Colony automation does not. Automation stops as soon as a queued
building or district exists, even when another native construction slot is
free.

This is an upstream scheduling problem:

- candidate generation is not reached while the guard is true;
- changing queue insertion cannot make automation fill another slot;
- adding script-side candidate logic cannot bypass the native scheduler guard;
- the patch must change whether the scheduler is allowed to run.

## Script API Investigation

The official trigger documentation and game script definitions were searched
for a trigger corresponding to construction capacity or a free construction
slot. Following the modifier name `planet_building_capacity_add` did not reveal
a script trigger that exposes:

- effective planet construction capacity;
- active construction slot count;
- free construction slot state; or
- a colony-automation-specific multi-queue condition.

The modifier registration was identified in the executable:

| Property | Value |
| --- | --- |
| Modifier string | `0x1424A7780` |
| Registration object | `0x14342A670` |
| Script ID | `0x2A93` |
| Runtime modifier slot | `0xA2` |

Directly reading modifier slot `0xA2` was rejected. It is an implementation
detail of the modifier container and would require duplicating base values,
clamping, and future modifier rules. The native queue already stores the
computed effective capacity and is the correct source.

## Investigation Method

The analysis used:

- Ghidra static disassembly, decompilation, references, and RTTI inspection;
- targeted searches around `common/colony_automation`;
- DbgEng hardware breakpoints and stack captures;
- runtime queue-object inspection;
- read-only `ReadProcessMemory` and `VirtualQueryEx` checks; and
- official game localisation and script files for semantic string searches.

The existing Ghidra project is external to the repository. Reproducible scripts
and generated reports are retained under:

- [`../../tools/ghidra_scripts/`](../../tools/ghidra_scripts/)
- [`../../tools/ghidra_reports/`](../../tools/ghidra_reports/)

Key evidence:

| Subject | Report |
| --- | --- |
| Automation guard and scheduler leaves | [`automation_scheduler_leaves.txt`](../../tools/ghidra_reports/automation_scheduler_leaves.txt) |
| Current queue object and item state | [`automation_queue_object_capture_restart.txt`](../../tools/ghidra_reports/automation_queue_object_capture_restart.txt) |
| Capacity-two queue capture | [`automation_queue_two_slots_capture.txt`](../../tools/ghidra_reports/automation_queue_two_slots_capture.txt) |
| Active-slot progress write | [`construction_active_slot_write_capture.txt`](../../tools/ghidra_reports/construction_active_slot_write_capture.txt) |
| Native queue methods | [`construction_queue_methods.txt`](../../tools/ghidra_reports/construction_queue_methods.txt) |
| Runtime capacity readers | [`construction_capacity_reader_capture.txt`](../../tools/ghidra_reports/construction_capacity_reader_capture.txt) and [`construction_capacity_reader_2_capture.txt`](../../tools/ghidra_reports/construction_capacity_reader_2_capture.txt) |
| Exact count/capacity candidates | [`queue_capacity_candidates_with_d1c480.txt`](../../tools/ghidra_reports/queue_capacity_candidates_with_d1c480.txt) |
| Executable cave scan | [`automation_patch_code_caves.txt`](../../tools/ghidra_reports/automation_patch_code_caves.txt) |

## Confirmed Scheduler Call Graph

The relevant native path is:

```text
FUN_14073B350
  -> FUN_140EE6D80       colony automation scheduler
     -> 0x140EE7081      call FUN_140E29300
     -> 0x140EE7086      test AL, AL
     -> 0x140EE7088      jump to scheduler exit when nonzero
```

The instructions at the local guard are:

```asm
140EE707D  mov  rcx, qword ptr [r13 + 0x8]
140EE7081  call 0x140E29300
140EE7086  test al, al
140EE7088  jnz  0x140EE874C
```

When the guard allows processing, the downstream path reaches:

```text
FUN_140EE6D80
  -> FUN_140EEA070 / A300 / A580 / A810 / AA90 / AD20
  -> FUN_140EEAFB0       shared automation eligibility
  -> FUN_140803810       generic can-build logic
  -> FUN_140803A30       generic queue insertion
```

A dynamic breakpoint on `FUN_140EEAFB0` did not hit while a relevant
construction was queued. It hit immediately after the queue was cleared. This
confirmed that the failure occurs before candidate generation.

## Existing Queue Guard

`FUN_140E29300(colony)`:

1. Resolves the planet reference through `FUN_140D464B0`.
2. Resolves the construction queue handle through the queue registry.
3. Iterates every queue entry.
4. RTTI-checks entries for `CBuildingType`.
5. Repeats the iteration for `CDistrictType`.
6. Returns `1` if any building or district exists.

It does not read or compare construction capacity.

The function has five callers:

- `FUN_140EE6D80`
- `FUN_140BB2410`
- `FUN_140BB3B90`
- `FUN_140C372E0`
- `FUN_141ADF5A0`

Globally replacing `FUN_140E29300` would therefore change unrelated behavior.
The proposed patch changes only the call at `0x140EE7081`.

## Native Queue Layout

Two independent runtime captures produced the same layout:

| Offset | Meaning | Evidence |
| --- | --- | --- |
| `+0x08` | queue handle/generation identity | handle registry validation |
| `+0x20` | pointer to queued item handles | guard iteration and captures |
| `+0x2C` | total queue item count | guard and progression loop |
| `+0x48` | effective parallel construction capacity | progression and UI |

Example captures:

| Queue count | Capacity | Active progress |
| ---: | ---: | --- |
| 9 | 2 | only items 0 and 1 had nonzero progress |
| 7 | 2 | only items 0 and 1 had nonzero progress |

The queue object address changed across game sessions. The field layout and
static code paths did not.

## Native Parallel Progression

A cross-thread write breakpoint on the first active item's progress field
identified `FUN_1408032B0` as the native construction scheduler.

Its governing behavior is:

```cpp
active_count = min(queue->count, queue->effective_capacity);

for (int index = active_count - 1; index >= 0; --index) {
    item[index].progress += item[index].type->progress_increment(...);
    if (item[index].progress >= item[index].required_progress) {
        complete_and_remove(item[index]);
    }
}
```

This establishes that:

- `queue+0x48` is not a raw modifier value;
- it is the official computed capacity consumed by native progression;
- the first `min(count, capacity)` entries are active; and
- comparing total count with capacity answers whether a physical slot is free.

## Capacity Reader Search

Runtime read breakpoints on `queue+0x48` found:

| Static address | Role |
| --- | --- |
| `0x140167360B` | UI item state, comparing queue index with capacity |
| `0x14015C933B` | UI aggregate refresh, computing `min(count, capacity)` |
| `0x1408032EE` | native construction progression |

`FUN_140804BD0(item)` returns an item's queue index. It is useful to the UI but
does not answer whether a free slot exists.

An additional ten-minute reader trace ignored the updater and both UI paths
but found no standalone semantic getter. Static scanning then searched the
entire program for functions that access both `+0x2C` and `+0x48`.

The only exact same-object `capacity` versus `count` comparisons were:

- `FUN_14082FCD0`
- `FUN_140830010`

Both are starbase building-removal checks and produce
`STARBASE_BUILDING_BUSY`. Their comparison is inlined:

```cpp
if (queue->effective_capacity <= queue->count) {
    // STARBASE_BUILDING_BUSY
}
```

Other candidates were eliminated:

- `FUN_14095A700` and nearby functions copy object fields into parallel UI or
  snapshot buffers.
- `FUN_140D1C480` formats a starbase name and accesses a different container
  with coincidental offsets.
- the queue object's first module pointer was initially suspected to be a
  standard MSVC vtable, but inspection showed a serialization/container
  operation table rather than usable class RTTI.

Current conclusion: the release binary does not preserve a reusable
`HasFreeConstructionSlot` function. The official code inlines field access.
Using `queue+0x48` remains preferable to reading modifier slot `0xA2` because
it consumes the engine's computed result rather than reconstructing it.

## Rejected Patch Locations

### Global Guard Replacement

Replacing `FUN_140E29300` globally affects five callers with different
semantics. This has an unnecessarily large behavioral surface.

### Queue Insertion

Changing `FUN_140803A30` is too late. The colony automation scheduler never
reaches candidate selection or insertion while the existing guard is true.

### Shared Eligibility

Changing `FUN_140EEAFB0` is also too late and would mix construction-capacity
policy into candidate-level eligibility.

### Raw Modifier Storage

Reading runtime modifier slot `0xA2` is version-fragile and bypasses official
base, modifier, and clamping logic.

### Existing Semantic Helper

No standalone planet free-slot helper survived compiler optimization. Starbase
checks demonstrate the intended comparison but operate on different owners and
cannot be called for a colony queue.

## Proposed Local Patch

Replace only the `CALL` at `0x140EE7081` with a call to a small helper:

```cpp
bool block_colony_automation(Colony* colony) {
    Queue* queue = resolve_planet_construction_queue(colony);
    if (!queue) {
        return false;
    }
    return queue->count >= queue->effective_capacity;
}
```

The result retains the call site's existing meaning:

- `AL = 1`: all native slots are occupied, exit automation;
- `AL = 0`: at least one native slot is free, continue automation.

Expected behavior:

| Capacity | Count | Result | Scheduler behavior |
| ---: | ---: | ---: | --- |
| 1 | 0 | 0 | automation may enqueue |
| 1 | 1 | 1 | preserves current single-slot behavior |
| 2 | 0 | 0 | automation may enqueue |
| 2 | 1 | 0 | automation may fill the second slot |
| 2 | 2 | 1 | prevents a waiting backlog |
| 2 | 3+ | 1 | prevents additional backlog |

The helper validates the queue handle in the same registry and generation
format as the original guard. Invalid or missing queues return `0`, matching
the old guard's practical empty-result behavior.

## Feature-Based Patcher

The feature scanner and explicitly gated disk patcher is:

- [`../../submods/colony_automation_parallelize_patch/src/automation_queue_capacity_patcher.py`](../../submods/colony_automation_parallelize_patch/src/automation_queue_capacity_patcher.py)

Without `--apply`, it only reads an unmodified PE32+ executable and emits a
JSON patch plan:

```powershell
python submods/colony_automation_parallelize_patch/src/automation_queue_capacity_patcher.py `
  "D:\SteamLibrary\steamapps\common\Stellaris\stellaris.exe" `
  --output automation_queue_capacity_plan.json
```

`--apply` reruns the same scan, creates and verifies a hash-suffixed sibling
backup, writes and verifies a same-directory temporary file, and only then
atomically replaces the executable. It has no running-process write mode:

```powershell
python submods/colony_automation_parallelize_patch/src/automation_queue_capacity_patcher.py `
  "D:\SteamLibrary\steamapps\common\Stellaris\stellaris.exe" `
  --apply --output automation_queue_capacity_apply_receipt.json
```

Rollback is also fail-closed. `--restore-backup` scans the original backup,
reconstructs the expected patched image, and restores only when the current
executable matches that image exactly. It retains a hash-named copy of the
patched executable:

```powershell
python submods/colony_automation_parallelize_patch/src/automation_queue_capacity_patcher.py `
  "D:\SteamLibrary\steamapps\common\Stellaris\stellaris.exe" `
  --restore-backup `
  "D:\SteamLibrary\steamapps\common\Stellaris\stellaris.exe.bca-backup-BC451C72D9654C89"
```

The scan resolves the patch from native features:

1. Find one scheduler-local instruction sequence around the guard call.
2. Resolve the existing `CALL rel32` target.
3. Validate that target as the two-loop building/district queue guard.
4. Derive the resolver, queue registry, colony reference offset, queue handle
   offset, and queue count offset from decoded operands.
5. Find and validate native `min(count, effective_capacity)` progression.
6. Derive the effective-capacity offset from that progression.
7. Find one sufficiently large zero-filled executable PE-section raw tail.
8. Generate helper and replacement-call bytes from the recovered values.

The helper's handle-registry assumptions are also checked: the `0xFFFFFF`
index mask, registry bounds and entries fields, 16-byte slot layout, and queue
generation identity. A changed private layout fails closed.

The signatures wildcard relative targets, stack temporaries, and queue
count/capacity offsets while retaining the surrounding opcode and register
relationships. This supports compatible code movement and field relocation.
It does not treat arbitrary future binaries as compatible.

Known executable hashes are regression labels only. They do not select
addresses, and an unknown hash is not rejected merely for being unknown. A
known hash cannot bypass a failed structural check.

## ABI And Machine-Code Design

The helper:

- accepts the colony in `RCX`;
- returns the guard result in `AL`;
- uses only volatile registers `RAX`, `RCX`, `RDX`, and `R8-R10`;
- allocates `0x20` bytes of Windows x64 shadow space;
- maintains 16-byte stack alignment for the nested
  `FUN_140D464B0` call; and
- uses ordinary direct `CALL`/`RET`, preserving CET shadow-stack behavior.

The corrected assembled helper is 97 bytes. Its source and payload are:

- [`../../submods/colony_automation_parallelize_patch/src/automation_queue_capacity_guard.asm`](../../submods/colony_automation_parallelize_patch/src/automation_queue_capacity_guard.asm)
- `submods/colony_automation_parallelize_patch/src/automation_queue_capacity_guard.bin`

Payload SHA-256:

```text
36E3B9CCC8ECB275E966CC12272F31ADEBAF89F154AE75228B2383283066CC85
```

Every injected reference to the Stellaris image is position-independent:

- the planet resolver uses `CALL rel32`;
- the queue registry uses a RIP-relative memory operand; and
- the scheduler call to the helper uses `CALL rel32`.

This is required because raw code-cave bytes do not receive entries in the
PE base-relocation table.

## Code Cave

The only unreferenced executable padding range of at least `0x80` bytes is:

| Property | Value |
| --- | --- |
| Static virtual address | `0x1423B4700` |
| RVA | `0x23B4700` |
| File offset | `0x23B3B00` |
| Available length | `0x100` |
| Initial fill | `0x00` |
| PE section | `.text` |
| `.text` memory range | `0x140001000–0x1423B47FF` |

The cave begins at the `.text` `VirtualSize` boundary but remains inside
`.text` `SizeOfRawData`. This was not accepted on file structure alone.
`VirtualQueryEx` and `ReadProcessMemory` confirmed in a running 4.4.6 process:

- state `MEM_COMMIT`;
- type `MEM_IMAGE`;
- protection `PAGE_EXECUTE_READ`;
- 256 readable bytes; and
- all 256 bytes equal to zero.

## Call-Site Patch

| Property | Original | Proposed |
| --- | --- | --- |
| Static address | `0x140EE7081` | `0x140EE7081` |
| File offset | `0x0EE6481` | `0x0EE6481` |
| Bytes | `E8 7A 22 F4 FF` | `E8 7A D6 4C 01` |
| Target | `0x140E29300` | `0x1423B4700` |

The replacement is another five-byte `CALL rel32`, so no surrounding
instructions are overwritten.

The fixed-address machine-readable regression record is:

- [`../../submods/colony_automation_parallelize_patch/src/automation_queue_capacity_guard.yaml`](../../submods/colony_automation_parallelize_patch/src/automation_queue_capacity_guard.yaml)

It records target hashes, expected original bytes, payload hash, offsets, and
rollback data. The feature scan reproduces this record for 4.4.6 without using
its addresses as locator inputs.

## Dynamic Debugging Safety

Two game processes were unintentionally terminated during early DbgEng
automation. These were debugger lifecycle failures, not Stellaris crashes:

1. A waiting Python debugger process was forcibly terminated while attached.
   Windows then terminated the debuggee.
2. `pybag.go(timeout)` returned immediately after requesting an interrupt,
   before its background `WaitForEvent` completed. The script accessed an
   inaccessible target and released the session without a confirmed detach.

The corrected lifecycle is implemented in:

- [`../../tools/debug_stellaris_session.py`](../../tools/debug_stellaris_session.py)

Required timeout sequence:

1. `go(timeout)` returns false.
2. Wait for pybag's background event to acknowledge the active interrupt.
3. Call `EndSession(DEBUG_END_ACTIVE_DETACH)`.
4. Release pybag only after the detach succeeds.

This sequence was tested against a disposable native `ping.exe` process. The
test reached a real timeout, detached, and verified that the target remained
alive. The test harness is:

- [`../../tools/test_dbgeng_timeout_detach.py`](../../tools/test_dbgeng_timeout_detach.py)

Operational rules:

- never force-kill an attached debugger process;
- use short bounded captures;
- let the debugger complete its own timeout cleanup;
- confirm the game still responds after every capture; and
- prefer static analysis or read-only process memory inspection when a
  breakpoint is not essential.

## Risks And Open Questions

### Queue Entry Semantics

The proposal treats every queue entry as occupying a physical native slot.
This matches `FUN_1408032B0`, which advances the first
`min(count, capacity)` entries. A focused test should still include decisions,
repairs, upgrades, districts, and buildings to confirm no entry type is
intentionally excluded from automation gating.

### Version Fragility

Queue offsets, registries, call sites, and code caves are private engine
details. Feature scanning reduces address and layout coupling, but cannot make
a native patch universally update-proof. Every required feature must be
unique and every semantic invariant must pass. Ambiguous or structurally
changed versions require renewed analysis.

### Executable Modification

A persistent disk patch can be overwritten by Steam verification or updates
and may trigger security tooling. It also complicates support and
reproducibility. Runtime-only patching is the recommended first validation
step.

### Automation Re-entry

Allowing the scheduler to run when one slot remains does not prove that every
automation category will select a second candidate. Candidate eligibility,
resource budgets, and per-colony automation state still apply normally. The
test must distinguish "scheduler reached candidate generation" from "candidate
was valid and inserted."

### Capacity Changes

The queue capacity field appears to be cached and is not rewritten every tick.
Long-running write breakpoints did not observe ordinary writes. This does not
weaken it as a read source: native progression and UI consume the same cached
field. Tests should still cover modifier changes while the game is running.

## Validation Plan

The preferred validation sequence uses a runtime-only patch before a
persistent executable change. The current local 4.4.6 test proceeded directly
to a backed-up persistent patch after the user explicitly approved it.

1. Verify executable hashes and all expected bytes.
2. Verify the cave remains committed, executable, and zero-filled.
3. Write the helper to the cave and flush the instruction cache.
4. Replace the local call target and flush the instruction cache.
5. Keep rollback bytes in memory before testing.
6. Test a unique colony with effective capacity two.
7. With one active construction, confirm automation reaches
   `FUN_140EEAFB0` and can enqueue one second valid construction.
8. With two active constructions, confirm automation does not reach candidate
   insertion and creates no waiting backlog.
9. Confirm capacity one preserves current behavior.
10. Test building, district, upgrade, repair, and decision queue entries.
11. Change `planet_building_capacity_add` at runtime and repeat.
12. Remove the runtime patch or restart the game.

Any persistent patch operation must:

- create a backup rather than editing without recovery;
- rerun the complete feature and semantic scan;
- record the executable hash for audit and rollback;
- validate original call bytes and the entire cave fill;
- write through a temporary output file;
- verify the patched output before replacement; and
- provide an explicit rollback operation.

## Current Status

Completed:

- script API and modifier investigation;
- scheduler and guard call-graph reconstruction;
- dynamic proof of the upstream blocker;
- native progression and queue-layout reconstruction;
- capacity reader and semantic-helper search;
- local patch design;
- executable cave verification;
- helper assembly and disassembly verification; and
- version-locked manifest verification;
- read-only feature-based PE scanning;
- semantic guard and native progression validation;
- dynamic helper and call-byte generation; and
- a 4.4.6 regression scan reproducing the reviewed payload hash;
- verified automatic backup and atomic disk-apply support; and
- rollback support that requires an exact backup-derived patched image;
- diagnosis of the initial helper's ASLR failure; and
- a corrected RIP-relative helper with an explicit ASLR rebase test; and
- corrected 4.4.6 disk application with independent instruction, range, and
  hash verification.

Not performed:

- no running-process memory write;
- no runtime behavior test with the corrected helper.

### Corrected Trial

| Property | Value |
| --- | --- |
| Corrected patched SHA-256 | `D5CD8DFB5E1219E36A6FEBF741025F8F197FDDCD8B9E31EE77814848CA222E3C` |
| Corrected helper SHA-256 | `36E3B9CCC8ECB275E966CC12272F31ADEBAF89F154AE75228B2383283066CC85` |
| Helper size | 97 bytes |
| Registry instruction | `mov rdx, qword ptr [rip + 0xED2FBB]` |
| Changes outside declared regions | 0 bytes |

The corrected application receipt is
[`../../tools/patches/automation_queue_capacity_corrected_apply_receipt.json`](../../tools/patches/automation_queue_capacity_corrected_apply_receipt.json).

### Failed Initial Trial

The first persistent trial was applied and independently byte-verified, but it
crashed on the next monthly automation execution:

| Property | Value |
| --- | --- |
| Original SHA-256 | `BC451C72D9654C8901F1BB0BEE1DD78D76F415465C2FBF746E9F98ADE333173A` |
| Failed patched SHA-256 | `66FA3D1059EC0BC6ED4708B0F885730E366C75671A418A2E849A230E11FFFB34` |
| Automatic backup | `stellaris.exe.bca-backup-BC451C72D9654C89` |
| Replacement call | `E8 7A D6 4C 01` |
| Failed helper SHA-256 | `A07FA8EC91B84DBFB87EBE5754B6A354229B0C55E4D8F7AAB55AFEF902C39848` |
| Exception | `C0000005` at helper `+0x20` |

The failed helper loaded the queue registry through an absolute immediate:

```asm
mov r10, 0x1432876D8
mov rdx, [r10]             ; access violation after ASLR rebasing
```

Raw injected bytes have no relocation entry, so `r10` retained the preferred
image address while the executable was loaded elsewhere. The corrected helper
uses:

```asm
mov rdx, [rel queue_registry]
```

The crash dump is `stellaris_20260731_144459`. Its module list records
`stellaris.exe` at `0x7FF6C8650000`; subtracting this from the exception
address `0x7FF6CAA04720` gives RVA `0x23B4720`, exactly helper offset `+0x20`.
The patcher now disassembles every generated helper and refuses image-range
absolute immediates or absolute memory operands.

The original executable was restored and verified at SHA-256
`BC451C72D9654C8901F1BB0BEE1DD78D76F415465C2FBF746E9F98ADE333173A`.

The failed application and successful restore receipts are
[`../../tools/patches/automation_queue_capacity_apply_receipt.json`](../../tools/patches/automation_queue_capacity_apply_receipt.json)
and
[`../../tools/patches/automation_queue_capacity_restore_receipt.json`](../../tools/patches/automation_queue_capacity_restore_receipt.json).
