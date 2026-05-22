## Cross-Stack Smells

Use this catalog to name convergence targets consistently. The goal is not to collect every possible anti-pattern, but to quickly classify whether structure should be deleted, inlined, merged, or left alone.

## Migrated Rule Index

- `R001` -> responsibility drift
- `R003` -> compatibility leftover
- `R004` -> multi-responsibility structure
- `R005` -> env-var escape hatch
- `R008` -> temporary logging-only variable
- `R009` -> single-consumer exported function
- `R010` -> single-consumer function or component
- `R011` -> tiny standalone utility file drift
- `R012` -> structure-self-proof test of tests or test fixtures
- `R013` -> nonexistent-object assertion
- `R014` -> logs used as user documentation
- `R015` -> single source of truth violation

### Thin Wrapper

Structure that only forwards props, params, context, children, calls, or config without adding behavior, ownership, or an independent contract.

Common actions:

- inline the caller-facing wrapper
- import the real implementation directly
- delete wrapper-only tests and alias files

### Single-Consumer Abstraction

An exported function, helper, hook, component, or file exists for only one real caller and does not protect a stable boundary.

Common actions:

- inline it into the caller
- make it private if a local name still helps readability
- merge tiny utility files back into the owning module

This bucket carries:

- `R009` single-consumer exported functions that should be inlined or made private
- `R010` single-consumer functions or components that should be inlined
- `R011` tiny standalone utility or helper files that exist without broad reuse

### Fake Boundary Or Facade

Provider, header, module shell, interface, adapter, or package edge that renames the real implementation but adds no policy, behavior, or independent ownership.

Common actions:

- collapse the facade
- keep a single import path or package entry
- delete indirection that only increases jump cost

### Duplicate Implementation

The same logic, state mapping, normalization, or protocol handling appears in multiple places because each new change added another copy.

Common actions:

- identify the canonical owner
- merge copies into one implementation
- keep behavior-focused verification around the unified path

### Multi-Responsibility Structure

One middleware, hook, provider, helper, or module handles several unrelated jobs and forces unrelated changes to land in the same place.

Common actions:

- split by real responsibility when a true seam exists
- otherwise move the misplaced behavior back to the owning module

This carries `R004`.

### Compatibility Leftover

Old branches, fields, files, commands, adapters, or schemas still exist only because earlier implementations were not fully removed.

Common actions:

- confirm real consumers first
- delete the obsolete path and repair remaining references
- avoid carrying new and old routes in parallel without active need

### Responsibility Drift

Code lives in the wrong layer: config owns behavior, route files own reusable UI, tests force business setup, or database shapes carry frontend-only presentation baggage.

Common actions:

- move logic back to its real owner
- separate runtime state from configuration
- restore route, package, and schema truth boundaries

This bucket carries:

- `R001` behavior living in the wrong module or layer
- `R015` violation of single source of truth when multiple fields, configs, or code paths must be updated together

### Structure-Self-Proof Test

Tests only prove that a wrapper, helper, field, or file exists, or that a fixture/setup helper behaves as written, instead of guarding a regression users would notice.

Common actions:

- delete the self-proof test
- replace it with behavior verification only if a real regression risk remains

This bucket carries:

- `R012` tests that test test helpers, fixtures, or test structure itself
- `R013` tests that assert an object, field, or function does not exist

### Magic Escape Hatch

The codebase hides coupling or breakage behind flags, env vars, `testMode`, `SkipXxxInit`, ignore-build settings, or shell indirection instead of fixing the root boundary.

Common actions:

- remove the escape hatch
- repair the real dependency or initialization boundary
- keep configuration focused on genuine deploy/runtime variation

This bucket carries `R005`: do not add new env vars for local logic when explicit inputs, typed config, files, or database-backed config are the honest boundary.

### Logging As Structure

Logs should describe runtime events, not patch over weak structure.

Common actions:

- inline temporary variables created only to feed log lines
- move usage guidance to docs, CLI help, or explicit errors instead of runtime logs

This bucket carries:

- `R008` temporary logging-only variables that should be inlined or removed
- `R014` logs used as user documentation instead of operational runtime output

## Decision Filter

Treat a smell as a convergence candidate only when all of these are true:

- the structure does not carry independent behavior or ownership
- the real consumers are understood
- the verification path is clear enough to preserve behavior
- removing it makes the codebase simpler, not just differently abstract
