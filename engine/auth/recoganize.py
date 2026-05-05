import cv2
import os
from deepface import DeepFace

def AuthenticateFace():

    cam = cv2.VideoCapture(0)
    flag = 0

    database_path = "engine/auth/database"

    print("Looking for authorized face...")

    while True:
        ret, frame = cam.read()

        try:
            # Search face inside database folder
            result = DeepFace.find(
                img_path=frame,
                db_path=database_path,
                model_name="Facenet",
                enforce_detection=False
            )

            # If match found
            if len(result[0]) > 0:
                print("Authorized User Detected!")
                flag = 1
                break

        except:
            pass

        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

    return flag
