import os
import re
import webbrowser
from urllib.parse import quote_plus

import pyautogui
from backend.db.database import SessionLocal
from backend.db.models import SysCommand, WebCommand, Contact
from backend.engine.helper import extract_yt_term

_SEARCH_TRIGGERS = (
    "search web", "search browser", "open google search",
    "search on google", "google it",
)
_MESSAGE_TRIGGERS = ("send message", "send sms", "whatsapp message")


def classify_command(query: str) -> str:
    q = query.lower().strip()
    if any(t in q for t in _SEARCH_TRIGGERS):
        return "search"
    if q.startswith("open "):
        return "open"
    if "close " in q:
        return "close"
    if "on youtube" in q:
        return "youtube"
    if any(t in q for t in _MESSAGE_TRIGGERS):
        return "message"
    if "ai status" in q or "api status" in q or "assistant status" in q:
        return "status"
    return "ai"


def _clean(query: str, remove: str) -> str:
    return query.lower().replace(remove, "").strip()


def open_command(query: str) -> str:
    app = _clean(query, "open")
    db = SessionLocal()
    try:
        row = db.query(SysCommand).filter(SysCommand.name.ilike(app)).first()
        if row:
            os.startfile(row.path)
            return f"Opening {app}"
        row = db.query(WebCommand).filter(WebCommand.name.ilike(app)).first()
        if row:
            webbrowser.open(row.url)
            return f"Opening {app}"
    finally:
        db.close()
    os.system(f"start {app}")
    return f"Opening {app}"


def close_command(query: str) -> str:
    try:
        import pygetwindow as gw
        app = _clean(query, "close")
        windows = gw.getAllTitles()
        for title in windows:
            if app in title.lower():
                wins = gw.getWindowsWithTitle(title)
                if wins:
                    wins[0].close()
                    return f"Closed {app}"
        os.system(f"taskkill /f /im {app}.exe")
        return f"Closed {app}"
    except Exception as e:
        return f"Could not close: {e}"


def web_search(query: str) -> str:
    q = query.lower()
    for t in _SEARCH_TRIGGERS:
        q = q.replace(t, "")
    q = q.strip()
    url = "https://www.google.com/search?q=" + quote_plus(q)
    webbrowser.open(url)
    return f"Searching {q}"


def play_youtube(query: str) -> str:
    term = extract_yt_term(query)
    if term:
        url = "https://www.youtube.com/results?search_query=" + quote_plus(term)
        webbrowser.open(url)
        return f"Playing {term} on YouTube"
    return "Could not extract YouTube search term"


def find_contact(query: str):
    db = SessionLocal()
    try:
        contacts = db.query(Contact).all()
        for c in contacts:
            if c.name.lower() in query.lower():
                mobile = c.mobile_no.strip()
                if not mobile.startswith("+"):
                    mobile = "+91" + re.sub(r"[^\d]", "", mobile)
                return mobile, c.name
        return None, None
    finally:
        db.close()


def send_whatsapp(mobile: str, message: str, name: str) -> str:
    import subprocess, time
    encoded = quote_plus(message)
    url = f"whatsapp://send?phone={mobile}&text={encoded}"
    subprocess.run(f'start "" "{url}"', shell=True)
    time.sleep(5)
    pyautogui.press("enter")
    return f"Message sent to {name}"


def run_command(query: str, session_id: int):
    intent = classify_command(query)
    try:
        if intent == "open":
            return open_command(query), False
        if intent == "close":
            return close_command(query), False
        if intent == "search":
            return web_search(query), False
        if intent == "youtube":
            return play_youtube(query), False
        if intent == "message":
            mobile, name = find_contact(query)
            if mobile:
                return send_whatsapp(mobile, query, name), False
            return "Contact not found", False
        if intent == "status":
            return "Groq AI is configured and ready", False
    except Exception as e:
        return f"Command failed: {e}", False
    return "", True
