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


def compress_history(messages: list) -> str:
    lines = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    prompt = f"Summarize this conversation in 2-3 sentences, preserving key facts:\n\n{lines}"
    resp = _client.chat.completions.create(
        model=settings.fast_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    return resp.choices[0].message.content


def _build_context(session_id: int):
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
        context = []
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
