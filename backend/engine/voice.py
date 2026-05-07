import io
import threading
import pyttsx3
from groq import Groq
from backend.engine.config import settings

_engine_lock = threading.Lock()
_engine = None


def _get_engine():
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
    audio_file.name = "audio.webm"
    result = client.audio.transcriptions.create(
        model=settings.whisper_model,
        file=audio_file,
        language="en",
    )
    return result.text.strip()
