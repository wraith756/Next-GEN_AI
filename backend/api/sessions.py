from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import ChatSession, ChatMessage

router = APIRouter()


class SessionIn(BaseModel):
    title: str


class SessionOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}


@router.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(ChatSession).order_by(ChatSession.created_at).all()


@router.post("/api/sessions", response_model=SessionOut, status_code=201)
def create_session(body: SessionIn, db: Session = Depends(get_db)):
    sess = ChatSession(title=body.title)
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


@router.put("/api/sessions/{session_id}", response_model=SessionOut)
def rename_session(session_id: int, body: SessionIn, db: Session = Depends(get_db)):
    sess = db.query(ChatSession).filter_by(id=session_id).first()
    if not sess:
        raise HTTPException(404, "Session not found")
    sess.title = body.title
    sess.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sess)
    return sess


@router.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    sess = db.query(ChatSession).filter_by(id=session_id).first()
    if not sess:
        raise HTTPException(404)
    db.delete(sess)
    db.commit()


@router.get("/api/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_messages(session_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ChatMessage)
        .filter_by(session_id=session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
