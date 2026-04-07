import json
import logging
from core.ai_engine import AIEngine
from core.utils.ai_logic import analyze_frame

logger = logging.getLogger(__name__)

class SentimentEngine:
    """
    Standalone Sentiment Analysis Engine.
    Acts as the main bridge between the Real-time Floating Sentiment Bubble (JS)
    and the centralized AIEngine / FER backend logic.
    """
    
    def __init__(self):
        self.ai = AIEngine()

    def process_frame(self, frame_b64):
        """
        Processes a base64 encoded frame from the frontend JS bubble.
        Returns the top emotion and confidence score.
        """
        try:
            result = analyze_frame(frame_b64)
            return {
                "ok": True,
                "emotion": result.get("emotion", "neutral"),
                # We also need display_label to maintain compatibility
                "display_label": result.get("emotion", "Neutral").title(),
                "score": result.get("score", 0.0),
                "risk_level": result.get("risk_level", "Low"),
                "flags": result.get("flags", []),
                "all_emotions": result.get("all_emotions", {})
            }
        except Exception as e:
            logger.error(f"SentimentEngine failed to process frame: {e}")
            return {"ok": False, "error": str(e), "emotion": "neutral", "display_label": "Neutral", "score": 0.0}
            
    def process_transcript_sentiment(self, transcript):
        """
        Analyzes the sentiment of a spoken transcript using Gemini/RAG.
        Used for the end-of-interview sentiment summary and confidence scoring.
        """
        prompt = f"Analyze the sentiment and confidence of this interview transcript: '{transcript}'. Return JSON: {{'emotion': '...', 'confidence_score': 0.0-1.0}}"
        response = self.ai.get_chat_response(prompt)
        try:
            return json.loads(response)
        except Exception:
            return {"emotion": "neutral", "confidence_score": 0.5}

if __name__ == "__main__":
    engine = SentimentEngine()
    print("[SUCCESS] Sentiment Engine Initialized.")
