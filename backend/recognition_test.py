
import cv2
from pathlib import Path

# Model paths
detector_path = "models/face_detection_yunet_2023mar.onnx"
recognizer_path = "models/face_recognition_sface_2021dec.onnx"

# Load AI models
detector = cv2.FaceDetectorYN.create(
    detector_path, "", (320, 320), 0.8, 0.3, 5000
)

recognizer = cv2.FaceRecognizerSF.create(
    recognizer_path, ""
)

# Load your saved face image
image_path = Path("face_images/student_1.jpg")
image = cv2.imread(str(image_path))

if image is None:
    print("ERROR: Face image not found:", image_path)
    raise SystemExit

# Detect faces
height, width = image.shape[:2]
detector.setInputSize((width, height))
_, faces = detector.detect(image)

if faces is None or len(faces) == 0:
    print("No face detected. Try a clearer image with better lighting.")
else:
    print("Faces detected:", len(faces))

    # Draw a box around each detected face
    for face in faces:
        x, y, w, h = map(int, face[:4])
        cv2.rectangle(
            image, (x, y), (x + w, y + h), (0, 255, 0), 2
        )

    cv2.imshow("YuNet Face Detection Test", image)
    print("Press Q to close the image.")
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
