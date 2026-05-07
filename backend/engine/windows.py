import base64
import os
from datetime import datetime

import psutil
import pyautogui
import pygetwindow as gw


def _desktop_path() -> str:
    return os.path.join(os.path.expanduser("~"), "Desktop")


def take_screenshot() -> dict:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{timestamp}.jpg"
    desktop = _desktop_path()
    if not os.path.isdir(desktop):
        desktop = os.getcwd()
    path = os.path.join(desktop, filename)

    img = pyautogui.screenshot()
    img.save(path, "JPEG", quality=85)

    with open(path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    return {
        "text": "Screenshot saved to desktop",
        "image_b64": image_b64,
        "path": path,
    }


def get_system_info(query: str) -> str:
    q = query.lower()

    if "cpu" in q:
        pct = psutil.cpu_percent(interval=1)
        return f"CPU is at {pct}%"

    if "ram" in q or "memory" in q:
        mem = psutil.virtual_memory()
        used = mem.used / (1024 ** 3)
        total = mem.total / (1024 ** 3)
        return f"RAM: {used:.1f} GB used of {total:.1f} GB ({mem.percent}%)"

    if "disk" in q or "storage" in q or "drive" in q:
        try:
            disk = psutil.disk_usage("C:\\")
        except Exception:
            disk = psutil.disk_usage("/")
        free = disk.free / (1024 ** 3)
        total = disk.total / (1024 ** 3)
        return f"C drive: {free:.0f} GB free of {total:.0f} GB"

    if "battery" in q:
        batt = psutil.sensors_battery()
        if batt is None:
            return "No battery detected"
        status = "plugged in" if batt.power_plugged else "on battery"
        return f"Battery at {batt.percent:.0f}%, {status}"

    # All metrics
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    try:
        disk = psutil.disk_usage("C:\\")
    except Exception:
        disk = psutil.disk_usage("/")
    batt = psutil.sensors_battery()

    lines = [
        f"CPU: {cpu}%",
        f"RAM: {mem.used / (1024**3):.1f} GB used of {mem.total / (1024**3):.1f} GB",
        f"Disk C: {disk.free / (1024**3):.0f} GB free",
    ]
    if batt:
        lines.append(f"Battery: {batt.percent:.0f}%")
    return "\n".join(lines)


def _find_window(app: str):
    titles = gw.getAllTitles()
    for title in titles:
        if app.lower() in title.lower():
            wins = gw.getWindowsWithTitle(title)
            if wins:
                return wins[0], title
    return None, None


def minimize_window(query: str) -> str:
    app = query.lower().replace("minimize", "").strip()
    win, _ = _find_window(app)
    if win is None:
        return "Window not found"
    win.minimize()
    return f"Minimized {app}"


def maximize_window(query: str) -> str:
    app = query.lower().replace("maximize", "").strip()
    win, _ = _find_window(app)
    if win is None:
        return "Window not found"
    win.maximize()
    return f"Maximized {app}"


def focus_window(query: str) -> str:
    app = query.lower().replace("switch to", "").replace("focus", "").strip()
    win, _ = _find_window(app)
    if win is None:
        return "Window not found"
    win.activate()
    return f"Switched to {app}"
