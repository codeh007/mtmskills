## Frontend Structure Truth

- `src/app` owns route boundaries, route-only orchestration, and page-level entry points.
- `src/components` owns genuinely reusable UI, not route-local glue renamed as reusable structure.
- Query and route state should stay truthful to the route boundary rather than being hidden behind extra wrappers.

If a frontend file does not add behavior, ownership, or a reusable contract, treat it as a convergence candidate instead of a permanent layer.

## Unified Smell Language

Map the old isolated UI terminology into the main refactor vocabulary:

- thin provider wrapper -> thin wrapper
- single-consumer alias -> single-consumer abstraction
- module shell facade -> fake boundary or facade
- wrapper-only tests -> structure-self-proof tests

## Red Flags

- a route file only returns one page component and adds no route logic
- a wrapper only forwards `children`, props, params, pathname, or search params unchanged
- a provider, header, layout, or module shell only renames an underlying primitive
- a file exists only to re-export one implementation under a second name
- a test only proves that the wrapper or alias file still renders or still exists
- a directory remains only because the deleted wrapper used to live there

## Required Rules

- Keep route-only ownership in `src/app` and reusable UI in `src/components`.
- Inline single-consumer route, layout, or page facades back into the real caller.
- Use the underlying provider or component directly when the wrapper adds no behavior.
- Delete export-only files and pass-through module shells when they do not define a real boundary.
- Delete wrapper-only tests and empty directories after collapsing the structure.
- Do not create a new hook, provider, helper, or facade just to replace the wrapper you removed.

## Scope Boundary

- This guidance is for structural convergence, not opportunistic product redesign.
- Keep a wrapper only when it adds real behavior, ownership, policy, or multiple true consumers.
- Route-local orchestration may stay in `src/app` when it actually binds route params, auth, data loading, or page composition.
- Reusable UI may stay in `src/components` when multiple call sites use it as a real component contract.

## Thin-Wrapper Example

```tsx
export function HermesHeader({ children }: { children: React.ReactNode }) {
  return <PageHeaderProvider>{children}</PageHeaderProvider>;
}
```

This is a thin wrapper when it only renames `PageHeaderProvider`. Delete `HermesHeader` and use `PageHeaderProvider` directly.

## Export-Only Example

```tsx
export { HermesModuleShell } from "./module-shell";
```

This is an export-only facade when the file exists only to create a second import path. Delete the file and import `./module-shell` directly.

## Route Boundary Example

```tsx
export default function Page() {
  return <StatusView />;
}
```

If `Page` adds no route logic and `StatusView` is only consumed by that route, collapse the split and keep the real route entry in `src/app`.

## Cleanup Pattern

When removing a frontend fake boundary:

1. update imports to the real implementation
2. inline the single consumer when appropriate
3. delete alias files, wrapper-only tests, and empty directories
4. verify that the route and reusable UI boundaries are still obvious
