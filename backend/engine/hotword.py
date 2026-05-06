import threading
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

_callbacks = []
_stop_event = threading.Event()

# Uses built-in "hey_jarvis" model for Phase 1.
# Replace MODEL_PATH with path to a custom .onnx file for "Next Gen" wake word.
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
    chunk_size = 1280
    sample_rate = 16000

    def audio_callback(indata, frames, time_info, status):
        if _stop_event.is_set():
            raise sd.CallbackStop()
        audio_np = indata[:, 0].astype(np.float32)
        audio_int16 = (audio_np * 32767).astype(np.int16)
        prediction = oww.predict(audio_int16)
        for score in prediction.values():
            if score > 0.5:
                print("HOTWORD DETECTED")
                _fire_callbacks()
                break

    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            blocksize=chunk_size,
            callback=audio_callback,
        ):
            _stop_event.wait()
    except Exception as e:
        print(f"Hotword error: {e}")


def stop() -> None:
    _stop_event.set()
