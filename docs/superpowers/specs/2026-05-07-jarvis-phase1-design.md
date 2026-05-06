# Next Gen AI — Phase 1 Design Spec
**Date:** 2026-05-07  
**Scope:** Migrate from Eel + plain HTML to FastAPI + Next.js + Groq. Production-clean architecture.

---

## Overview

Phase 1 replaces the deprecated Eel desktop framework with a proper FastAPI backend and Next.js frontend while preserving the exact visual design, all existing SQLite data, and the face authentication system. Groq becomes the sole AI provider for both LLM responses and Whisper STT. OpenWakeWord replaces pvporcupine for the custom "Next Gen" wake word at zero cost.

---

## Decisions Made

| Concern | Decision |
|---|---|
| Architecture | FastAPI (backend) + Next.js (frontend) |
| Migration strategy | Backend-first (port engine/ → FastAPI), then build Next.js |
| Frontend style | Pixel-perfect recreation of current Eel HTML/CSS |
| Face authentication | Keep — DeepFace + OpenCV, port to FastAPI endpoint |
| Wake word | OpenWakeWord, custom "Next Gen" model (Colab training) |
| TTS | pyttsx3 (keep, Windows SAPI5) |
| STT | Groq Whisper API (replaces Google Speech Recognition) |
| LLM | Groq dual-model: `llama-3.1-8b-instant` (commands) + `llama-3.3-70b-versatile` (complex AI) |
| Chat sessions UI | Tab bar across the top of the JARVIS HUD |
| Database | SQLite + SQLAlchemy, 3 new tables added |

---

## Architecture

Two processes launched by a single `run.py`:

1. **FastAPI** on port 8000 — WebSocket hub + REST endpoints + background engine threads
2. **Next.js** on port 3000 — opens automatically in the browser on startup

```
run.py
├── subprocess: uvicorn backend/main.py --port 8000
└── subprocess: next start frontend/ --port 3000 (then os.startfile browser)
```

> **Prerequisite:** `cd frontend && npm run build` must be run once after cloning or after any frontend change. `run.py` calls `next start` (production mode), not `next dev`.

Communication:
- **WebSocket** (`ws://localhost:8000/ws`) — real-time: wake events, audio streaming, AI responses, TTS text, status
- **REST** (`http://localhost:8000/api/...`) — CRUD: sessions, messages, contacts, sys/web commands, profile
- **External** — Groq API (LLM + Whisper STT)

---

## Folder Structure

```
Next-GEN_AI/
├── run.py                        # rewritten: launches both servers
├── .env                          # add GROQ_API_KEY
├── requirements.txt              # ~15 clean deps
├── jarvis.db                     # preserved
│
├── backend/
│   ├── main.py                   # FastAPI app, mounts routers, starts engines
│   ├── api/
│   │   ├── ws.py                 # WebSocket hub (/ws)
│   │   ├── auth.py               # POST /api/auth/face
│   │   ├── sessions.py           # GET/POST/PUT/DELETE /api/sessions
│   │   └── settings.py           # profile, contacts, sys/web commands
│   ├── engine/
│   │   ├── voice.py              # pyttsx3 TTS + Groq Whisper STT
│   │   ├── ai.py                 # dual Groq model routing + history compression
│   │   ├── automation.py         # open/close/search/youtube (ported from features.py)
│   │   ├── hotword.py            # OpenWakeWord listener (background thread)
│   │   ├── face_auth.py          # DeepFace wrapper (ported from engine/auth/)
│   │   ├── config.py             # Pydantic Settings (replaces current config.py)
│   │   └── helper.py             # kept as-is
│   ├── db/
│   │   ├── database.py           # SQLAlchemy engine + session
│   │   └── models.py             # all table models
│   └── engine/
│       └── auth/                 # face samples + haarcascade (moved, unchanged)
│
└── frontend/
    ├── pages/
    │   ├── index.tsx             # startup + face auth overlay
    │   └── assistant.tsx         # main JARVIS HUD page
    ├── components/
    │   ├── JarvisHUD.tsx         # animated SVG rings (pixel-perfect port)
    │   ├── SiriWave.tsx          # siriwave.js wrapper
    │   ├── SessionTabs.tsx       # tab bar at top (create/rename/delete)
    │   ├── ChatInput.tsx         # mic button + text input + send
    │   ├── SettingsModal.tsx     # profile, sys/web commands, contacts
    │   └── FaceAuthOverlay.tsx   # lottie animation + webcam feed
    ├── hooks/
    │   ├── useWebSocket.ts       # WS connection + message dispatch
    │   ├── useVoice.ts           # mic capture, send audio bytes over WS
    │   └── useSession.ts         # active session state, tab management
    └── styles/
        └── globals.css           # exact port of www/style.css
```

---

## Database Schema

### Existing tables (unchanged)
- `sys_command(id, name, path)`
- `web_command(id, name, url)`
- `contacts(id, name, mobile_no, email, address)`
- `info(name, designation, mobileno, email, city)`

### New tables
```sql
CREATE TABLE chat_sessions (
    id         INTEGER PRIMARY KEY,
    title      TEXT,           -- user-editable, default "Chat #N"
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE chat_messages (
    id         INTEGER PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id),
    role       TEXT,           -- "user" | "assistant"
    content    TEXT,
    created_at DATETIME
);

CREATE TABLE session_summaries (
    id            INTEGER PRIMARY KEY,
    session_id    INTEGER REFERENCES chat_sessions(id),
    summary       TEXT,        -- compressed context from llama-3.1-8b-instant
    message_count INTEGER,     -- how many messages were compressed
    created_at    DATETIME
);
```

**History compression:** When a session accumulates 10 new messages since the last summary, `ai.py` calls `llama-3.1-8b-instant` with a summarisation prompt, stores the result in `session_summaries`, and prepends `"Previous context: {summary}"` to subsequent LLM calls instead of replaying all 10 messages.

---

## Key Flows

### Startup
1. `run.py` spawns FastAPI (uvicorn) and Next.js, opens browser
2. Next.js loads `index.tsx` — shows SVG loader animation (ported exactly from current HTML)
3. Frontend calls `POST /api/auth/face` — backend captures webcam frame, runs DeepFace verify against `engine/auth/database/`
4. On success: redirect to `/assistant`, WS connects, OpenWakeWord thread starts, TTS says "Welcome Sir"
5. On failure: TTS says "Face Authentication Failed", retry overlay shown

### Voice Command
1. OpenWakeWord detects "Next Gen" → sends `{"type":"wake"}` over WS
2. Frontend activates SiriWave, mic captures audio (8s window)
3. Audio WAV bytes sent to backend over WS
4. Backend sends to Groq Whisper → transcript returned
5. `automation.py` classifies by keyword: `open/close/search/youtube/send message` → runs direct action
6. Otherwise → `ai.py` routes to Groq LLM:
   - **`llama-3.1-8b-instant`** — query ≤ 8 words OR no question words (`why/how/explain/what is/analyze/write/compare`)
   - **`llama-3.3-70b-versatile`** — query > 8 words AND contains at least one question word
7. Response text → pyttsx3 speaks it + WS sends `{"type":"response","text":"..."}` to frontend
8. Frontend displays message in active session tab, saves to `chat_messages`

### Text Input
Same as voice command from step 5 onward — skip STT, use typed text directly.

### Session Management
- Default session created on first launch
- Tab bar shows all sessions; active session highlighted
- Double-click tab to rename; right-click (or × button) to delete
- New session button (`+`) at end of tab bar
- Sessions persist in `chat_sessions` table; messages load on tab click

---

## What Gets Deleted

| File/Folder | Reason |
|---|---|
| `www/` | Replaced by Next.js frontend |
| `main.py` | Eel entry point, replaced by `backend/main.py` |
| `device.bat` | Eel device driver, no longer needed |
| `engine/command.py` | Logic split into `engine/voice.py` + `engine/automation.py` |
| `engine/features.py` | Logic split into `engine/ai.py` + `engine/automation.py` |
| `engine/db.py` | Replaced by `db/database.py` + `db/models.py` |

### Packages Removed
`eel`, `flask`, `bottle`, `gevent`, `chatterbot`, `hugchat`, `openai==0.27`, `pymongo`, `nltk`, `google-generativeai`, `pywhatkit`, `playsound`, `pvporcupine`, `SpeechRecognition`, `tensorflow` (direct dep)

### Clean requirements.txt
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
```

---

## What Gets Preserved

- `jarvis.db` — all existing user data
- `engine/auth/samples/` — face training images
- `engine/auth/haarcascade_frontalface_default.xml`
- `engine/auth/database/` — trained face model
- `engine/helper.py` — unchanged
- `.env` — add `GROQ_API_KEY=` line

---

## Out of Scope (Phase 2)

- Google Workspace (Gmail, Calendar, Drive, Docs/Sheets)
- YouTube search, transcripts, AI summarisation
- Windows Automation beyond open/close/search
- OpenWakeWord custom model training (Phase 1 uses `"hey jarvis"` built-in until model is trained)
