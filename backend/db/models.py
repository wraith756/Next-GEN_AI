from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SysCommand(Base):
    __tablename__ = "sys_command"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    path = Column(Text)


class WebCommand(Base):
    __tablename__ = "web_command"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    url = Column(Text)


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    mobile_no = Column(Text)
    email = Column(Text)
    address = Column(Text)


class UserInfo(Base):
    __tablename__ = "info"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    designation = Column(Text)
    mobileno = Column(Text)
    email = Column(Text)
    city = Column(Text)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True)
    title = Column(Text, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role = Column(Text)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class SessionSummary(Base):
    __tablename__ = "session_summaries"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    summary = Column(Text)
    message_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
