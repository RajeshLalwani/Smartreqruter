import os
import json
import queue
import sounddevice as sd
import vosk
from interviewer import AIInterviewer

# --- CONFIGURATION ---
MODEL_PATH = "2_AI_Modules/Interview_Bot/vosk-model-small-en-us-0.15"
ESPEAK_COMMAND = "espeak"  # Or specify the full path if not in your system's PATH

# --- VOSK INITIALIZATION ---
if not os.path.exists(MODEL_PATH):
    print(f"Vosk model not found at '{MODEL_PATH}'. Please download it from https://alphacephei.com/vosk/models")
    exit(1)

model = vosk.Model(MODEL_PATH)
q = queue.Queue()

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, flush=True)
    q.put(bytes(indata))

# --- VOICE FUNCTIONS ---
def speak(text):
    """Converts text to speech using the espeak command-line tool."""
    try:
        os.system(f'{ESPEAK_COMMAND} "{text}"')
    except Exception as e:
        print(f"Error using espeak: {e}. Please ensure espeak is installed and in your PATH.")

def listen():
    """Listens for user input and returns the recognized text."""
    with sd.RawInputStream(samplerate=16000, blocksize=8000, device=None, dtype='int16',
                            channels=1, callback=callback):
        print("Listening...")
        rec = vosk.KaldiRecognizer(model, 16000)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    print(f"You said: {text}")
                    return text
            else:
                # You can optionally print partial results here
                pass


def chat():
    """
    Initializes a voice-based chat session with the AI Interviewer.
    """
    bot = AIInterviewer()

    speak("Hello! What's your name?")
    candidate_name = listen()

    speak(f"Nice to meet you, {candidate_name}! What job role are you applying for today?")
    job_title = listen()

    speak(f"Excellent. We're starting your interview for the {job_title} position. Good luck!")

    conversation_history = []
    current_question = bot.generate_question(job_title)

    while True:
        speak(current_question)
        candidate_answer = listen()

        if candidate_answer.lower() in ["exit", "quit"]:
            speak("Thanks for your time. The interview is now complete.")
            break

        conversation_history.append({"q": current_question, "a": candidate_answer})

        evaluation = bot.evaluate_response(current_question, candidate_answer, job_title)
        speak(f"Analysis: {evaluation.get('feedback', 'Analyzing...')}")

        current_question = bot.generate_dynamic_question(job_title, conversation_history)

if __name__ == "__main__":
    # Check for Gemini API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("[INFO] No GEMINI_API_KEY found. Using fallback mode.")

    # Check for espeak installation
    if os.system(f'{ESPEAK_COMMAND} --version') != 0:
        print(f"espeak not found. Please install it and ensure it's in your system's PATH.")
        exit(1)
    
    chat()
