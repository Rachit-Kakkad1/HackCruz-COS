"""
COS AI Core — Screen Capture & OCR
Captures periodic screenshots and extracts visible semantic text context.
"""
import mss
import cv2
import numpy as np
import pytesseract
import time


def capture_screen_text() -> str:
    """
    Takes a snapshot of the primary screen, converts to grayscale for efficiency, 
    and uses Tesseract OCR to extract semantic content.
    """
    try:
        with mss.mss() as sct:
            # Get primary monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # Convert to numpy array for OpenCV
            img = np.array(screenshot)
            
            # Convert BGRA to grayscale to speed up OCR and improve contrast
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            
            # Optional thresholding to enhance text
            # _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # Run pytesseract OCR
            # Requires tesseract to be installed and in PATH
            text = pytesseract.image_to_string(gray)
            
            # Clean up the text
            clean_text = " ".join(text.split())
            return clean_text
            
    except Exception as e:
        print(f"[Screen Capture] Error extracting text: {e}")
        return ""

if __name__ == "__main__":
    # Quick test
    print("Capturing screen...")
    start = time.time()
    text = capture_screen_text()
    print(f"Captured {len(text)} chars in {time.time() - start:.2f}s")
    print(f"Sample: {text[:200]}")
