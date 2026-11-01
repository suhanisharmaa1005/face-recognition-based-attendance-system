
import cv2
import json
import sqlite3
import numpy as np
from datetime import datetime

DETECTOR_PATH = "models/face_detection_yunet_2023mar.onnx"
RECOGNIZER_PATH = "models/face_recognition_sface_2021dec.onnx"

MATCH_THRESHOLD = 0.363
marked_this_session = set()

# Load AI models
detector = cv2.FaceDetectorYN.create(
    DETECTOR_PATH, "", (320, 320), 0.8, 0.3, 5000
)

recognizer = cv2.FaceRecognizerSF.create(
    RECOGNIZER_PATH, ""
)

# Connect database
connection = sqlite3.connect("attendance.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT id, name, face_encoding
    FROM students
    WHERE face_encoding IS NOT NULL
""")

students = cursor.fetchall()

if not students:
    connection.close()
    raise SystemExit("No registered faces found.")

registered_students = []

for student_id, name, encoding_json in students:
    saved_data = json.loads(encoding_json)

    # Support old single-face and new multi-angle registrations
    if (
        isinstance(saved_data, list)
        and len(saved_data) > 0
        and isinstance(saved_data[0], (int, float))
    ):
        saved_data = [saved_data]

    features = [
        np.asarray(feature, dtype=np.float32).reshape(1, -1)
        for feature in saved_data
    ]

    registered_students.append((student_id, name, features))
    print(f"{name}: {len(features)} face samples loaded")

print(f"\nTotal registered students: {len(registered_students)}")

# Open camera
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    connection.close()
    raise SystemExit("Cannot open webcam.")

print("\nAttendance started.")
print("Press Q in the camera window to stop.")

try:
    while True:
        success, frame = camera.read()

        if not success:
            break

        height, width = frame.shape[:2]
        detector.setInputSize((width, height))
        _, faces = detector.detect(frame)

        if faces is not None:
            for face in faces:

                x, y, w, h = map(int, face[:4])

                aligned_face = recognizer.alignCrop(frame, face)
                current_feature = recognizer.feature(
                    aligned_face
                ).reshape(1, -1)

                best_score = -1.0
                best_student = None

                # Compare with every student's saved angles
                for student_id, name, saved_features in registered_students:

                    student_score = max(
                        recognizer.match(
                            current_feature,
                            saved_feature,
                            cv2.FaceRecognizerSF_FR_COSINE
                        )
                        for saved_feature in saved_features
                    )

                    if student_score > best_score:
                        best_score = student_score
                        best_student = (student_id, name)

                if best_student and best_score >= MATCH_THRESHOLD:
                    student_id, name = best_student
                    label = f"{name} ({best_score:.2f})"
                    color = (0, 200, 0)

                    if student_id not in marked_this_session:
                        today = datetime.now().strftime("%Y-%m-%d")
                        now = datetime.now().strftime("%H:%M:%S")

                        try:
                            cursor.execute("""
                                INSERT INTO attendance
                                (student_id, attendance_date,
                                 attendance_time, status)
                                VALUES (?, ?, ?, 'Present')
                            """, (student_id, today, now))

                            connection.commit()
                            print(f"Attendance marked: {name} at {now}")

                        except sqlite3.IntegrityError:
                            print(f"Already marked today: {name}")

                        marked_this_session.add(student_id)

                else:
                    label = "Unknown"
                    color = (0, 0, 255)

                cv2.rectangle(
                    frame, (x, y), (x + w, y + h), color, 2
                )

                cv2.putText(
                    frame, label, (x, max(25, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2
                )

        cv2.imshow("Face Attendance System", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera.release()
    cv2.destroyAllWindows()
    connection.close()
    print("Attendance system stopped.")
