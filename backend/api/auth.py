import threading
from fastapi import APIRouter
from pydantic import BaseModel
from backend.engine import face_auth, voice

router = APIRouter()


class AuthResult(BaseModel):
    success: bool
    message: str


@router.post("/api/auth/face", response_model=AuthResult)
def face_authenticate():
    success = face_auth.authenticate()
    if success:
        threading.Thread(
            target=voice.speak,
            args=("Face Authentication Successful. Hello, Welcome Sir.",),
            daemon=True,
        ).start()
        return AuthResult(success=True, message="Authenticated")
    threading.Thread(
        target=voice.speak, args=("Face Authentication Failed",), daemon=True
    ).start()
    return AuthResult(success=False, message="Authentication failed")
