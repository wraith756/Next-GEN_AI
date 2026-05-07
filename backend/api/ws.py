import asyncio
import json
import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.engine import voice, automation
from backend.engine import ai as ai_engine
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
        if ws in _connections:
            _connections.remove(ws)


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
                    await _handle_command(ws, msg["text"], session_id)
            elif "bytes" in data:
                session_id = _get_or_create_default_session()
                await ws.send_json({"type": "display", "text": "Recognizing..."})
                try:
                    transcript = voice.transcribe(data["bytes"])
                    await ws.send_json({"type": "transcript", "text": transcript})
                    if transcript:
                        await _handle_command(ws, transcript, session_id)
                except Exception as e:
                    await ws.send_json({"type": "error", "text": str(e)})
    except WebSocketDisconnect:
        if ws in _connections:
            _connections.remove(ws)
