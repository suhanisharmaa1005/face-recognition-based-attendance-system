
import cv2
import json
import sqlite3
import numpy as np
import sys
import os

DETECTOR_PATH = "models/face_detection_yunet_2023mar.onnx"
RECOGNIZER_PATH = "models/face_recognition_sface_2021dec.onnx"

# Get student ID from command line
if len(sys.argv) < 2:
    print("Student ID is required.")
    sys.exit(1)

student_id = int(sys.argv[1])

connection = sqlite3.connect("attendance.db")
cursor = connection.cursor()

cursor.execute(
    "SELECT name, face_encoding FROM students WHERE id = ?",
    (student_id,)
)
student = cursor.fetchone()

if not student:
    connection.close()
    print("Student not found.")
    sys.exit(1)

name, old_encoding = student

if old_encoding:
    connection.close()
    print("This student already has registered face data.")
    print("Use the replace option only after confirming with the user.")
    sys.exit(1)

detector = cv2.FaceDetectorYN.create(
    DETECTOR_PATH, "", (320, 320), 0.8, 0.3, 5000
)

recognizer = cv2.FaceRecognizerSF.create(
    RECOGNIZER_PATH, ""
)

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    connection.close()
    print("Cannot open webcam.")
    sys.exit(1)

angles = [
    "Look straight",
    "Turn slightly left",
    "Turn slightly right",
    "Look slightly up",
    "Look slightly down"
]

features = []

print(f"Registering face for: {name}")
print("Press C to capture each angle.")
print("Press Q to cancel.")

try:
    for angle in angles:
        captured = False

        while not captured:
            success, frame = camera.read()

            if not success:
                raise RuntimeError("Could not read webcam.")

            height, width = frame.shape[:2]
            detector.setInputSize((width, height))

            _, faces = detector.detect(frame)

            cv2.putText(
                frame, angle, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (0, 255, 0), 2
            )

            if faces is not None and len(faces) > 0:
                cv2.putText(
                    frame, "Face detected - Press C",
                    (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2
                )
            else:
                cv2.putText(
                    frame, "No face detected",
                    (20, 80), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 0, 255), 2
                )

            cv2.imshow("Student Face Registration", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                raise KeyboardInterrupt

            if key == ord("c") and faces is not None and len(faces) > 0:
                face = faces[0]
                aligned_face = recognizer.alignCrop(frame, face)
                feature = recognizer.feature(aligned_face)

                features.append(feature.flatten().tolist())
                captured = True

                print(f"{angle} captured ({len(features)}/5)")

    # Save all five face samples
    cursor.execute(
        "UPDATE students SET face_encoding = ? WHERE id = ?",
        (json.dumps(features), student_id)
    )
    connection.commit()

    print(f"Face registration successful for {name}!")

except KeyboardInterrupt:
    print("Registration cancelled. No new face data saved.")

except Exception as error:
    print("Registration failed:", error)

finally:
    camera.release()
    cv2.destroyAllWindows()
    connection.close()
