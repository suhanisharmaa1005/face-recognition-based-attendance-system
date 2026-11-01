
import cv2

# Load the saved student image
image_path = "face_images/student_1.jpg"
image = cv2.imread(image_path)

if image is None:
    print("Error: Image not found!")
    raise SystemExit

# Load OpenCV's pre-trained face detector
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Convert image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Detect faces
faces = face_detector.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(30, 30)
)

# Draw rectangles around detected faces
for (x, y, w, h) in faces:
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

if len(faces) > 0:
    print(f"Success! Detected {len(faces)} face(s).")
else:
    print("No face detected. Try a clearer image with good lighting.")

cv2.imshow("Face Detection Result", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
