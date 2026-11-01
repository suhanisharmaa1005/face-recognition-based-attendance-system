
import cv2

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not open camera.")
else:
    print("Camera connected! Press Q to close.")

    while True:
        success, frame = camera.read()

        if not success:
            print("Could not read camera frame.")
            break

        cv2.imshow("Face Attendance - Camera Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

camera.release()
cv2.destroyAllWindows()
