#!/usr/bin/env python3
"""Fast guarded Windows desktop automation with human-priority resume."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Iterable
import uuid


if os.name != "nt":
    raise SystemExit("human_priority_desktop.py only supports Windows.")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


configure_stdio()


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

ULONG_PTR = wintypes.WPARAM
LRESULT = wintypes.LPARAM
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def enable_dpi_awareness() -> None:
    try:
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError):
        pass
    try:
        shcore = ctypes.WinDLL("shcore", use_last_error=True)
        if shcore.SetProcessDpiAwareness(2) == 0:
            return
    except (AttributeError, OSError):
        pass
    try:
        user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


enable_dpi_awareness()

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
VK_CANCEL = 0x03
VK_MBUTTON = 0x04
VK_XBUTTON1 = 0x05
VK_XBUTTON2 = 0x06
VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_PAUSE = 0x13
VK_CAPITAL = 0x14
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_END = 0x23
VK_HOME = 0x24
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_INSERT = 0x2D
VK_DELETE = 0x2E
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_NUMPAD0 = 0x60
VK_F1 = 0x70

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
HC_ACTION = 0
LLKHF_LOWER_IL_INJECTED = 0x02
LLKHF_INJECTED = 0x10
LLMHF_INJECTED = 0x01
LLMHF_LOWER_IL_INJECTED = 0x02
WM_QUIT = 0x0012

SW_RESTORE = 9
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_SHOWWINDOW = 0x0040

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL
user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
user32.GetLastInputInfo.restype = wintypes.BOOL
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = wintypes.SHORT
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetSystemMetrics.restype = ctypes.c_int
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user32.AttachThreadInput.restype = wintypes.BOOL
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = LRESULT
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE
user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
user32.CountClipboardFormats.argtypes = []
user32.CountClipboardFormats.restype = ctypes.c_int
kernel32.GetTickCount.argtypes = []
kernel32.GetTickCount.restype = wintypes.DWORD
kernel32.GetCurrentThreadId.argtypes = []
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL
kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalFree.restype = wintypes.HGLOBAL


KEYS: dict[str, int] = {
    "backspace": VK_BACK,
    "tab": VK_TAB,
    "enter": VK_RETURN,
    "return": VK_RETURN,
    "shift": VK_SHIFT,
    "ctrl": VK_CONTROL,
    "control": VK_CONTROL,
    "alt": VK_MENU,
    "pause": VK_PAUSE,
    "capslock": VK_CAPITAL,
    "caps": VK_CAPITAL,
    "esc": VK_ESCAPE,
    "escape": VK_ESCAPE,
    "space": VK_SPACE,
    "pageup": VK_PRIOR,
    "pgup": VK_PRIOR,
    "pagedown": VK_NEXT,
    "pgdn": VK_NEXT,
    "end": VK_END,
    "home": VK_HOME,
    "left": VK_LEFT,
    "up": VK_UP,
    "right": VK_RIGHT,
    "down": VK_DOWN,
    "insert": VK_INSERT,
    "ins": VK_INSERT,
    "delete": VK_DELETE,
    "del": VK_DELETE,
    "win": VK_LWIN,
    "windows": VK_LWIN,
    "rwin": VK_RWIN,
}

for digit in "0123456789":
    KEYS[digit] = ord(digit)

for letter in "abcdefghijklmnopqrstuvwxyz":
    KEYS[letter] = ord(letter.upper())

for i in range(10):
    KEYS[f"num{i}"] = VK_NUMPAD0 + i

for i in range(1, 25):
    KEYS[f"f{i}"] = VK_F1 + i - 1

VK_NAMES = {value: key for key, value in KEYS.items()}
VK_NAMES.update({
    VK_LBUTTON: "left_mouse",
    VK_RBUTTON: "right_mouse",
    VK_MBUTTON: "middle_mouse",
    VK_XBUTTON1: "xbutton1",
    VK_XBUTTON2: "xbutton2",
})

WATCHED_VKS = list(range(1, 256))
BUTTON_EVENTS = {
    "left": (VK_LBUTTON, MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "right": (VK_RBUTTON, MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "middle": (VK_MBUTTON, MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}
DEFAULT_REVIEW_ROOT = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".codex" / "desktop-reviews"
SCRIPT_DIR = Path(__file__).resolve().parent
UIA_SCRIPT = SCRIPT_DIR / "desktop_uia.ps1"
UIA_ACTIONS = {"uia_invoke", "uia_set_value", "uia_toggle", "uia_select", "uia_expand", "uia_collapse", "uia_focus", "uia_scroll"}
UIA_CLI_COMMANDS = {
    "uia-invoke": "invoke",
    "uia-set-value": "set-value",
    "uia-toggle": "toggle",
    "uia-select": "select",
    "uia-expand": "expand",
    "uia-collapse": "collapse",
    "uia-focus": "focus",
    "uia-scroll": "scroll",
}


def fail_if_false(result: Any, name: str) -> None:
    if not result:
        raise ctypes.WinError(ctypes.get_last_error(), name)


def json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def print_json(data: Any) -> None:
    print(json_text(data))


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def safe_filename(value: str, fallback: str = "item") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return cleaned[:80] or fallback


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_text(data) + "\n", encoding="utf-8")


def expand_path(value: str | Path) -> Path:
    return Path(os.path.expandvars(str(value))).expanduser()


def read_text_value(value: str | None, path_value: str | None) -> str:
    if path_value:
        return expand_path(path_value).read_text(encoding="utf-8")
    return value or ""


def now_tick() -> int:
    return int(kernel32.GetTickCount())


def tick_elapsed(start_tick: int, end_tick: int | None = None) -> int:
    if end_tick is None:
        end_tick = now_tick()
    return (end_tick - start_tick) & 0xFFFFFFFF


def tick_near(a: int, b: int, tolerance_ms: int) -> bool:
    return min(tick_elapsed(a, b), tick_elapsed(b, a)) <= tolerance_ms


def cursor_pos() -> tuple[int, int]:
    point = wintypes.POINT()
    fail_if_false(user32.GetCursorPos(ctypes.byref(point)), "GetCursorPos")
    return int(point.x), int(point.y)


def set_cursor(x: int, y: int) -> None:
    fail_if_false(user32.SetCursorPos(int(x), int(y)), "SetCursorPos")


def last_input_tick() -> int:
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    fail_if_false(user32.GetLastInputInfo(ctypes.byref(info)), "GetLastInputInfo")
    return int(info.dwTime)


def idle_ms() -> int:
    return tick_elapsed(last_input_tick())


def key_is_down(vk: int) -> bool:
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def pressed_keys(limit: int = 12, ignored_vks: Iterable[int] = ()) -> list[str]:
    ignored = set(ignored_vks)
    keys: list[str] = []
    for vk in WATCHED_VKS:
        if vk in ignored:
            continue
        if key_is_down(vk):
            keys.append(VK_NAMES.get(vk, hex(vk)))
            if len(keys) >= limit:
                keys.append("...")
                break
    return keys


def send_input(*items: INPUT) -> None:
    if not items:
        return
    array_type = INPUT * len(items)
    sent = user32.SendInput(len(items), array_type(*items), ctypes.sizeof(INPUT))
    if sent != len(items):
        raise ctypes.WinError(ctypes.get_last_error(), "SendInput")


def mouse_input(flags: int, data: int = 0) -> INPUT:
    item = INPUT()
    item.type = INPUT_MOUSE
    item.union.mi = MOUSEINPUT(0, 0, data, flags, 0, 0)
    return item


def key_input(vk: int, flags: int = 0) -> INPUT:
    item = INPUT()
    item.type = INPUT_KEYBOARD
    item.union.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
    return item


def unicode_input(unit: int, flags: int = 0) -> INPUT:
    item = INPUT()
    item.type = INPUT_KEYBOARD
    item.union.ki = KEYBDINPUT(0, unit, KEYEVENTF_UNICODE | flags, 0, 0)
    return item


def utf16_units(text: str) -> list[int]:
    data = text.encode("utf-16le")
    return [int.from_bytes(data[i:i + 2], "little") for i in range(0, len(data), 2)]


def resolve_key(key: str) -> int:
    normalized = key.lower().replace("-", "").replace("_", "")
    if normalized not in KEYS:
        known = ", ".join(sorted(KEYS)[:24])
        raise ValueError(f"Unknown key {key!r}. Examples: {known}, ...")
    return KEYS[normalized]


def hwnd_int(hwnd: wintypes.HWND | int | None) -> int:
    return int(hwnd or 0)


def window_title(hwnd: wintypes.HWND | int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def window_class(hwnd: wintypes.HWND | int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, 256)
    return buffer.value


def window_rect(hwnd: wintypes.HWND | int) -> tuple[int, int, int, int]:
    rect = RECT()
    fail_if_false(user32.GetWindowRect(hwnd, ctypes.byref(rect)), "GetWindowRect")
    return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)


def window_info(hwnd: wintypes.HWND | int) -> dict[str, Any]:
    left, top, right, bottom = window_rect(hwnd)
    pid = wintypes.DWORD()
    thread_id = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return {
        "hwnd": hwnd_int(hwnd),
        "title": window_title(hwnd),
        "class": window_class(hwnd),
        "pid": int(pid.value),
        "thread_id": int(thread_id),
        "rect": {
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "width": right - left,
            "height": bottom - top,
        },
    }


def enum_visible_windows(min_width: int = 80, min_height: int = 60) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []

    def callback(hwnd: wintypes.HWND, _lparam: wintypes.LPARAM) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        try:
            info = window_info(hwnd)
        except OSError:
            return True
        rect = info["rect"]
        if rect["width"] >= min_width and rect["height"] >= min_height:
            windows.append(info)
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return windows


def matches_window(info: dict[str, Any], title: str | None, class_name: str | None, exact: bool, regex: bool) -> bool:
    if title:
        candidate = info["title"]
        if regex:
            if not re.search(title, candidate):
                return False
        elif exact:
            if candidate != title:
                return False
        elif title.lower() not in candidate.lower():
            return False
    if class_name:
        candidate = info["class"]
        if exact:
            if candidate != class_name:
                return False
        elif class_name.lower() not in candidate.lower():
            return False
    return True


def find_window(title: str | None, class_name: str | None, exact: bool = False, regex: bool = False) -> dict[str, Any]:
    matches = [
        info for info in enum_visible_windows()
        if matches_window(info, title, class_name, exact, regex)
    ]
    if not matches:
        raise ValueError(f"No visible window matched title={title!r} class={class_name!r}.")
    return matches[0]


def activate_window(hwnd: wintypes.HWND | int, timeout_ms: int = 2000) -> bool:
    if not hwnd or not user32.IsWindow(hwnd):
        return False

    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
    time.sleep(0.02)
    user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

    current = user32.GetForegroundWindow()
    current_thread = kernel32.GetCurrentThreadId()
    foreground_thread = user32.GetWindowThreadProcessId(current, None) if current else 0
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)

    attached: list[tuple[int, int]] = []
    for other in {int(foreground_thread), int(target_thread)}:
        if other and other != int(current_thread):
            if user32.AttachThreadInput(current_thread, other, True):
                attached.append((int(current_thread), other))
    try:
        user32.SetForegroundWindow(hwnd)
    finally:
        for src, dst in attached:
            user32.AttachThreadInput(src, dst, False)

    start = now_tick()
    while tick_elapsed(start) <= timeout_ms:
        if hwnd_int(user32.GetForegroundWindow()) == hwnd_int(hwnd):
            return True
        time.sleep(0.02)
    return hwnd_int(user32.GetForegroundWindow()) == hwnd_int(hwnd)


def clipboard_text() -> str | None:
    if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
        return None
    if not user32.OpenClipboard(None):
        return None
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return None
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def clipboard_format_count() -> int:
    if not user32.OpenClipboard(None):
        return 0
    try:
        return max(0, int(user32.CountClipboardFormats()))
    finally:
        user32.CloseClipboard()


def set_clipboard_text(text: str) -> None:
    encoded = text.encode("utf-16le") + b"\x00\x00"
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error(), "GlobalAlloc")
    ptr = kernel32.GlobalLock(handle)
    if not ptr:
        kernel32.GlobalFree(handle)
        raise ctypes.WinError(ctypes.get_last_error(), "GlobalLock")
    ctypes.memmove(ptr, encoded, len(encoded))
    kernel32.GlobalUnlock(handle)

    fail_if_false(user32.OpenClipboard(None), "OpenClipboard")
    try:
        fail_if_false(user32.EmptyClipboard(), "EmptyClipboard")
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise ctypes.WinError(ctypes.get_last_error(), "SetClipboardData")
        handle = None
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)


class HumanInputMonitor:
    def __init__(self, enabled: bool, verbose: bool) -> None:
        self.enabled = enabled
        self.verbose = verbose
        self.installed = False
        self.error: str | None = None
        self.last_physical_tick = 0
        self.last_event = ""
        self.thread_id = 0
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._keyboard_hook = wintypes.HHOOK()
        self._mouse_hook = wintypes.HHOOK()
        self._keyboard_proc: HOOKPROC | None = None
        self._mouse_proc: HOOKPROC | None = None

    def start(self) -> None:
        if not self.enabled:
            self._ready.set()
            return
        self._thread = threading.Thread(target=self._run, name="human-input-monitor", daemon=True)
        self._thread.start()
        self._ready.wait(0.75)

    def stop(self) -> None:
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(0.5)

    def record(self, event: str) -> None:
        with self._lock:
            self.last_physical_tick = now_tick()
            self.last_event = event

    def snapshot(self) -> tuple[int, str]:
        with self._lock:
            return self.last_physical_tick, self.last_event

    def _run(self) -> None:
        self.thread_id = int(kernel32.GetCurrentThreadId())

        @HOOKPROC
        def keyboard_proc(code: int, wparam: wintypes.WPARAM, lparam: wintypes.LPARAM) -> LRESULT:
            if code == HC_ACTION:
                data = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if not (data.flags & (LLKHF_INJECTED | LLKHF_LOWER_IL_INJECTED)):
                    self.record(f"keyboard:{int(data.vkCode)}")
            return user32.CallNextHookEx(self._keyboard_hook, code, wparam, lparam)

        @HOOKPROC
        def mouse_proc(code: int, wparam: wintypes.WPARAM, lparam: wintypes.LPARAM) -> LRESULT:
            if code == HC_ACTION:
                data = ctypes.cast(lparam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                if not (data.flags & (LLMHF_INJECTED | LLMHF_LOWER_IL_INJECTED)):
                    self.record(f"mouse:{int(wparam)}")
            return user32.CallNextHookEx(self._mouse_hook, code, wparam, lparam)

        self._keyboard_proc = keyboard_proc
        self._mouse_proc = mouse_proc
        module = kernel32.GetModuleHandleW(None)
        self._keyboard_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_proc, module, 0)
        self._mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_proc, module, 0)
        self.installed = bool(self._keyboard_hook or self._mouse_hook)
        if not self.installed:
            self.error = f"SetWindowsHookExW failed: {ctypes.get_last_error()}"
        self._ready.set()

        msg = MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            if self._keyboard_hook:
                user32.UnhookWindowsHookEx(self._keyboard_hook)
            if self._mouse_hook:
                user32.UnhookWindowsHookEx(self._mouse_hook)


class HumanPriorityGuard:
    def __init__(
        self,
        initial_idle_ms: int,
        resume_idle_ms: int,
        poll_ms: int,
        cursor_tolerance_px: int,
        timeout_ms: int | None,
        verbose: bool,
        dry_run: bool,
        monitor: HumanInputMonitor,
    ) -> None:
        self.initial_idle_ms = initial_idle_ms
        self.resume_idle_ms = resume_idle_ms
        self.poll_ms = max(5, poll_ms)
        self.cursor_tolerance_px = cursor_tolerance_px
        self.timeout_ms = timeout_ms
        self.verbose = verbose
        self.dry_run = dry_run
        self.monitor = monitor
        self.expected_cursor: tuple[int, int] | None = None
        self.last_ai_tick = 0
        self.pause_count = 0

    def log(self, message: str) -> None:
        if self.verbose:
            print(message, file=sys.stderr)

    def mark_ai_input(self) -> None:
        self.last_ai_tick = now_tick()
        try:
            self.expected_cursor = cursor_pos()
        except OSError:
            self.expected_cursor = None

    def last_input_is_ai(self, tick: int) -> bool:
        return bool(self.last_ai_tick and tick_near(tick, self.last_ai_tick, 250))

    def human_idle_elapsed(self) -> int:
        large = 0x7FFFFFFF
        last = last_input_tick()
        last_input_idle = large if self.last_input_is_ai(last) else tick_elapsed(last)
        physical_tick, _event = self.monitor.snapshot()
        hook_idle = tick_elapsed(physical_tick) if physical_tick else large
        return min(last_input_idle, hook_idle)

    def cursor_was_taken(self) -> bool:
        if self.expected_cursor is None:
            return False
        x, y = cursor_pos()
        ex, ey = self.expected_cursor
        return math.hypot(x - ex, y - ey) > self.cursor_tolerance_px

    def activity_reason(
        self,
        required_idle_ms: int,
        include_cursor: bool = True,
        ignored_vks: Iterable[int] = (),
    ) -> str | None:
        down = pressed_keys(ignored_vks=ignored_vks)
        if down:
            return "pressed: " + ",".join(down)
        if include_cursor and self.cursor_was_taken():
            return "cursor moved by human"
        idle = self.human_idle_elapsed()
        if idle < required_idle_ms:
            _tick, event = self.monitor.snapshot()
            suffix = f" event={event}" if event else ""
            return f"human input idle={idle}ms required={required_idle_ms}ms{suffix}"
        return None

    def wait_ready(
        self,
        reason: str,
        required_idle_ms: int | None = None,
        timeout_ms: int | None = None,
        ignored_vks: Iterable[int] = (),
    ) -> None:
        if self.dry_run:
            self.log(f"[dry-run] would guard before {reason}")
            return

        required = self.initial_idle_ms if required_idle_ms is None else required_idle_ms
        timeout = self.timeout_ms if timeout_ms is None else timeout_ms
        started = now_tick()
        last_report = 0
        paused = False

        while True:
            detail = self.activity_reason(required, ignored_vks=ignored_vks)
            if detail is None:
                return

            if not paused:
                paused = True
                self.pause_count += 1
                required = self.resume_idle_ms
                self.log(f"Paused before {reason}: {detail}")

            if self.cursor_was_taken():
                self.expected_cursor = cursor_pos()

            current = now_tick()
            if timeout is not None and tick_elapsed(started, current) > timeout:
                raise TimeoutError(f"Timed out waiting for human-priority guard before {reason}: {detail}")
            if self.verbose and tick_elapsed(last_report, current) >= 1000:
                self.log(f"Waiting before {reason}: {detail}")
                last_report = current
            time.sleep(self.poll_ms / 1000)

    def interruptible_sleep(self, ms: int) -> None:
        if self.dry_run:
            print(f"[dry-run] sleep {ms}ms")
            return
        started = now_tick()
        total = max(0, ms)
        while tick_elapsed(started) < total:
            self.wait_ready("sleep")
            remaining = total - tick_elapsed(started)
            time.sleep(min(self.poll_ms, remaining) / 1000)

    def move_to(self, x: int, y: int, duration_ms: int) -> None:
        self.wait_ready(f"move to {x},{y}")
        if self.dry_run:
            print(f"[dry-run] move to {x},{y} over {duration_ms}ms")
            self.expected_cursor = (x, y)
            return

        if duration_ms <= 0:
            set_cursor(x, y)
            self.mark_ai_input()
            return

        steps = max(1, duration_ms // self.poll_ms)
        for step in range(steps):
            self.wait_ready(f"move to {x},{y}")
            cx, cy = cursor_pos()
            remaining = max(1, steps - step)
            nx = round(cx + (x - cx) / remaining)
            ny = round(cy + (y - cy) / remaining)
            set_cursor(nx, ny)
            self.mark_ai_input()
            time.sleep(self.poll_ms / 1000)

        set_cursor(x, y)
        self.mark_ai_input()

    def button_down(self, button: str) -> None:
        _vk, down, _up = BUTTON_EVENTS[button]
        self.wait_ready(f"{button} down")
        if self.dry_run:
            print(f"[dry-run] {button} down")
            return
        send_input(mouse_input(down))
        self.mark_ai_input()

    def button_up(self, button: str) -> None:
        _vk, _down, up = BUTTON_EVENTS[button]
        if self.dry_run:
            print(f"[dry-run] {button} up")
            return
        send_input(mouse_input(up))
        self.mark_ai_input()

    def click(
        self,
        x: int | None,
        y: int | None,
        button: str,
        clicks: int,
        duration_ms: int,
        down_ms: int,
        between_ms: int,
    ) -> None:
        if (x is None) != (y is None):
            raise ValueError("Provide both x and y, or neither.")
        if x is not None and y is not None:
            self.move_to(x, y, duration_ms)
        self.wait_ready(f"{button} click")
        if self.dry_run:
            target = cursor_pos() if x is None or y is None else (x, y)
            print(f"[dry-run] {button} click x{clicks} at {target[0]},{target[1]}")
            return

        _vk, down, up = BUTTON_EVENTS[button]
        for index in range(clicks):
            self.wait_ready(f"{button} click")
            send_input(mouse_input(down))
            self.mark_ai_input()
            if down_ms:
                time.sleep(down_ms / 1000)
            send_input(mouse_input(up))
            self.mark_ai_input()
            if index < clicks - 1 and between_ms:
                time.sleep(between_ms / 1000)

    def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: str,
        duration_ms: int,
    ) -> None:
        self.move_to(start_x, start_y, 0)
        self.wait_ready(f"{button} drag")
        if self.dry_run:
            print(f"[dry-run] {button} drag {start_x},{start_y} -> {end_x},{end_y} over {duration_ms}ms")
            return

        button_vk, down, up = BUTTON_EVENTS[button]
        send_input(mouse_input(down))
        self.mark_ai_input()
        button_is_down = True
        try:
            steps = max(1, duration_ms // self.poll_ms) if duration_ms > 0 else 1
            for step in range(1, steps + 1):
                detail = self.activity_reason(self.initial_idle_ms, ignored_vks={button_vk})
                if detail is not None:
                    send_input(mouse_input(up))
                    self.mark_ai_input()
                    button_is_down = False
                    self.log(f"Paused during {button} drag: {detail}")
                    self.wait_ready(f"resume {button} drag", self.resume_idle_ms)
                    send_input(mouse_input(down))
                    self.mark_ai_input()
                    button_is_down = True

                cx, cy = cursor_pos()
                remaining = max(1, steps - step + 1)
                nx = round(cx + (end_x - cx) / remaining)
                ny = round(cy + (end_y - cy) / remaining)
                set_cursor(nx, ny)
                self.mark_ai_input()
                if duration_ms > 0 and step < steps:
                    time.sleep(self.poll_ms / 1000)
            set_cursor(end_x, end_y)
            self.mark_ai_input()
        finally:
            if button_is_down:
                send_input(mouse_input(up))
                self.mark_ai_input()

    def scroll(self, amount: int, repeats: int, interval_ms: int) -> None:
        for index in range(repeats):
            self.wait_ready(f"scroll {amount}")
            if self.dry_run:
                print(f"[dry-run] scroll {amount}")
            else:
                send_input(mouse_input(MOUSEEVENTF_WHEEL, amount))
                self.mark_ai_input()
            if index < repeats - 1 and interval_ms:
                time.sleep(interval_ms / 1000)

    def press_key(self, key: str) -> None:
        vk = resolve_key(key)
        self.wait_ready(f"key {key}")
        if self.dry_run:
            print(f"[dry-run] key {key}")
            return
        send_input(key_input(vk), key_input(vk, KEYEVENTF_KEYUP))
        self.mark_ai_input()

    def hotkey(self, keys: Iterable[str], hold_ms: int = 20) -> None:
        key_list = list(keys)
        vks = [resolve_key(key) for key in key_list]
        self.wait_ready("hotkey " + "+".join(key_list))
        if self.dry_run:
            print("[dry-run] hotkey " + "+".join(key_list))
            return
        send_input(*(key_input(vk) for vk in vks))
        if hold_ms:
            time.sleep(hold_ms / 1000)
        send_input(*(key_input(vk, KEYEVENTF_KEYUP) for vk in reversed(vks)))
        self.mark_ai_input()

    def type_unicode(self, text: str, interval_ms: int, chunk_size: int) -> None:
        units = utf16_units(text)
        chunk_size = max(1, chunk_size)
        if self.dry_run:
            self.wait_ready(f"type {len(text)} chars")
            print(f"[dry-run] type {text!r}")
            return

        if interval_ms:
            for unit in units:
                self.wait_ready("type char")
                send_input(unicode_input(unit), unicode_input(unit, KEYEVENTF_KEYUP))
                self.mark_ai_input()
                time.sleep(interval_ms / 1000)
            return

        for start in range(0, len(units), chunk_size):
            self.wait_ready("type chunk")
            chunk = units[start:start + chunk_size]
            items: list[INPUT] = []
            for unit in chunk:
                items.append(unicode_input(unit))
                items.append(unicode_input(unit, KEYEVENTF_KEYUP))
            send_input(*items)
            self.mark_ai_input()

    def paste_text(self, text: str, restore_clipboard: bool, post_ms: int) -> None:
        self.wait_ready(f"paste {len(text)} chars")
        if self.dry_run:
            print(f"[dry-run] paste {text!r}")
            return
        previous = clipboard_text() if restore_clipboard else None
        if restore_clipboard and previous is None and clipboard_format_count() > 0:
            raise RuntimeError(
                "Clipboard contains non-text data and cannot be safely restored after paste. "
                "Use Unicode typing or pass --no-restore-clipboard if overwriting the clipboard is acceptable."
            )
        set_clipboard_text(text)
        try:
            self.hotkey(["ctrl", "v"])
            if post_ms:
                self.interruptible_sleep(post_ms)
        finally:
            if restore_clipboard and previous is not None:
                set_clipboard_text(previous)


class ForegroundRestorer:
    def __init__(self, enabled: bool, verbose: bool, dry_run: bool) -> None:
        self.enabled = enabled
        self.verbose = verbose
        self.dry_run = dry_run
        self.hwnd = user32.GetForegroundWindow() if enabled else None
        self.info: dict[str, Any] | None = None
        if self.hwnd:
            try:
                self.info = window_info(self.hwnd)
            except OSError:
                self.info = None

    def restore(self, guard: HumanPriorityGuard | None = None) -> None:
        if not self.enabled or not self.hwnd or not user32.IsWindow(self.hwnd):
            return
        if hwnd_int(user32.GetForegroundWindow()) == hwnd_int(self.hwnd):
            return
        title = self.info["title"] if self.info else str(hwnd_int(self.hwnd))
        if self.dry_run:
            print(f"[dry-run] restore foreground {title!r}")
            return
        if guard:
            guard.wait_ready("restore foreground")
        ok = activate_window(self.hwnd)
        if self.verbose:
            print(f"Restored foreground {title!r}: {ok}", file=sys.stderr)


def save_screenshot(path: str, hwnd: int | None = None) -> str:
    try:
        from PIL import ImageGrab
    except Exception as exc:
        raise RuntimeError("Screenshot requires Pillow/PIL in the active Python environment.") from exc

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    bbox = None
    if hwnd:
        left, top, right, bottom = window_rect(hwnd)
        bbox = (left, top, right, bottom)
    image = ImageGrab.grab(bbox=bbox)
    image.save(path)
    return path


def powershell_executable() -> str:
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("PowerShell is required for UI Automation commands.")


def ps_bool_arg(enabled: bool) -> str | None:
    return "$true" if enabled else None


def uia_command_args(
    command_name: str,
    hwnd: int | None = None,
    name: str | None = None,
    automation_id: str | None = None,
    control_type: str | None = None,
    class_name: str | None = None,
    text: str | None = None,
    regex: bool = False,
    index: int = 0,
    max_depth: int = 8,
    limit: int = 80,
    include_offscreen: bool = False,
    value: str | None = None,
    horizontal_amount: str | None = None,
    vertical_amount: str | None = None,
    dry_run: bool = False,
) -> list[str]:
    if not UIA_SCRIPT.exists():
        raise FileNotFoundError(f"Missing UI Automation helper: {UIA_SCRIPT}")
    args = [
        powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(UIA_SCRIPT),
        command_name,
        "-Hwnd",
        str(int(hwnd or 0)),
        "-Index",
        str(index),
        "-MaxDepth",
        str(max_depth),
        "-Limit",
        str(limit),
    ]
    optional_pairs = [
        ("-Name", name),
        ("-AutomationId", automation_id),
        ("-ControlType", control_type),
        ("-ClassName", class_name),
        ("-Text", text),
        ("-Value", value),
        ("-HorizontalAmount", horizontal_amount),
        ("-VerticalAmount", vertical_amount),
    ]
    for flag, item in optional_pairs:
        if item is not None:
            args.extend([flag, str(item)])
    if regex:
        args.append("-Regex")
    if include_offscreen:
        args.append("-IncludeOffscreen")
    if dry_run:
        args.append("-DryRun")
    return args


def parse_uia_output(process: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    output = (process.stdout or "").strip()
    if not output:
        output = (process.stderr or "").strip()
    try:
        data = json.loads(output) if output else {}
    except json.JSONDecodeError:
        data = {
            "status": "error",
            "error": output or "UI Automation command produced no JSON output.",
        }
    if process.returncode != 0:
        if data.get("status") != "error":
            data["status"] = "error"
        if process.stderr and process.stderr.strip():
            data.setdefault("stderr", process.stderr.strip())
        raise RuntimeError(json_text(data))
    return data


def run_uia_command(
    command_name: str,
    hwnd: int | None = None,
    name: str | None = None,
    automation_id: str | None = None,
    control_type: str | None = None,
    class_name: str | None = None,
    text: str | None = None,
    regex: bool = False,
    index: int = 0,
    max_depth: int = 8,
    limit: int = 80,
    include_offscreen: bool = False,
    value: str | None = None,
    horizontal_amount: str | None = None,
    vertical_amount: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    process = subprocess.run(
        uia_command_args(
            command_name,
            hwnd=hwnd,
            name=name,
            automation_id=automation_id,
            control_type=control_type,
            class_name=class_name,
            text=text,
            regex=regex,
            index=index,
            max_depth=max_depth,
            limit=limit,
            include_offscreen=include_offscreen,
            value=value,
            horizontal_amount=horizontal_amount,
            vertical_amount=vertical_amount,
            dry_run=dry_run,
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return parse_uia_output(process)


def hwnd_for_uia(args_or_action: argparse.Namespace | dict[str, Any]) -> int | None:
    if isinstance(args_or_action, argparse.Namespace):
        if getattr(args_or_action, "hwnd", None):
            return int(args_or_action.hwnd)
        title = getattr(args_or_action, "title", None)
        class_name = getattr(args_or_action, "window_class", None)
        if title or class_name:
            info = find_window(
                title,
                class_name,
                bool(getattr(args_or_action, "window_exact", False)),
                bool(getattr(args_or_action, "window_regex", False)),
            )
            return int(info["hwnd"])
        return None
    if args_or_action.get("hwnd"):
        return int(args_or_action["hwnd"])
    title = args_or_action.get("window_title", args_or_action.get("title"))
    window_class = args_or_action.get("window_class", args_or_action.get("window_class_name"))
    if title or window_class:
        info = find_window(
            title,
            window_class,
            bool(args_or_action.get("window_exact", args_or_action.get("exact", False))),
            bool(args_or_action.get("window_regex", False)),
        )
        return int(info["hwnd"])
    return None


def uia_result_artifact(review: ReviewSession | None, result: dict[str, Any], label: str) -> None:
    if not review:
        return
    result_path = review.evidence_dir / f"uia-{safe_filename(label, 'action')}-{int(time.time() * 1000)}.json"
    write_json(result_path, result)
    review.add_artifact(result_path, "uia", label)


def collect_status(monitor: HumanInputMonitor, restore_foreground: bool, dry_run: bool) -> dict[str, Any]:
    x, y = cursor_pos()
    fg = user32.GetForegroundWindow()
    physical_tick, physical_event = monitor.snapshot()
    return {
        "platform": "Windows",
        "timestamp": iso_now(),
        "screen": {"width": user32.GetSystemMetrics(0), "height": user32.GetSystemMetrics(1)},
        "cursor": {"x": x, "y": y},
        "last_input_idle_ms": idle_ms(),
        "human_physical_input_idle_ms": tick_elapsed(physical_tick) if physical_tick else None,
        "human_physical_last_event": physical_event or None,
        "pressed_keys": pressed_keys(),
        "foreground": window_info(fg) if fg else None,
        "hooks": {"enabled": monitor.enabled, "installed": monitor.installed, "error": monitor.error},
        "restore_foreground": bool(restore_foreground),
        "dry_run": dry_run,
    }


class ReviewSession:
    def __init__(self, path: Path, create_dirs: bool = True) -> None:
        self.path = path
        self.evidence_dir = path / "evidence"
        self.events_path = path / "events.jsonl"
        self.notes_path = path / "notes.jsonl"
        self.manifest_path = path / "manifest.json"
        self.report_path = path / "report.md"
        if create_dirs:
            self.path.mkdir(parents=True, exist_ok=True)
            self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self._load_manifest()

    @classmethod
    def create(
        cls,
        root: Path,
        objective: str,
        target: dict[str, Any] | None,
        mode: str = "ai-pre-review",
    ) -> "ReviewSession":
        timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        slug_source = objective or (target or {}).get("title") or "desktop-review"
        review_id = f"{timestamp}-{safe_filename(slug_source, 'desktop-review')}-{uuid.uuid4().hex[:8]}"
        session = cls(root / review_id)
        session.manifest.update({
            "id": review_id,
            "created_at": iso_now(),
            "updated_at": iso_now(),
            "objective": objective,
            "mode": mode,
            "status": "pending_ai_pre_review",
            "target": target,
            "requires_human_final_review": True,
            "ai_pre_review": None,
            "human_final_review": None,
            "artifacts": [],
        })
        session.save_manifest()
        session.event("review_created", {"objective": objective, "target": target})
        return session

    @classmethod
    def open(cls, path: str | Path | None) -> "ReviewSession | None":
        if not path:
            return None
        review_path = expand_path(path)
        if not (review_path / "manifest.json").exists():
            raise FileNotFoundError(f"Review directory is missing manifest.json: {review_path}")
        return cls(review_path)

    def _load_manifest(self) -> dict[str, Any]:
        if self.manifest_path.exists():
            try:
                return json.loads(self.manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {"id": self.path.name, "manifest_error": "invalid json"}
        return {"id": self.path.name}

    def save_manifest(self) -> None:
        self.manifest["updated_at"] = iso_now()
        write_json(self.manifest_path, self.manifest)

    def event(self, kind: str, data: dict[str, Any] | None = None, status: str = "ok") -> None:
        record = {
            "timestamp": iso_now(),
            "kind": kind,
            "status": status,
            "data": data or {},
        }
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def add_artifact(self, path: str | Path, kind: str, label: str) -> None:
        artifact_path = Path(path)
        try:
            rel = str(artifact_path.relative_to(self.path))
        except ValueError:
            rel = str(artifact_path)
        artifacts = self.manifest.setdefault("artifacts", [])
        artifacts.append({
            "kind": kind,
            "label": label,
            "path": rel,
            "created_at": iso_now(),
        })
        self.save_manifest()

    def note(self, author: str, status: str, summary: str, details: str = "", recommendation: str = "") -> None:
        record = {
            "timestamp": iso_now(),
            "author": author,
            "status": status,
            "summary": summary,
            "details": details,
            "recommendation": recommendation,
        }
        with self.notes_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        if author == "ai":
            self.manifest["ai_pre_review"] = record
            self.manifest["status"] = "pending_human_final_review"
        elif author == "human":
            self.manifest["human_final_review"] = record
            self.manifest["status"] = f"human_final_{status}"
        self.save_manifest()
        self.event("review_note", {"author": author, "status": status, "summary": summary})

    def render_report(self) -> None:
        lines = [
            "# Desktop Review",
            "",
            f"- Review ID: `{self.manifest.get('id', self.path.name)}`",
            f"- Objective: {self.manifest.get('objective') or '(not specified)'}",
            f"- Status: `{self.manifest.get('status', 'unknown')}`",
            f"- Created: {self.manifest.get('created_at', '')}",
            f"- Updated: {self.manifest.get('updated_at', '')}",
            f"- Requires Human Final Review: {self.manifest.get('requires_human_final_review', True)}",
            "",
            "## Target",
            "",
            "```json",
            json.dumps(self.manifest.get("target"), ensure_ascii=False, indent=2),
            "```",
            "",
            "## Evidence",
            "",
        ]
        artifacts = self.manifest.get("artifacts", [])
        if artifacts:
            for artifact in artifacts:
                lines.append(f"- `{artifact.get('kind')}` {artifact.get('label')}: `{artifact.get('path')}`")
        else:
            lines.append("- No artifacts recorded.")

        lines.extend(["", "## AI Pre-Review", ""])
        ai = self.manifest.get("ai_pre_review")
        if ai:
            lines.extend([
                f"- Status: `{ai.get('status')}`",
                f"- Summary: {ai.get('summary')}",
                f"- Recommendation: {ai.get('recommendation') or '(none)'}",
                "",
                ai.get("details") or "",
            ])
        else:
            lines.append("Pending. AI should inspect the evidence and append a note with `review-note --author ai`.")

        lines.extend(["", "## Human Final Review", ""])
        human = self.manifest.get("human_final_review")
        if human:
            lines.extend([
                f"- Decision: `{human.get('status')}`",
                f"- Summary: {human.get('summary')}",
                "",
                human.get("details") or "",
            ])
        else:
            lines.append("Pending. Human final decision must be recorded before treating this review as complete.")

        lines.extend([
            "",
            "## Event Log",
            "",
            f"- Full event log: `{self.events_path.name}`",
            f"- Notes log: `{self.notes_path.name}`",
            "",
        ])
        self.report_path.write_text("\n".join(lines), encoding="utf-8")


def resolve_optional_window_from_args(args: argparse.Namespace) -> dict[str, Any] | None:
    if getattr(args, "title", None) or getattr(args, "class_name", None):
        return resolve_window_from_args(args)
    return None


def foreground_info() -> dict[str, Any] | None:
    hwnd = user32.GetForegroundWindow()
    return window_info(hwnd) if hwnd else None


def refresh_window(info: dict[str, Any] | None) -> dict[str, Any] | None:
    if not info:
        return None
    hwnd = info.get("hwnd")
    if hwnd and user32.IsWindow(hwnd):
        try:
            return window_info(hwnd)
        except OSError:
            return info
    return info


def review_root(path_value: str | None) -> Path:
    return expand_path(path_value) if path_value else DEFAULT_REVIEW_ROOT


def create_review_session_from_args(
    args: argparse.Namespace,
    guard: HumanPriorityGuard,
    restorer: ForegroundRestorer,
) -> ReviewSession:
    target = resolve_optional_window_from_args(args) or foreground_info()
    session = ReviewSession.create(review_root(args.root), args.objective, target)

    status_path = session.evidence_dir / "status.json"
    write_json(status_path, collect_status(guard.monitor, args.restore_foreground, args.dry_run))
    session.add_artifact(status_path, "json", "desktop status")

    windows_path = session.evidence_dir / "windows.json"
    write_json(windows_path, enum_visible_windows())
    session.add_artifact(windows_path, "json", "visible windows")

    if not args.no_screenshot:
        screenshot_target = target
        screenshot_path = session.evidence_dir / "target.png"
        if args.dry_run:
            session.event("screenshot_skipped", {"path": str(screenshot_path), "reason": "dry-run"})
        else:
            if screenshot_target and not args.no_activate:
                guard.wait_ready("activate review target for screenshot")
                activate_window(screenshot_target["hwnd"])
                screenshot_target = refresh_window(screenshot_target)
            save_screenshot(str(screenshot_path), screenshot_target["hwnd"] if screenshot_target else None)
            session.add_artifact(screenshot_path, "screenshot", "target window" if screenshot_target else "full screen")

    session.manifest["target"] = refresh_window(target)
    session.event("evidence_collected", {"artifacts": len(session.manifest.get("artifacts", []))})
    session.render_report()
    return session


def add_review_note_from_args(args: argparse.Namespace) -> ReviewSession:
    session = ReviewSession.open(args.review_dir)
    if session is None:
        raise ValueError("--review-dir is required.")
    details = read_text_value(args.details, args.details_file)
    recommendation = read_text_value(args.recommendation, args.recommendation_file)
    session.note(args.author, args.status, args.summary, details, recommendation)
    session.render_report()
    return session


def finalize_review_from_args(args: argparse.Namespace) -> ReviewSession:
    session = ReviewSession.open(args.review_dir)
    if session is None:
        raise ValueError("--review-dir is required.")
    session.note("human", args.decision, args.summary, read_text_value(args.details, args.details_file), "")
    session.render_report()
    return session


def assert_window_from_args(args: argparse.Namespace, review: ReviewSession | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "assertion": "window",
        "timestamp": iso_now(),
        "expected": {
            "title": args.title,
            "class_name": args.class_name,
            "exact": args.exact,
            "regex": args.regex,
            "foreground": args.foreground,
            "min_width": args.min_width,
            "min_height": args.min_height,
        },
        "passed": False,
        "window": None,
        "reason": "",
    }
    if not args.title and not args.class_name:
        result["reason"] = "expected --title or --class-name"
    else:
        try:
            info = resolve_window_from_args(args)
        except Exception as exc:
            result["reason"] = str(exc)
        else:
            rect = info["rect"]
            foreground_matches = True
            if args.foreground:
                foreground_matches = hwnd_int(user32.GetForegroundWindow()) == hwnd_int(info["hwnd"])
            size_matches = rect["width"] >= args.min_width and rect["height"] >= args.min_height
            result["window"] = info
            result["passed"] = bool(foreground_matches and size_matches)
            if not foreground_matches:
                result["reason"] = "matched window is not foreground"
            elif not size_matches:
                result["reason"] = "matched window is smaller than required"
            else:
                result["reason"] = "matched"

    if review:
        review.event("assert_window", result, "pass" if result["passed"] else "fail")
        assertion_path = review.evidence_dir / f"assert-window-{int(time.time() * 1000)}.json"
        write_json(assertion_path, result)
        review.add_artifact(assertion_path, "assertion", "window assertion")
        review.render_report()
    return result


def review_response(session: ReviewSession) -> dict[str, Any]:
    return {
        "review_dir": str(session.path),
        "manifest": str(session.manifest_path),
        "report": str(session.report_path),
        "status": session.manifest.get("status"),
        "requires_human_final_review": session.manifest.get("requires_human_final_review", True),
    }


def summarize_action(action: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key, value in action.items():
        if key == "text":
            summary["text_length"] = len(str(value))
        else:
            summary[key] = value
    return summary


def record_plan_result(review: ReviewSession | None, result: dict[str, Any]) -> None:
    if not review:
        return
    result_path = review.evidence_dir / f"plan-result-{int(time.time() * 1000)}.json"
    write_json(result_path, result)
    review.add_artifact(result_path, "json", "plan execution result")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--idle-ms", dest="initial_idle_ms", type=int, default=250, help="Initial human idle threshold before AI acts.")
    parser.add_argument("--resume-idle-ms", type=int, default=3000, help="After human input, resume only after this much idle time.")
    parser.add_argument("--poll-ms", type=int, default=25, help="Human-priority guard polling interval.")
    parser.add_argument("--cursor-tolerance-px", type=int, default=8, help="Cursor drift before pausing.")
    parser.add_argument("--timeout-ms", type=int, default=None, help="Optional guard wait timeout.")
    parser.add_argument("--move-duration-ms", type=int, default=0, help="Default pointer move duration. Zero is fastest.")
    parser.add_argument("--click-down-ms", type=int, default=20, help="Mouse button hold time for clicks.")
    parser.add_argument("--double-click-ms", type=int, default=55, help="Delay between double-click clicks.")
    parser.add_argument("--text-chunk-size", type=int, default=32, help="Unicode input units per fast typing batch.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without sending input.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print guard wait details.")
    parser.add_argument("--no-hooks", dest="hooks", action="store_false", default=True, help="Disable low-level physical input hooks.")
    restore = parser.add_mutually_exclusive_group()
    restore.add_argument("--restore-foreground", dest="restore_foreground", action="store_true", default=True, help="Restore the starting foreground window on exit.")
    restore.add_argument("--no-restore-foreground", dest="restore_foreground", action="store_false", help="Leave the last activated window in front.")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Print cursor, screen, foreground, and input state as JSON.")

    windows = sub.add_parser("windows", help="List visible windows.")
    windows.add_argument("--filter", default=None, help="Case-insensitive title/class substring filter.")
    windows.add_argument("--limit", type=int, default=30)

    foreground = sub.add_parser("foreground", help="Print current foreground window as JSON.")
    foreground.add_argument("--screenshot", default=None, help="Optional path to save a foreground screenshot.")

    sub.add_parser("wait-idle", help="Wait until the human-priority guard clears.")

    activate = sub.add_parser("activate", help="Activate a visible window by title/class.")
    add_window_match_args(activate)

    move = sub.add_parser("move", help="Move the cursor.")
    move.add_argument("--x", type=int, required=True)
    move.add_argument("--y", type=int, required=True)
    move.add_argument("--duration-ms", type=int)

    click = sub.add_parser("click", help="Click at a screen coordinate or current cursor.")
    click.add_argument("--x", type=int)
    click.add_argument("--y", type=int)
    click.add_argument("--button", choices=["left", "right", "middle"], default="left")
    click.add_argument("--clicks", type=int, default=1)
    click.add_argument("--duration-ms", type=int)

    double_click = sub.add_parser("double-click", help="Double-click at a coordinate or current cursor.")
    double_click.add_argument("--x", type=int)
    double_click.add_argument("--y", type=int)
    double_click.add_argument("--button", choices=["left", "right", "middle"], default="left")
    double_click.add_argument("--duration-ms", type=int)

    drag = sub.add_parser("drag", help="Drag from one screen coordinate to another.")
    drag.add_argument("--from", dest="start", nargs=2, type=int, required=True, metavar=("X", "Y"))
    drag.add_argument("--to", dest="end", nargs=2, type=int, required=True, metavar=("X", "Y"))
    drag.add_argument("--button", choices=["left", "right", "middle"], default="left")
    drag.add_argument("--duration-ms", type=int, default=250)

    click_window = sub.add_parser("click-window", help="Activate a window and click inside it.")
    add_window_match_args(click_window)
    point = click_window.add_mutually_exclusive_group(required=True)
    point.add_argument("--point", nargs=2, type=int, metavar=("X", "Y"), help="Window-relative physical pixel point.")
    point.add_argument("--ratio", nargs=2, type=float, metavar=("RX", "RY"), help="Window-relative ratio point from 0.0 to 1.0.")
    click_window.add_argument("--button", choices=["left", "right", "middle"], default="left")
    click_window.add_argument("--clicks", type=int, default=1)
    click_window.add_argument("--duration-ms", type=int)

    drag_window = sub.add_parser("drag-window", help="Activate a window and drag inside it.")
    add_window_match_args(drag_window)
    start_group = drag_window.add_mutually_exclusive_group(required=True)
    start_group.add_argument("--from-point", nargs=2, type=int, metavar=("X", "Y"))
    start_group.add_argument("--from-ratio", nargs=2, type=float, metavar=("RX", "RY"))
    end_group = drag_window.add_mutually_exclusive_group(required=True)
    end_group.add_argument("--to-point", nargs=2, type=int, metavar=("X", "Y"))
    end_group.add_argument("--to-ratio", nargs=2, type=float, metavar=("RX", "RY"))
    drag_window.add_argument("--button", choices=["left", "right", "middle"], default="left")
    drag_window.add_argument("--duration-ms", type=int, default=250)

    key = sub.add_parser("key", help="Press one key.")
    key.add_argument("key")

    hotkey = sub.add_parser("hotkey", help="Press a key combination.")
    hotkey.add_argument("--keys", nargs="+", required=True)
    hotkey.add_argument("--hold-ms", type=int, default=20)

    type_cmd = sub.add_parser("type", help="Type Unicode text, optionally via clipboard paste.")
    type_cmd.add_argument("--text", required=True)
    type_cmd.add_argument("--method", choices=["unicode", "paste"], default="unicode")
    type_cmd.add_argument("--interval-ms", type=int, default=0)
    type_cmd.add_argument("--chunk-size", type=int)
    type_cmd.add_argument("--no-restore-clipboard", dest="restore_clipboard", action="store_false", default=True)

    paste = sub.add_parser("paste", help="Paste text through the clipboard and Ctrl+V.")
    paste.add_argument("--text", required=True)
    paste.add_argument("--post-ms", type=int, default=50)
    paste.add_argument("--no-restore-clipboard", dest="restore_clipboard", action="store_false", default=True)

    scroll = sub.add_parser("scroll", help="Scroll the mouse wheel.")
    scroll.add_argument("--amount", type=int, required=True, help="Positive scrolls up, negative scrolls down.")
    scroll.add_argument("--repeats", type=int, default=1)
    scroll.add_argument("--interval-ms", type=int, default=25)

    sleep_cmd = sub.add_parser("sleep", help="Human-priority sleep.")
    sleep_cmd.add_argument("--ms", type=int, required=True)

    screenshot = sub.add_parser("screenshot", help="Save a screenshot of a window or the full screen.")
    screenshot.add_argument("--path", required=True)
    add_window_match_args(screenshot, required=False)

    review = sub.add_parser("review", help="Create an AI pre-review session and collect desktop evidence.")
    review.add_argument("--objective", required=True, help="What the AI should inspect before human final review.")
    review.add_argument("--root", default=None, help="Review root directory. Defaults to %%USERPROFILE%%\\.codex\\desktop-reviews.")
    add_window_match_args(review, required=False)
    review.add_argument("--no-screenshot", action="store_true", help="Skip screenshot evidence.")
    review.add_argument("--no-activate", action="store_true", help="Do not activate the matched target before screenshot evidence.")

    review_note = sub.add_parser("review-note", help="Append an AI or human note to a review session.")
    review_note.add_argument("--review-dir", required=True)
    review_note.add_argument("--author", choices=["ai", "human"], default="ai")
    review_note.add_argument("--status", required=True, help="Short status such as pass, fail, needs_changes, or blocked.")
    review_note.add_argument("--summary", required=True)
    review_note.add_argument("--details", default="")
    review_note.add_argument("--details-file", default=None)
    review_note.add_argument("--recommendation", default="")
    review_note.add_argument("--recommendation-file", default=None)

    finalize_review = sub.add_parser("finalize-review", help="Record the human final decision for a review session.")
    finalize_review.add_argument("--review-dir", required=True)
    finalize_review.add_argument("--decision", choices=["approved", "rejected", "needs_changes", "blocked"], required=True)
    finalize_review.add_argument("--summary", required=True)
    finalize_review.add_argument("--details", default="")
    finalize_review.add_argument("--details-file", default=None)

    assert_window = sub.add_parser("assert-window", help="Assert that a target window exists and optionally matches foreground/size requirements.")
    add_window_match_args(assert_window)
    assert_window.add_argument("--foreground", action="store_true", help="Require the matched window to be foreground.")
    assert_window.add_argument("--min-width", type=int, default=1)
    assert_window.add_argument("--min-height", type=int, default=1)
    assert_window.add_argument("--review-dir", default=None, help="Optional review session to receive assertion evidence.")
    assert_window.add_argument("--fail-on-miss", action="store_true", help="Exit non-zero when the assertion fails.")

    uia_status = sub.add_parser("uia-status", help="Verify Windows UI Automation availability.")
    uia_status.add_argument("--review-dir", default=None)

    uia_tree = sub.add_parser("uia-tree", help="Dump the UI Automation control tree for a window or the desktop root.")
    add_uia_scope_args(uia_tree)
    add_uia_tree_args(uia_tree)
    uia_tree.add_argument("--review-dir", default=None)

    uia_find = sub.add_parser("uia-find", help="Find controls by UI Automation properties.")
    add_uia_scope_args(uia_find)
    add_uia_query_args(uia_find)
    uia_find.add_argument("--review-dir", default=None)

    uia_assert = sub.add_parser("uia-assert", help="Assert that a matching UI Automation control exists.")
    add_uia_scope_args(uia_assert)
    add_uia_query_args(uia_assert)
    uia_assert.add_argument("--review-dir", default=None)
    uia_assert.add_argument("--fail-on-miss", action="store_true", help="Exit non-zero when no matching control exists.")

    uia_click = sub.add_parser("uia-click", help="Click the clickable point or center of a matched UI Automation control.")
    add_uia_scope_args(uia_click)
    add_uia_query_args(uia_click)
    uia_click.add_argument("--button", choices=["left", "right", "middle"], default="left")
    uia_click.add_argument("--clicks", type=int, default=1)
    uia_click.add_argument("--duration-ms", type=int)
    uia_click.add_argument("--review-dir", default=None)

    uia_invoke = sub.add_parser("uia-invoke", help="Invoke a matched UI Automation control using InvokePattern.")
    add_uia_scope_args(uia_invoke)
    add_uia_query_args(uia_invoke)
    uia_invoke.add_argument("--review-dir", default=None)

    uia_set_value = sub.add_parser("uia-set-value", help="Set a matched UI Automation control value using ValuePattern.")
    add_uia_scope_args(uia_set_value)
    add_uia_query_args(uia_set_value)
    uia_set_value.add_argument("--value", required=True)
    uia_set_value.add_argument("--review-dir", default=None)

    for parser_name, help_text in [
        ("uia-toggle", "Toggle a matched UI Automation control using TogglePattern."),
        ("uia-select", "Select a matched UI Automation control using SelectionItemPattern."),
        ("uia-expand", "Expand a matched UI Automation control using ExpandCollapsePattern."),
        ("uia-collapse", "Collapse a matched UI Automation control using ExpandCollapsePattern."),
        ("uia-focus", "Focus a matched UI Automation control."),
    ]:
        uia_parser = sub.add_parser(parser_name, help=help_text)
        add_uia_scope_args(uia_parser)
        add_uia_query_args(uia_parser)
        uia_parser.add_argument("--review-dir", default=None)

    uia_scroll = sub.add_parser("uia-scroll", help="Scroll a matched UI Automation control using ScrollPattern.")
    add_uia_scope_args(uia_scroll)
    add_uia_query_args(uia_scroll)
    uia_scroll.add_argument("--horizontal-amount", choices=["LargeIncrement", "LargeDecrement", "SmallIncrement", "SmallDecrement", "NoAmount"], default="NoAmount")
    uia_scroll.add_argument("--vertical-amount", choices=["LargeIncrement", "LargeDecrement", "SmallIncrement", "SmallDecrement", "NoAmount"], default="NoAmount")
    uia_scroll.add_argument("--review-dir", default=None)

    plan = sub.add_parser("plan", help="Run a JSON action plan.")
    plan.add_argument("--review-dir", default=None, help="Optional review session directory for plan event logging.")
    plan.add_argument("path")

    return parser


def add_window_match_args(parser: argparse.ArgumentParser, required: bool = False) -> None:
    parser.add_argument("--title", required=required, help="Window title substring by default.")
    parser.add_argument("--class-name", help="Window class substring by default.")
    parser.add_argument("--exact", action="store_true", help="Match title/class exactly.")
    parser.add_argument("--regex", action="store_true", help="Treat --title as a regular expression.")


def add_uia_scope_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--hwnd", type=int, default=0, help="Target window handle. Defaults to the desktop root.")
    parser.add_argument("--title", default=None, help="Target window title substring.")
    parser.add_argument("--window-class", dest="window_class", default=None, help="Target window class substring.")
    parser.add_argument("--window-exact", action="store_true", help="Match the target window title/class exactly.")
    parser.add_argument("--window-regex", action="store_true", help="Treat the target window title as a regular expression.")


def add_uia_tree_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-depth", type=int, default=8)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--include-offscreen", action="store_true")


def add_uia_query_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name", default=None, help="Control Name property substring.")
    parser.add_argument("--automation-id", default=None, help="Control AutomationId property substring.")
    parser.add_argument("--control-type", default=None, help="Control type such as Button, Edit, MenuItem, ListItem, TabItem.")
    parser.add_argument("--uia-class-name", dest="uia_class_name", default=None, help="Control ClassName property substring.")
    parser.add_argument("--text", default=None, help="Search across common UI Automation text properties.")
    parser.add_argument("--regex", action="store_true", help="Treat control text matchers as regular expressions.")
    parser.add_argument("--index", type=int, default=0, help="Zero-based index when multiple controls match.")
    add_uia_tree_args(parser)


def resolve_window_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return find_window(args.title, args.class_name, args.exact, args.regex)


def window_point(info: dict[str, Any], action: dict[str, Any] | argparse.Namespace) -> tuple[int, int]:
    rect = info["rect"]
    left = rect["left"]
    top = rect["top"]
    width = rect["width"]
    height = rect["height"]

    if isinstance(action, argparse.Namespace):
        if getattr(action, "ratio", None) is not None:
            rx, ry = action.ratio
            return left + round(width * rx), top + round(height * ry)
        x, y = action.point
        return left + x, top + y

    if "ratio" in action:
        rx, ry = action["ratio"]
        return left + round(width * float(rx)), top + round(height * float(ry))
    if "rx" in action and "ry" in action:
        return left + round(width * float(action["rx"])), top + round(height * float(action["ry"]))
    return left + int(action["x"]), top + int(action["y"])


def relative_window_point(
    info: dict[str, Any],
    point: Iterable[int] | None = None,
    ratio: Iterable[float] | None = None,
) -> tuple[int, int]:
    rect = info["rect"]
    left = rect["left"]
    top = rect["top"]
    width = rect["width"]
    height = rect["height"]
    if ratio is not None:
        rx, ry = ratio
        return left + round(width * float(rx)), top + round(height * float(ry))
    if point is not None:
        x, y = point
        return left + int(x), top + int(y)
    raise ValueError("Expected either a point or a ratio.")


def uia_query_from_action(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": action.get("name"),
        "automation_id": action.get("automation_id"),
        "control_type": action.get("control_type"),
        "class_name": action.get("class_name"),
        "text": action.get("text_query", action.get("text")),
        "regex": bool(action.get("regex", False)),
        "index": int(action.get("index", 0)),
        "max_depth": int(action.get("max_depth", 8)),
        "limit": int(action.get("limit", 80)),
        "include_offscreen": bool(action.get("include_offscreen", False)),
    }


def uia_query_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "name": getattr(args, "name", None),
        "automation_id": getattr(args, "automation_id", None),
        "control_type": getattr(args, "control_type", None),
        "class_name": getattr(args, "uia_class_name", None),
        "text": getattr(args, "text", None),
        "regex": bool(getattr(args, "regex", False)),
        "index": int(getattr(args, "index", 0)),
        "max_depth": int(getattr(args, "max_depth", 8)),
        "limit": int(getattr(args, "limit", 80)),
        "include_offscreen": bool(getattr(args, "include_offscreen", False)),
    }


def find_uia_target(hwnd: int | None, query: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    limit = max(int(query.get("limit", 80)), int(query.get("index", 0)) + 1)
    result = run_uia_command(
        "find",
        hwnd=hwnd,
        name=query.get("name"),
        automation_id=query.get("automation_id"),
        control_type=query.get("control_type"),
        class_name=query.get("class_name"),
        text=query.get("text"),
        regex=bool(query.get("regex", False)),
        index=int(query.get("index", 0)),
        max_depth=int(query.get("max_depth", 8)),
        limit=limit,
        include_offscreen=bool(query.get("include_offscreen", False)),
        dry_run=dry_run,
    )
    matches = result.get("matches", [])
    index = int(query.get("index", 0))
    if len(matches) <= index:
        raise ValueError(f"No UI Automation element matched the query at index {index}. Matched {len(matches)} element(s).")
    return matches[index]


def point_from_uia_element(element: dict[str, Any]) -> tuple[int, int]:
    point = element.get("clickable_point")
    if point:
        return int(point["x"]), int(point["y"])
    rect = element.get("rect") or {}
    width = int(rect.get("width", 0))
    height = int(rect.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("Matched UI Automation element has no clickable point or usable bounds.")
    return int(rect["left"] + width / 2), int(rect["top"] + height / 2)


def activate_for_uia(hwnd: int | None, guard: HumanPriorityGuard, dry_run: bool) -> None:
    if not hwnd:
        return
    guard.wait_ready("activate window for UI Automation")
    if dry_run:
        print(f"[dry-run] activate window hwnd={hwnd} for UI Automation")
    else:
        activate_window(hwnd)


def run_uia_action_from_data(
    action_name: str,
    action: dict[str, Any],
    guard: HumanPriorityGuard,
    defaults: argparse.Namespace,
    review: ReviewSession | None = None,
) -> dict[str, Any]:
    hwnd = hwnd_for_uia(action)
    activate_for_uia(hwnd, guard, defaults.dry_run)
    query = uia_query_from_action(action)

    if action_name == "uia_click":
        target = find_uia_target(hwnd, query, defaults.dry_run)
        x, y = point_from_uia_element(target)
        guard.click(
            x,
            y,
            action.get("button", "left"),
            int(action.get("clicks", 1)),
            int(action.get("duration_ms", defaults.move_duration_ms)),
            defaults.click_down_ms,
            defaults.double_click_ms,
        )
        result = {
            "status": "ok" if not defaults.dry_run else "dry-run",
            "command": "uia-click",
            "hwnd": hwnd,
            "target": target,
            "resolved_point": {"x": x, "y": y},
        }
        uia_result_artifact(review, result, "uia-click")
        return result

    command_map = {
        "uia_invoke": "invoke",
        "uia_set_value": "set-value",
        "uia_toggle": "toggle",
        "uia_select": "select",
        "uia_expand": "expand",
        "uia_collapse": "collapse",
        "uia_focus": "focus",
        "uia_scroll": "scroll",
    }
    command_name = command_map[action_name]
    guard.wait_ready(f"UI Automation {command_name}")
    result = run_uia_command(
        command_name,
        hwnd=hwnd,
        name=query.get("name"),
        automation_id=query.get("automation_id"),
        control_type=query.get("control_type"),
        class_name=query.get("class_name"),
        text=query.get("text"),
        regex=bool(query.get("regex", False)),
        index=int(query.get("index", 0)),
        max_depth=int(query.get("max_depth", 8)),
        limit=int(query.get("limit", 80)),
        include_offscreen=bool(query.get("include_offscreen", False)),
        value=action.get("value"),
        horizontal_amount=action.get("horizontal_amount"),
        vertical_amount=action.get("vertical_amount"),
        dry_run=defaults.dry_run,
    )
    uia_result_artifact(review, result, command_name)
    return result


def run_uia_command_from_args(
    command_name: str,
    args: argparse.Namespace,
    guard: HumanPriorityGuard,
    review: ReviewSession | None = None,
) -> dict[str, Any]:
    hwnd = hwnd_for_uia(args)
    if command_name not in {"status", "tree", "find", "assert"}:
        activate_for_uia(hwnd, guard, args.dry_run)
        guard.wait_ready(f"UI Automation {command_name}")
    query = uia_query_from_args(args)
    result = run_uia_command(
        command_name,
        hwnd=hwnd,
        name=query.get("name"),
        automation_id=query.get("automation_id"),
        control_type=query.get("control_type"),
        class_name=query.get("class_name"),
        text=query.get("text"),
        regex=bool(query.get("regex", False)),
        index=int(query.get("index", 0)),
        max_depth=int(query.get("max_depth", 8)),
        limit=int(query.get("limit", 80)),
        include_offscreen=bool(query.get("include_offscreen", False)),
        value=getattr(args, "value", None),
        horizontal_amount=getattr(args, "horizontal_amount", None),
        vertical_amount=getattr(args, "vertical_amount", None),
        dry_run=args.dry_run,
    )
    uia_result_artifact(review, result, command_name)
    return result


def run_uia_click_from_args(args: argparse.Namespace, guard: HumanPriorityGuard, review: ReviewSession | None = None) -> dict[str, Any]:
    hwnd = hwnd_for_uia(args)
    activate_for_uia(hwnd, guard, args.dry_run)
    target = find_uia_target(hwnd, uia_query_from_args(args), args.dry_run)
    x, y = point_from_uia_element(target)
    guard.click(
        x,
        y,
        args.button,
        args.clicks,
        args.duration_ms if args.duration_ms is not None else args.move_duration_ms,
        args.click_down_ms,
        args.double_click_ms,
    )
    result = {
        "status": "ok" if not args.dry_run else "dry-run",
        "command": "uia-click",
        "hwnd": hwnd,
        "target": target,
        "resolved_point": {"x": x, "y": y},
    }
    uia_result_artifact(review, result, "uia-click")
    return result


def run_plan(
    path: str,
    guard: HumanPriorityGuard,
    defaults: argparse.Namespace,
    restorer: ForegroundRestorer,
    review: ReviewSession | None = None,
) -> dict[str, Any]:
    plan_path = expand_path(path)
    with plan_path.open("r", encoding="utf-8") as handle:
        actions = json.load(handle)
    if not isinstance(actions, list):
        raise ValueError("Plan must be a JSON list.")

    result: dict[str, Any] = {
        "plan": str(plan_path),
        "started_at": iso_now(),
        "dry_run": defaults.dry_run,
        "action_count": len(actions),
        "actions": [],
        "status": "running",
    }
    if review:
        review.event("plan_started", {"path": str(plan_path), "action_count": len(actions), "dry_run": defaults.dry_run})

    try:
        for index, action in enumerate(actions, start=1):
            if not isinstance(action, dict):
                raise ValueError(f"Action {index} must be an object.")
            name = action.get("action")
            action_record: dict[str, Any] = {
                "index": index,
                "action": name,
                "started_at": iso_now(),
                "input": summarize_action(action),
            }
            action_started = time.perf_counter()
            if review:
                review.event("plan_action_started", action_record)

            try:
                if name == "move":
                    guard.move_to(int(action["x"]), int(action["y"]), int(action.get("duration_ms", defaults.move_duration_ms)))
                elif name == "click":
                    guard.click(
                        action.get("x"),
                        action.get("y"),
                        action.get("button", "left"),
                        int(action.get("clicks", 1)),
                        int(action.get("duration_ms", defaults.move_duration_ms)),
                        defaults.click_down_ms,
                        defaults.double_click_ms,
                    )
                elif name == "double_click":
                    guard.click(
                        action.get("x"),
                        action.get("y"),
                        action.get("button", "left"),
                        2,
                        int(action.get("duration_ms", defaults.move_duration_ms)),
                        defaults.click_down_ms,
                        defaults.double_click_ms,
                    )
                elif name == "drag":
                    start = action.get("from", action.get("start"))
                    end = action.get("to", action.get("end"))
                    if not start or not end:
                        raise ValueError(f"Drag action {index} requires from/start and to/end points.")
                    guard.drag(
                        int(start[0]),
                        int(start[1]),
                        int(end[0]),
                        int(end[1]),
                        action.get("button", "left"),
                        int(action.get("duration_ms", 250)),
                    )
                elif name == "click_window":
                    info = find_window(action.get("title"), action.get("class_name"), bool(action.get("exact", False)), bool(action.get("regex", False)))
                    guard.wait_ready("activate window")
                    if not defaults.dry_run:
                        activate_window(info["hwnd"])
                        info = refresh_window(info) or info
                    x, y = window_point(info, action)
                    action_record["resolved_point"] = {"x": x, "y": y}
                    action_record["window"] = info
                    guard.click(x, y, action.get("button", "left"), int(action.get("clicks", 1)), int(action.get("duration_ms", defaults.move_duration_ms)), defaults.click_down_ms, defaults.double_click_ms)
                elif name == "drag_window":
                    info = find_window(action.get("title"), action.get("class_name"), bool(action.get("exact", False)), bool(action.get("regex", False)))
                    guard.wait_ready("activate window")
                    if not defaults.dry_run:
                        activate_window(info["hwnd"])
                        info = refresh_window(info) or info
                    start = relative_window_point(info, action.get("from_point"), action.get("from_ratio"))
                    end = relative_window_point(info, action.get("to_point"), action.get("to_ratio"))
                    action_record["resolved_start"] = {"x": start[0], "y": start[1]}
                    action_record["resolved_end"] = {"x": end[0], "y": end[1]}
                    action_record["window"] = info
                    guard.drag(start[0], start[1], end[0], end[1], action.get("button", "left"), int(action.get("duration_ms", 250)))
                elif name == "activate":
                    info = find_window(action.get("title"), action.get("class_name"), bool(action.get("exact", False)), bool(action.get("regex", False)))
                    guard.wait_ready("activate window")
                    if defaults.dry_run:
                        print(f"[dry-run] activate {info['title']!r}")
                    else:
                        activate_window(info["hwnd"])
                        info = refresh_window(info) or info
                    action_record["window"] = info
                elif name == "type":
                    method = action.get("method", "unicode")
                    if method == "paste":
                        guard.paste_text(str(action["text"]), bool(action.get("restore_clipboard", True)), int(action.get("post_ms", 50)))
                    else:
                        guard.type_unicode(str(action["text"]), int(action.get("interval_ms", 0)), int(action.get("chunk_size", defaults.text_chunk_size)))
                elif name == "paste":
                    guard.paste_text(str(action["text"]), bool(action.get("restore_clipboard", True)), int(action.get("post_ms", 50)))
                elif name == "key":
                    guard.press_key(str(action["key"]))
                elif name == "hotkey":
                    guard.hotkey(action["keys"], int(action.get("hold_ms", 20)))
                elif name == "scroll":
                    guard.scroll(int(action["amount"]), int(action.get("repeats", 1)), int(action.get("interval_ms", 25)))
                elif name == "sleep":
                    guard.interruptible_sleep(int(action.get("ms", 0)))
                elif name == "screenshot":
                    info = None
                    if action.get("title") or action.get("class_name"):
                        info = find_window(action.get("title"), action.get("class_name"), bool(action.get("exact", False)), bool(action.get("regex", False)))
                    screenshot_path = expand_path(str(action["path"]))
                    if defaults.dry_run:
                        print(f"[dry-run] screenshot {str(screenshot_path)!r}")
                    else:
                        if info:
                            guard.wait_ready("activate window for screenshot")
                            activate_window(info["hwnd"])
                            info = refresh_window(info) or info
                        save_screenshot(str(screenshot_path), info["hwnd"] if info else None)
                        if review:
                            review.add_artifact(screenshot_path, "screenshot", f"plan action {index} screenshot")
                    action_record["path"] = str(screenshot_path)
                    action_record["window"] = info
                elif name == "uia_tree":
                    hwnd = hwnd_for_uia(action)
                    result_uia = run_uia_command(
                        "tree",
                        hwnd=hwnd,
                        max_depth=int(action.get("max_depth", 8)),
                        limit=int(action.get("limit", 80)),
                        include_offscreen=bool(action.get("include_offscreen", False)),
                        dry_run=defaults.dry_run,
                    )
                    action_record["uia"] = result_uia
                    uia_result_artifact(review, result_uia, "tree")
                elif name == "uia_find":
                    hwnd = hwnd_for_uia(action)
                    query = uia_query_from_action(action)
                    result_uia = run_uia_command(
                        "find",
                        hwnd=hwnd,
                        name=query.get("name"),
                        automation_id=query.get("automation_id"),
                        control_type=query.get("control_type"),
                        class_name=query.get("class_name"),
                        text=query.get("text"),
                        regex=bool(query.get("regex", False)),
                        index=int(query.get("index", 0)),
                        max_depth=int(query.get("max_depth", 8)),
                        limit=int(query.get("limit", 80)),
                        include_offscreen=bool(query.get("include_offscreen", False)),
                        dry_run=defaults.dry_run,
                    )
                    action_record["uia"] = result_uia
                    uia_result_artifact(review, result_uia, "find")
                elif name == "uia_assert":
                    hwnd = hwnd_for_uia(action)
                    query = uia_query_from_action(action)
                    result_uia = run_uia_command(
                        "assert",
                        hwnd=hwnd,
                        name=query.get("name"),
                        automation_id=query.get("automation_id"),
                        control_type=query.get("control_type"),
                        class_name=query.get("class_name"),
                        text=query.get("text"),
                        regex=bool(query.get("regex", False)),
                        index=int(query.get("index", 0)),
                        max_depth=int(query.get("max_depth", 8)),
                        limit=1,
                        include_offscreen=bool(query.get("include_offscreen", False)),
                        dry_run=defaults.dry_run,
                    )
                    action_record["uia"] = result_uia
                    uia_result_artifact(review, result_uia, "assert")
                    if action.get("fail_on_miss", True) and not result_uia.get("passed"):
                        raise AssertionError("UI Automation assertion failed.")
                elif name == "uia_click":
                    action_record["uia"] = run_uia_action_from_data(name, action, guard, defaults, review)
                elif name in UIA_ACTIONS:
                    action_record["uia"] = run_uia_action_from_data(name, action, guard, defaults, review)
                elif name == "restore_foreground":
                    restorer.restore(guard)
                else:
                    raise ValueError(f"Unsupported action {name!r} at item {index}.")
            except Exception as exc:
                action_record["status"] = "error"
                action_record["error"] = str(exc)
                action_record["duration_ms"] = round((time.perf_counter() - action_started) * 1000)
                result["actions"].append(action_record)
                if review:
                    review.event("plan_action_failed", action_record, "fail")
                raise

            action_record["status"] = "ok"
            action_record["duration_ms"] = round((time.perf_counter() - action_started) * 1000)
            action_record["completed_at"] = iso_now()
            result["actions"].append(action_record)
            if review:
                review.event("plan_action_completed", action_record)

    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        result["completed_at"] = iso_now()
        if review:
            record_plan_result(review, result)
            review.event("plan_failed", {"path": str(plan_path), "error": str(exc)}, "fail")
            review.render_report()
        raise

    result["status"] = "ok"
    result["completed_at"] = iso_now()
    if review:
        record_plan_result(review, result)
        review.event("plan_completed", {"path": str(plan_path), "action_count": len(actions)})
        review.render_report()
    return result


def dispatch(args: argparse.Namespace, guard: HumanPriorityGuard, restorer: ForegroundRestorer) -> int:
    if args.command == "status":
        print_json(collect_status(guard.monitor, args.restore_foreground, args.dry_run))
    elif args.command == "windows":
        rows = enum_visible_windows()
        if args.filter:
            needle = args.filter.lower()
            rows = [row for row in rows if needle in row["title"].lower() or needle in row["class"].lower()]
        print_json(rows[:args.limit])
    elif args.command == "foreground":
        hwnd = user32.GetForegroundWindow()
        info = window_info(hwnd) if hwnd else None
        if args.screenshot and hwnd:
            save_screenshot(args.screenshot, hwnd)
        print_json(info)
    elif args.command == "wait-idle":
        guard.wait_ready("wait-idle", guard.resume_idle_ms)
        print_json({"status": "clear"})
    elif args.command == "activate":
        info = resolve_window_from_args(args)
        guard.wait_ready("activate window")
        if args.dry_run:
            print_json({"activated": False, "dry_run": True, "window": info})
        else:
            ok = activate_window(info["hwnd"])
            print_json({"activated": ok, "window": refresh_window(info) or info})
    elif args.command == "move":
        guard.move_to(args.x, args.y, args.duration_ms if args.duration_ms is not None else args.move_duration_ms)
    elif args.command == "click":
        guard.click(args.x, args.y, args.button, args.clicks, args.duration_ms if args.duration_ms is not None else args.move_duration_ms, args.click_down_ms, args.double_click_ms)
    elif args.command == "double-click":
        guard.click(args.x, args.y, args.button, 2, args.duration_ms if args.duration_ms is not None else args.move_duration_ms, args.click_down_ms, args.double_click_ms)
    elif args.command == "drag":
        guard.drag(args.start[0], args.start[1], args.end[0], args.end[1], args.button, args.duration_ms)
    elif args.command == "click-window":
        info = resolve_window_from_args(args)
        guard.wait_ready("activate window")
        if not args.dry_run:
            activate_window(info["hwnd"])
            info = refresh_window(info) or info
        x, y = window_point(info, args)
        guard.click(x, y, args.button, args.clicks, args.duration_ms if args.duration_ms is not None else args.move_duration_ms, args.click_down_ms, args.double_click_ms)
    elif args.command == "drag-window":
        info = resolve_window_from_args(args)
        guard.wait_ready("activate window")
        if not args.dry_run:
            activate_window(info["hwnd"])
            info = refresh_window(info) or info
        start = relative_window_point(info, args.from_point, args.from_ratio)
        end = relative_window_point(info, args.to_point, args.to_ratio)
        guard.drag(start[0], start[1], end[0], end[1], args.button, args.duration_ms)
    elif args.command == "key":
        guard.press_key(args.key)
    elif args.command == "hotkey":
        guard.hotkey(args.keys, args.hold_ms)
    elif args.command == "type":
        if args.method == "paste":
            guard.paste_text(args.text, args.restore_clipboard, 50)
        else:
            guard.type_unicode(args.text, args.interval_ms, args.chunk_size if args.chunk_size is not None else args.text_chunk_size)
    elif args.command == "paste":
        guard.paste_text(args.text, args.restore_clipboard, args.post_ms)
    elif args.command == "scroll":
        guard.scroll(args.amount, args.repeats, args.interval_ms)
    elif args.command == "sleep":
        guard.interruptible_sleep(args.ms)
    elif args.command == "screenshot":
        info = resolve_window_from_args(args) if args.title or args.class_name else None
        if args.dry_run:
            print(f"[dry-run] screenshot {args.path!r}")
        else:
            if info:
                guard.wait_ready("activate window for screenshot")
                activate_window(info["hwnd"])
                info = refresh_window(info) or info
            save_screenshot(args.path, info["hwnd"] if info else None)
            print_json({"path": args.path, "window": info})
    elif args.command == "review":
        session = create_review_session_from_args(args, guard, restorer)
        print_json(review_response(session))
    elif args.command == "review-note":
        session = add_review_note_from_args(args)
        print_json(review_response(session))
    elif args.command == "finalize-review":
        session = finalize_review_from_args(args)
        print_json(review_response(session))
    elif args.command == "assert-window":
        review = ReviewSession.open(args.review_dir)
        result = assert_window_from_args(args, review)
        print_json(result)
        if args.fail_on_miss and not result["passed"]:
            return 1
    elif args.command == "uia-status":
        review = ReviewSession.open(args.review_dir)
        result = run_uia_command("status", dry_run=args.dry_run)
        uia_result_artifact(review, result, "status")
        print_json(result)
    elif args.command == "uia-tree":
        review = ReviewSession.open(args.review_dir)
        result = run_uia_command_from_args("tree", args, guard, review)
        print_json(result)
    elif args.command == "uia-find":
        review = ReviewSession.open(args.review_dir)
        result = run_uia_command_from_args("find", args, guard, review)
        print_json(result)
    elif args.command == "uia-assert":
        review = ReviewSession.open(args.review_dir)
        result = run_uia_command_from_args("assert", args, guard, review)
        print_json(result)
        if args.fail_on_miss and not result.get("passed"):
            return 1
    elif args.command == "uia-click":
        review = ReviewSession.open(args.review_dir)
        result = run_uia_click_from_args(args, guard, review)
        print_json(result)
    elif args.command in UIA_CLI_COMMANDS:
        review = ReviewSession.open(args.review_dir)
        result = run_uia_command_from_args(UIA_CLI_COMMANDS[args.command], args, guard, review)
        print_json(result)
    elif args.command == "plan":
        review = ReviewSession.open(args.review_dir)
        result = run_plan(args.path, guard, args, restorer, review)
        print_json(result)
    else:
        raise ValueError(f"Unhandled command {args.command!r}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    monitor = HumanInputMonitor(enabled=args.hooks and not args.dry_run, verbose=args.verbose)
    monitor.start()
    guard = HumanPriorityGuard(
        initial_idle_ms=args.initial_idle_ms,
        resume_idle_ms=args.resume_idle_ms,
        poll_ms=args.poll_ms,
        cursor_tolerance_px=args.cursor_tolerance_px,
        timeout_ms=args.timeout_ms,
        verbose=args.verbose,
        dry_run=args.dry_run,
        monitor=monitor,
    )
    restorer = ForegroundRestorer(enabled=args.restore_foreground, verbose=args.verbose, dry_run=args.dry_run)
    try:
        exit_code = dispatch(args, guard, restorer)
    finally:
        try:
            restorer.restore(guard)
        finally:
            monitor.stop()
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print_json({"status": "interrupted"})
        raise SystemExit(130)
    except Exception as exc:
        print_json({
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        })
        raise SystemExit(1)
