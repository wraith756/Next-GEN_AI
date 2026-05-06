import cv2
import os

def capture_face():

    user_id = input("Enter Numeric User ID: ")

    save_dir = "engine/auth/database"
    os.makedirs(save_dir, exist_ok=True)

    save_path = f"{save_dir}/{user_id}.jpg"

    # Load face detector
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    cam = cv2.VideoCapture(0)

    print("Look at the camera... Press SPACE to capture")

    while True:
        ret, frame = cam.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            face_crop = frame[y:y+h, x:x+w]

        cv2.imshow("Capture Face", frame)

        key = cv2.waitKey(1)

        # Press SPACE to capture
        if key == 32:
            if len(faces) > 0:
                cv2.imwrite(save_path, face_crop)
                print("Face Captured Successfully!")
                break
            else:
                print("No face detected. Try again.")

        # Press ESC to exit
        if key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

capture_face()
