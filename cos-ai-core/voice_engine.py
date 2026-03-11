"""
COS AI Core — Voice Engine
Handles speech-to-text (STT) via faster-whisper and text-to-speech (TTS) via pyttsx3.
Listens dynamically from microphone when triggered.
"""
import pyttsx3
from faster_whisper import WhisperModel
import speech_recognition as sr
import threading
import os
import requests

BACKEND_URL = "http://localhost:8000"

# Initialize TTS
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 165)
tts_engine.setProperty('volume', 0.9)

# Load Whisper model (local execution)
print("[Voice Engine] Loading Whisper model (base.en)...")
model_size = "base.en"
whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
print("[Voice Engine] Model loaded.")


def speak(text: str):
    """Speaks the text aloud in a non-blocking thread."""
    def _speak():
        tts_engine.say(text)
        tts_engine.runAndWait()
    threading.Thread(target=_speak, daemon=True).start()


def listen_and_process():
    """Records audio from the mic, transcribes it, and sends to backend."""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("[Voice Engine] Adjusting for ambient noise...")
        # recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("\n[Voice Engine] 🎙️ LISTENING NOW (Speak your command)...")
        speak("I am listening.")
        
        try:
            # Listen for up to 5 seconds of speech
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=10)
            print("[Voice Engine] Processing audio...")
            
            # Save temporary wav
            wav_path = "temp_voice.wav"
            with open(wav_path, "wb") as f:
                f.write(audio.get_wav_data())
            
            # Transcribe with faster-whisper
            segments, _ = whisper_model.transcribe(wav_path, beam_size=5)
            transcription = "".join([segment.text for segment in segments]).strip()
            
            print(f"[Voice Engine] Transcribed: '{transcription}'")
            
            if os.path.exists(wav_path):
                os.remove(wav_path)
                
            if transcription:
                # Send to backend
                send_to_backend(transcription)
            else:
                speak("I didn't catch that.")
                
        except sr.WaitTimeoutError:
            print("[Voice Engine] No speech detected.")
            speak("No speech detected.")
        except Exception as e:
            print(f"[Voice Engine] Error: {e}")
            speak("Error processing voice.")


def send_to_backend(query: str):
    """Sends transcription to /voice/command and speaks the response."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/voice/command",
            json={"query": query},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "I could not generate an answer.")
            print(f"\n[COS AI] {answer}\n")
            speak(answer)
        else:
            speak("The backend encountered an error.")
    except requests.exceptions.ConnectionError:
        print("[Voice Engine] Could not connect to backend.")
        speak("Cognitive backend is offline.")

if __name__ == "__main__":
    listen_and_process()
