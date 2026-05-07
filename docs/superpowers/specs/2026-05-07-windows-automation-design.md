# Windows Automation+ — Phase 2A Design Spec
**Date:** 2026-05-07
**Scope:** Add screenshot, system info, and window management commands to the existing JARVIS assistant. No new dependencies required.

---

## Decisions Made

| Concern | Decision |
|---|---|
| Architecture | New `windows.py` module; `automation.py` gains 5 new intents |
| Screenshot output | Save to desktop + base64 thumbnail in chat panel |
| Chat history display | Scrollable panel below JARVIS HUD (always visible, max 35vh) |
| Screenshot size | JPEG, max 200px wide thumbnail in chat; full-size saved to disk |
| System info scope | CPU, RAM, disk (C:\\), battery — detected from query keywords |
| Window management | minimize / maximize / focus via pygetwindow |
| New WS message type | `{"type": "image", "data": "<b64>", "path": "...", "text": "..."}` |

---

## Architecture

**One new file:** `backend/engine/windows.py`

**Two files modified:**
- `backend/engine/automation.py` — 5 new intents in `classify_command()`, 5 new delegation calls in `run_command()`
- `frontend/pages/assistant.tsx` — visible chat history panel + image message rendering

**No new dependencies.** `pyautogui`, `pygetwindow`, and `psutil` already installed.

---

## `backend/engine/windows.py`

Five pure functions, each returns a plain value (no side-effects beyond disk write for screenshot):

### `take_screenshot() → dict`
- Capture full screen with `pyautogui.screenshot()`
- Save as `screenshot_YYYY-MM-DD_HH-MM-SS.jpg` to `~/Desktop` (fallback: current dir)
- Convert saved file to base64 JPEG string
- Return `{"text": "Screenshot saved to desktop", "image_b64": "<str>", "path": "<str>"}`

### `get_system_info(query: str) → str`
Detects metric from query keywords, returns spoken-style string:

| Keyword(s) | psutil call | Example response |
|---|---|---|
| `"cpu"` | `cpu_percent(interval=1)` | `"CPU is at 34%"` |
| `"ram"`, `"memory"` | `virtual_memory()` | `"RAM: 6.2 GB used of 16 GB (39%)"` |
| `"disk"`, `"storage"`, `"drive"` | `disk_usage("C:\\")` | `"C drive: 120 GB free of 500 GB"` |
| `"battery"` | `sensors_battery()` | `"Battery at 78%, plugged in"` |
| anything else | all four | Multi-line summary of all metrics |

### `minimize_window(query: str) → str`
- Strip `"minimize"` from query
- Fuzzy-match against `pygetwindow.getAllTitles()` (substring match, case-insensitive)
- Call `win.minimize()`
- Return `"Minimized <app>"` or `"Window not found"`

### `maximize_window(query: str) → str`
- Same pattern as minimize, call `win.maximize()`
- Return `"Maximized <app>"` or `"Window not found"`

### `focus_window(query: str) → str`
- Strip `"focus"` / `"switch to"` from query
- Find window, call `win.activate()`
- Return `"Switched to <app>"` or `"Window not found"`

---

## `automation.py` Changes

### New intents in `classify_command()`

```
"screenshot" or "take a screenshot"             → "screenshot"
"cpu", "ram", "memory", "disk", "battery",
  "system info", "how much"                     → "sysinfo"
"minimize "                                     → "win_minimize"
"maximize "                                     → "win_maximize"
"focus ", "switch to "                          → "win_focus"
```

Order matters: these are inserted **before** the `"open "` check so `"open ..."` doesn't consume `"focus chrome"`.

### New branches in `run_command()`
```python
if intent == "screenshot":
    return windows.take_screenshot(), False   # returns dict, not str
if intent == "sysinfo":
    return windows.get_system_info(query), False
if intent == "win_minimize":
    return windows.minimize_window(query), False
if intent == "win_maximize":
    return windows.maximize_window(query), False
if intent == "win_focus":
    return windows.focus_window(query), False
```

`run_command()` return type changes from `tuple[str, bool]` to `tuple[str | dict, bool]`. The WebSocket handler in `ws.py` checks `isinstance(response, dict)` to decide whether to send `{"type": "image"}` or `{"type": "response"}`.

---

## WebSocket Protocol Addition

**New message type — Backend → Frontend:**
```json
{
  "type": "image",
  "data": "<base64 JPEG string>",
  "path": "C:/Users/HP/Desktop/screenshot_2026-05-07_14-30-00.jpg",
  "text": "Screenshot saved to desktop"
}
```

**`ws.py` change:** After `run_command()` returns, check if response is a dict:
```python
if isinstance(response, dict) and "image_b64" in response:
    await ws.send_json({
        "type": "image",
        "data": response["image_b64"],
        "path": response["path"],
        "text": response["text"],
        "session_id": session_id,
    })
else:
    await ws.send_json({"type": "response", "text": response, "session_id": session_id})
# Both paths also save the message to chat_messages via _save_message() as usual.
```

---

## Frontend Changes (`assistant.tsx`)

### Layout
```
[ Session Tabs ]
[ JARVIS HUD orb / SiriWave ]
[ Chat history panel — scrollable, max-height: 35vh ]   ← NEW
[ Input bar ]
```

### Message state
```typescript
type ChatMsg = { role: 'user' | 'assistant'; text: string; image?: string }
const [messages, setMessages] = useState<ChatMsg[]>([])
```

### WebSocket handler additions
```typescript
case 'transcript':
  setMessages(p => [...p, { role: 'user', text: msg.text ?? '' }])
  break
case 'response':
  setMessages(p => [...p, { role: 'assistant', text: msg.text ?? '' }])
  break
case 'image':
  setMessages(p => [...p, {
    role: 'assistant',
    text: msg.text ?? 'Screenshot saved',
    image: msg.data,
  }])
  break
```

### Chat panel render
```tsx
<div style={{ maxHeight: '35vh', overflowY: 'auto', padding: '0 20px' }} ref={chatBottomRef}>
  {messages.map((m, i) => (
    <div key={i} className={`row ${m.role === 'user' ? 'justify-content-end' : 'justify-content-start'} mb-2`}>
      <div className="width-size">
        <div className={m.role === 'user' ? 'sender_message' : 'receiver_message'}>
          {m.image && (
            <a href={`data:image/jpeg;base64,${m.image}`} target="_blank" rel="noreferrer">
              <img src={`data:image/jpeg;base64,${m.image}`} style={{ maxWidth: 200, display: 'block', marginBottom: 6 }} alt="screenshot" />
            </a>
          )}
          {m.text}
        </div>
      </div>
    </div>
  ))}
  <div ref={chatBottomRef} />
</div>
```
`chatBottomRef` is a `useRef` scrolled into view on every new message via `useEffect`.

---

## Tests

**`tests/test_windows.py`**

| Test | What it checks |
|---|---|
| `test_screenshot_returns_dict` | Returns dict with `text`, `image_b64`, `path` keys |
| `test_sysinfo_cpu` | Query containing "cpu" returns string with "%" |
| `test_sysinfo_ram` | Query containing "ram" returns string with "GB" |
| `test_sysinfo_disk` | Query containing "disk" returns string with "GB" |
| `test_sysinfo_all` | Generic query returns multi-line string |
| `test_classify_screenshot` | `classify_command("take a screenshot")` → `"screenshot"` |
| `test_classify_sysinfo_cpu` | `classify_command("what is my cpu usage")` → `"sysinfo"` |
| `test_classify_win_minimize` | `classify_command("minimize chrome")` → `"win_minimize"` |
| `test_classify_win_focus` | `classify_command("focus notepad")` → `"win_focus"` |

Screenshot test mocks `pyautogui.screenshot()` to avoid requiring a display.
System info tests run against live `psutil` (no mock needed — works headless).

---

## Files Changed

| File | Change |
|---|---|
| `backend/engine/windows.py` | **NEW** — 5 handler functions |
| `backend/engine/automation.py` | Add 5 intents + 5 `run_command()` branches |
| `backend/api/ws.py` | Add `isinstance(response, dict)` check → send image type |
| `frontend/pages/assistant.tsx` | Visible chat panel + image message rendering |
| `tests/test_windows.py` | **NEW** — 9 tests |
