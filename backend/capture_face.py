
import cv2
import os

# Create a folder to save face images
os.makedirs("face_images", exist_ok=True)

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not open camera.")
    raise SystemExit

print("Press S to save a face image.")
print("Press Q to exit.")

while True:
    success, frame = camera.read()

    if not success:
        print("Could not read camera frame.")
        break

    cv2.imwrite("face_images/student_1_second.jpg", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        filename = os.path.join("face_images", "student_1.jpg")
        saved = cv2.imwrite(filename, frame)

        if saved:
            print("Face image saved:", filename)
        else:
            print("Error saving image.")

    elif key == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
