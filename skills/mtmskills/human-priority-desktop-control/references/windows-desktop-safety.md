# Windows Desktop Safety Notes

## Prefer Safer Control Surfaces

Prefer these in order when they can complete the task:

1. Project files, config files, or app data files.
2. Official CLI/API/automation interfaces.
3. Browser automation for web apps.
4. Windows UI Automation control patterns for native desktop controls.
5. Window-relative guarded mouse/keyboard input.
6. Raw screen-coordinate input as a last resort.

Desktop input is brittle because coordinates, focus, window z-order, DPI scaling, keyboard layout, popups, and user intervention can change the outcome.

UI Automation is less brittle than coordinates but still not universal. Some apps expose only a top-level window or pane, and some controls expose names without invokable patterns. Inspect `patterns` from `uia-tree` or `uia-find` before choosing `uia-invoke`, `uia-set-value`, `uia-toggle`, `uia-select`, `uia-expand`, `uia-collapse`, or `uia-scroll`.

## Human-Priority Meaning

Human-priority means the automation must yield when the user appears to be interacting. The helper detects:

- Recent keyboard or mouse input reported by Windows.
- Cursor movement away from the expected AI-controlled position.
- Mouse buttons or common keyboard keys currently held down.

This is not the same as a kernel driver, a low-level keyboard/mouse hook, or a full accessibility service. If a task requires guaranteed capture of all physical input events, build or install a dedicated trusted local service and get explicit user approval.

## Stop Conditions

Stop and ask the user when:

- The active UI differs from the expected target.
- `uia-tree` or `uia-find` shows only coarse panes and the visual target is not confidently located.
- A matched UIA control lacks the required pattern for the intended operation.
- A password, payment, legal agreement, irreversible action, deletion, or system permission prompt appears.
- The next step is an approval, publish, purchase, delete, permission grant, account change, or other final decision.
- Human input repeatedly interrupts the guard.
- The target coordinates are not known and no matching UIA control or screenshot evidence identifies the target.
- The task would require bypassing security controls.

## Review Evidence Chain

For work that needs oversight, create a review session before interacting with the GUI. Attach screenshots, status snapshots, window assertions, and plan execution results to the same `review_dir`.

The AI role is pre-review: collect evidence, run non-destructive checks, summarize findings, and recommend what the human should inspect. The human role is final review: approve, reject, request changes, or block the work.

Do not treat an AI `review-note --author ai` as approval. Completion requires a human `finalize-review` record or an explicit user decision in the conversation.

## Coordinate Discipline

When using coordinates:

- Capture or inspect the current UI state first whenever possible.
- Try `uia-tree`, `uia-find`, or `uia-click` before raw coordinates when the target app exposes controls.
- Prefer short movement paths and small action batches.
- Use `status` to check the cursor position.
- Avoid edge or corner clicks unless intentional.
- Re-check after scrolling, resizing, DPI changes, or app navigation.
- Prefer window-relative points and ratios, then assert the target window before acting.

## UI Automation Discipline

When using UI Automation:

- Scope the query to a target window with `--title`, `--window-class`, or `--hwnd` unless the desktop root is intentional.
- Start with `uia-tree --max-depth 2` or `uia-find --limit 20`; increase depth only when needed.
- Match controls by stable properties first: `automation_id`, then `control_type` plus `name`, then `class_name`, then broad `text`.
- Use `--index` only after inspecting all matches; a later app layout change can reorder matches.
- For fields, prefer `uia-set-value` only when the target exposes `ValuePattern`; otherwise focus the control and paste.
- For buttons and menu items, prefer `uia-invoke`; use `uia-click` when the app exposes a location but no useful invoke pattern.
- Attach `uia-assert` results to a review session before destructive or high-risk UI steps.
