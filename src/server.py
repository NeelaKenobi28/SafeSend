import socket
import cv2
import pickle
import struct
import numpy as np

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('127.0.0.1', 3001))
server_socket.listen(5)
print("Server listening on 127.0.0.1:3001")

client_socket, addr = server_socket.accept()
print(f"Connection from: {addr}")

data = b""
payload_size = struct.calcsize("Q")

while True:
    while len(data) < payload_size:
        packet = client_socket.recv(4096)
        if not packet:
            break
        data += packet

    if len(data) < payload_size:
        break

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(4096)

    frame_data = data[:msg_size]
    data = data[msg_size:]

    buffer = pickle.loads(frame_data)
    frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    cv2.imshow("Receiving Video", frame)
    if cv2.waitKey(1) == ord('q'):
        break

client_socket.close()
server_socket.close()
cv2.destroyAllWindows()
