---
name: human-priority-desktop-control
description: Control the Windows desktop with human-priority pause behavior, UI Automation control discovery/actions, window targeting, screenshots, mouse, keyboard, clipboard paste, and JSON action plans. Use when Codex is asked to operate a local Windows computer like a person, click/type/use hotkeys, inspect desktop UI, interact with app controls, run GUI workflows, or build desktop automation that pauses whenever the human user moves the mouse, presses keys, or otherwise takes over.
---

# Human-Priority Desktop Control

## Capability Boundary

Use this skill for local Windows desktop automation from shell-accessible Codex sessions. It provides a reusable helper for guarded Win32 mouse/keyboard/window/screenshot actions plus Windows UI Automation control-tree discovery and control-pattern actions.

Do not claim that the model itself has native, always-on desktop control. This skill only works when the current Codex environment can run local commands and the process has permission to inject input into the active Windows session.

The bundled helper is best-effort human-priority automation. It installs low-level keyboard/mouse hooks while running, ignores its own injected input when Windows marks it as injected, checks recent input, cursor drift, and currently pressed keys/buttons, and resumes after the configured human-idle window. It is still not a trusted kernel driver or accessibility service.

UI Automation support uses Windows' built-in `System.Windows.Automation` APIs through `scripts/desktop_uia.ps1`. It works best for Win32, WPF, WinForms, Qt, Chromium/Electron, and other apps that expose accessibility metadata. Some custom canvases, games, remote desktops, and GPU-only surfaces may expose only a coarse pane; use screenshots and guarded coordinates for those cases.

## Workflow

1. State the task type as Feature unless the user is reporting a broken automation.
2. Confirm the target app/window and the exact user-visible goal.
3. Prefer app-native APIs, files, CLI commands, COM automation, browser automation, or MCP/app connectors when those can complete the task more safely.
4. For GUI interaction, prefer this order: UI Automation controls, window-relative clicks, screenshot-guided coordinates, raw screen coordinates.
5. Run one status check near the start of a desktop-control session, not before every action:

```powershell
python "$env:USERPROFILE\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" status
```

6. Before clicking unknown UI, inspect it with `windows`, `foreground`, `screenshot`, and when available `uia-tree` or `uia-find`.
7. Prefer `uia-invoke`, `uia-set-value`, `uia-toggle`, `uia-select`, `uia-click`, `click-window`, and `activate` over raw screen coordinates.
8. For real actions, use JSON plans for multi-step workflows so the helper can restore the original foreground window once the plan exits.
9. Stop immediately when the target UI differs from expectations or when a protected/destructive confirmation appears.

## Speed Path

Optimize for fewer GUI round trips before optimizing pointer speed.

1. Complete deterministic work outside the GUI first: use local files, database CLIs, PowerShell, COM automation, app-native command lines, or APIs whenever possible.
2. Use the GUI for the parts that genuinely need visible state, logged-in desktop state, or screenshot evidence.
3. Use `uia-tree` and `uia-find` to locate named controls before falling back to visual coordinates.
4. Batch uninterrupted GUI steps into one JSON plan. Avoid separate shell calls for each click or keystroke when the UI state is known.
5. Use `uia-set-value` for fields that expose `ValuePattern`; otherwise use `type --method paste` or `paste` for long text. Avoid character-by-character typing except in fields that reject paste.
6. Capture only the evidence needed: prefer one target-window screenshot after a meaningful state change instead of repeated full-screen screenshots.
7. Skip dry-run plans for simple read-only commands (`windows`, `foreground`, `screenshot`, `status`, `uia-tree`, `uia-find`, `uia-assert`) and for already-proven low-risk action plans. Keep dry-runs for uncertain coordinates, destructive flows, or unfamiliar UI.

For low-risk, user-requested workflows where no secrets, payments, deletion, or irreversible confirmations are involved, use a fast profile:

```powershell
python "$env:USERPROFILE\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" --idle-ms 100 --resume-idle-ms 1200 --move-duration-ms 0 plan .\desktop-plan.json
```

Keep the default profile for risky workflows or when the human is actively using the computer.

## Hybrid GUI Pattern

For database tools, office documents, IDEs, browsers, chat clients, and other apps with reliable automation surfaces:

1. Prepare state with deterministic tooling first. Examples: run SQL through `mysql.exe`, export Word/PDF through Word COM, edit project files directly, or use an app's command-line import/export.
2. If a GUI step remains, check whether the target exposes UI Automation controls with `uia-tree --title "<window>" --max-depth 3 --limit 50`.
3. Use UI Automation control patterns for stable controls: `InvokePattern` for buttons/menu items, `ValuePattern` for editable values, `TogglePattern` for checkboxes, `SelectionItemPattern` for list/tab choices, `ExpandCollapsePattern` for expandable controls, and `ScrollPattern` for scrollable containers.
4. Open or activate the GUI only to verify the resulting state, complete a GUI-only setup, or capture screenshots required by the user.
5. If a GUI setup fails or is slow, preserve the deterministic artifact and explain what evidence is still missing instead of spending many iterations on blind clicks.

## AI Pre-Review + Human Final Review

Use the review workflow whenever the desktop task needs inspection, evidence, or approval. The AI may collect evidence, run assertions, execute guarded non-destructive plans, and write an AI pre-review. The AI pre-review is never final approval; the human performs the final review.

1. Create a review session before meaningful GUI work:

```powershell
python "$env:USERPROFILE\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" review --objective "Inspect the current desktop state before changing settings" --title "Target App"
```

2. Reuse the returned `review_dir` for assertions and plans:

```powershell
python "$env:USERPROFILE\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" assert-window --review-dir "<review_dir>" --title "Target App" --foreground --min-width 800 --min-height 600 --fail-on-miss
python "$env:USERPROFILE\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" plan --review-dir "<review_dir>" .\desktop-plan.json
```

3. After inspecting the collected evidence, append the AI pre-review:

```powershell
python "$env:USERPROFILE\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" review-note --review-dir "<review_dir>" --author ai --status needs_human_review --summary "Evidence collected; no destructive action taken." --details-file .\ai-review.md --recommendation "Human should verify the final UI state before approval."
```

4. Only the human final reviewer records completion:

```powershell
python "$env:USERPROFILE\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" finalize-review --review-dir "<review_dir>" --decision approved --summary "Human final review approved."
```

Each review directory contains `manifest.json`, `events.jsonl`, `notes.jsonl`, `report.md`, and an `evidence` folder. Treat `report.md` as the handoff document from AI pre-review to human final review.

## Human-Priority Rules

- Treat human input as higher priority than AI input.
- Before each mouse/keyboard action, wait until recent input has been idle for `--idle-ms` (default 250 ms).
- If human input appears during execution, pause rather than fail; resume after `--resume-idle-ms` (default 3000 ms).
- During pointer motion, pause if the cursor position diverges from the expected path.
- Restore the starting foreground window on exit by default. Use `--no-restore-foreground` only when the user explicitly wants the target app left in front.
- Keep action batches short enough that the user can interrupt naturally.
- Avoid entering secrets, payment details, destructive confirmations, or irreversible actions unless the user explicitly asks and the final confirmation is left to the user.

## Helper Script

The script is:

```text
scripts/human_priority_desktop.py
```

Common commands:

```powershell
# Inspect current cursor and last input age.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" status

# Wait until the user has stopped interacting for 3 seconds.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" wait-idle

# List or inspect windows.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" windows --filter "MCP"
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" foreground

# Inspect UI Automation availability and controls. Prefer this before unknown clicks.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-status
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-tree --title "Target App" --max-depth 3 --limit 50
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-find --title "Target App" --name "Save" --control-type Button
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-assert --title "Target App" --name "Save" --control-type Button --fail-on-miss

# Act on UI Automation controls when the target supports a matching pattern.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-invoke --title "Target App" --name "Save" --control-type Button
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-set-value --title "Target App" --automation-id "SearchBox" --control-type Edit --value "query text"
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-toggle --title "Target App" --name "Enable option" --control-type CheckBox
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-select --title "Target App" --name "General" --control-type TabItem
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-click --title "Target App" --name "Canvas Area" --control-type Pane

# Activate a window, click inside it, and restore the previous foreground window on exit.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" click-window --title "MCP For Unity" --ratio 0.87 0.59

# Drag inside a target window.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" drag-window --title "Blender" --from-ratio 0.5 0.5 --to-ratio 0.6 0.5 --duration-ms 250

# Screenshot a target window. The helper activates it first so it is not captured behind another window.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" screenshot --title "MCP For Unity" --path "$env:TEMP\mcp-window.png"

# Fast Unicode typing. Use --method paste for long text in normal text fields.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" type --text "hello"
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" type --method paste --text "long text"

# Press a hotkey.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" hotkey --keys ctrl l

# Create an evidence-backed AI pre-review session.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" review --objective "Check the visible state before proceeding" --title "MCP For Unity"

# Assert expected UI state and attach the result to a review session.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" assert-window --review-dir "<review_dir>" --title "MCP For Unity" --foreground --min-width 800 --min-height 600

# Record AI pre-review and human final review notes.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" review-note --review-dir "<review_dir>" --author ai --status needs_human_review --summary "Evidence captured for human final review."
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" finalize-review --review-dir "<review_dir>" --decision approved --summary "Human final review approved."

# Preview a JSON action plan without moving the mouse or typing.
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" --dry-run plan .\desktop-plan.json
```

JSON plan format:

```json
[
  {"action": "activate", "title": "Untitled - Notepad"},
  {"action": "hotkey", "keys": ["ctrl", "l"]},
  {"action": "type", "text": "notepad"},
  {"action": "key", "key": "enter"},
  {"action": "sleep", "ms": 500},
  {"action": "uia_assert", "title": "Target App", "name": "Save", "control_type": "Button"},
  {"action": "uia_invoke", "title": "Target App", "name": "Save", "control_type": "Button"},
  {"action": "uia_set_value", "title": "Target App", "automation_id": "SearchBox", "control_type": "Edit", "value": "query text"},
  {"action": "uia_toggle", "title": "Target App", "name": "Enable option", "control_type": "CheckBox"},
  {"action": "uia_select", "title": "Target App", "name": "General", "control_type": "TabItem"},
  {"action": "uia_click", "title": "Target App", "name": "Canvas Area", "control_type": "Pane"},
  {"action": "click_window", "title": "MCP For Unity", "ratio": [0.87, 0.59]},
  {"action": "drag_window", "title": "Blender", "from_ratio": [0.5, 0.5], "to_ratio": [0.6, 0.5], "duration_ms": 250},
  {"action": "restore_foreground"}
]
```

Supported action names: `activate`, `move`, `click`, `double_click`, `drag`, `click_window`, `drag_window`, `type`, `paste`, `key`, `hotkey`, `scroll`, `sleep`, `screenshot`, `restore_foreground`, `uia_tree`, `uia_find`, `uia_assert`, `uia_click`, `uia_invoke`, `uia_set_value`, `uia_toggle`, `uia_select`, `uia_expand`, `uia_collapse`, `uia_focus`, and `uia_scroll`.

UIA action fields:

- Window scope: `hwnd`, or `title`/`window_title` plus optional `window_class`, `window_exact`, `window_regex`.
- Control query: `name`, `automation_id`, `control_type`, `class_name`, `text_query`, `regex`, `index`, `max_depth`, `limit`, `include_offscreen`.
- Pattern values: `value` for `uia_set_value`; `horizontal_amount` and `vertical_amount` for `uia_scroll`.
- `uia_click` uses the control's clickable point when available, otherwise its bounding rectangle center.

Review-oriented commands: `review`, `assert-window`, `uia-assert`, `review-note`, `finalize-review`, and `plan --review-dir`.

Useful global defaults:

- `--idle-ms 250`: fast initial start when no human is active.
- `--resume-idle-ms 3000`: pause and resume three seconds after human input ends.
- `--move-duration-ms 0`: fastest pointer motion; increase for visually inspectable movement.
- `--no-restore-foreground`: leave the target app in front.
- `--no-hooks`: fallback mode if low-level hooks cannot be installed.

## Verification

For skill maintenance, validate the skill:

```powershell
python "C:\Users\Nullqqq\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control"
```

For the helper, run safe checks first:

```powershell
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" status
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-status
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" uia-tree --title "Codex" --max-depth 1 --limit 3
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" --dry-run click --x 10 --y 10
python "C:\Users\Nullqqq\.codex\skills\human-priority-desktop-control\scripts\human_priority_desktop.py" --dry-run review --objective "Verify review workflow" --no-screenshot
```

Only run real click/type tests when the active desktop state is known and harmless.

## Reference

Read `references/windows-desktop-safety.md` when deciding whether desktop control is appropriate or when explaining limitations to the user.
