"""
core/chatbot.py — Sentinel Prime Chatbot Wrapper
================================================
Now fully delegates AI logic and fallback handling to the 
Centralized `AIEngine` to prevent duplicated Quota exhaustion crashes.
"""

import logging
from datetime import datetime
from core.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class SmartBot:
    """
    Sentinel Prime — Enterprise AI Recruitment Assistant.
    Delegates generation to the Centralized Dual-Engine AI Service.
    """

    def _get_user_context(self, user) -> str:
        if not user or not user.is_authenticated:
            return "The user is browsing as a Guest."
        role = "Recruiter" if getattr(user, "is_recruiter", False) else "Candidate"
        ctx = f"The authenticated user is '{user.username}' ({role})."
        try:
            if hasattr(user, "candidate_profile"):
                skills = user.candidate_profile.skills_extracted or "No specific skills recorded."
                ctx += f" Their extracted skill-set: {skills}."
        except Exception:
            pass
        return ctx

    def get_response(self, user_query: str, user=None, is_voice: bool = False) -> str:
        """
        Primary entry point. 
        Instant local commands run here, AI prompts route to AIEngine.
        """
        lower_query = user_query.lower().strip()

        # ── Instant local commands (no AI needed) ──────────────────────────
        if any(w in lower_query for w in ["time", "clock", "what time"]):
            ts = datetime.now().strftime('%I:%M %p')
            return (
                ts if is_voice
                else f"🕐 Current synchronization time: <strong>{ts}</strong> (IST)."
            )

        if any(w in lower_query for w in ["date", "today", "what day"]):
            ds = datetime.now().strftime('%A, %B %d, %Y')
            return (
                f"Today is {ds}." if is_voice
                else f"📅 System calendar: <strong>{ds}</strong>."
            )

        # ── Build context & Call Central AI ─────────────────────────────────
        user_context = self._get_user_context(user)
        ai = AIEngine()
        
        try:
            if is_voice:
                return ai.get_voice_response(user_audio_text=user_query)
            else:
                return ai.get_chat_response(user_message=user_query, context_history=user_context)
        except Exception as e:
            logger.error(f"[Chatbot] Delegated AIEngine call failed: {e}")
            return "I am currently processing high-priority analytical data. Please re-synchronize your request in a few moments."

# Singleton instance
bot = SmartBot()
