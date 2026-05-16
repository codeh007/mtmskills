## Refactor Loop

Each `gomtm-refactor` run should complete a full five-phase convergence loop. Do not skip directly from discovery to edits.

### Phase 1: Context Scan

- Read the current task, relevant docs, touched code paths, and recent implementation context.
- Use GitNexus, graphify, LSP, static analysis, `grep`, or `glob` to narrow hotspots.
- Decide whether this round is repo-wide inventory or a themed cleanup pass.
- Stop here if you still do not understand the real consumers or current ownership boundary.

Output:

- a short hotspot inventory
- the stack areas in scope
- any context gaps or risk warnings

### Phase 2: Problem Identification

- Turn hotspots into concrete smells or structure problems.
- Merge duplicates so the same smell is not tracked as many tiny tasks.
- Separate low-risk convergence candidates from items that need their own plan.

Output:

- a candidate problem list grouped by smell language
- a risk split: safe this round vs defer

### Phase 3: Batch Plan

- Group the current round into one or more themed batches.
- Every batch needs a goal, boundary, verification path, and stop condition.
- If you cannot describe the batch in one sentence, the scope is still too fuzzy.

Output:

- themed batches such as thin-wrapper removal, duplicate glue cleanup, or compatibility branch deletion
- explicit out-of-scope items for this round

### Phase 4: Execute

- Work batch by batch.
- Prefer delete, inline, merge, or de-duplicate before inventing new helpers, wrappers, hooks, services, or adapters.
- Keep product behavior stable unless the task explicitly authorizes behavior change.
- Remove companion clutter together: alias files, wrapper-only tests, empty directories, obsolete exports.

Output:

- the converged code changes for the chosen batch
- no leftover fake boundary around the removed structure

### Phase 5: Verify And Record

- Run the smallest trustworthy verification for the touched stack.
- Confirm the batch still preserves the intended behavior.
- Record what changed, what was intentionally not changed, and why.
- If the task came from a plan or todo chain, prepare the evidence needed for result backfill.

Output:

- verification evidence
- a short convergence summary
- a deferred-items list with reasons

## Stop Conditions

- Stop when the batch goal is complete and only real boundaries remain.
- Stop and re-plan when the work expands beyond the declared theme.
- Stop and ask for direction when a suspected smell turns out to carry real runtime behavior or external consumers.
