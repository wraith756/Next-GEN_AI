# Next Gen AI — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the JARVIS assistant from Eel + plain HTML to FastAPI + Next.js + Groq, preserving the exact visual design, all SQLite data, and face authentication.

**Architecture:** FastAPI on port 8000 serves WebSocket + REST. Next.js on port 3000 pixel-perfectly recreates the existing UI. Backend-first: port all Python engine logic before building the frontend. A single `run.py` launches both.

**Tech Stack:** Python 3.10+, FastAPI, uvicorn, groq SDK, SQLAlchemy 2.x, pydantic-settings, pyttsx3, PyAudio, openwakeword, DeepFace, OpenCV, PyAutoGUI, PyGetWindow, psutil; Next.js 14, TypeScript, Bootstrap 5, siriwave npm package, lottie-react

---

## File Map

| File | Role |
|---|---|
| `backend/engine/config.py` | Pydantic Settings — GROQ_API_KEY, model names, assistant name |
| `backend/db/database.py` | SQLAlchemy engine + session factory |
| `backend/db/models.py` | All 7 table models (4 existing + 3 new) |
| `backend/engine/helper.py` | Copied from `engine/helper.py` (keep only used functions) |
| `backend/engine/ai.py` | Groq dual-model routing + session history + compression |
| `backend/engine/voice.py` | pyttsx3 TTS (thread-safe) + Groq Whisper STT |
| `backend/engine/automation.py` | Command classifier + actions (open/close/search/youtube/whatsapp) |
| `backend/engine/face_auth.py` | DeepFace verify wrapper |
| `backend/engine/hotword.py` | OpenWakeWord background thread + wake callback registry |
| `backend/api/ws.py` | WebSocket hub — message dispatch, wake broadcast, audio pipeline |
| `backend/api/auth.py` | `POST /api/auth/face` |
| `backend/api/sessions.py` | CRUD `/api/sessions` and `/api/sessions/{id}/messages` |
| `backend/api/settings.py` | Profile, contacts, sys/web commands CRUD |
| `backend/main.py` | FastAPI app — mounts routers, starts hotword thread on startup |
| `frontend/styles/globals.css` | Exact port of `www/style.css` |
| `frontend/pages/_app.tsx` | Bootstrap CSS/JS import |
| `frontend/next.config.js` | Proxy `/api` → `localhost:8000` |
| `frontend/hooks/useWebSocket.ts` | WS connection, message dispatch, reconnect |
| `frontend/hooks/useVoice.ts` | MediaRecorder capture, send binary audio over WS |
| `frontend/hooks/useSession.ts` | Active session state, tab list management |
| `frontend/components/JarvisHUD.tsx` | Animated SVG rings (pixel-perfect port from index.html:39–248) |
| `frontend/components/FaceAuthOverlay.tsx` | Lottie animations (Loader → FaceAuth → Success → Greet) |
| `frontend/components/SiriWave.tsx` | siriwave ios9 style wrapper |
| `frontend/components/SessionTabs.tsx` | Tab bar (create/rename/delete sessions) |
| `frontend/components/ChatInput.tsx` | Text input + mic button + send button |
| `frontend/components/SettingsModal.tsx` | Bootstrap modal: profile, commands, contacts |
| `frontend/pages/index.tsx` | Startup page — shows FaceAuthOverlay, calls POST /api/auth/face |
| `frontend/pages/assistant.tsx` | JARVIS HUD page — assembles all components |
| `run.py` | Launches uvicorn + next start + opens browser |
| `requirements.txt` | 15 clean deps |
| `tests/test_ai.py` | route_model, compress_history logic |
| `tests/test_automation.py` | classify_command |
| `tests/test_sessions_api.py` | REST CRUD via FastAPI TestClient |

---

## Task 1: Scaffold & Cleanup

**Files:**
- Delete: `www/`, `main.py`, `device.bat`, `engine/command.py`, `engine/features.py`, `engine/db.py`
- Create: `backend/`, `backend/api/`, `backend/engine/`, `backend/db/`, `tests/`, `frontend/`
- Move: `engine/auth/` → `backend/engine/auth/`, `engine/helper.py` → `backend/engine/helper.py`
- Create: `requirements.txt`

- [ ] **Step 1: Create directory structure**

```powershell
New-Item -ItemType Directory -Force -Path backend/api, backend/engine, backend/db, tests
$null = New-Item -ItemType File -Force -Path backend/__init__.py, backend/api/__init__.py, backend/engine/__init__.py, backend/db/__init__.py, tests/__init__.py
```

- [ ] **Step 2: Move preserved assets**

```powershell
Copy-Item -Recurse engine/auth backend/engine/auth
Copy-Item engine/helper.py backend/engine/helper.py
```

- [ ] **Step 3: Delete old files**

```powershell
Remove-Item -Recurse -Force www, engine
Remove-Item -Force main.py, device.bat
```

- [ ] **Step 4: Write clean requirements.txt**

```
fastapi
uvicorn[standard]
groq
sqlalchemy
pydantic-settings
pyttsx3
pyaudio
openwakeword
deepface
opencv-python
pyautogui
pygetwindow
psutil
python-multipart
websockets
markdown2
beautifulsoup4
```

- [ ] **Step 5: Install backend deps**

```powershell
pip install -r requirements.txt
```

Expected: all packages install without error. DeepFace pulls TensorFlow as a transitive dep (~3 min).

- [ ] **Step 6: Scaffold Next.js frontend**

```powershell
npx create-next-app@14 frontend --typescript --no-tailwind --no-eslint --no-src-dir --no-app --import-alias "@/*"
```

Expected: `frontend/` created with `pages/`, `public/`, `styles/`.

- [ ] **Step 7: Install frontend deps**

```powershell
cd frontend; npm install bootstrap bootstrap-icons siriwave lottie-react; cd ..
```

- [ ] **Step 8: Commit scaffold**

```powershell
git add -A
git commit -m "chore: scaffold FastAPI + Next.js structure, remove Eel"
```

---

## Task 2: Database Layer

**Files:**
- Create: `backend/db/database.py`
- Create: `backend/db/models.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_db.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base, SysCommand, ChatSession, ChatMessage, SessionSummary

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()

def test_sys_command_crud(session):
    cmd = SysCommand(name="notepad", path="C:/Windows/notepad.exe")
    session.add(cmd)
    session.commit()
    result = session.query(SysCommand).filter_by(name="notepad").first()
    assert result.path == "C:/Windows/notepad.exe"

def test_chat_session_with_messages(session):
    sess = ChatSession(title="Chat #1")
    session.add(sess)
    session.commit()
    msg = ChatMessage(session_id=sess.id, role="user", content="hello")
    session.add(msg)
    session.commit()
    assert session.query(ChatMessage).filter_by(session_id=sess.id).count() == 1

def test_session_summary(session):
    sess = ChatSession(title="Chat #1")
    session.add(sess)
    session.commit()
    summary = SessionSummary(session_id=sess.id, summary="User asked about AI.", message_count=10)
    session.add(summary)
    session.commit()
    assert session.query(SessionSummary).filter_by(session_id=sess.id).first().message_count == 10
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/test_db.py -v
```

Expected: `ImportError: cannot import name 'Base' from 'backend.db.models'`

- [ ] **Step 3: Write `backend/db/models.py`**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SysCommand(Base):
    __tablename__ = "sys_command"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    path = Column(Text)


class WebCommand(Base):
    __tablename__ = "web_command"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    url = Column(Text)


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    mobile_no = Column(Text)
    email = Column(Text)
    address = Column(Text)


class UserInfo(Base):
    __tablename__ = "info"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    designation = Column(Text)
    mobileno = Column(Text)
    email = Column(Text)
    city = Column(Text)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True)
    title = Column(Text, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role = Column(Text)  # "user" | "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class SessionSummary(Base):
    __tablename__ = "session_summaries"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    summary = Column(Text)
    message_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 4: Write `backend/db/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base

DATABASE_URL = "sqlite:///./jarvis.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: Run tests — expect PASS**

```powershell
python -m pytest tests/test_db.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add backend/db/ tests/test_db.py
git commit -m "feat: SQLAlchemy models + database session (7 tables)"
```

---

## Task 3: Backend Config

**Files:**
- Create: `backend/engine/config.py`

- [ ] **Step 1: Write `backend/engine/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    assistant_name: str = "jarvis"
    groq_api_key: str = ""
    fast_model: str = "llama-3.1-8b-instant"
    smart_model: str = "llama-3.3-70b-versatile"
    whisper_model: str = "whisper-large-v3"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

- [ ] **Step 2: Add GROQ_API_KEY to .env**

Open `.env` and add:
```
GROQ_API_KEY=your_groq_api_key_here
ASSISTANT_NAME=jarvis
```

- [ ] **Step 3: Verify import works**

```powershell
python -c "from backend.engine.config import settings; print(settings.fast_model)"
```

Expected: `llama-3.1-8b-instant`

- [ ] **Step 4: Commit**

```powershell
git add backend/engine/config.py .env
git commit -m "feat: Pydantic Settings config (Groq models + API key)"
```

---

## Task 4: AI Engine

**Files:**
- Create: `backend/engine/ai.py`
- Create: `tests/test_ai.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_ai.py`:

```python
from unittest.mock import MagicMock, patch
from backend.engine.ai import route_model, compress_history


def test_route_short_query_uses_fast_model():
    assert route_model("open chrome") == "llama-3.1-8b-instant"


def test_route_complex_query_uses_smart_model():
    result = route_model("why is machine learning so powerful and how does it work")
    assert result == "llama-3.3-70b-versatile"


def test_route_9_words_no_question_uses_fast():
    result = route_model("play some music on youtube please now today here")
    assert result == "llama-3.1-8b-instant"


def test_route_8_words_with_question_word_uses_fast():
    # ≤ 8 words always uses fast even with question word
    result = route_model("how are you doing today")
    assert result == "llama-3.1-8b-instant"


def test_compress_history_calls_groq():
    messages = [
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language."},
    ] * 5
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = "User asked about Python."
    with patch("backend.engine.ai._client", mock_client):
        result = compress_history(messages)
    assert result == "User asked about Python."
    mock_client.chat.completions.create.assert_called_once()
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/test_ai.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `backend/engine/ai.py`**

```python
import json
from groq import Groq
from backend.engine.config import settings
from backend.db.database import SessionLocal
from backend.db.models import ChatMessage, SessionSummary

QUESTION_WORDS = {
    "why", "how", "explain", "what is", "analyze",
    "write", "compare", "describe", "tell me about",
}

_client = Groq(api_key=settings.groq_api_key)


def route_model(query: str) -> str:
    words = query.lower().split()
    if len(words) > 8 and any(w in query.lower() for w in QUESTION_WORDS):
        return settings.smart_model
    return settings.fast_model


def compress_history(messages: list[dict]) -> str:
    lines = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    prompt = f"Summarize this conversation in 2-3 sentences, preserving key facts:\n\n{lines}"
    resp = _client.chat.completions.create(
        model=settings.fast_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    return resp.choices[0].message.content


def _build_context(session_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        summary = (
            db.query(SessionSummary)
            .filter_by(session_id=session_id)
            .order_by(SessionSummary.id.desc())
            .first()
        )
        summarized_count = summary.message_count if summary else 0

        messages = (
            db.query(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.id.asc())
            .offset(summarized_count)
            .all()
        )
        context: list[dict] = []
        if summary:
            context.append({"role": "user", "content": f"Previous context: {summary.summary}"})
            context.append({"role": "assistant", "content": "Understood."})
        context.extend({"role": m.role, "content": m.content} for m in messages)
        return context, len(messages)
    finally:
        db.close()


def _maybe_compress(session_id: int, total_new: int):
    if total_new < 10:
        return
    db = SessionLocal()
    try:
        summary = (
            db.query(SessionSummary)
            .filter_by(session_id=session_id)
            .order_by(SessionSummary.id.desc())
            .first()
        )
        offset = summary.message_count if summary else 0
        messages = (
            db.query(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.id.asc())
            .offset(offset)
            .all()
        )
        if len(messages) >= 10:
            msg_dicts = [{"role": m.role, "content": m.content} for m in messages]
            new_summary = compress_history(msg_dicts)
            db.add(SessionSummary(
                session_id=session_id,
                summary=new_summary,
                message_count=offset + len(messages),
            ))
            db.commit()
    finally:
        db.close()


def ask(query: str, session_id: int) -> str:
    context, total_new = _build_context(session_id)
    model = route_model(query)
    context.append({"role": "user", "content": query})

    system = (
        f"You are {settings.assistant_name.upper()}, a concise AI assistant. "
        "Give short, direct answers."
    )
    resp = _client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}] + context,
        temperature=0.5,
        max_tokens=250,
    )
    answer = resp.choices[0].message.content
    _maybe_compress(session_id, total_new + 1)
    return answer
```

- [ ] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest tests/test_ai.py -v
```

Expected: 5 tests PASS (compress_history uses mock, no real API call).

- [ ] **Step 5: Commit**

```powershell
git add backend/engine/ai.py tests/test_ai.py
git commit -m "feat: AI engine — dual-model Groq routing + 10-message history compression"
```

---

## Task 5: Voice Engine

**Files:**
- Create: `backend/engine/voice.py`

- [ ] **Step 1: Write `backend/engine/voice.py`**

```python
import io
import threading
import pyttsx3
from groq import Groq
from backend.engine.config import settings

_engine_lock = threading.Lock()
_engine: pyttsx3.Engine | None = None


def _get_engine() -> pyttsx3.Engine:
    global _engine
    if _engine is None:
        _engine = pyttsx3.init("sapi5")
        voices = _engine.getProperty("voices")
        if voices:
            _engine.setProperty("voice", voices[0].id)
        _engine.setProperty("rate", 174)
    return _engine


def speak(text: str) -> None:
    with _engine_lock:
        engine = _get_engine()
        engine.say(str(text))
        engine.runAndWait()


def transcribe(audio_bytes: bytes) -> str:
    client = Groq(api_key=settings.groq_api_key)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.wav"
    result = client.audio.transcriptions.create(
        model=settings.whisper_model,
        file=audio_file,
        language="en",
    )
    return result.text.strip()
```

- [ ] **Step 2: Smoke-test TTS (manual)**

```powershell
python -c "from backend.engine.voice import speak; speak('Hello from Next Gen AI')"
```

Expected: your PC speakers say "Hello from Next Gen AI".

- [ ] **Step 3: Commit**

```powershell
git add backend/engine/voice.py
git commit -m "feat: voice engine — pyttsx3 TTS + Groq Whisper STT"
```

---

## Task 6: Automation Engine

**Files:**
- Create: `backend/engine/automation.py`
- Create: `tests/test_automation.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_automation.py`:

```python
from backend.engine.automation import classify_command


def test_open_command():
    assert classify_command("open chrome") == "open"


def test_close_command():
    assert classify_command("close notepad") == "close"


def test_youtube():
    assert classify_command("play despacito on youtube") == "youtube"


def test_search():
    assert classify_command("search on google python tutorial") == "search"


def test_search_variant():
    assert classify_command("google it what is fastapi") == "search"


def test_message():
    assert classify_command("send message to john") == "message"


def test_status():
    assert classify_command("ai status") == "status"


def test_ai_fallback():
    assert classify_command("what is the meaning of life") == "ai"


def test_open_with_search_word_goes_to_search():
    assert classify_command("open google search") == "search"
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/test_automation.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write `backend/engine/automation.py`**

```python
import os
import re
import webbrowser
from urllib.parse import quote_plus

import pyautogui
import pygetwindow as gw
from backend.db.database import SessionLocal
from backend.db.models import SysCommand, WebCommand, Contact
from backend.engine.helper import extract_yt_term, markdown_to_text

_SEARCH_TRIGGERS = (
    "search web", "search browser", "open google search",
    "search on google", "google it", "search browser",
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
        row = db.query(SysCommand).filter(
            SysCommand.name.ilike(app)
        ).first()
        if row:
            os.startfile(row.path)
            return f"Opening {app}"
        row = db.query(WebCommand).filter(
            WebCommand.name.ilike(app)
        ).first()
        if row:
            webbrowser.open(row.url)
            return f"Opening {app}"
    finally:
        db.close()
    os.system(f"start {app}")
    return f"Opening {app}"


def close_command(query: str) -> str:
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


def web_search(query: str) -> str:
    q = query.lower()
    for t in _SEARCH_TRIGGERS:
        q = q.replace(t, "")
    q = q.strip()
    url = "https://www.google.com/search?q=" + quote_plus(q)
    webbrowser.open(url)
    return f"Searching {q}"


def play_youtube(query: str) -> str:
    import pywhatkit as kit  # lazy import — not in requirements but can be pip-installed
    term = extract_yt_term(query)
    if term:
        kit.playonyt(term)
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


def run_command(query: str, session_id: int) -> tuple[str, bool]:
    """
    Returns (response_text, needs_ai).
    needs_ai=True means caller should forward to ai.ask().
    """
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
    return "", True  # needs_ai
```

- [ ] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest tests/test_automation.py -v
```

Expected: 9 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/engine/automation.py tests/test_automation.py
git commit -m "feat: automation engine — command classifier + open/close/search/youtube/whatsapp"
```

---

## Task 7: Face Auth Engine

**Files:**
- Create: `backend/engine/face_auth.py`

- [ ] **Step 1: Write `backend/engine/face_auth.py`**

```python
import os
import cv2
from deepface import DeepFace

_AUTH_DB = os.path.join(os.path.dirname(__file__), "auth", "database")


def authenticate() -> bool:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False
    try:
        ret, frame = cap.read()
        if not ret:
            return False
        tmp = "/tmp/face_frame.jpg"
        cv2.imwrite(tmp, frame)
        result = DeepFace.find(
            img_path=tmp,
            db_path=_AUTH_DB,
            enforce_detection=False,
            silent=True,
        )
        # result is a list of DataFrames; non-empty means a match was found
        return bool(result and len(result[0]) > 0)
    except Exception:
        return False
    finally:
        cap.release()
```

- [ ] **Step 2: Smoke-test (manual, needs webcam)**

```powershell
python -c "from backend.engine.face_auth import authenticate; print(authenticate())"
```

Expected: `True` if your face is in `backend/engine/auth/database/`, `False` otherwise.

- [ ] **Step 3: Commit**

```powershell
git add backend/engine/face_auth.py
git commit -m "feat: face auth engine — DeepFace verify against stored database"
```

---

## Task 8: Hotword Engine

**Files:**
- Create: `backend/engine/hotword.py`

- [ ] **Step 1: Write `backend/engine/hotword.py`**

```python
import threading
import numpy as np
import pyaudio
from openwakeword.model import Model

_callbacks: list = []
_stop_event = threading.Event()

# Phase 1 uses the built-in "hey_jarvis" model until a custom "Next Gen" model is trained.
# To use a custom model, replace MODEL_PATH with the path to your .onnx file.
MODEL_PATH = "hey_jarvis"


def register_callback(fn) -> None:
    _callbacks.append(fn)


def _fire_callbacks():
    for fn in _callbacks:
        try:
            fn()
        except Exception:
            pass


def start() -> None:
    oww = Model(wakeword_models=[MODEL_PATH], inference_framework="onnx")
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=16000,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=1280,
    )
    try:
        while not _stop_event.is_set():
            audio = stream.read(1280, exception_on_overflow=False)
            audio_np = np.frombuffer(audio, dtype=np.int16)
            prediction = oww.predict(audio_np)
            for score in prediction.values():
                if score > 0.5:
                    print("HOTWORD DETECTED")
                    _fire_callbacks()
                    break
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


def stop() -> None:
    _stop_event.set()
```

- [ ] **Step 2: Verify openwakeword model download**

```powershell
python -c "from openwakeword.model import Model; m = Model(wakeword_models=['hey_jarvis'], inference_framework='onnx'); print('OK')"
```

Expected: `OK` (downloads model on first run ~50MB).

- [ ] **Step 3: Commit**

```powershell
git add backend/engine/hotword.py
git commit -m "feat: hotword engine — OpenWakeWord hey_jarvis, callback registry"
```

---

## Task 9: WebSocket Hub

**Files:**
- Create: `backend/api/ws.py`

- [ ] **Step 1: Write `backend/api/ws.py`**

```python
import asyncio
import json
import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.engine import voice, automation, ai as ai_engine
from backend.db.database import SessionLocal
from backend.db.models import ChatMessage, ChatSession

router = APIRouter()

_connections: list[WebSocket] = []
_loop: asyncio.AbstractEventLoop | None = None


def set_event_loop(loop: asyncio.AbstractEventLoop):
    global _loop
    _loop = loop


def on_wake():
    if _loop and _connections:
        asyncio.run_coroutine_threadsafe(_broadcast({"type": "wake"}), _loop)


async def _broadcast(msg: dict):
    dead = []
    for ws in _connections:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections.remove(ws)


async def _handle_text_command(ws: WebSocket, text: str, session_id: int):
    await ws.send_json({"type": "display", "text": text})
    _save_message(session_id, "user", text)

    response, needs_ai = automation.run_command(text, session_id)
    if needs_ai:
        response = ai_engine.ask(text, session_id)

    from backend.engine.helper import markdown_to_text
    response = markdown_to_text(response)

    threading.Thread(target=voice.speak, args=(response,), daemon=True).start()
    await ws.send_json({"type": "response", "text": response, "session_id": session_id})
    _save_message(session_id, "assistant", response)
    await ws.send_json({"type": "show_hood"})


def _save_message(session_id: int, role: str, content: str):
    db = SessionLocal()
    try:
        db.add(ChatMessage(session_id=session_id, role=role, content=content))
        db.commit()
    finally:
        db.close()


def _get_or_create_default_session() -> int:
    db = SessionLocal()
    try:
        sess = db.query(ChatSession).first()
        if not sess:
            sess = ChatSession(title="Chat #1")
            db.add(sess)
            db.commit()
            db.refresh(sess)
        return sess.id
    finally:
        db.close()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _connections.append(ws)
    try:
        while True:
            data = await ws.receive()
            if "text" in data:
                msg = json.loads(data["text"])
                msg_type = msg.get("type")
                session_id = msg.get("session_id") or _get_or_create_default_session()

                if msg_type == "command":
                    await _handle_text_command(ws, msg["text"], session_id)

            elif "bytes" in data:
                # Binary audio from mic — transcribe then handle as text command
                session_id = _get_or_create_default_session()
                await ws.send_json({"type": "display", "text": "Recognizing..."})
                try:
                    transcript = voice.transcribe(data["bytes"])
                    await ws.send_json({"type": "transcript", "text": transcript})
                    if transcript:
                        await _handle_text_command(ws, transcript, session_id)
                except Exception as e:
                    await ws.send_json({"type": "error", "text": str(e)})

    except WebSocketDisconnect:
        _connections.remove(ws)
```

- [ ] **Step 2: Commit**

```powershell
git add backend/api/ws.py
git commit -m "feat: WebSocket hub — text commands, audio STT pipeline, wake broadcast"
```

---

## Task 10: REST API Endpoints

**Files:**
- Create: `backend/api/auth.py`
- Create: `backend/api/sessions.py`
- Create: `backend/api/settings.py`
- Create: `tests/test_sessions_api.py`

- [ ] **Step 1: Write `backend/api/auth.py`**

```python
from fastapi import APIRouter
from pydantic import BaseModel
from backend.engine import face_auth
from backend.engine import voice

router = APIRouter()


class AuthResult(BaseModel):
    success: bool
    message: str


@router.post("/api/auth/face", response_model=AuthResult)
def face_authenticate():
    success = face_auth.authenticate()
    if success:
        import threading
        threading.Thread(target=voice.speak, args=("Face Authentication Successful. Hello, Welcome Sir.",), daemon=True).start()
        return AuthResult(success=True, message="Authenticated")
    threading.Thread(target=voice.speak, args=("Face Authentication Failed",), daemon=True).start()
    return AuthResult(success=False, message="Authentication failed")
```

- [ ] **Step 2: Write failing tests for sessions**

Create `tests/test_sessions_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base
from backend.db.database import get_db


@pytest.fixture(scope="module")
def client():
    # Use in-memory DB for tests
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    from backend.main import app
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_session(client):
    resp = client.post("/api/sessions", json={"title": "Test Chat"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "Test Chat"
    assert "id" in resp.json()


def test_list_sessions(client):
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_rename_session(client):
    create = client.post("/api/sessions", json={"title": "Old"})
    sid = create.json()["id"]
    resp = client.put(f"/api/sessions/{sid}", json={"title": "New"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"


def test_delete_session(client):
    create = client.post("/api/sessions", json={"title": "ToDelete"})
    sid = create.json()["id"]
    resp = client.delete(f"/api/sessions/{sid}")
    assert resp.status_code == 204


def test_get_messages(client):
    create = client.post("/api/sessions", json={"title": "Msg Test"})
    sid = create.json()["id"]
    resp = client.get(f"/api/sessions/{sid}/messages")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

- [ ] **Step 3: Run — expect FAIL**

```powershell
python -m pytest tests/test_sessions_api.py -v
```

Expected: `ImportError` from `backend.main`

- [ ] **Step 4: Write `backend/api/sessions.py`**

```python
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import ChatSession, ChatMessage

router = APIRouter()


class SessionIn(BaseModel):
    title: str


class SessionOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(ChatSession).order_by(ChatSession.created_at).all()


@router.post("/api/sessions", response_model=SessionOut, status_code=201)
def create_session(body: SessionIn, db: Session = Depends(get_db)):
    sess = ChatSession(title=body.title)
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


@router.put("/api/sessions/{session_id}", response_model=SessionOut)
def rename_session(session_id: int, body: SessionIn, db: Session = Depends(get_db)):
    sess = db.query(ChatSession).filter_by(id=session_id).first()
    if not sess:
        raise HTTPException(404, "Session not found")
    sess.title = body.title
    sess.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sess)
    return sess


@router.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    sess = db.query(ChatSession).filter_by(id=session_id).first()
    if not sess:
        raise HTTPException(404, "Session not found")
    db.delete(sess)
    db.commit()


@router.get("/api/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_messages(session_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ChatMessage)
        .filter_by(session_id=session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
```

- [ ] **Step 5: Write `backend/api/settings.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import UserInfo, SysCommand, WebCommand, Contact

router = APIRouter()


# ---- Personal Info ----

class InfoOut(BaseModel):
    name: str | None
    designation: str | None
    mobileno: str | None
    email: str | None
    city: str | None

    class Config:
        from_attributes = True


class InfoIn(BaseModel):
    name: str
    designation: str
    mobileno: str
    email: str
    city: str


@router.get("/api/settings/info", response_model=InfoOut)
def get_info(db: Session = Depends(get_db)):
    row = db.query(UserInfo).first()
    return row or InfoOut(name="", designation="", mobileno="", email="", city="")


@router.post("/api/settings/info", response_model=InfoOut)
def save_info(body: InfoIn, db: Session = Depends(get_db)):
    row = db.query(UserInfo).first()
    if row:
        for k, v in body.dict().items():
            setattr(row, k, v)
    else:
        row = UserInfo(**body.dict())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ---- Sys Commands ----

class CmdOut(BaseModel):
    id: int
    name: str
    path: str | None = None
    url: str | None = None

    class Config:
        from_attributes = True


@router.get("/api/settings/syscommands", response_model=list[CmdOut])
def list_syscommands(db: Session = Depends(get_db)):
    return db.query(SysCommand).all()


@router.post("/api/settings/syscommands", response_model=CmdOut, status_code=201)
def add_syscommand(body: dict, db: Session = Depends(get_db)):
    cmd = SysCommand(name=body["name"], path=body["path"])
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    return cmd


@router.delete("/api/settings/syscommands/{cmd_id}", status_code=204)
def delete_syscommand(cmd_id: int, db: Session = Depends(get_db)):
    cmd = db.query(SysCommand).filter_by(id=cmd_id).first()
    if not cmd:
        raise HTTPException(404)
    db.delete(cmd)
    db.commit()


# ---- Web Commands ----

@router.get("/api/settings/webcommands", response_model=list[CmdOut])
def list_webcommands(db: Session = Depends(get_db)):
    return db.query(WebCommand).all()


@router.post("/api/settings/webcommands", response_model=CmdOut, status_code=201)
def add_webcommand(body: dict, db: Session = Depends(get_db)):
    cmd = WebCommand(name=body["name"], url=body["url"])
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    return cmd


@router.delete("/api/settings/webcommands/{cmd_id}", status_code=204)
def delete_webcommand(cmd_id: int, db: Session = Depends(get_db)):
    cmd = db.query(WebCommand).filter_by(id=cmd_id).first()
    if not cmd:
        raise HTTPException(404)
    db.delete(cmd)
    db.commit()


# ---- Contacts ----

class ContactOut(BaseModel):
    id: int
    name: str
    mobile_no: str
    email: str | None
    address: str | None

    class Config:
        from_attributes = True


class ContactIn(BaseModel):
    name: str
    mobile_no: str
    email: str = ""
    address: str = ""


@router.get("/api/settings/contacts", response_model=list[ContactOut])
def list_contacts(db: Session = Depends(get_db)):
    return db.query(Contact).all()


@router.post("/api/settings/contacts", response_model=ContactOut, status_code=201)
def add_contact(body: ContactIn, db: Session = Depends(get_db)):
    c = Contact(**body.dict())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/api/settings/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    c = db.query(Contact).filter_by(id=contact_id).first()
    if not c:
        raise HTTPException(404)
    db.delete(c)
    db.commit()
```

- [ ] **Step 6: Commit**

```powershell
git add backend/api/auth.py backend/api/sessions.py backend/api/settings.py
git commit -m "feat: REST API — auth, sessions CRUD, settings (profile/commands/contacts)"
```

---

## Task 11: FastAPI App Entry

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: Write `backend/main.py`**

```python
import asyncio
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import auth, sessions, settings
from backend.api.ws import router as ws_router, set_event_loop, on_wake
from backend.db.database import init_db
from backend.engine import hotword


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    loop = asyncio.get_event_loop()
    set_event_loop(loop)
    hotword.register_callback(on_wake)
    hw_thread = threading.Thread(target=hotword.start, daemon=True)
    hw_thread.start()
    yield
    hotword.stop()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(settings.router)
```

- [ ] **Step 2: Run sessions API tests — expect PASS**

```powershell
python -m pytest tests/test_sessions_api.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 3: Smoke-test FastAPI starts**

```powershell
python -m uvicorn backend.main:app --port 8000
```

Expected: `Application startup complete.` with no errors. Ctrl+C to stop.

- [ ] **Step 4: Commit**

```powershell
git add backend/main.py tests/test_sessions_api.py
git commit -m "feat: FastAPI app entry — CORS, routers, hotword + DB init on startup"
```

---

## Task 12: Next.js Scaffold + CSS

**Files:**
- Modify: `frontend/styles/globals.css`
- Create: `frontend/pages/_app.tsx`
- Create: `frontend/next.config.js`
- Delete: `frontend/styles/Home.module.css`

- [ ] **Step 1: Write `frontend/next.config.js`**

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' },
      { source: '/ws', destination: 'http://localhost:8000/ws' },
    ]
  },
}

module.exports = nextConfig
```

- [ ] **Step 2: Replace `frontend/styles/globals.css` with exact port of `www/style.css`**

Copy the full content of `www/style.css` (lines 1–417) verbatim and add these extra session tabs styles at the bottom:

```css
/* --- above: full content of www/style.css verbatim --- */

/* Session Tabs */
.session-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 20px;
  background: rgba(0, 0, 0, 0.6);
  border-bottom: 1px solid rgba(0, 170, 255, 0.2);
  overflow-x: auto;
  scrollbar-width: none;
}
.session-tabs::-webkit-scrollbar { display: none; }

.session-tab {
  background: transparent;
  border: 1px solid rgba(0, 170, 255, 0.3);
  border-radius: 6px 6px 0 0;
  color: #888;
  padding: 4px 14px;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  transition: 0.2s;
  user-select: none;
}
.session-tab:hover { color: #00AAFF; border-color: #00AAFF; }
.session-tab.active {
  background: rgba(0, 43, 255, 0.25);
  border-color: #002bff;
  color: white;
  box-shadow: 0 0 12px rgb(25, 0, 255);
}
.session-tab-close {
  margin-left: 6px;
  opacity: 0.5;
  font-size: 10px;
}
.session-tab-close:hover { opacity: 1; color: red; }
.session-tab-new {
  background: transparent;
  border: 1px dashed rgba(0, 170, 255, 0.4);
  border-radius: 6px;
  color: rgba(0, 170, 255, 0.6);
  padding: 4px 10px;
  cursor: pointer;
  font-size: 14px;
}
.session-tab-new:hover { color: #00AAFF; border-color: #00AAFF; }
```

- [ ] **Step 3: Write `frontend/pages/_app.tsx`**

```tsx
import type { AppProps } from 'next/app'
import { useEffect } from 'react'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    require('bootstrap/dist/js/bootstrap.bundle.min.js')
  }, [])
  return <Component {...pageProps} />
}
```

- [ ] **Step 4: Delete default files**

```powershell
Remove-Item -Force frontend/styles/Home.module.css -ErrorAction SilentlyContinue
Remove-Item -Force frontend/pages/index.tsx -ErrorAction SilentlyContinue
Remove-Item -Force frontend/pages/api -Recurse -ErrorAction SilentlyContinue
```

- [ ] **Step 5: Verify Next.js builds**

```powershell
cd frontend; npm run build; cd ..
```

Expected: build succeeds (may show missing page warnings — expected at this point).

- [ ] **Step 6: Commit**

```powershell
git add frontend/
git commit -m "feat: Next.js scaffold — Bootstrap, CSS port, API proxy to FastAPI"
```

---

## Task 13: Frontend Hooks

**Files:**
- Create: `frontend/hooks/useWebSocket.ts`
- Create: `frontend/hooks/useVoice.ts`
- Create: `frontend/hooks/useSession.ts`

- [ ] **Step 1: Write `frontend/hooks/useWebSocket.ts`**

```typescript
import { useEffect, useRef, useCallback } from 'react'

export type WSMessage = {
  type: string
  text?: string
  session_id?: number
  success?: boolean
}

type Handler = (msg: WSMessage) => void

export function useWebSocket(onMessage: Handler) {
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<NodeJS.Timeout>()

  const connect = useCallback(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws')

    ws.current.onmessage = (e) => {
      try {
        const msg: WSMessage = JSON.parse(e.data)
        onMessage(msg)
      } catch {}
    }

    ws.current.onclose = () => {
      reconnectTimer.current = setTimeout(connect, 2000)
    }
  }, [onMessage])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      ws.current?.close()
    }
  }, [connect])

  const send = useCallback((msg: WSMessage) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(msg))
    }
  }, [])

  const sendBinary = useCallback((data: ArrayBuffer) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(data)
    }
  }, [])

  return { send, sendBinary }
}
```

- [ ] **Step 2: Write `frontend/hooks/useVoice.ts`**

```typescript
import { useRef, useCallback, useState } from 'react'

export function useVoice(onAudio: (data: ArrayBuffer) => void) {
  const recorder = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])
  const [listening, setListening] = useState(false)

  const startListening = useCallback(async () => {
    if (listening) return
    setListening(true)
    chunks.current = []

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    recorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' })

    recorder.current.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.current.push(e.data)
    }

    recorder.current.onstop = async () => {
      const blob = new Blob(chunks.current, { type: 'audio/webm' })
      const buffer = await blob.arrayBuffer()
      onAudio(buffer)
      stream.getTracks().forEach((t) => t.stop())
      setListening(false)
    }

    recorder.current.start()

    // Auto-stop after 8 seconds
    setTimeout(() => {
      if (recorder.current?.state === 'recording') {
        recorder.current.stop()
      }
    }, 8000)
  }, [listening, onAudio])

  const stopListening = useCallback(() => {
    if (recorder.current?.state === 'recording') {
      recorder.current.stop()
    }
  }, [])

  return { listening, startListening, stopListening }
}
```

- [ ] **Step 3: Write `frontend/hooks/useSession.ts`**

```typescript
import { useState, useEffect, useCallback } from 'react'

export type Session = { id: number; title: string }

export function useSession() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)

  const load = useCallback(async () => {
    const res = await fetch('/api/sessions')
    const data: Session[] = await res.json()
    setSessions(data)
    if (data.length > 0 && !activeId) setActiveId(data[0].id)
  }, [activeId])

  useEffect(() => { load() }, [])

  const createSession = useCallback(async () => {
    const title = `Chat #${sessions.length + 1}`
    const res = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    const sess: Session = await res.json()
    setSessions((prev) => [...prev, sess])
    setActiveId(sess.id)
    return sess
  }, [sessions.length])

  const renameSession = useCallback(async (id: number, title: string) => {
    await fetch(`/api/sessions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title } : s)))
  }, [])

  const deleteSession = useCallback(async (id: number) => {
    await fetch(`/api/sessions/${id}`, { method: 'DELETE' })
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== id)
      if (activeId === id) setActiveId(next[0]?.id ?? null)
      return next
    })
  }, [activeId])

  return { sessions, activeId, setActiveId, createSession, renameSession, deleteSession, reload: load }
}
```

- [ ] **Step 4: Commit**

```powershell
git add frontend/hooks/
git commit -m "feat: frontend hooks — useWebSocket, useVoice, useSession"
```

---

## Task 14: JarvisHUD Component

**Files:**
- Create: `frontend/components/JarvisHUD.tsx`
- Create: `frontend/components/SiriWave.tsx`

- [ ] **Step 1: Write `frontend/components/JarvisHUD.tsx`**

Port the SVG rings exactly from `www/index.html` lines 39–248. The component structure is:

```tsx
export default function JarvisHUD() {
  return (
    <div className="svg-frame mb-4">
      {/* SVG 1 — base (--i:0) */}
      <svg style={{ '--i': 0 } as React.CSSProperties}>
        {/* COPY <g id="big-outter"> from index.html line 41 to line 99 verbatim */}
        {/* COPY <circle id="base"> from index.html line 91 */}
        {/* COPY <mask id="path-2-inside-1_115_2"> from index.html line 92 to line 98 */}
      </svg>

      {/* SVG 2 — big centro (--i:1) */}
      <svg style={{ '--i': 1 } as React.CSSProperties}>
        {/* COPY <g id="big-centro"> from index.html line 103 to line 175 verbatim */}
      </svg>

      {/* SVG 3 — solo lines (--i:2) */}
      <svg style={{ '--i': 2 } as React.CSSProperties}>
        {/* COPY <g id="solo-lines"> from index.html line 179 to line 198 verbatim */}
      </svg>

      {/* SVG 4 — outter center (--i:3) */}
      <svg style={{ '--i': 3 } as React.CSSProperties}>
        {/* COPY <g id="outter-center"> from index.html line 202 to line 227 verbatim */}
      </svg>

      {/* SVG 5 — center lines (--i:4) */}
      <svg style={{ '--i': 4 } as React.CSSProperties}>
        {/* COPY <g id="center-lines"> from index.html line 231 to line 237 verbatim */}
      </svg>

      {/* SVG 6 — center (--i:5) */}
      <svg style={{ '--i': 5 } as React.CSSProperties}>
        {/* COPY <g id="center"> from index.html line 241 to line 247 verbatim */}
      </svg>
    </div>
  )
}
```

Open `www/index.html` (before deletion in Task 1 — if already deleted, use git: `git show HEAD~1:www/index.html`), copy each SVG group's inner content verbatim into the matching `<svg>` block above. No path data should be modified.

- [ ] **Step 2: Write `frontend/components/SiriWave.tsx`**

```tsx
import { useEffect, useRef } from 'react'
import SiriWaveLib from 'siriwave'

interface Props {
  visible: boolean
}

export default function SiriWave({ visible }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const waveRef = useRef<SiriWaveLib | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    waveRef.current = new SiriWaveLib({
      container: containerRef.current,
      width: 800,
      height: 200,
      style: 'ios9',
      amplitude: 1,
      speed: 0.3,
      autostart: true,
    })
    return () => { waveRef.current?.stop() }
  }, [])

  return (
    <section id="SiriWave" className="mb-4" hidden={!visible}>
      <div className="container">
        <div className="row">
          <div className="col-md-12">
            <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
              <div>
                <p className="text-start text-light mb-4 siri-message" style={{ fontSize: 28 }}>
                  Hello, I am J.A.R.V.I.S
                </p>
                <div ref={containerRef} id="siri-container" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 3: Commit**

```powershell
git add frontend/components/JarvisHUD.tsx frontend/components/SiriWave.tsx
git commit -m "feat: JarvisHUD SVG rings component + SiriWave wrapper"
```

---

## Task 15: FaceAuthOverlay + Startup Page

**Files:**
- Create: `frontend/components/FaceAuthOverlay.tsx`
- Create: `frontend/pages/index.tsx`

- [ ] **Step 1: Write `frontend/components/FaceAuthOverlay.tsx`**

```tsx
import dynamic from 'next/dynamic'

const Lottie = dynamic(() => import('lottie-react'), { ssr: false })

// Lottie animation JSON URLs (same as current index.html)
const FACE_AUTH_URL = 'https://assets2.lottiefiles.com/temp/lf20_XcJCfR.json'
const FACE_AUTH_SUCCESS_URL = 'https://assets1.lottiefiles.com/packages/lf20_lk80fpsm.json'
const HELLO_GREET_URL = 'https://lottie.host/f60d18d4-5199-412c-b687-e5e63ae38f75/CoqjMcJIx0.json'

type Step = 'loader' | 'scanning' | 'success' | 'greet'

interface Props {
  step: Step
  message: string
}

export default function FaceAuthOverlay({ step, message }: Props) {
  return (
    <div className="d-flex justify-content-center align-items-center flex-column" style={{ height: '80vh' }}>
      {step === 'loader' && (
        <div className="svg-frame mb-4">
          {/* Reuse JarvisHUD loader rings — import JarvisHUD here */}
        </div>
      )}
      {step === 'scanning' && (
        <div id="FaceAuth" className="mb-4">
          <Lottie
            path={FACE_AUTH_URL}
            style={{ width: 300, height: 300 }}
            loop
            autoplay
          />
        </div>
      )}
      {step === 'success' && (
        <div id="FaceAuthSuccess" className="mb-4">
          <Lottie
            path={FACE_AUTH_SUCCESS_URL}
            style={{ width: 300, height: 300 }}
            loop
            autoplay
          />
        </div>
      )}
      {step === 'greet' && (
        <div id="HelloGreet" className="mb-4">
          <Lottie
            path={HELLO_GREET_URL}
            style={{ width: 300, height: 300 }}
            loop
            autoplay
          />
        </div>
      )}
      <h1 className="text-center text-light mt-4 siri-message">{message}</h1>
    </div>
  )
}
```

- [ ] **Step 2: Write `frontend/pages/index.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import FaceAuthOverlay from '../components/FaceAuthOverlay'

type Step = 'loader' | 'scanning' | 'success' | 'greet'

export default function StartPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>('loader')
  const [message, setMessage] = useState('Initializing...')

  useEffect(() => {
    // Show loader for 1.5s, then start face auth
    const t1 = setTimeout(() => {
      setStep('scanning')
      setMessage('Ready for Face Authentication')
      doAuth()
    }, 1500)
    return () => clearTimeout(t1)
  }, [])

  async function doAuth() {
    try {
      const res = await fetch('/api/auth/face', { method: 'POST' })
      const data = await res.json()
      if (data.success) {
        setStep('success')
        setMessage('Face Authentication Successful')
        setTimeout(() => {
          setStep('greet')
          setMessage('Hello, Welcome Sir')
          setTimeout(() => router.push('/assistant'), 2000)
        }, 1500)
      } else {
        setMessage('Face Authentication Failed — Retrying...')
        setTimeout(doAuth, 2000)
      }
    } catch {
      setMessage('Authentication error — Retrying...')
      setTimeout(doAuth, 3000)
    }
  }

  return (
    <div className="container">
      <section id="Start">
        <div className="row">
          <div className="col-lg-12">
            <FaceAuthOverlay step={step} message={message} />
          </div>
        </div>
      </section>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```powershell
git add frontend/components/FaceAuthOverlay.tsx frontend/pages/index.tsx
git commit -m "feat: startup page + FaceAuthOverlay — Lottie animations, auth flow"
```

---

## Task 16: SessionTabs + ChatInput

**Files:**
- Create: `frontend/components/SessionTabs.tsx`
- Create: `frontend/components/ChatInput.tsx`

- [ ] **Step 1: Write `frontend/components/SessionTabs.tsx`**

```tsx
import { useRef } from 'react'
import { Session } from '../hooks/useSession'

interface Props {
  sessions: Session[]
  activeId: number | null
  onSelect: (id: number) => void
  onNew: () => void
  onRename: (id: number, title: string) => void
  onDelete: (id: number) => void
}

export default function SessionTabs({ sessions, activeId, onSelect, onNew, onRename, onDelete }: Props) {
  const editRef = useRef<{ id: number; timer: NodeJS.Timeout } | null>(null)

  function handleClick(id: number) {
    onSelect(id)
  }

  function handleDoubleClick(id: number, currentTitle: string) {
    const newTitle = prompt('Rename session:', currentTitle)
    if (newTitle && newTitle.trim()) onRename(id, newTitle.trim())
  }

  function handleClose(e: React.MouseEvent, id: number) {
    e.stopPropagation()
    if (sessions.length > 1) onDelete(id)
  }

  return (
    <div className="session-tabs">
      {sessions.map((s) => (
        <div
          key={s.id}
          className={`session-tab ${s.id === activeId ? 'active' : ''}`}
          onClick={() => handleClick(s.id)}
          onDoubleClick={() => handleDoubleClick(s.id, s.title)}
        >
          {s.title}
          <span
            className="session-tab-close"
            onClick={(e) => handleClose(e, s.id)}
          >
            ×
          </span>
        </div>
      ))}
      <button className="session-tab-new" onClick={onNew} title="New session">+</button>
    </div>
  )
}
```

- [ ] **Step 2: Write `frontend/components/ChatInput.tsx`**

```tsx
import { useState } from 'react'

interface Props {
  onSendText: (text: string) => void
  onMicClick: () => void
  isListening: boolean
  isProcessing: boolean
}

export default function ChatInput({ onSendText, onMicClick, isListening, isProcessing }: Props) {
  const [value, setValue] = useState('')

  function handleSend() {
    const text = value.trim()
    if (text && !isProcessing) {
      onSendText(text)
      setValue('')
    }
  }

  function handleKeyPress(e: React.KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="col-md-12 mt-4 pt-4">
      <div className="text-center">
        <div id="TextInput" className="d-flex">
          <input
            type="text"
            className="input-field"
            placeholder="type here ..."
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isProcessing}
          />
          {value.trim() ? (
            <button
              id="SendBtn"
              className="glow-on-hover"
              onClick={handleSend}
              disabled={isProcessing}
            >
              <i className="bi bi-send" />
            </button>
          ) : (
            <button
              id="MicBtn"
              className={`glow-on-hover ${isListening ? 'active' : ''}`}
              onClick={onMicClick}
              disabled={isProcessing}
            >
              <i className={`bi ${isListening ? 'bi-mic-fill' : 'bi-mic'}`} />
            </button>
          )}
          <button
            id="SettingsBtn"
            className="glow-on-hover"
            data-bs-toggle="modal"
            data-bs-target="#settingsModal"
          >
            <i className="bi bi-gear" />
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```powershell
git add frontend/components/SessionTabs.tsx frontend/components/ChatInput.tsx
git commit -m "feat: SessionTabs (create/rename/delete) + ChatInput (mic/text/send)"
```

---

## Task 17: SettingsModal

**Files:**
- Create: `frontend/components/SettingsModal.tsx`

- [ ] **Step 1: Write `frontend/components/SettingsModal.tsx`**

```tsx
import { useState, useEffect } from 'react'

interface SysCmd { id: number; name: string; path: string }
interface WebCmd { id: number; name: string; url: string }
interface Contact { id: number; name: string; mobile_no: string; email: string; address: string }
interface Info { name: string; designation: string; mobileno: string; email: string; city: string }

export default function SettingsModal() {
  const [info, setInfo] = useState<Info>({ name: '', designation: '', mobileno: '', email: '', city: '' })
  const [sysCmds, setSysCmds] = useState<SysCmd[]>([])
  const [webCmds, setWebCmds] = useState<WebCmd[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])

  useEffect(() => {
    fetch('/api/settings/info').then(r => r.json()).then(setInfo)
    fetch('/api/settings/syscommands').then(r => r.json()).then(setSysCmds)
    fetch('/api/settings/webcommands').then(r => r.json()).then(setWebCmds)
    fetch('/api/settings/contacts').then(r => r.json()).then(setContacts)
  }, [])

  async function saveInfo() {
    await fetch('/api/settings/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(info),
    })
    alert('Updated Successfully')
  }

  async function addSysCmd(name: string, path: string) {
    await fetch('/api/settings/syscommands', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, path }),
    })
    fetch('/api/settings/syscommands').then(r => r.json()).then(setSysCmds)
  }

  async function deleteSysCmd(id: number) {
    await fetch(`/api/settings/syscommands/${id}`, { method: 'DELETE' })
    setSysCmds(prev => prev.filter(c => c.id !== id))
  }

  async function addWebCmd(name: string, url: string) {
    await fetch('/api/settings/webcommands', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, url }),
    })
    fetch('/api/settings/webcommands').then(r => r.json()).then(setWebCmds)
  }

  async function deleteWebCmd(id: number) {
    await fetch(`/api/settings/webcommands/${id}`, { method: 'DELETE' })
    setWebCmds(prev => prev.filter(c => c.id !== id))
  }

  async function addContact(name: string, mobile_no: string, email: string, address: string) {
    await fetch('/api/settings/contacts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, mobile_no, email, address }),
    })
    fetch('/api/settings/contacts').then(r => r.json()).then(setContacts)
  }

  async function deleteContact(id: number) {
    await fetch(`/api/settings/contacts/${id}`, { method: 'DELETE' })
    setContacts(prev => prev.filter(c => c.id !== id))
  }

  return (
    <div className="modal fade" id="settingsModal" tabIndex={-1} aria-hidden="true">
      <div className="modal-dialog modal-xl">
        <div className="modal-content glass-effect">
          <div className="modal-header">
            <h5 className="modal-title" style={{ color: 'white' }}>Assistant Settings</h5>
            <button type="button" className="btn-close btn-glow-red" data-bs-dismiss="modal" aria-label="Close" />
          </div>
          <div className="modal-body">
            <nav>
              <div className="nav nav-tabs" id="settings-tab" role="tablist">
                <button className="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-personal" type="button">Personal</button>
                <button className="nav-link" data-bs-toggle="tab" data-bs-target="#tab-commands" type="button">Commands</button>
                <button className="nav-link" data-bs-toggle="tab" data-bs-target="#tab-contacts" type="button">Phone Book</button>
              </div>
            </nav>
            <div className="tab-content mt-3">

              {/* Personal Tab */}
              <div className="tab-pane fade show active" id="tab-personal">
                <div className="p-4">
                  {(['name','designation','mobileno','email','city'] as const).map(field => (
                    <div className="mb-3" key={field}>
                      <input
                        type="text"
                        className="form-control glassy-form"
                        placeholder={field}
                        value={info[field]}
                        onChange={e => setInfo(prev => ({ ...prev, [field]: e.target.value }))}
                      />
                    </div>
                  ))}
                  <div className="text-center mt-4">
                    <button className="btn btn-glow" onClick={saveInfo}>Save</button>
                  </div>
                </div>
              </div>

              {/* Commands Tab */}
              <div className="tab-pane fade" id="tab-commands">
                <SysCmdSection cmds={sysCmds} onAdd={addSysCmd} onDelete={deleteSysCmd} />
                <WebCmdSection cmds={webCmds} onAdd={addWebCmd} onDelete={deleteWebCmd} />
              </div>

              {/* Contacts Tab */}
              <div className="tab-pane fade" id="tab-contacts">
                <ContactSection contacts={contacts} onAdd={addContact} onDelete={deleteContact} />
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function SysCmdSection({ cmds, onAdd, onDelete }: { cmds: SysCmd[]; onAdd: (n:string,p:string)=>void; onDelete: (id:number)=>void }) {
  const [name, setName] = useState(''); const [path, setPath] = useState('')
  return (
    <div className="p-2">
      <p>System Commands</p>
      <div className="d-flex mt-2 gap-2">
        <input className="form-control glassy-form" placeholder="keyword" value={name} onChange={e=>setName(e.target.value)} />
        <input className="form-control glassy-form" placeholder="path" value={path} onChange={e=>setPath(e.target.value)} />
        <button className="btn btn-glow" onClick={()=>{ if(name&&path){ onAdd(name,path); setName(''); setPath('') } }}>Add</button>
      </div>
      <div className="table-responsive table-scroll mt-3">
        <table className="table">
          <thead><tr><th className="text-light">#</th><th className="text-light">Keyword</th><th className="text-light">Path</th><th className="text-light">Delete</th></tr></thead>
          <tbody>
            {cmds.map((c,i)=>(
              <tr key={c.id}>
                <td className="text-light">{i+1}</td>
                <td className="text-light">{c.name}</td>
                <td className="text-light">{c.path}</td>
                <td><button className="btn btn-sm btn-glow-red" onClick={()=>onDelete(c.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function WebCmdSection({ cmds, onAdd, onDelete }: { cmds: WebCmd[]; onAdd: (n:string,u:string)=>void; onDelete: (id:number)=>void }) {
  const [name, setName] = useState(''); const [url, setUrl] = useState('')
  return (
    <div className="p-2 mt-4">
      <p>Web Commands</p>
      <div className="d-flex mt-2 gap-2">
        <input className="form-control glassy-form" placeholder="keyword" value={name} onChange={e=>setName(e.target.value)} />
        <input className="form-control glassy-form" placeholder="url" value={url} onChange={e=>setUrl(e.target.value)} />
        <button className="btn btn-glow" onClick={()=>{ if(name&&url){ onAdd(name,url); setName(''); setUrl('') } }}>Add</button>
      </div>
      <div className="table-responsive table-scroll mt-3">
        <table className="table">
          <thead><tr><th className="text-light">#</th><th className="text-light">Keyword</th><th className="text-light">URL</th><th className="text-light">Delete</th></tr></thead>
          <tbody>
            {cmds.map((c,i)=>(
              <tr key={c.id}>
                <td className="text-light">{i+1}</td>
                <td className="text-light">{c.name}</td>
                <td className="text-light">{c.url}</td>
                <td><button className="btn btn-sm btn-glow-red" onClick={()=>onDelete(c.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ContactSection({ contacts, onAdd, onDelete }: { contacts: Contact[]; onAdd: (n:string,m:string,e:string,a:string)=>void; onDelete: (id:number)=>void }) {
  const [form, setForm] = useState({ name:'', mobile_no:'', email:'', address:'' })
  return (
    <div className="p-4">
      <div className="d-flex flex-column gap-2 mb-3">
        {(['name','mobile_no','email','address'] as const).map(f=>(
          <input key={f} className="form-control glassy-form" placeholder={f} value={form[f]} onChange={e=>setForm(p=>({...p,[f]:e.target.value}))} />
        ))}
        <div className="text-center">
          <button className="btn btn-glow" onClick={()=>{ if(form.name&&form.mobile_no){ onAdd(form.name,form.mobile_no,form.email,form.address); setForm({name:'',mobile_no:'',email:'',address:''}) } }}>Add Contact</button>
        </div>
      </div>
      <div className="table-responsive table-scroll">
        <table className="table">
          <thead><tr><th className="text-light">#</th><th className="text-light">Name</th><th className="text-light">Mobile</th><th className="text-light">Email</th><th className="text-light">Address</th><th className="text-light">Delete</th></tr></thead>
          <tbody>
            {contacts.map((c,i)=>(
              <tr key={c.id}>
                <td className="text-light">{i+1}</td>
                <td className="text-light">{c.name}</td>
                <td className="text-light">{c.mobile_no}</td>
                <td className="text-light">{c.email}</td>
                <td className="text-light">{c.address}</td>
                <td><button className="btn btn-sm btn-glow-red" onClick={()=>onDelete(c.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```powershell
git add frontend/components/SettingsModal.tsx
git commit -m "feat: SettingsModal — profile, sys/web commands, contacts CRUD"
```

---

## Task 18: Assistant Page + run.py

**Files:**
- Create: `frontend/pages/assistant.tsx`
- Rewrite: `run.py`

- [ ] **Step 1: Write `frontend/pages/assistant.tsx`**

```tsx
import { useCallback, useState } from 'react'
import { useWebSocket, WSMessage } from '../hooks/useWebSocket'
import { useVoice } from '../hooks/useVoice'
import { useSession } from '../hooks/useSession'
import JarvisHUD from '../components/JarvisHUD'
import SiriWave from '../components/SiriWave'
import SessionTabs from '../components/SessionTabs'
import ChatInput from '../components/ChatInput'
import SettingsModal from '../components/SettingsModal'

interface Message { role: 'user' | 'assistant'; text: string }

export default function AssistantPage() {
  const [showSiriWave, setShowSiriWave] = useState(false)
  const [displayText, setDisplayText] = useState('Ask me anything')
  const [isProcessing, setIsProcessing] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])

  const { sessions, activeId, setActiveId, createSession, renameSession, deleteSession } = useSession()

  const handleWSMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'wake':
        setShowSiriWave(true)
        setIsProcessing(true)
        setDisplayText('Listening...')
        break
      case 'transcript':
        setDisplayText(msg.text ?? '')
        setMessages(p => [...p, { role: 'user', text: msg.text ?? '' }])
        break
      case 'display':
        setDisplayText(msg.text ?? '')
        break
      case 'response':
        setMessages(p => [...p, { role: 'assistant', text: msg.text ?? '' }])
        setDisplayText(msg.text ?? '')
        break
      case 'show_hood':
        setShowSiriWave(false)
        setIsProcessing(false)
        break
    }
  }, [])

  const { send, sendBinary } = useWebSocket(handleWSMessage)

  const handleAudio = useCallback((data: ArrayBuffer) => {
    sendBinary(data)
  }, [sendBinary])

  const { listening, startListening, stopListening } = useVoice(handleAudio)

  function handleSendText(text: string) {
    if (!activeId) return
    setIsProcessing(true)
    setShowSiriWave(true)
    setDisplayText(text)
    setMessages(p => [...p, { role: 'user', text }])
    send({ type: 'command', text, session_id: activeId })
  }

  function handleMicClick() {
    if (listening) {
      stopListening()
    } else {
      setShowSiriWave(true)
      setIsProcessing(true)
      startListening()
    }
  }

  return (
    <>
      <SessionTabs
        sessions={sessions}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={createSession}
        onRename={renameSession}
        onDelete={deleteSession}
      />

      <div className="container">
        {/* JARVIS HUD */}
        <section id="Oval" className="mb-4" hidden={showSiriWave}>
          <div className="row">
            <div className="col-md-1" />
            <div className="col-md-10">
              <div className="d-flex justify-content-center align-items-center" style={{ height: '80vh' }}>
                <div id="JarvisHood">
                  <div className="square">
                    <span className="circle" />
                    <span className="circle" />
                    <span className="circle" />
                  </div>
                </div>
              </div>
              <h5 className="text-light text text-center">{displayText}</h5>
              <ChatInput
                onSendText={handleSendText}
                onMicClick={handleMicClick}
                isListening={listening}
                isProcessing={isProcessing}
              />
            </div>
            <div className="col-md-1" />
          </div>
        </section>

        {/* Siri Wave (during voice) */}
        <SiriWave visible={showSiriWave} />
      </div>

      <SettingsModal />

      {/* Chat history — rendered off-screen for session context, not displayed inline */}
      <div style={{ display: 'none' }}>
        {messages.map((m, i) => (
          <span key={i} data-role={m.role}>{m.text}</span>
        ))}
      </div>
    </>
  )
}
```

- [ ] **Step 2: Rewrite `run.py`**

```python
import os
import sys
import time
import signal
import subprocess
import webbrowser

BACKEND_CMD = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
FRONTEND_CMD = ["npx", "next", "start", "frontend", "--port", "3000"]
FRONTEND_URL = "http://localhost:3000"

procs: list[subprocess.Popen] = []


def shutdown(sig=None, frame=None):
    for p in procs:
        p.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

if __name__ == "__main__":
    print("Starting FastAPI backend...")
    backend = subprocess.Popen(BACKEND_CMD)
    procs.append(backend)

    print("Starting Next.js frontend...")
    frontend = subprocess.Popen(FRONTEND_CMD, shell=(sys.platform == "win32"))
    procs.append(frontend)

    print(f"Waiting for servers to start...")
    time.sleep(4)

    print(f"Opening {FRONTEND_URL}")
    webbrowser.open(FRONTEND_URL)

    print("Next Gen AI running. Press Ctrl+C to stop.")
    try:
        backend.wait()
    except KeyboardInterrupt:
        shutdown()
```

- [ ] **Step 3: Build Next.js**

```powershell
cd frontend; npm run build; cd ..
```

Expected: Build succeeds.

- [ ] **Step 4: Run the full application (manual test)**

```powershell
python run.py
```

Expected:
1. Browser opens to `http://localhost:3000`
2. SVG loader animation displays
3. Face auth flow triggers
4. On auth success → redirects to `/assistant`
5. JARVIS HUD visible with session tabs
6. Type a command → response appears, TTS speaks

- [ ] **Step 5: Run full test suite**

```powershell
python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Final commit**

```powershell
git add frontend/pages/assistant.tsx run.py
git commit -m "feat: assistant page + run.py — full Phase 1 integration complete"
```

---

## Self-Review Checklist

- [x] **Startup flow** (spec §Key Flows / Startup) → Task 15 `index.tsx` + Task 7 `face_auth.py` + Task 11 `main.py`
- [x] **Voice command pipeline** (spec §Voice Command) → Task 8 hotword → Task 9 WS → Task 5 STT → Task 6 classify → Task 4 AI
- [x] **Text command** (spec §Text Input) → Task 9 WS `command` type → Task 6 → Task 4
- [x] **Session tabs** (spec §Session Management) → Task 16 `SessionTabs.tsx` + Task 10 `sessions.py` + Task 13 `useSession.ts`
- [x] **10-message compression** (spec §Database) → Task 4 `ai.py` `_maybe_compress` + `session_summaries` table
- [x] **Dual Groq model routing** (spec §LLM) → Task 4 `route_model()` — 8 words + question words
- [x] **Settings modal** (spec §frontend components) → Task 17 `SettingsModal.tsx`
- [x] **Pixel-perfect CSS** (spec §Frontend style) → Task 12 `globals.css` direct port of `www/style.css`
- [x] **Package cleanup** (spec §Packages Removed) → Task 1 `requirements.txt`
- [x] **File deletions** (spec §What Gets Deleted) → Task 1 removes `www/`, `main.py`, `device.bat`, old engine files
- [x] **Existing data preserved** → `jarvis.db` never deleted; `Base.metadata.create_all` adds new tables, touches none
- [x] **OpenWakeWord** → Task 8 uses `hey_jarvis` built-in; note for custom "Next Gen" model in Phase 2

**Type consistency verified:** `WSMessage` defined in `useWebSocket.ts` and used consistently in `assistant.tsx`. `Session` type from `useSession.ts` passed to `SessionTabs.tsx`. All API response shapes match Pydantic models in `sessions.py` and `settings.py`.
