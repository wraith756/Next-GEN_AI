from unittest.mock import patch, MagicMock
from backend.engine.youtube import (
    extract_youtube_url,
    extract_video_id,
    open_youtube,
    search_youtube,
)
from backend.engine.automation import classify_command


# --- URL helpers ---

def test_extract_youtube_url_watch():
    text = "summarize https://www.youtube.com/watch?v=dQw4w9WgXcQ please"
    assert extract_youtube_url(text) == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_extract_youtube_url_short():
    text = "video details https://youtu.be/dQw4w9WgXcQ"
    assert extract_youtube_url(text) == "https://youtu.be/dQw4w9WgXcQ"


def test_extract_youtube_url_shorts():
    text = "summarize https://www.youtube.com/shorts/abc1234abcd"
    assert extract_youtube_url(text) == "https://www.youtube.com/shorts/abc1234abcd"


def test_extract_youtube_url_none():
    assert extract_youtube_url("what is the weather today") is None


def test_extract_video_id_watch():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_short():
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_shorts():
    assert extract_video_id("https://www.youtube.com/shorts/abc1234abcd") == "abc1234abcd"


# --- Browser openers ---

def test_open_youtube_opens_browser():
    with patch("webbrowser.open") as mock_open:
        result = open_youtube()
    mock_open.assert_called_once_with("https://www.youtube.com")
    assert result == "Opening YouTube"


def test_search_youtube_opens_browser():
    with patch("webbrowser.open") as mock_open:
        result = search_youtube("search youtube for lo-fi music")
    mock_open.assert_called_once()
    url = mock_open.call_args[0][0]
    assert "youtube.com/results" in url
    assert "lo" in url or "fi" in url or "music" in url
    assert "Searching YouTube" in result


# --- Classify command ---

def test_classify_yt_open():
    assert classify_command("open youtube") == "yt_open"


def test_classify_yt_search():
    assert classify_command("search youtube for jazz music") == "yt_search"


def test_classify_youtube_play():
    assert classify_command("play despacito on youtube") == "youtube"


def test_classify_yt_summarize():
    assert classify_command("summarize https://youtu.be/dQw4w9WgXcQ") == "yt_summarize"


def test_classify_yt_details():
    assert classify_command("video details https://youtu.be/dQw4w9WgXcQ") == "yt_details"


# --- Summarize edge cases ---

def test_summarize_no_transcript():
    from backend.engine.youtube import summarize_video
    mock_api = MagicMock()
    mock_api.fetch.side_effect = Exception("No transcript")
    with patch("youtube_transcript_api.YouTubeTranscriptApi", return_value=mock_api):
        result = summarize_video("https://youtu.be/dQw4w9WgXcQ")
    assert "No transcript available" in result


def test_summarize_calls_groq():
    from backend.engine.youtube import summarize_video

    snippet = MagicMock()
    snippet.text = "Hello world this is a test video about Python programming."
    mock_api = MagicMock()
    mock_api.fetch.return_value = [snippet]

    mock_groq = MagicMock()
    mock_groq.chat.completions.create.return_value.choices[0].message.content = "A Python tutorial video."

    with patch("youtube_transcript_api.YouTubeTranscriptApi", return_value=mock_api), \
         patch("groq.Groq", return_value=mock_groq):
        result = summarize_video("https://youtu.be/dQw4w9WgXcQ")

    assert result == "A Python tutorial video."
    mock_groq.chat.completions.create.assert_called_once()
