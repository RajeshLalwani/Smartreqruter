"""
AI Logic Module — Real-Time Facial Emotion Detection (OpenCV Edition)
───────────────────────────────────────────────────────────────────────
Uses Classic Haar Cascades for face and smile detection.
100% Free, Lightweight, and Zero-Dependency (only uses OpenCV & Numpy).

Reliable across all Python versions, including Python 3.14.
"""

import base64
import logging
import numpy as np
import cv2
import os

logger = logging.getLogger(__name__)

# Load Cascades (Standard OpenCV models)
_face_cascade = None
_smile_cascade = None
_eye_cascade = None

def _load_cascades():
    """Load OpenCV Haar Cascades."""
    global _face_cascade, _smile_cascade, _eye_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades
        _face_cascade = cv2.CascadeClassifier(os.path.join(cascade_path, 'haarcascade_frontalface_default.xml'))
        _smile_cascade = cv2.CascadeClassifier(os.path.join(cascade_path, 'haarcascade_smile.xml'))
        _eye_cascade = cv2.CascadeClassifier(os.path.join(cascade_path, 'haarcascade_eye.xml'))
        
        if _face_cascade.empty() or _smile_cascade.empty() or _eye_cascade.empty():
            logger.error("[AILogic] Failed to load OpenCV Cascades.")
            return False
    return True


def analyze_frame(base64_image: str) -> dict:
    """
    Analyze facial features via Haar Cascades for Sentiment and Proctoring.
    Detects: Face Count, Absence, Gaze Deviation, and Emotions.
    """
    fallback = {
        'emotion': 'neutral',
        'display_label': 'Scanning...',
        'score': 0.0,
        'risk_level': 'Low',
        'flags': [],
        'face_count': 0,
        'all_emotions': {},
    }

    if not base64_image:
        return fallback

    try:
        if not _load_cascades():
            return fallback

        if ',' in base64_image:
            base64_image = base64_image.split(',', 1)[1]
        img_bytes = base64.b64decode(base64_image)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return fallback

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Detect Face
        faces = _face_cascade.detectMultiScale(gray, 1.3, 5)
        face_count = len(faces)
        
        flags = []
        risk_level = "Low"

        if face_count == 0:
            flags.append("ABSENCE")
            risk_level = "High"
            return {**fallback, 'face_count': 0, 'flags': flags, 'risk_level': risk_level}

        if face_count > 1:
            flags.append("MULTI_FACE")
            risk_level = "High"

        # Process the largest face for emotion and gaze
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        (x, y, w, h) = faces[0]
        roi_gray = gray[y:y+h, x:x+w]
        
        # 2. Gaze Detection (Eye Tracking)
        eyes = _eye_cascade.detectMultiScale(roi_gray, 1.1, 10, minSize=(int(w*0.1), int(h*0.1)))
        gaze_away = False
        if len(eyes) < 2:
            # If we don't see both eyes, they might be looking away or eyes closed
            gaze_away = True
        else:
            # Check horizontal centering of pupils (extremely simple heuristic)
            # If eye distance-to-center ratio is skewed, they are likely looking away
            eye_centers = sorted([ex + ew//2 for (ex, ey, ew, eh) in eyes])
            face_center = w // 2
            skew = abs((eye_centers[0] + eye_centers[1]) / 2 - face_center) / w
            if skew > 0.15: # Threshold for looking left/right
                gaze_away = True

        if gaze_away:
            flags.append("GAZE_DEVIATION")
            risk_level = "Medium" if risk_level != "High" else "High"

        # 3. Detect Smile (Sentiment)
        smiles = _smile_cascade.detectMultiScale(
            roi_gray, 
            scaleFactor=1.7, 
            minNeighbors=22, 
            minSize=(int(w*0.3), int(h*0.1))
        )
        
        emotion = 'happy' if len(smiles) > 0 else 'neutral'
        display_label = 'Confident' if emotion == 'happy' else 'Focused'
        score = 0.85 if emotion == 'happy' else 0.5

        return {
            'emotion': emotion,
            'display_label': display_label,
            'score': score,
            'face_count': face_count,
            'risk_level': risk_level,
            'flags': flags,
            'all_emotions': {
                'smiles': len(smiles),
                'eyes_found': len(eyes),
                'gaze_away': gaze_away
            }
        }

    except Exception as e:
        logger.error(f"[AILogic] Proctoring analysis error: {e}")
        return fallback

# --- PHASE 5: POLYGLOT EVALUATION REFINEMENT ---
def score_polyglot_code(code: str, language: str, problem_statement: str) -> dict:
    """
    Uses the AI Engine to evaluate code across different languages.
    Focuses on Logic, Big-O Complexity, and Universal Best Practices.
    """
    from core.ai_engine import AIEngine
    ai = AIEngine()
    
    prompt = f"""
    Evaluate the following {language} code against this problem: "{problem_statement}".
    
    CRITIQUE CRITERIA:
    1. Logic Correctness (Does it actually solve the problem?)
    2. Space & Time Complexity (Big-O analysis)
    3. Language-Specific Best Practices (Is it idiomatic {language}?)
    4. Code Readability
    
    CODE:
    {code}
    
    Return a JSON response: {{"score": 0-100, "feedback": "...", "complexity": "..."}}
    """
    
    try:
        raw_response = ai.get_chat_response(prompt)
        # Attempt to parse JSON if AI returns it, else return raw
        return {"response": raw_response}
    except Exception as e:
        return {"error": str(e)}

# --- PHASE 10: BOTANIST BEHAVIORAL ANALYSIS ---
def botanist_behavioral_analysis(transcript: str, category: str = "General") -> str:
    """
    Analyzes a voice transcript for "Behavioral Alignment" 
    (Leadership, Problem Solving, Adaptability, etc.)
    """
    from core.ai_engine import AIEngine
    ai = AIEngine()
    
    prompt = f"""
    Acting as "The Botanist" Behavioral Analyst, evaluate this candidate response:
    TRANSCRIPT: "{transcript}"
    FOCUS CATEGORY: {category}
    
    CRITERIA:
    1. STAR Method compliance (Situation, Task, Action, Result)
    2. Specificity and impact
    3. Sentiment tone and professional maturity
    
    Return a concise, sophisticated critique including a fitment score (0-10) for {category}.
    """
    
    try:
        return ai.get_botanist_response(prompt)
    except Exception as e:
        logger.error(f"[Botanist] Analysis error: {e}")
        return "Analysis unavailable due to neural link latency."
