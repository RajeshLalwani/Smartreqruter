"""
core/ai_engine.py — Centralized Dual-Engine AI Service
======================================================
This service acts as the SINGLE SOURCE OF TRUTH for all generative AI tasks 
across the SmartRecruit platform (Chatbot, Resumes, Interviews, Voice).

Primary Engine   : Google GenAI (gemini-2.0-flash)
Secondary Engine : Groq API (llama3-8b-8192) format via requests (ultra-low latency)
Tertiary Engine  : Hugging Face Inference API (Mistral-7B)

Universal Graceful Degradation: If Gemini hits a 429 Quota Exceeded limit,
it instantly wraps and routes to the Groq/HF fallback while maintaining the persona.
"""

import os
import logging
import requests
import json
from google import genai
import groq
from django.conf import settings

logger = logging.getLogger(__name__)

# --- API KEY INITIALIZATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", "")
HF_API_TOKEN = os.getenv("HF_API_TOKEN") or getattr(settings, "HF_API_TOKEN", "")

class AIEngine:
    """
    Centralized Multi-LLM AI Engine with Zero-Downtime Graceful Fallback Pipeline.
    Single Source of Truth for Chatbot, Voice Assistant, Resume Parsing, and AI Interviewer.
    """

    def __init__(self):
        # 1. Initialize Gemini Client (Primary)
        self.gemini_client = None
        if GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"[AIEngine] Failed to initialize Gemini Client: {e}")
        else:
            logger.warning("[AIEngine] GEMINI_API_KEY not found.")

        # 2. Initialize Groq Client (Speed & Tier-1 Fallback)
        self.groq_client = None
        if GROQ_API_KEY:
            try:
                self.groq_client = groq.Groq(api_key=GROQ_API_KEY)
            except Exception as e:
                logger.warning(f"[AIEngine] Failed to initialize Groq Client: {e}")
        else:
            logger.warning("[AIEngine] GROQ_API_KEY not found.")

        # 3. Hugging Face Inference API details (Ultimate Fallback)
        self.hf_token = HF_API_TOKEN
        self.hf_model_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

    # ==========================================
    # GENERIC GENERATOR (Backward Compatibility)
    # ==========================================
    def generate(self, user_prompt: str, system_prompt: str = "", **kwargs) -> str:
        """
        Generic prompt dispatcher with full fallback logic.
        Used by various platform modules for non-specialized tasks.
        """
        from jobs.models import PlatformSetting
        active_llm = PlatformSetting.get('ACTIVE_LLM', 'groq-llama3')
        combined_prompt = f"{system_prompt}\n\n{user_prompt}".strip()

        if active_llm == 'groq-llama3':
            try:
                return self._generate_via_groq(combined_prompt)
            except Exception as e:
                logger.warning(f"GENERIC: Groq Exception: {e}. Falling back to Gemini.")
        elif active_llm == 'openai-gpt4':
            # Simulated placeholder for OpenAI - default to primary if API not configured
            pass

        # 1. Primary: Groq (Ultra-low Latency)
        try:
            return self._generate_via_groq(combined_prompt)
        except Exception as e:
            logger.warning(f"GENERIC: Groq Exception: {e}. Falling back to Gemini.")

        # 2. Tier 1: Gemini (High Intelligence Fallback)
        try:
            return self._generate_via_gemini(combined_prompt)
        except Exception as e:
            logger.warning(f"GENERIC: Gemini Fallback Exception: {e}. Falling back to HF.")

        # 3. Tier 2: HF
        try:
            return self._generate_via_hf(combined_prompt)
        except Exception as e:
            logger.error(f"GENERIC: All Engines Failed: {e}")
            return "AI_UNAVAILABLE_FALLBACK"

    # ==========================================
    # INTERNAL ENGINE GENERATORS
    # ==========================================
    def _generate_via_gemini(self, prompt: str) -> str:
        if not self.gemini_client:
            raise Exception("Gemini Client not initialized.")
        response = self.gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        if not response.text:
            raise Exception("Gemini returned empty response.")
        return response.text.strip()

    def _generate_via_groq(self, prompt: str) -> str:
        if not self.groq_client:
            raise Exception("Groq Client not initialized.")
        chat_completion = self.groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192",
            temperature=0.7,
        )
        content = chat_completion.choices[0].message.content
        if not content:
            raise Exception("Groq returned empty response.")
        return content.strip()

    def _generate_via_hf(self, prompt: str) -> str:
        if not self.hf_token or self.hf_token.startswith("hf_YOUR"):
            raise Exception("HF API Token not configured.")
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {
            "inputs": f"<s>[INST] {prompt} [/INST]",
            "parameters": {"max_new_tokens": 512, "temperature": 0.7, "return_full_text": False}
        }
        res = requests.post(self.hf_model_url, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0].get('generated_text', '').strip()
        elif isinstance(data, dict):
            return data.get('generated_text', '').strip()
        raise Exception("Failed to parse HF Response.")

    def embed(self, texts: list) -> list:
        """
        Embeds a list of strings using Gemini-1.5 Embedding model.
        Falls back to local Sentence-Transformers if Gemini fails.
        """
        if not texts: return []
        
        # 1. Primary: Gemini Embeddings
        if self.gemini_client:
            try:
                response = self.gemini_client.models.embed_content(
                    model='text-embedding-004',
                    contents=texts
                )
                return [e.values for e in response.embeddings]
            except Exception as e:
                logger.warning(f"[AIEngine] Gemini Embedding failed: {e}. Falling back to Local.")

        # 2. Fallback: Local Sentence-Transformers
        try:
            from sentence_transformers import SentenceTransformer
            # Using multi-lingual model for global support
            model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            embeddings = model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"[AIEngine] Local Embedding fallback failed: {e}")
            return []

    # ==========================================
    # PUBLIC FACING METHODS (WITH FALLBACK PIPELINE)
    # ==========================================

    def get_chat_response(self, user_message: str, context_history: str = None) -> str:
        """
        Chatbot logic: Gemini -> Groq -> HF. Maintains the 'Sentinel Prime' persona.
        """
        persona = (
            "You are 'Sentinel Prime', an elite AI Recruitment Assistant for SmartRecruit. "
            "Your purpose is to assist recruiters and candidates with job searches, resume guidance, "
            "interview preparation, and HR best practices. "
            "Be highly professional, concise, and focused on recruitment, jobs, and HR."
            "Output ONLY clean HTML. Use <strong> for emphasis, <br> for line breaks, "
            "and <ul>/<li> for lists. Never use markdown triple backticks (```)."
        )
        prompt = f"{persona}\n\nContext: {context_history or 'None'}\n\nUser Message: {user_message}"

        # 1. Primary Engine: Groq (Instant Interaction)
        try:
            return self._generate_via_groq(prompt).replace("```html", "").replace("```", "").strip()
        except Exception as e:
            logger.warning(f"WARNING: Groq Exception: {e}. Falling back to Gemini.")

        # 2. Tier 1 Fallback: Gemini (High Wisdom)
        try:
            return self._generate_via_gemini(prompt).replace("```html", "").replace("```", "").strip()
        except Exception as e:
            logger.warning(f"WARNING: Gemini Fallback Exception: {e}. Falling back to Hugging Face.")

        # 3. Tier 2 Fallback: Hugging Face
        try:
            return self._generate_via_hf(prompt).replace("```html", "").replace("```", "").strip()
        except Exception as e:
            logger.error(f"ERROR: Hugging Face Fallback Exception: {e}. All Engines Failed.")
            return "My advanced generative intelligence is currently undergoing a scheduled optimization. Please check back shortly."

    def get_voice_response(self, user_audio_text: str) -> str:
        """
        Voice Assistant Logic: Defaults to Groq (Speed) -> Gemini -> HF.
        """
        persona = (
            "You are 'Sentinel Prime', an elite AI Recruitment Assistant for SmartRecruit. "
            "FORMATTING: The user is listening via Voice Text-to-Speech (TTS). "
            "Respond in plain, conversational text. Do NOT use any Markdown. "
            "Do NOT use HTML tags. Keep sentences short, natural, and easy to hear."
        )
        prompt = f"{persona}\n\nUser said: {user_audio_text}"

        # 1. Speed Engine: Groq
        try:
            return self._generate_via_groq(prompt)
        except Exception as e:
            logger.warning(f"WARNING: Voice Groq Exception: {e}. Falling back to Gemini.")

        # 2. Tier 1 Fallback: Gemini
        try:
            return self._generate_via_gemini(prompt)
        except Exception as e:
            logger.warning(f"WARNING: Voice Gemini Fallback Exception: {e}. Falling back to Hugging Face.")

        # 3. Tier 2 Fallback: HF
        try:
            return self._generate_via_hf(prompt)
        except Exception as e:
            logger.error(f"ERROR: Voice HF Fallback Exception: {e}. All Engines Failed.")
            return "I am currently undergoing network maintenance. Please try your voice query again later."

    def analyze_resume(self, resume_text: str, job_description: str) -> str:
        """
        Resume Parsing Logic: Defaults to Gemini (High Context) -> Groq.
        Mandated to return a STRICTLY valid JSON string for RAG pipelines.
        """
        prompt = (
            "You are an Elite AI Assessor and ATS Optimization Expert. "
            "Evaluate the provided resume against the job description. "
            "Return ONLY a strictly valid JSON object. No markdown, no pre-amble.\n\n"
            "Required Schema:\n"
            "{\n"
            "  \"ats_score\": <integer 0-100>,\n"
            "  \"strengths\": [\"string\", \"string\"],\n"
            "  \"missing_skills\": [\"string\", \"string\"],\n"
            "  \"recommendation\": \"Shortlist\" or \"Reject\"\n"
            "}\n\n"
            f"Job Description:\n{job_description}\n\n"
            f"Resume Content:\n{resume_text}"
        )

        # 1. Primary Engine: Groq (Fast Screening)
        try:
            res = self._generate_via_groq(prompt)
            return res.replace("```json", "").replace("```", "").strip()
        except Exception as e:
            logger.warning(f"WARNING: Resume Parsing Groq Exception: {e}. Falling back to Gemini.")
            
        # 2. Tier 1 Fallback: Gemini (Deep Context)
        try:
            res = self._generate_via_gemini(prompt)
            return res.replace("```json", "").replace("```", "").strip()
        except Exception as e:
            logger.warning(f"WARNING: Resume Parsing Gemini Exception: {e}. Falling back to HF.")

        # 3. Tier 2 Fallback: HF
        try:
            res = self._generate_via_hf(prompt)
            return res.replace("```json", "").replace("```", "").strip()
        except Exception as e:
            logger.error(f"ERROR: Resume Parsing All Engines Failed: {e}")
            return '{"ats_score": 0, "strengths": [], "missing_skills": [], "recommendation": "Reject"}'

    def get_botanist_response(self, user_audio_text: str, context_history: str = None, candidate_language: str = "en") -> str:
        """
        Botanist AI Interviewer Logic: gemini-2.0-flash optimized for behavioral pre-screening.
        Responsible for generating context-aware follow-up questions and evaluation.
        """
        from jobs.models import PlatformSetting
        base_persona = PlatformSetting.get('PROMPT_BOTANIST', '')
        if not base_persona:
            base_persona = (
                "You are 'The Botanist', a highly sophisticated AI Behavioral Interviewer for SmartRecruit. "
                "Your specialty is pre-screening candidates for behavioral fitment using the STAR method. "
                "Current Goal: Analyze the candidate's responses to behavioral questions and ask insightful follow-up questions. "
                "FORMATTING: The user is listening via Voice TTS. Keep your response conversational, concise, and professional. "
                "Respond ONLY as if you are speaking. Use NO markdown and NO HTML labels."
            )

        persona = (
            f"{base_persona}\n"
            f"CRITICAL INSTRUCTION: You MUST conduct this interview entirely in the following ISO language code: {candidate_language}. "
            f"If the code is 'es', speak Spanish. If 'hi', speak Hindi. If 'gu', speak Gujarati."
        )
        prompt = f"{persona}\n\nInterview Context/History: {context_history or 'None'}\n\nCandidate just said: {user_audio_text}"

        # Primary Engine: Groq (Conversational Speed)
        try:
            return self._generate_via_groq(prompt)
        except Exception as e:
            logger.warning(f"WARNING: Botanist Groq Exception: {e}. Falling back to Gemini.")

        # Tier 1 Fallback: Gemini
        try:
            return self._generate_via_gemini(prompt)
        except Exception as e:
            logger.error(f"ERROR: Botanist All Engines Failed: {e}")
            return "Thank you for that response. I appreciate your input. Let's move to the next part of our discussion."

    def evaluate_behavioral_fitment(self, full_transcript: str, candidate_language: str = "en") -> str:
        """
        Final evaluation of a voice interview transcript for behavioral fitment.
        Used to generate the 'Behavioral Fitment Summary' for recruiters.
        """
        prompt = (
            "You are an Elite AI Behavioral Assessor. Evaluate the following interview transcript. "
            "Provide a concise summary of the candidate's behavioral fitment, emotional intelligence, and professional communication. "
            "Return a SHORT summary (max 150 words) suitable for a recruiter dashboard.\n"
            "CRITICAL INSTRUCTION: No matter what language the candidate spoke in, you MUST write your final evaluation report entirely in English.\n\n"
            f"Candidate Native Language Used: {candidate_language}\n"
            f"Transcript:\n{full_transcript}"
        )

        try:
            return self._generate_via_gemini(prompt)
        except Exception as e:
            logger.warning(f"Fitment evaluation fallback: {e}")
            return self._generate_via_groq(prompt)

    def evaluate_architecture(self, topology_desc: str) -> dict:
        """
        Evaluates a System Architecture visual diagram represented as a string.
        Returns a dictionary with 'score' and 'feedback'.
        """
        prompt = (
            "You are an Elite Cloud Solutions Architect. Evaluate the following system architecture. "
            "Analyze for potential single points of failure, scalability, security, and best practices. "
            "Return ONLY a strictly valid JSON object. No markdown, no pre-amble.\\n\\n"
            "Required Schema:\\n"
            "{\\n"
            '  "score": <integer 0-100>,\\n'
            '  "feedback": "Concise paragraph highlighting strengths, flaws, and recommendations"\\n'
            "}\\n\\n"
            f"Architecture Description:\\n{topology_desc}"
        )

        # 1. Primary Engine: Groq
        try:
            res = self._generate_via_groq(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            return json.loads(res)
        except Exception as e:
            logger.warning(f"Architecture Groq Exception: {e}. Falling back to Gemini.")

        # 2. Tier 1 Fallback: Gemini
        try:
            res = self._generate_via_gemini(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            return json.loads(res)
        except Exception as e:
            logger.error(f"Architecture Evaluation All Engines Failed: {e}")
            return {
                "score": 50,
                "feedback": "AI evaluation currently unavailable. Default score applied."
            }


    def generate_questions(self, round_type: str, category: str, difficulty: str, count: int = 5) -> list:
        """
        Generates a list of high-quality MCQs for the QuestionBank.
        Returns a list of dictionaries matching the QuestionBank schema.
        """
        prompt = (
            "You are an Elite Technical Recruiter and Subject Matter Expert. "
            f"Generate {count} unique and challenging Multiple Choice Questions (MCQs) for a recruitment interview.\n\n"
            "STRICT CONSTRAINTS:\n"
            f"1. Round Type: {round_type}\n"
            f"2. Category: {category}\n"
            f"3. Difficulty: {difficulty}\n"
            "4. Return ONLY a strictly valid JSON list of objects. No markdown, no pre-amble.\n"
            "5. Each object MUST follow this schema:\n"
            "{\n"
            '  "question_text": "string",\n'
            '  "options": ["Option A", "Option B", "Option C", "Option D"],\n'
            '  "correct_answer": "Exact text of the correct option from the options list",\n'
            '  "explanation": "Brief reasoning why it is correct"\n'
            "}\n"
        )

        try:
            res = self._generate_via_groq(prompt)
            res = res.replace("```json", "").replace("```", "").strip()
            return json.loads(res)
        except Exception as e:
            logger.warning(f"Question Generation Groq Exception: {e}. Falling back to Gemini.")
            try:
                res = self._generate_via_gemini(prompt)
                res = res.replace("```json", "").replace("```", "").strip()
                return json.loads(res)
            except Exception as e2:
                logger.error(f"Question Generation All Engines Failed: {e2}")
                return []
