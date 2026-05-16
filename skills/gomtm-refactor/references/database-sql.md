## Database And SQL Refactor Boundaries

This reference keeps only the convergence-oriented rules for database and SQL cleanup. If the current environment provides a dedicated `gomtm-db-dev` skill, treat that as the database-specific development truth for operational SQL workflow, pgTAP organization, mock strategy, and canonical verification entrypoints. Otherwise fall back to the current repo's database conventions and any `AGENTS.md`-defined verification truth.

## Required Boundary

- Before database refactor, database smell cleanup, or pgTAP convergence work, use the dedicated database skill when available; otherwise follow the current repo database conventions and `AGENTS.md`-defined verification truth.
- Keep this file focused on refactor decisions, not full database development process truth.

## Common Smells

### Hidden Skip Or Silence Path

The code logs around a failure, swallows it, or silently stops important handling instead of fixing the root cause.

### Shared Test Magic

Database tests depend on global helper files, implicit shared state, `pg_sleep`, or environment accidents instead of self-contained fixtures and deterministic setup.

### Mock Rows Or Fake-Only Branches

Business SQL grows `mock` rows, fake data branches, or `test_mode`-style code paths that exist only so tests can pass.

### Structure-Self-Proof SQL Test

Tests only prove that a table, column, field, or object exists, rather than validating the business entry point that would fail if the structure were wrong.

### Redundant Contract Shape

Fields or JSON keys remain only to satisfy outdated frontend shapes, dead components, or static types, even though the canonical business contract no longer needs them.

### Query Side Effects

Read-oriented functions mutate state, emit hidden writes, or blend command behavior into query behavior.

### Naming And Parameter Drift

Function names hide intent, or complex functions keep accumulating positional arguments when named parameters or clearer contracts are needed.

## Convergence Rules

- Let database fields serve business semantics, permissions, state transitions, and true read/write contracts first.
- If only outdated UI code or dead consumers still reference a field, prefer fixing or deleting the frontend residue over restoring the field.
- Keep tests close to real business entry points instead of proving schema trivia in isolation.
- Do not add `test_mode`, mock branches, fake-only branches, mock rows, or other test-only logic into business SQL.
- Prefer theme-based test organization over many tiny migration-cleanup proof files.

## Verification Boundary

- When SQL contracts change, run the canonical database verification path.
- When only Go or frontend adapters change and the SQL contract is untouched, do not treat full database verification as the automatic default.
- Never delete fields, functions, or compatibility layers only because tooling says they look unused; confirm actual runtime consumers first.
