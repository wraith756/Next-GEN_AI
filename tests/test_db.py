import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base, SysCommand, ChatSession, ChatMessage, SessionSummary


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_sys_command_crud(session):
    cmd = SysCommand(name="notepad", path="C:/Windows/notepad.exe")
    session.add(cmd)
    session.commit()
    result = session.query(SysCommand).filter_by(name="notepad").first()
    assert result.path == "C:/Windows/notepad.exe"


def test_chat_session_with_messages(session):
    sess = ChatSession(title="Chat #1")
    session.add(sess)
    session.commit()
    msg = ChatMessage(session_id=sess.id, role="user", content="hello")
    session.add(msg)
    session.commit()
    assert session.query(ChatMessage).filter_by(session_id=sess.id).count() == 1


def test_session_summary(session):
    sess = ChatSession(title="Chat #1")
    session.add(sess)
    session.commit()
    summary = SessionSummary(session_id=sess.id, summary="User asked about AI.", message_count=10)
    session.add(summary)
    session.commit()
    assert session.query(SessionSummary).filter_by(session_id=sess.id).first().message_count == 10
