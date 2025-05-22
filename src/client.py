import socket
import cv2
import pickle
import struct
import time

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('127.0.0.1', 3001))

video = cv2.VideoCapture(0)
video.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
video.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

FPS = 10
frame_time = 1 / FPS
last_time = time.time()

while True:
    if time.time() - last_time < frame_time:
        continue
    last_time = time.time()

    ret, frame = video.read()
    if not ret:
        break

    # Compress frame to JPEG before sending
    ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    data = pickle.dumps(buffer)

    message = struct.pack("Q", len(data)) + data
    client_socket.sendall(message)

    cv2.imshow("Sending Video", frame)
    if cv2.waitKey(1) == ord('q'):
        break

video.release()
client_socket.close()
cv2.destroyAllWindows()
