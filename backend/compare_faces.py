
import cv2

# Model paths
detector = cv2.FaceDetectorYN.create(
    "models/face_detection_yunet_2023mar.onnx",
    "",
    (320, 320),
    0.8,
    0.3,
    5000
)

recognizer = cv2.FaceRecognizerSF.create(
    "models/face_recognition_sface_2021dec.onnx",
    ""
)

def get_face_feature(image_path):
    image = cv2.imread(image_path)

    if image is None:
        print("Cannot load image:", image_path)
        return None

    height, width = image.shape[:2]
    detector.setInputSize((width, height))
    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:
        print("No face detected in:", image_path)
        return None

    # Use the largest detected face
    face = max(faces, key=lambda f: f[2] * f[3])

    aligned_face = recognizer.alignCrop(image, face)
    feature = recognizer.feature(aligned_face)

    return feature

image1 = "face_images/student_1.jpg"
image2 = "face_images/student_1_second.jpg"

feature1 = get_face_feature(image1)
feature2 = get_face_feature(image2)

if feature1 is not None and feature2 is not None:
    score = recognizer.match(
        feature1,
        feature2,
        cv2.FaceRecognizerSF_FR_COSINE
    )

    print(f"\nFace similarity score: {score:.4f}")

    if score >= 0.363:
        print("Result: Likely the same person")
    else:
        print("Result: Match not confident enough")

    print("Note: This is a preliminary test, not a guarantee of identity.")
