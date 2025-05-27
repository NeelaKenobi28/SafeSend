from flask import Flask, request, jsonify, send_from_directory, session, send_file
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPT_FOLDER = os.path.join(BASE_DIR, 'transcripts')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

VALID_USERNAMES = {"ramey", "ankur", "rahul", "marzooqa", "mustafiz", "bob", "tom"}

def signal_handler(sig, frame):
    print('\nShutting down server gracefully...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@app.route('/')
def index():
    if 'user_id' not in session:
        session['user_id'] = f"user_{uuid4().hex}"
    return send_from_directory('static', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    timestamp = int(time.time())
    saved_video_path = os.path.join(UPLOAD_FOLDER, f"video_{timestamp}.webm")
    file.save(saved_video_path)

    temp_wav = NamedTemporaryFile(suffix=".wav", delete=False)

    try:
        audio = AudioSegment.from_file(saved_video_path, format="webm")
        audio.export(temp_wav.name, format="wav")

        result = model.transcribe(temp_wav.name, language="en")
        text = result['text']

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Session expired. Please refresh the page.'}), 400

        transcript_filename = os.path.join(TRANSCRIPT_FOLDER, f"{user_id}.txt")

        # Ensure file exists before writing
        os.makedirs(os.path.dirname(transcript_filename), exist_ok=True)

        # Create the file if it doesn't exist yet
        if not os.path.exists(transcript_filename):
            open(transcript_filename, 'w').close()

        question_text = request.form.get('question', '')
        submitted_transcription = request.form.get('transcription', '').strip()
        final_text = submitted_transcription if submitted_transcription else text.strip()

        with open(transcript_filename, "a", encoding="utf-8") as f:
            f.write(f"Q: {question_text}\nA: {final_text}\n\n")

            if any(kw in question_text.lower() for kw in ["first name", "your name", "what is your name"]):
                spoken_name = final_text.split()[0].lower() if final_text else ""
                if spoken_name in VALID_USERNAMES:
                    session['validated_user'] = spoken_name.capitalize()
                    f.write(f"Validated user: {session['validated_user']}\n\n")
                else:
                    session['validated_user'] = None
                    f.write("User name NOT recognized\n")
                    f.write("Please register at https://app.bitgo.com/web/auth/signup\n\n")
                    return jsonify({
                        'text': final_text,
                        'speak': 'User name not recognized. Please register at https://app.bitgo.com/web/auth/signup.',
                        'valid': False
                    })
        return jsonify({'text': final_text, 'valid': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(temp_wav.name)

@app.route('/download_transcript')
def download_transcript(filename):
    user_id = session.get('user_id')
    if not user_id:
        return "No user session found", 400

    transcript_filename = os.path.join(TRANSCRIPT_FOLDER, f"{user_id}.txt")
    os.makedirs(os.path.dirname(transcript_filename), exist_ok=True)
    if not os.path.exists(transcript_filename):
        open(transcript_filename, 'w').close()  # Create empty transcript if not found

    return send_file(
        transcript_filename,
        as_attachment=True,
        download_name=f"{user_id}_transcript.txt",
        mimetype='text/plain'
    )

@app.route('/validate_user')
def check_valid_name(question):
    data = request.get_json()
    name = data.get("first name", "").lower()
    is_valid = name in VALID_USERNAMES
    return jsonify({"valid": is_valid})

@app.route('/self-transaction')
def check_if_self(question):
    data = request.get_json()
    transaction = data.get("your transaction", "").lower()
    is_valid = True if transaction == True else False
    return jsonify({"valid": is_valid})

@app.route('/amount')
def check_amount(question):
    data = request.get_json()
    amount = data.get("amount", "").lower()
    if amount < 0:
        return jsonify({"valid": False})
    return jsonify({"valid": True})

if __name__ == '__main__':
    app.run(debug=True, port=5001)