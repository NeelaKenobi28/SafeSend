from flask import Flask, request, jsonify, send_from_directory, session
import whisper
import os
from pydub import AudioSegment
from tempfile import NamedTemporaryFile
import time
from uuid import uuid4
import signal
import sys
import random

app = Flask(__name__, static_folder='static', template_folder='static')
app.secret_key = 'supersecretkey'  # Required for session usage
model = whisper.load_model("base")

UPLOAD_FOLDER = 'uploads'
TRANSCRIPT_FOLDER = 'transcripts'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

# List of known user names (case-insensitive match)
VALID_USERNAMES = {"ramey", "ankur", "rahul", "marzooqa", "mustafiz"}

# Validate username if the current question is asking for first name
if "first name" in question_text.lower():
    first_name = text.strip().lower()
    if first_name in VALID_USERNAMES:
        session['validated_user'] = first_name.capitalize()
    else:
        session['validated_user'] = None


def signal_handler(sig, frame):
    print('\nShutting down server gracefully...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signal

@app.route('/')
def index():
    # Each user gets a unique ID per session
    if 'user_id' not in session:
        session['user_id'] = f"user_{random.randint(1000, 999999)}"
    return send_from_directory('static', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    # Save original uploaded video file
    timestamp = int(time.time())
    saved_video_path = os.path.join(UPLOAD_FOLDER, f"video_{timestamp}.webm")
    file.save(saved_video_path)

    temp_wav = NamedTemporaryFile(suffix=".wav", delete=False)

    try:
        # Convert WebM to WAV
        audio = AudioSegment.from_file(saved_video_path, format="webm")
        audio.export(temp_wav.name, format="wav")

        result = model.transcribe(temp_wav.name, language="en")
        text = result['text']

        # Create user-specific transcript file
        user_id = session.get('user_id', f"user_{random.randint(1000, 999999)}")
        print(user_id)
        transcript_filename = os.path.join(TRANSCRIPT_FOLDER, f"{user_id}.txt")

        # Append question and answer
        question_text = request.form.get('question', '')
        with open(transcript_filename, "a", encoding="utf-8") as f:
            f.write(f"Q: {question_text}\nA: {text.strip()}\n\n")
            if "first name" in question_text.lower():
                if session['validated_user']:
                    f.write(f"Validated user: {session['validated_user']}\n\n")
                else:
                    f.write(f"User name not recognized\n\n")


        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(temp_wav.name)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
