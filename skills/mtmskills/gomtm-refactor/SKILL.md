---
name: gomtm-refactor
description: Use when a gomtm feature or implementation batch is already functionally correct and now needs structural convergence, or when thin wrappers, duplicate implementations, fragmented structure, or other refactor smells appear, or when running a periodic cleanup pass to normalize and harden already-working code without changing product behavior.
---

# gomtm-refactor

## Overview

`gomtm-refactor` is the single control skill for periodic gomtm convergence work.

Use it after behavior is already correct and the next job is to make the codebase healthier: inventory hotspots, choose a themed cleanup batch, execute the convergence work, verify behavior still holds, and leave a clear record of what was intentionally not changed.

This skill controls the round. Detailed smell rules and stack-specific guidance belong in the reference files, not inline in this main skill.

## When to Use

- after a large feature, migration, or implementation batch is already working and needs structural cleanup
- when thin wrappers, single-consumer abstractions, duplicate implementations, semantic duplicate functions, compatibility leftovers, or local fragmentation start accumulating
- when a periodic refactor pass should normalize already-correct code without changing product behavior

Do not use this skill as the starting point for net-new feature design or opportunistic product changes.

## Required Workflow

1. Inventory the current context before editing. Review the relevant code paths, real consumers, touched docs, tests, and recent hotspots first.
2. Turn discoveries into candidate convergence targets. Group them by theme, estimate risk, and prefer batches that remove valueless structure instead of adding new abstraction.
3. Define the current round explicitly. Choose at least one meaningful themed batch and state which nearby issues are intentionally out of scope for this round.
4. Execute the batch end to end. Inline or delete thin boundaries, collapse fake indirection, remove obsolete compatibility structure, and keep behavior unchanged.
5. Verify the touched surface with the smallest trustworthy checks for the affected stack. The round is not complete until the relevant behavior is re-confirmed.
6. Close the loop. Summarize what converged, what remains, and which reference guidance drove the decisions so the next refactor round starts from a better baseline.

## Reference Routing

Load `references/workflow.md` first when you need the detailed round structure for hotspot inventory, batch planning, stop conditions, and intentional non-changes.

Load the matching topic references for the current batch:

- `references/smell-catalog.md`: cross-stack smells such as thin wrappers, duplicate implementations, single-consumer abstractions, obsolete compatibility branches, and structure-self-proof tests
- `references/behavior-equivalence.md`: guardrails for behavior-preserving cleanup, GitNexus impact checks, high-risk runtime/installer boundaries, and verification choices
- `references/semantic-duplicate-functions.md`: workflow for finding same-purpose functions with different names or implementations; uses prompts and scripts under this skill
- `references/frontend-structure.md`: frontend route boundaries, provider/header/module-shell facades, export-only files, wrapper-only tests, and other UI structure cleanup
- `references/go-backend.md`: Go and backend convergence topics such as package boundaries, interface misuse, context misuse, glue-code drift, and shell-command overreach
- `references/testing.md`: regression-focused test cleanup, anti-patterns, and choosing the right verification layer
- `references/database-sql.md`: database and SQL refactor boundaries, smell decisions, and database-specific verification constraints

## Tooling Guidance

- Use GitNexus, graphify, LSP or IDE navigation, static analysis, and `grep` or `glob` as candidate hotspot finders.
- For semantic duplicate functions in TypeScript/JavaScript, use `scripts/duplicate-functions/` and the `semantic-duplicate-functions` references as candidate finders.
- Treat tool output as discovery input only. Tools can suggest where to look; they do not decide what is safe to delete or inline.
- Before changing structure, confirm the real consumers, current ownership boundary, and available verification path in the source itself.
- Do not batch-delete wrappers, files, tests, or compatibility branches only because a tool report makes them look redundant.

## Scope Boundary

- This skill is for convergence of already-correct behavior, not speculative redesign.
- Prefer deleting valueless structure over inventing new helpers, providers, hooks, services, adapters, or wrappers.
- Do not mix unrelated feature work into the same convergence round.
- Do not preserve alias files, thin facades, or structure-self-proof tests unless they still protect a real boundary or regression risk.
