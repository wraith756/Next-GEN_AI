# Windows Automation+ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add screenshot, system info, and window management voice commands to the JARVIS assistant, with screenshots displayed as thumbnails in a new visible chat history panel.

**Architecture:** One new file `backend/engine/windows.py` holds the 5 handler functions. `automation.py` gains 5 new intents + delegates to `windows.py`. `ws.py` detects dict responses and sends a new `{"type":"image"}` WebSocket message. `assistant.tsx` gains a visible scrollable chat panel below the HUD that renders text and image messages.

**Tech Stack:** Python — pyautogui (screenshots), psutil (system info), pygetwindow (window management); TypeScript/React — base64 image rendering, useRef auto-scroll, useEffect

---

## File Map

| File | Change |
|---|---|
| `backend/engine/windows.py` | **NEW** — 5 handler functions |
| `backend/engine/automation.py` | 5 new intents in `classify_command()` + 5 branches in `run_command()` |
| `backend/api/ws.py` | `_handle_command()` — detect dict response, send `image` WS type, skip `markdown_to_text` on dicts |
| `frontend/pages/assistant.tsx` | Add `ChatMsg` state, visible chat panel (35vh), image message rendering, HUD height reduced to 40vh |
| `tests/test_windows.py` | **NEW** — 9 tests |

---

## Task 1: `backend/engine/windows.py` — screenshot + system info

**Files:**
- Create: `backend/engine/windows.py`
- Create: `tests/test_windows.py`

- [ ] **Step 1: Write failing tests for screenshot and sysinfo**

Create `tests/test_windows.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import io


def test_screenshot_returns_dict():
    mock_img = MagicMock(spec=Image.Image)
    mock_img.save = MagicMock()
    with patch("pyautogui.screenshot", return_value=mock_img), \
         patch("backend.engine.windows._desktop_path", return_value="/tmp"), \
         patch("builtins.open", create=True) as mock_open, \
         patch("base64.b64encode", return_value=b"abc123"):
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.read = MagicMock(return_value=b"fakejpeg")
        from backend.engine.windows import take_screenshot
        result = take_screenshot()
    assert "image_b64" in result
    assert "text" in result
    assert "path" in result


def test_sysinfo_cpu():
    from backend.engine.windows import get_system_info
    result = get_system_info("what is my cpu usage")
    assert "%" in result
    assert "CPU" in result or "cpu" in result.lower()


def test_sysinfo_ram():
    from backend.engine.windows import get_system_info
    result = get_system_info("how much ram do I have")
    assert "GB" in result or "MB" in result


def test_sysinfo_disk():
    from backend.engine.windows import get_system_info
    result = get_system_info("how much disk space is left")
    assert "GB" in result or "TB" in result


def test_sysinfo_all():
    from backend.engine.windows import get_system_info
    result = get_system_info("system info")
    assert len(result) > 30  # multi-line summary
```

- [ ] **Step 2: Run — expect FAIL**

```
python -m pytest tests/test_windows.py -v
```

Expected: `ImportError: cannot import name 'take_screenshot' from 'backend.engine.windows'`

- [ ] **Step 3: Write `backend/engine/windows.py` — screenshot + sysinfo**

```python
import base64
import os
from datetime import datetime

import psutil
import pyautogui


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
        disk = psutil.disk_usage("C:\\")
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
    disk = psutil.disk_usage("C:\\")
    batt = psutil.sensors_battery()

    lines = [
        f"CPU: {cpu}%",
        f"RAM: {mem.used / (1024**3):.1f} GB used of {mem.total / (1024**3):.1f} GB",
        f"Disk C: {disk.free / (1024**3):.0f} GB free",
    ]
    if batt:
        lines.append(f"Battery: {batt.percent:.0f}%")
    return "\n".join(lines)
```

- [ ] **Step 4: Run — expect PASS**

```
python -m pytest tests/test_windows.py::test_screenshot_returns_dict tests/test_windows.py::test_sysinfo_cpu tests/test_windows.py::test_sysinfo_ram tests/test_windows.py::test_sysinfo_disk tests/test_windows.py::test_sysinfo_all -v
```

Expected: 5 PASS

- [ ] **Step 5: Commit**

```
git add backend/engine/windows.py tests/test_windows.py
git commit -m "feat: windows.py — take_screenshot + get_system_info"
```

---

## Task 2: `windows.py` — window management functions

**Files:**
- Modify: `backend/engine/windows.py`
- Modify: `tests/test_windows.py`

- [ ] **Step 1: Add failing tests for window management**

Append to `tests/test_windows.py`:

```python
def test_minimize_window_not_found():
    from backend.engine.windows import minimize_window
    with patch("pygetwindow.getAllTitles", return_value=["Notepad", "Chrome"]):
        result = minimize_window("minimize spotify")
    assert result == "Window not found"


def test_minimize_window_found():
    from backend.engine.windows import minimize_window
    mock_win = MagicMock()
    with patch("pygetwindow.getAllTitles", return_value=["Google Chrome", "Notepad"]), \
         patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        result = minimize_window("minimize chrome")
    mock_win.minimize.assert_called_once()
    assert "Minimized" in result


def test_maximize_window_found():
    from backend.engine.windows import maximize_window
    mock_win = MagicMock()
    with patch("pygetwindow.getAllTitles", return_value=["Notepad - Untitled"]), \
         patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        result = maximize_window("maximize notepad")
    mock_win.maximize.assert_called_once()
    assert "Maximized" in result


def test_focus_window_found():
    from backend.engine.windows import focus_window
    mock_win = MagicMock()
    with patch("pygetwindow.getAllTitles", return_value=["Spotify"]), \
         patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        result = focus_window("switch to spotify")
    mock_win.activate.assert_called_once()
    assert "Switched" in result
```

- [ ] **Step 2: Run — expect FAIL**

```
python -m pytest tests/test_windows.py::test_minimize_window_found -v
```

Expected: `ImportError` or `AttributeError`

- [ ] **Step 3: Add window management functions to `backend/engine/windows.py`**

Append to the existing file (after `get_system_info`):

```python
import pygetwindow as gw


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
    win, title = _find_window(app)
    if win is None:
        return "Window not found"
    win.minimize()
    return f"Minimized {app}"


def maximize_window(query: str) -> str:
    app = query.lower().replace("maximize", "").strip()
    win, title = _find_window(app)
    if win is None:
        return "Window not found"
    win.maximize()
    return f"Maximized {app}"


def focus_window(query: str) -> str:
    app = query.lower().replace("switch to", "").replace("focus", "").strip()
    win, title = _find_window(app)
    if win is None:
        return "Window not found"
    win.activate()
    return f"Switched to {app}"
```

- [ ] **Step 4: Run all window tests — expect PASS**

```
python -m pytest tests/test_windows.py -v
```

Expected: 9 tests PASS

- [ ] **Step 5: Commit**

```
git add backend/engine/windows.py tests/test_windows.py
git commit -m "feat: windows.py — minimize/maximize/focus window management"
```

---

## Task 3: Update `automation.py` — new intents + delegation

**Files:**
- Modify: `backend/engine/automation.py:18-32` (classify_command)
- Modify: `backend/engine/automation.py:118-138` (run_command)
- Modify: `tests/test_automation.py`

- [ ] **Step 1: Add failing intent tests**

Append to `tests/test_automation.py`:

```python
def test_classify_screenshot():
    assert classify_command("take a screenshot") == "screenshot"

def test_classify_screenshot_short():
    assert classify_command("screenshot") == "screenshot"

def test_classify_sysinfo_cpu():
    assert classify_command("what is my cpu usage") == "sysinfo"

def test_classify_sysinfo_ram():
    assert classify_command("how much ram do I have") == "sysinfo"

def test_classify_sysinfo_battery():
    assert classify_command("check battery") == "sysinfo"

def test_classify_win_minimize():
    assert classify_command("minimize chrome") == "win_minimize"

def test_classify_win_maximize():
    assert classify_command("maximize notepad") == "win_maximize"

def test_classify_win_focus():
    assert classify_command("focus spotify") == "win_focus"

def test_classify_switch_to():
    assert classify_command("switch to chrome") == "win_focus"
```

- [ ] **Step 2: Run — expect FAIL**

```
python -m pytest tests/test_automation.py::test_classify_screenshot tests/test_automation.py::test_classify_win_minimize -v
```

Expected: AssertionError (returns `"ai"` instead of correct intent)

- [ ] **Step 3: Replace `classify_command()` in `backend/engine/automation.py`**

Replace lines 18–32 with:

```python
def classify_command(query: str) -> str:
    q = query.lower().strip()

    # Windows automation — checked before "open" to prevent misrouting
    if "screenshot" in q or "take a screenshot" in q:
        return "screenshot"
    if any(k in q for k in ("cpu", "ram", "memory", "disk", "storage", "drive", "battery", "system info", "how much")):
        return "sysinfo"
    if q.startswith("minimize "):
        return "win_minimize"
    if q.startswith("maximize "):
        return "win_maximize"
    if q.startswith("focus ") or q.startswith("switch to "):
        return "win_focus"

    # Original intents
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
```

- [ ] **Step 4: Add import + new branches to `run_command()` in `automation.py`**

At the top of the file, add the import after line 9:

```python
from backend.engine import windows
```

Replace `run_command()` (currently lines 118–138) with:

```python
def run_command(query: str, session_id: int):
    intent = classify_command(query)
    try:
        if intent == "screenshot":
            return windows.take_screenshot(), False
        if intent == "sysinfo":
            return windows.get_system_info(query), False
        if intent == "win_minimize":
            return windows.minimize_window(query), False
        if intent == "win_maximize":
            return windows.maximize_window(query), False
        if intent == "win_focus":
            return windows.focus_window(query), False
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
```

- [ ] **Step 5: Run full automation tests — expect PASS**

```
python -m pytest tests/test_automation.py -v
```

Expected: 18 tests PASS (9 original + 9 new)

- [ ] **Step 6: Commit**

```
git add backend/engine/automation.py tests/test_automation.py
git commit -m "feat: automation.py — 5 new intents delegating to windows.py"
```

---

## Task 4: Update `ws.py` — handle dict response → image WS message

**Files:**
- Modify: `backend/api/ws.py:38-55` (`_handle_command`)

- [ ] **Step 1: Replace `_handle_command()` in `backend/api/ws.py`**

Replace the existing `_handle_command` function (lines 38–55) with:

```python
async def _handle_command(ws: WebSocket, text: str, session_id: int):
    await ws.send_json({"type": "display", "text": text})
    _save_message(session_id, "user", text)

    response, needs_ai = automation.run_command(text, session_id)
    if needs_ai:
        response = ai_engine.ask(text, session_id)

    # Screenshot returns a dict — all other commands return a str
    if isinstance(response, dict) and "image_b64" in response:
        spoken_text = response["text"]
        threading.Thread(target=voice.speak, args=(spoken_text,), daemon=True).start()
        await ws.send_json({
            "type": "image",
            "data": response["image_b64"],
            "path": response["path"],
            "text": spoken_text,
            "session_id": session_id,
        })
        _save_message(session_id, "assistant", spoken_text)
    else:
        try:
            from backend.engine.helper import markdown_to_text
            response = markdown_to_text(response)
        except Exception:
            pass
        threading.Thread(target=voice.speak, args=(response,), daemon=True).start()
        await ws.send_json({"type": "response", "text": response, "session_id": session_id})
        _save_message(session_id, "assistant", response)

    await ws.send_json({"type": "show_hood"})
```

- [ ] **Step 2: Run existing API tests — expect PASS (no regression)**

```
python -m pytest tests/test_sessions_api.py tests/test_db.py -v
```

Expected: 8 tests PASS

- [ ] **Step 3: Commit**

```
git add backend/api/ws.py
git commit -m "feat: ws.py — route image dict responses to new image WS message type"
```

---

## Task 5: Update `assistant.tsx` — visible chat panel + image rendering

**Files:**
- Modify: `frontend/pages/assistant.tsx`

- [ ] **Step 1: Replace `frontend/pages/assistant.tsx` with the updated version**

```tsx
import { useCallback, useState, useRef, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { useWebSocket, WSMessage } from '../hooks/useWebSocket'
import { useVoice } from '../hooks/useVoice'
import { useSession } from '../hooks/useSession'
import SessionTabs from '../components/SessionTabs'
import ChatInput from '../components/ChatInput'
import SettingsModal from '../components/SettingsModal'

const SiriWave = dynamic(() => import('../components/SiriWave'), { ssr: false })

type ChatMsg = { role: 'user' | 'assistant'; text: string; image?: string }

export default function AssistantPage() {
  const [showSiriWave, setShowSiriWave] = useState(false)
  const [displayText, setDisplayText] = useState('Ask me anything')
  const [isProcessing, setIsProcessing] = useState(false)
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const chatBottomRef = useRef<HTMLDivElement>(null)

  const { sessions, activeId, setActiveId, createSession, renameSession, deleteSession } = useSession()

  // Auto-scroll chat to bottom on new messages
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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
        setDisplayText(msg.text ?? '')
        setMessages(p => [...p, { role: 'assistant', text: msg.text ?? '' }])
        break
      case 'image':
        setMessages(p => [...p, {
          role: 'assistant',
          text: (msg as any).text ?? 'Screenshot saved',
          image: (msg as any).data,
        }])
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
        {!showSiriWave && (
          <section id="Oval" className="mb-2">
            <div className="row">
              <div className="col-md-1" />
              <div className="col-md-10">
                {/* HUD reduced to 40vh to make room for chat panel */}
                <div className="d-flex justify-content-center align-items-center" style={{ height: '40vh' }}>
                  <div id="JarvisHood">
                    <div className="square">
                      <span className="circle" />
                      <span className="circle" />
                      <span className="circle" />
                    </div>
                  </div>
                </div>
                <h5 className="text-light text-center mb-2">{displayText}</h5>

                {/* Chat history panel */}
                <div
                  style={{
                    maxHeight: '35vh',
                    overflowY: 'auto',
                    padding: '0 4px',
                    marginBottom: '8px',
                  }}
                >
                  {messages.map((m, i) => (
                    <div
                      key={i}
                      className={`row ${m.role === 'user' ? 'justify-content-end' : 'justify-content-start'} mb-2`}
                    >
                      <div className="width-size">
                        <div className={m.role === 'user' ? 'sender_message' : 'receiver_message'}>
                          {m.image && (
                            <a
                              href={`data:image/jpeg;base64,${m.image}`}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <img
                                src={`data:image/jpeg;base64,${m.image}`}
                                style={{ maxWidth: 200, display: 'block', marginBottom: 6, borderRadius: 4 }}
                                alt="screenshot"
                              />
                            </a>
                          )}
                          {m.text}
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={chatBottomRef} />
                </div>

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
        )}

        <SiriWave visible={showSiriWave} message={displayText} />
      </div>

      <SettingsModal />
    </>
  )
}
```

- [ ] **Step 2: Update `useWebSocket.ts` to include `data` field on WSMessage type**

Open `frontend/hooks/useWebSocket.ts` and replace the `WSMessage` type:

```typescript
export type WSMessage = {
  type: string
  text?: string
  session_id?: number
  success?: boolean
  data?: string   // base64 image data for image messages
  path?: string   // file path for screenshots
}
```

- [ ] **Step 3: Rebuild Next.js**

```
cd frontend && npm run build
```

Expected: Build succeeds with routes: `/`, `/assistant`

- [ ] **Step 4: Run full backend test suite — no regressions**

```
cd .. && python -m pytest tests/ -v
```

Expected: 27+ tests PASS (22 original + new windows tests)

- [ ] **Step 5: Commit**

```
git add frontend/pages/assistant.tsx frontend/hooks/useWebSocket.ts
git commit -m "feat: assistant.tsx — visible chat panel, image message rendering, HUD 40vh"
```

---

## Task 6: Integration smoke test

- [ ] **Step 1: Start the app**

```
python run.py
```

Expected: browser opens to `http://localhost:3000`, face auth runs, JARVIS HUD appears with session tabs and empty chat panel below.

- [ ] **Step 2: Test screenshot command**

Type `take a screenshot` in the chat input and press Enter.

Expected:
- SiriWave activates briefly
- Screenshot thumbnail appears in chat panel
- pyttsx3 speaks `"Screenshot saved to desktop"`
- A `.jpg` file appears on your Desktop

- [ ] **Step 3: Test system info command**

Type `what is my cpu usage`.

Expected: Response like `"CPU is at 34%"` appears in chat, spoken aloud.

- [ ] **Step 4: Test window minimize**

Open Notepad. Type `minimize notepad`.

Expected: Notepad minimizes to taskbar, response `"Minimized notepad"` appears in chat.

- [ ] **Step 5: Final commit**

```
git add -A
git commit -m "feat: Phase 2A Windows Automation complete — screenshot, sysinfo, window management"
```

---

## Self-Review

**Spec coverage:**
- [x] `take_screenshot()` → Task 1
- [x] `get_system_info()` → Task 1
- [x] `minimize_window()` / `maximize_window()` / `focus_window()` → Task 2
- [x] 5 new intents in `classify_command()` → Task 3
- [x] `run_command()` updated → Task 3
- [x] `ws.py` dict response routing → Task 4
- [x] Chat history panel (35vh, scrollable) → Task 5
- [x] Image message rendering (base64 thumbnail, clickable) → Task 5
- [x] HUD height reduced to 40vh → Task 5
- [x] 9 new tests → Tasks 1 + 2 + 3
- [x] `WSMessage` type updated for `data` field → Task 5

**Type consistency:**
- `take_screenshot()` returns `dict` with keys `text`, `image_b64`, `path` — used consistently in `ws.py` (`response["image_b64"]`, `response["path"]`, `response["text"]`) ✓
- `WSMessage.data` added in Task 5 Step 2 — accessed as `(msg as any).data` in `handleWSMessage` ✓ (could use typed cast instead, but `as any` is safe here since the type is narrowed by `msg.type === 'image'`)
- `_find_window()` is a private helper inside `windows.py`, not exported — consistent ✓
