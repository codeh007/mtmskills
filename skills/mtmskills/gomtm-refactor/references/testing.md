## Testing Convergence Principles

Tests exist to protect regressions that matter, not to prove that current structure, fixtures, or helper code still look the same.

## Keep

- behavior-facing assertions at the lowest layer that can express the regression clearly
- the smallest reliable verification path for the changed stack
- self-contained setup where possible instead of test-driven production hooks

## Delete Or Avoid

### Structure-Self-Proof Tests

Examples:

- tests that only prove a wrapper, alias, or helper file exists
- tests that only prove a fixture helper behaves exactly as implemented
- tests that assert an object, field, or function does not exist

These do not protect user-visible behavior. Delete them.

### Test-Driven Production Intrusion

Avoid changing business code only to support tests, such as:

- `testMode` branches
- setup-only public helpers
- special cleanup functions added only for tests

Fix the test boundary instead.

### Duplicate Assertion Layers

Do not repeat the same logic across SQL tests, unit tests, component tests, integration tests, and E2E.

- lower layers should prove branch-heavy behavior
- higher layers should prove the critical workflow still works

### Heavyweight Default Verification

- Do not default to E2E when a unit, component, SQL, or integration check already expresses the regression.
- Do not bind otherwise fast tests to real network, disk, cloud resources, or remote databases unless that external dependency is the point of the test.

## Stack-Specific Verification Order

- database SQL contract changes: run the canonical database verification first
- Go integration or adapter changes without SQL contract change: run the relevant Go tests first
- frontend display or interaction changes: run the minimal frontend checks first, then heavier browser coverage only if needed

## Naming The Smell

When cleaning tests, classify the issue first:

- structure-self-proof test
- duplicate assertion layer
- test-driven production intrusion
- heavyweight verification mismatch

Keeping the same smell language helps convergence work stay focused on regression value instead of test count.
