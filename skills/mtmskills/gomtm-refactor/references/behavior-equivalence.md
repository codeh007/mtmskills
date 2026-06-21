## Behavior Equivalence Guardrails

Use these rules when a convergence round changes structure but must preserve existing product behavior.

## Required Checks Before Editing

- For repositories indexed by GitNexus, run impact analysis on the target function, method, route, or class before changing shared behavior.
- Confirm real consumers in current source. If an index was built before recent file moves, cross-check tool output against the live diff and source tree.
- Define the verification path before changing code. If the expected repo script does not exist, inspect the repo and choose the smallest available trustworthy command.

## Safe Convergence Examples

- delete repeated condition branches without changing branch outcomes
- narrow a private helper after confirming every call site fits the narrower meaning
- preallocate capacity, early-continue, or filter empty values without changing externally visible order or semantics
- merge duplicate map initialization or local string assembly when keys, values, paths, and command arguments remain identical
- move tiny helper types closer to their real owner when imports and exported contracts stay stable

## High-Risk Areas

- runtime assembly chains, proxy chains, `Start` flows, and runtime spec resolution
- installer and local tool installation helpers
- path construction, environment variable interpretation, download URLs, retry policy, command arguments, and startup parameters
- auth, billing, routing, provider selection, persistence, and migration boundaries

Treat LOW impact as only a signal about graph fan-out, not proof of no runtime risk.

## Rules During Editing

- Keep the round behavior-equivalent unless the task explicitly authorizes behavior change.
- Do not change route semantics, startup flow, skip decisions, config key names, real external side effects, install commands, or retry behavior during a cleanup pass.
- When replacing a broad helper with a narrower helper, search the whole file or package for remaining old references before compiling.
- If a tool reports touched symbols that no longer exist or are adjacent to the real diff, verify against `git diff` and current source before treating it as a blocker.
- Stop and re-plan when a suspected cleanup target carries external behavior, ownership, or compatibility obligations.

## Final Verification

- Run the focused test, typecheck, build, or static check that best covers the touched behavior.
- Re-run compile/typecheck after helper renames or signature changes.
- Summarize what stayed intentionally out of scope so future refactor rounds do not inherit hidden behavior changes.
