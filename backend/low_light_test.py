
import cv2

MODEL_PATH = "models/face_detection_yunet_2023mar.onnx"

detector = cv2.FaceDetectorYN.create(
    MODEL_PATH,
    "",
    (320, 320),
    0.7,
    0.3,
    5000
)

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise SystemExit("Cannot open webcam.")

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Improve local contrast in darker images
clahe = cv2.createCLAHE(
    clipLimit=2.0,
    tileGridSize=(8, 8)
)

print("Low-light test started. Press Q in the camera window to quit.")

try:
    while True:
        success, frame = camera.read()

        if not success:
            print("Cannot read camera frame.")
            break

        # Measure brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = gray.mean()

        # Enhance contrast only when the image is dim
        if brightness < 90:
            enhanced_gray = clahe.apply(gray)
            enhanced_frame = cv2.cvtColor(
                enhanced_gray, cv2.COLOR_GRAY2BGR
            )
        else:
            enhanced_frame = frame.copy()

        height, width = enhanced_frame.shape[:2]
        detector.setInputSize((width, height))

        _, faces = detector.detect(enhanced_frame)

        if faces is not None:
            for face in faces:
                x, y, w, h = map(int, face[:4])

                cv2.rectangle(
                    enhanced_frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

        status = (
            f"Brightness: {brightness:.1f} | "
            f"Faces: {0 if faces is None else len(faces)}"
        )

        cv2.putText(
            enhanced_frame,
            status,
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        cv2.imshow("Low-Light Face Detection Test", enhanced_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    camera.release()
    cv2.destroyAllWindows()
    print("Low-light test stopped.")
