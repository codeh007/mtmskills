## Go And Backend Convergence

Use these rules when Go or backend structure has started to drift toward glue-heavy, facade-heavy, or configuration-heavy code.

## Common Smells

### God Package

One package mixes CLI, database, transport, business logic, and utilities until ownership becomes unclear.

Converge by:

- restoring package boundaries around real responsibilities
- moving logic to the domain that owns it
- avoiding new package splits unless they reduce real coupling

### Misplaced Interface

Interfaces expose implementation details, live in the wrong package, or force frequent `.(*ConcreteType)` casts.

Converge by:

- defining interfaces only where a real consuming boundary needs them
- deleting zombie interface layers with no polymorphic value
- using concrete types directly when that is the honest contract

### Context As Factory

`FromCtx` or similar helpers create expensive runtime objects instead of only retrieving already-owned request state.

Converge by:

- treating `context.Context` as a transport mechanism, not object construction
- moving object ownership to explicit initialization paths

### Single-Consumer Glue

Exported helpers, utility files, or adapter shims exist for one caller only.

Converge by:

- inlining single-consumer helpers
- merging tiny utility files back into the owning source file or package

### Shell Command Overreach

Business logic relies on `exec.Command("sh", "-c", ...)` for work that should be explicit, typed, or platform-safe.

Converge by:

- replacing shell strings with direct command invocation or native Go logic
- removing platform-coupled hidden behavior where possible

### Initialization Escape Hatches

Flags such as `SkipXxxInit` or similar toggles hide real dependency problems and let callers bypass correct ownership.

Converge by:

- repairing the actual initialization boundary
- separating configuration from runtime state
- deleting flags that exist only to mask coupling

## Direction Rules

- Interfaces are contracts, not convenience wrappers.
- Context passes request-scoped values; it is not a service locator or factory.
- Prefer one honest path over parallel old/new paths.
- Do not add another helper, service, or adapter when deleting one layer would be enough.
