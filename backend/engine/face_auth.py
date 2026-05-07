import os
import cv2

_AUTH_DB = os.path.join(os.path.dirname(__file__), "auth", "database")


def authenticate() -> bool:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Face auth: could not open camera")
        return False

    try:
        # Warm up camera — discard first 15 frames so exposure settles
        for _ in range(15):
            cap.read()

        from deepface import DeepFace

        # Try up to 5 frames to find a match
        for attempt in range(5):
            ret, frame = cap.read()
            if not ret:
                continue

            tmp = os.path.join(os.path.dirname(__file__), "_tmp_face.jpg")
            cv2.imwrite(tmp, frame)

            try:
                result = DeepFace.find(
                    img_path=tmp,
                    db_path=_AUTH_DB,
                    model_name="Facenet",
                    enforce_detection=False,
                    silent=True,
                )
                if result and len(result[0]) > 0:
                    print(f"Face auth: match found on attempt {attempt + 1}")
                    return True
            except Exception as e:
                print(f"Face auth attempt {attempt + 1} error: {e}")

        print("Face auth: no match after 5 attempts")
        return False

    finally:
        cap.release()
