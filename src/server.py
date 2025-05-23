# from flask import Flask, request, jsonify, send_from_directory, session
# import whisper
# import os
# from pydub import AudioSegment
# from tempfile import NamedTemporaryFile
# import time
# from uuid import uuid4
# import signal
# import sys
# import random
#
# app = Flask(__name__, static_folder='static', template_folder='static')
# app.secret_key = 'supersecretkey'  # Required for session usage
# model = whisper.load_model("base")
#
# UPLOAD_FOLDER = 'uploads'
# TRANSCRIPT_FOLDER = 'transcripts'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)
#
# # List of known user names (case-insensitive match)
# VALID_USERNAMES = {"ramey", "ankur", "rahul", "marzooqa", "mustafiz"}
#
# # Validate username if the current question is asking for first name
# # if "first name" in question_text.lower():
# #     first_name = text.strip().lower()
# #     if first_name in VALID_USERNAMES:
# #         session['validated_user'] = first_name.capitalize()
# #     else:
# #         session['validated_user'] = None
#
#
# def signal_handler(sig, frame):
#     print('\nShutting down server gracefully...')
#     sys.exit(0)
#
# signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl+C
# signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signal
#
# @app.route('/')
# def index():
#     # Each user gets a unique ID per session
#     if 'user_id' not in session:
#         session['user_id'] = f"user_{random.randint(1000, 999999)}"
#     return send_from_directory('static', 'index.html')
#
# @app.route('/transcribe', methods=['POST'])
# def transcribe():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file uploaded'}), 400
#
#     file = request.files['file']
#
#     # Save original uploaded video file
#     timestamp = int(time.time())
#     saved_video_path = os.path.join(UPLOAD_FOLDER, f"video_{timestamp}.webm")
#     file.save(saved_video_path)
#
#     temp_wav = NamedTemporaryFile(suffix=".wav", delete=False)
#
#     try:
#         # Convert WebM to WAV
#         audio = AudioSegment.from_file(saved_video_path, format="webm")
#         audio.export(temp_wav.name, format="wav")
#
#         result = model.transcribe(temp_wav.name, language="en")
#         text = result['text']
#
#         # Create user-specific transcript file
#         user_id = session.get('user_id', f"user_{random.randint(1000, 999999)}")
#         print(user_id)
#         transcript_filename = os.path.join(TRANSCRIPT_FOLDER, f"{user_id}.txt")
#         user_id += f"_{uuid4()}"
#
#         # Append question and answer
#         question_text = request.form.get('question', '')
#         submitted_transcription = request.form.get('transcription', '').strip()
#         with open(transcript_filename, "a", encoding="utf-8") as f:
#             final_text = submitted_transcription if submitted_transcription else text.strip()
#             f.write(f"Q: {question_text}\nA: {final_text}\n\n")
#
#             # Attempt to validate user based on audio response content
#             spoken_name = final_text.split()[0].lower()
#             if spoken_name in VALID_USERNAMES:
#                 session['validated_user'] = spoken_name.capitalize()
#                 f.write(f"Validated user: {session['validated_user']}\n\n")
#             else:
#                 session['validated_user'] = None
#                 f.write("User name NOT recognized\n")
#                 f.write("Please register at https://app.bitgo.com/web/auth/signup\n\n")
#                 return jsonify({
#                     'text': text,
#                     'speak': 'User name not recognized. Please register at https://app.bitgo.com/web/auth/signup.'
#                 })
#
# #         with open(transcript_filename, "a", encoding="utf-8") as f:
# #             f.write(f"Q: {question_text}\nA: {text.strip()}\n\n")
# #             if "first name" in question_text.lower():
# #                 if session['validated_user']:
# #                     f.write(f"Validated user: {session['validated_user']}\n\n")
# #                 else:
# #                     f.write(f"User name NOT recognized\n\n")
#
#
#
#         return jsonify({'text': text})
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#     finally:
#         os.remove(temp_wav.name)
#
# if __name__ == '__main__':
#     app.run(debug=True, port=5001)


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
from flask import send_file

app = Flask(__name__, static_folder='static', template_folder='static')
app.secret_key = 'supersecretkey'  # Required for session usage
model = whisper.load_model("base")

UPLOAD_FOLDER = 'uploads'
TRANSCRIPT_FOLDER = 'transcripts'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

VALID_USERNAMES = {"ramey", "ankur", "rahul", "marzooqa", "mustafiz", "vignesh", "abhishek", "shashwat", "sreeraj"}

def signal_handler(sig, frame):
    print('\nShutting down server gracefully...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.static_folder), 'favicon.ico')

@app.route('/')
def index():
    if 'user_id' not in session:
        session['user_id'] = f"user_{uuid4().hex}"
    return send_from_directory('static', 'index.html')

@app.route('/download_transcript')
def download_transcript():
    user_id = session.get('user_id')
    if not user_id:
        return "No transcript available", 404

    transcript_filename = os.path.join(TRANSCRIPT_FOLDER, f"{user_id}.txt")
    if not os.path.exists(transcript_filename):
        return "Transcript not found", 404

    return send_file(transcript_filename, as_attachment=True)

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

        user_id = session.get('user_id', f"user_{uuid4().hex}")
        transcript_filename = os.path.join(TRANSCRIPT_FOLDER, f"{user_id}.txt")
        user_id += f"_{uuid4().hex}"

        question_text = request.form.get('question', '').lower()
        submitted_transcription = request.form.get('transcription', '').strip()
        final_text = submitted_transcription if submitted_transcription else text.strip()

        with open(transcript_filename, "a", encoding="utf-8") as f:
            f.write(f"Q: {question_text}\nA: {final_text}\n\n")

            # Only validate user if the question contains 'first name'
            if "first name" in question_text:
                spoken_name = final_text.split()[0].lower() if final_text else ""
                if spoken_name in VALID_USERNAMES:
                    session['validated_user'] = spoken_name.capitalize()
                    f.write(f"Validated user: {session['validated_user']}\n\n")
                else:
                    session['validated_user'] = None
                    f.write("User name \\033[1mNOT} recognized\n")
                    f.write("Please register at https://app.bitgo.com/web/auth/signup\n\n")
                    return jsonify({
                        'text': final_text,
                        'speak': 'User name not recognized. Please register at https://app.bitgo.com/web/auth/signup.'
                    })
            else:
                # For other questions, no user validation — just continue normally
                pass

        return jsonify({'text': final_text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(temp_wav.name)

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
    is_valid = True ? transaction == true : False
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
