# YouTube Integration — Phase 2B Design Spec
**Date:** 2026-05-07
**Scope:** Full YouTube voice/text command integration — open, play, search, video details, AI summary. No Google API key required.

---

## Decisions Made

| Concern | Decision |
|---|---|
| Play behavior | Find top result URL via `youtube-search-python`, open directly in browser (auto-plays) |
| Search behavior | Open YouTube search results page in browser |
| Transcript source | `youtube-transcript-api` (no API key) |
| Video metadata | `yt-dlp` Python API (no API key, handles all URL formats) |
| AI summary model | Groq `llama-3.3-70b-versatile` |
| URL input method | Typed in chat input (users cannot speak URLs) |
| New libraries | `youtube-search-python`, `youtube-transcript-api`, `yt-dlp` |

---

## Architecture

**One new file:** `backend/engine/youtube.py`

**One file modified:** `backend/engine/automation.py` — 4 new intents, `youtube` intent upgraded, old `play_youtube()` deleted

**`requirements.txt`:** Add 3 new packages

---

## `backend/engine/youtube.py`

### `extract_youtube_url(text: str) → str | None`
Regex helper used by `summarize_video()` and `get_video_details()`.
Matches:
- `https://www.youtube.com/watch?v=XXXXXXXXXXX`
- `https://youtu.be/XXXXXXXXXXX`
- `https://www.youtube.com/shorts/XXXXXXXXXXX`

Returns the matched URL string or `None` if no YouTube URL found in text.

```python
import re

_YT_URL_RE = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)[\w-]+'
)

def extract_youtube_url(text: str):
    m = _YT_URL_RE.search(text)
    return m.group(0) if m else None
```

### `extract_video_id(url: str) → str | None`
Extracts the 11-character video ID from any YouTube URL format. Used by `summarize_video()`.

```python
def extract_video_id(url: str):
    patterns = [
        r'v=([\w-]{11})',
        r'youtu\.be/([\w-]{11})',
        r'shorts/([\w-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None
```

### `open_youtube() → str`
```python
def open_youtube() -> str:
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube"
```

### `play_on_youtube(query: str) → str`
Strips trigger words, searches for top result, opens the video URL directly.

```python
def play_on_youtube(query: str) -> str:
    term = query.lower()
    for w in ("play", "on youtube", "youtube"):
        term = term.replace(w, "")
    term = term.strip()
    if not term:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube"
    try:
        from youtubesearchpython import VideosSearch
        results = VideosSearch(term, limit=1).result()
        videos = results.get("result", [])
        if videos:
            url = videos[0]["link"]
            title = videos[0].get("title", term)
            webbrowser.open(url)
            return f"Playing {title} on YouTube"
    except Exception:
        pass
    # Fallback: open search results
    webbrowser.open("https://www.youtube.com/results?search_query=" + quote_plus(term))
    return f"Searching YouTube for {term}"
```

### `search_youtube(query: str) -> str`
```python
def search_youtube(query: str) -> str:
    term = query.lower()
    for w in ("search youtube for", "youtube search for", "search youtube", "youtube search"):
        term = term.replace(w, "")
    term = term.strip()
    webbrowser.open("https://www.youtube.com/results?search_query=" + quote_plus(term))
    return f"Searching YouTube for {term}"
```

### `get_video_details(url: str) → str`
Uses `yt-dlp` Python API to extract metadata without downloading.

```python
def get_video_details(url: str) -> str:
    try:
        import yt_dlp
        opts = {"quiet": True, "no_warnings": True, "extract_flat": False}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        title = info.get("title", "Unknown")
        channel = info.get("uploader", "Unknown")
        views = info.get("view_count")
        duration = info.get("duration")  # seconds

        views_str = f"{views:,}" if views else "unknown"
        if duration:
            mins, secs = divmod(int(duration), 60)
            dur_str = f"{mins} minutes {secs} seconds"
        else:
            dur_str = "unknown"

        return (
            f"Title: {title}. "
            f"Channel: {channel}. "
            f"Duration: {dur_str}. "
            f"Views: {views_str}."
        )
    except Exception as e:
        return f"Could not fetch video details: {e}"
```

### `summarize_video(url: str) → str`
Fetches transcript via `youtube-transcript-api`, truncates to 3000 words, summarizes via Groq.

```python
def summarize_video(url: str) -> str:
    video_id = extract_video_id(url)
    if not video_id:
        return "Could not extract video ID from that URL"
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(entry["text"] for entry in transcript)
        # Truncate to ~3000 words for Groq context safety
        words = text.split()
        if len(words) > 3000:
            text = " ".join(words[:3000]) + "..."
    except Exception:
        return "No transcript available for this video"

    try:
        from groq import Groq
        from backend.engine.config import settings
        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            model=settings.smart_model,
            messages=[{
                "role": "user",
                "content": f"Summarize this YouTube video transcript in 3-4 sentences:\n\n{text}"
            }],
            max_tokens=200,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Could not summarize: {e}"
```

---

## `automation.py` Changes

### New intents in `classify_command()`
Inserted **before** the existing `"on youtube"` check and **before** the `"open "` check:

```python
# YouTube — checked before "open" and existing youtube intent
if q == "open youtube" or q.startswith("open youtube"):
    return "yt_open"
if any(k in q for k in ("search youtube", "youtube search")):
    return "yt_search"
if ("summarize" in q or "summary" in q) and extract_youtube_url(q):
    return "yt_summarize"
if any(k in q for k in ("video details", "get details", "youtube details")) and extract_youtube_url(q):
    return "yt_details"
# existing: "on youtube" → "youtube"  (kept, handler upgraded)
```

### New/updated branches in `run_command()`
```python
if intent == "yt_open":
    return youtube.open_youtube(), False
if intent == "yt_search":
    return youtube.search_youtube(query), False
if intent == "yt_summarize":
    url = youtube.extract_youtube_url(query)
    return youtube.summarize_video(url), False
if intent == "yt_details":
    url = youtube.extract_youtube_url(query)
    return youtube.get_video_details(url), False
if intent == "youtube":
    return youtube.play_on_youtube(query), False   # replaces old play_youtube()
```

### New import in `automation.py`
```python
from backend.engine import youtube
from backend.engine.youtube import extract_youtube_url
```
(`extract_youtube_url` is needed directly in `classify_command()` to detect URL-based intents.)

### Deleted from `automation.py`
- `play_youtube()` function (replaced by `youtube.play_on_youtube()`)
- `from backend.engine.helper import extract_yt_term` import (no longer needed)

---

## Command Examples

| User types/says | Intent | Result |
|---|---|---|
| `"open youtube"` | `yt_open` | youtube.com opens in browser |
| `"play Blinding Lights on youtube"` | `youtube` | Top result video opens, auto-plays |
| `"search youtube for lo-fi music"` | `yt_search` | YouTube search results page opens |
| `"video details https://youtu.be/abc123"` | `yt_details` | Speaks title, channel, duration, views |
| `"summarize https://youtube.com/watch?v=abc123"` | `yt_summarize` | Fetches transcript, Groq summary spoken + in chat |

---

## Requirements Updates

Add to `requirements.txt`:
```
youtube-search-python
youtube-transcript-api
yt-dlp
```

---

## Tests

**`tests/test_youtube.py`**

| Test | What it checks |
|---|---|
| `test_extract_youtube_url_watch` | Extracts from `youtube.com/watch?v=` |
| `test_extract_youtube_url_short` | Extracts from `youtu.be/` |
| `test_extract_youtube_url_shorts` | Extracts from `youtube.com/shorts/` |
| `test_extract_youtube_url_none` | Returns `None` for non-YouTube text |
| `test_extract_video_id_watch` | Extracts 11-char ID from watch URL |
| `test_extract_video_id_short` | Extracts ID from youtu.be URL |
| `test_search_youtube_opens_browser` | Mocks `webbrowser.open`, checks URL |
| `test_open_youtube_opens_browser` | Mocks `webbrowser.open`, checks URL |
| `test_classify_yt_open` | `classify_command("open youtube")` → `"yt_open"` |
| `test_classify_yt_search` | `classify_command("search youtube for jazz")` → `"yt_search"` |
| `test_classify_youtube_play` | `classify_command("play despacito on youtube")` → `"youtube"` |
| `test_classify_yt_summarize` | `classify_command("summarize https://youtu.be/abc1234abcd")` → `"yt_summarize"` |
| `test_classify_yt_details` | `classify_command("video details https://youtu.be/abc1234abcd")` → `"yt_details"` |
| `test_summarize_no_transcript` | Mocks `YouTubeTranscriptApi` to raise → returns "No transcript available" |
| `test_summarize_calls_groq` | Mocks transcript + Groq → returns summary string |

`play_on_youtube` and `get_video_details` are not unit-tested directly (require live network/browser) — verified manually in integration smoke test.

---

## Files Changed

| File | Change |
|---|---|
| `backend/engine/youtube.py` | **NEW** — 7 functions |
| `backend/engine/automation.py` | 4 new intents, delete `play_youtube()`, upgrade `youtube` intent |
| `requirements.txt` | Add 3 packages |
| `tests/test_youtube.py` | **NEW** — 15 tests |
