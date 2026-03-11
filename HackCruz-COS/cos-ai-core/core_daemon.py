"""
COS AI Core — Orchestrator Daemon
Runs the OS loops and hooks the global voice hotkey.
"""
import time
import requests
import threading
import keyboard
from datetime import datetime

from os_monitor import get_active_window_info
from screen_capture import capture_screen_text
from voice_engine import listen_and_process, speak

BACKEND_URL = "http://localhost:8000"
POLL_INTERVAL = 30  # Seconds between automated context captures

last_os_context = None
last_screen_text = None

def os_loop():
    """Polls OS active window window and sends to backend."""
    global last_os_context
    while True:
        info = get_active_window_info()
        if info:
            # Deduplication: ignore if same app window is active
            context_id = f"{info['app']}-{info['title']}"
            if context_id != last_os_context:
                last_os_context = context_id
                print(f"[Daemon] OS Context Changed: {info['app']} -> {info['title']}")
                
                payload = {
                    "app": info['app'],
                    "window_title": info['title'],
                    "workspace": info.get('workspace'),
                    "timestamp": datetime.now().isoformat()
                }
                
                try:
                    requests.post(f"{BACKEND_URL}/context/os", json=payload, timeout=2)
                except requests.exceptions.ConnectionError:
                    pass
        
        time.sleep(2)  # fast polling for window changes

def screen_loop():
    """Polls screen OCR and sends to backend."""
    global last_screen_text
    while True:
        print("[Daemon] Capturing screen OCR...")
        text = capture_screen_text()
        
        # Deduplication: only send if we pulled actual text and it changed heavily
        if len(text) > 50 and text != last_screen_text:
            last_screen_text = text
            
            payload = {
                "text": text,
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                requests.post(f"{BACKEND_URL}/context/screen", json=payload, timeout=5)
                print("[Daemon] Sent screen context to backend.")
            except requests.exceptions.ConnectionError:
                print("[Daemon] Cannot connect to backend for screen data.")
        
        time.sleep(POLL_INTERVAL)

def setup_hotkeys():
    """Listens for the global hotkey CTRL + ALT + SPACE."""
    print("[Daemon] Binding global voice hotkey: Ctrl + Alt + Space")
    keyboard.add_hotkey('ctrl+alt+space', listen_and_process)
    
if __name__ == "__main__":
    print("====================================")
    print(" COS AI Core Daemon Initializing... ")
    print("====================================")
    
    # Needs SpeechRecognition library to be installed too, let's verify later.
    
    setup_hotkeys()
    
    os_thread = threading.Thread(target=os_loop, daemon=True)
    os_thread.start()
    
    screen_thread = threading.Thread(target=screen_loop, daemon=True)
    screen_thread.start()
    
    speak("Cognitive OS sensors active.")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Daemon] Shutting down.")
