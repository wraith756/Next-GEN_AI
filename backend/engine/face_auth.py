import os
import cv2

_AUTH_DB = os.path.join(os.path.dirname(__file__), "auth", "database")


def authenticate() -> bool:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False
    try:
        ret, frame = cap.read()
        if not ret:
            return False
        tmp = os.path.join(os.path.dirname(__file__), "_tmp_face.jpg")
        cv2.imwrite(tmp, frame)
        from deepface import DeepFace
        result = DeepFace.find(
            img_path=tmp,
            db_path=_AUTH_DB,
            enforce_detection=False,
            silent=True,
        )
        return bool(result and len(result[0]) > 0)
    except Exception:
        return False
    finally:
        cap.release()
