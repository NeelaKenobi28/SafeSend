import socket
import cv2
import pickle
import struct
import time
import whisper
import sounddevice as sd
import numpy as np
import queue
import threading

# Setup client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('127.0.0.1', 3001))

# Video capture settings
video = cv2.VideoCapture(0)
fps = 10
frame_interval = 1 / fps

# Load Whisper model (base for speed)
model = whisper.load_model("base")

# Audio capture parameters
sample_rate = 16000
channels = 1
audio_chunk_duration = 0.5  # seconds per audio chunk

q_audio = queue.Queue()
running = threading.Event()

def audio_callback(indata, frames, time_, status):
    if status:
        print("Audio callback status:", status)
    # Convert float32 input to int16 for smaller size and compatibility
    audio_int16 = (indata * 32767).astype(np.int16)
    q_audio.put(audio_int16.copy())

def audio_capture_thread():
    """Continuously transcribe audio blocks with Whisper and send transcriptions"""
    while running.is_set():
        try:
            audio_block = q_audio.get(timeout=1)
        except queue.Empty:
            continue

        # Flatten audio block for Whisper
        audio_float32 = audio_block.astype(np.float32).flatten() / 32767.0

        try:
            result = model.transcribe(audio_float32, fp16=False, language="en", task="transcribe")
            text = result.get("text", "").strip()
        except Exception as e:
            print("Whisper transcription error:", e)
            continue

        if text:
            print("Transcription:", text)
            text_bytes = text.encode('utf-8')
            message = b'T' + struct.pack("Q", len(text_bytes)) + text_bytes
            try:
                client_socket.sendall(message)
            except Exception as e:
                print("Error sending transcription:", e)

def audio_stream_thread():
    while running.is_set():
        try:
            audio_block = q_audio.get(timeout=1)
        except queue.Empty:
            continue

        audio_bytes = audio_block.tobytes()
        message = b'A' + struct.pack("Q", len(audio_bytes)) + audio_bytes
        try:
            client_socket.sendall(message)
        except (BrokenPipeError, ConnectionResetError):
            print("Broken pipe or connection reset detected. Stopping sending.")
            running.clear()
            break
        except Exception as e:
            print("Error sending data:", e)
            running.clear()
            break

# Start audio input stream with int16 dtype for smaller data size
stream = sd.InputStream(samplerate=sample_rate, channels=channels,
                        dtype='float32', callback=audio_callback)

running.set()

# Start threads
thread_transcribe = threading.Thread(target=audio_capture_thread, daemon=True)
thread_stream = threading.Thread(target=audio_stream_thread, daemon=True)
thread_transcribe.start()
thread_stream.start()

stream.start()

start_time = time.time()
duration = 12  # seconds
last_send = 0

try:
    while time.time() - start_time < duration:
        if time.time() - last_send < frame_interval:
            continue
        last_send = time.time()

        ret, frame = video.read()
        if not ret:
            print("Failed to capture frame")
            break

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            print("Failed to encode frame")
            continue

        data = pickle.dumps(buffer)
        message = b'V' + struct.pack("Q", len(data)) + data
        try:
            client_socket.sendall(message)
            print("Frame sent")
        except Exception as e:
            print("Error sending frame:", e)
            break

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    running.clear()

    # Stop audio threads gracefully
    thread_transcribe.join(timeout=2)
    thread_stream.join(timeout=2)

    # Stop and close the audio stream
    stream.stop()
    stream.close()

    # Cleanup
    time.sleep(0.5)
    client_socket.close()
    video.release()
    print("Client shutdown complete")
