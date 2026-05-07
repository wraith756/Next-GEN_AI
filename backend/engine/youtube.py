import re
import webbrowser
from urllib.parse import quote_plus

from backend.engine.config import settings

_YT_URL_RE = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)[\w-]+'
)


def extract_youtube_url(text: str):
    m = _YT_URL_RE.search(text)
    return m.group(0) if m else None


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


def open_youtube() -> str:
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube"


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

    # Fallback: open search results page
    webbrowser.open("https://www.youtube.com/results?search_query=" + quote_plus(term))
    return f"Searching YouTube for {term}"


def search_youtube(query: str) -> str:
    term = query.lower()
    for w in ("search youtube for", "youtube search for", "search youtube", "youtube search"):
        term = term.replace(w, "")
    term = term.strip()
    webbrowser.open("https://www.youtube.com/results?search_query=" + quote_plus(term))
    return f"Searching YouTube for {term}"


def get_video_details(url: str) -> str:
    try:
        import yt_dlp
        opts = {"quiet": True, "no_warnings": True, "extract_flat": False}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get("title", "Unknown")
        channel = info.get("uploader", "Unknown")
        views = info.get("view_count")
        duration = info.get("duration")

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


def summarize_video(url: str) -> str:
    if not url:
        return "Please provide a YouTube URL to summarize"

    video_id = extract_video_id(url)
    if not video_id:
        return "Could not extract video ID from that URL"

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        text = " ".join(snippet.text for snippet in transcript)
        words = text.split()
        if len(words) > 3000:
            text = " ".join(words[:3000]) + "..."
    except Exception:
        return "No transcript available for this video"

    try:
        from groq import Groq
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
