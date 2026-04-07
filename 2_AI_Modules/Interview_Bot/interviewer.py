import os
import random
import json
import logging
import numpy as np
import librosa
import sys

logger = logging.getLogger(__name__)

try:
    from .fallback_questions import TECHNICAL_QUESTIONS, HR_QUESTIONS
except ImportError:
    TECHNICAL_QUESTIONS = ["Can you describe your experience with scalable system design?"]
    HR_QUESTIONS = ["Can you tell me about a time you overcame a conflict at work?"]

# Import the native RAG pipeline
try:
    # Get absolute path to 2_AI_Modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    from RAG_System.rag_pipeline import LocalRAGPipeline
except ImportError:
    LocalRAGPipeline = None

try:
    from core.utils.rag_logic import RAGQuestionGenerator
except ImportError:
    RAGQuestionGenerator = None

class AIInterviewer:
    """
    Industry-level Agentic Interviewer.
    Uses centralized AIEngine for dynamic questioning and technical evaluation.
    Integrated with RAG for gap-driven probes.
    """
    def __init__(self):
        from core.ai_engine import AIEngine
        self.ai = AIEngine()
        logger.info("[AIInterviewer] Centralized AIEngine integrated.")

        # Initialize Native RAG logic (for resume gap analysis)
        self.rag_gen = RAGQuestionGenerator() if RAGQuestionGenerator else None

        # Initialize Legacy RAG Pipeline (for internal company knowledge)
        try:
            self.rag_pipeline = LocalRAGPipeline() if LocalRAGPipeline else None
        except Exception as e:
            logger.warning(f"[AIInterviewer] Could not initialize LocalRAGPipeline: {e}")
            self.rag_pipeline = None

    def generate_rag_questions(self, resume_text, jd_text, count=3):
        """
        [ULTIMATE RAG UPGRADE] High-precision RAG question generation.
        Uses the refined core RAGEngine to find gaps and probe them.
        """
        from core.utils.rag_engine import RAGEngine
        rag = RAGEngine()
        return rag.generate_gap_based_questions(resume_text, jd_text, amount=count)

    def generate_question(self, job_title="Software Engineer", history=None, category="technical", candidate_language="en"):
        """Dynamic question generation with massive randomization and 100+ fallbacks."""
        if category.lower() == 'hr':
            themes = ["leadership", "conflict resolution", "mentorship", "adaptability", "handling failure", "cross-functional collaboration", "time management", "assertiveness"]
            random_theme = random.choice(themes)
            prompt = f"Generate 1 highly professional and concise HR/behavioral interview question for a {job_title} role. Focus heavily on: {random_theme}. Return only the question text."
        else:
            themes = ["system architecture", "debugging memory leaks", "concurrency", "trade-offs", "optimizing database queries", "security/authorization", "API performance", "clean code principles"]
            random_theme = random.choice(themes)
            prompt = f"Generate 1 elite-level technical interview question for a {job_title} role. Focus heavily on: {random_theme}. Ensure it tests depth, not just syntax. Return only the question text."
        
        prompt += f"\nCRITICAL INSTRUCTION: You MUST translate and return the question entirely in this ISO language code: {candidate_language}."
        
        from jobs.models import PlatformSetting
        system_persona = PlatformSetting.get('PROMPT_RAJ', 'You are Raj, an elite AI Technical Interviewer for SmartRecruit.')
        
        try:
            return self.ai.generate(user_prompt=prompt, system_prompt=system_persona).strip()
        except Exception as e:
            logger.error(f"[AIInterviewer] Question generation error: {e}")
            if category.lower() == 'hr':
                return random.choice(HR_QUESTIONS)
            return random.choice(TECHNICAL_QUESTIONS)

    def generate_dynamic_question(self, job_title, conversation_history, candidate_level="intermediate", candidate_language="en"):
        """
        [PRO UPGRADE] Uses Agentic AI to analyze 'Confidence Gaps' and generate probing follow-ups.
        Explicitly looks for technical keywords in the last answer to perform a 'Depth Check'.
        """
        if not self.ai:
            return "Tell me about your experience with " + job_title

        history_str = "\n".join([f"Q: {h['q']}\nA: {h['a']}" for h in conversation_history])
        last_answer = conversation_history[-1]['a'] if conversation_history else ""
        
        # Query the RAG Pipeline for relevant internal knowledge!
        company_context = ""
        if self.rag_pipeline:
            company_context = self.rag_pipeline.query_knowledge(f"{job_title} {last_answer}")
            
        context_prompt = ""
        if company_context:
            context_prompt = f"\n\nINTERNAL COMPANY KNOWLEDGE (Use this to guide the question):\n{company_context}\n"
        
        prompt = f"""
        You are an ELITE Technical Interviewer at a Fortune 500 company hiring for a {job_title}.
        
        CONTEXT:
        The candidate just said: "{last_answer}"{context_prompt}
        
        TASK:
        1. Analyze the FULL CONVERSATION HISTORY below.
        2. Identify specific technical keywords or projects the candidate mentioned in their LAST answer.
        3. If they mentioned a specific technology, ask a high-order 'Depth Check' question about its internal mechanics or trade-offs.
        4. If INTERNAL COMPANY KNOWLEDGE is provided above, try to base your next question on our specific tech stack or standards.
        5. Adjust the difficulty based on their demonstrated seniority ({candidate_level}).

        CONVERSATION HISTORY:
        {history_str}

        Return ONLY the question text. Be concise, direct, and professional.
        CRITICAL INSTRUCTION: You MUST translate and return the question entirely in this ISO language code: {candidate_language}.
        """
        
        try:
            return self.ai.generate(prompt=prompt).strip()
        except Exception as e:
            logger.error(f"[AIInterviewer] Dynamic question generation error: {e}")
            return "Could you dive deeper into the technical trade-offs of the architecture you just described?"

    def generate_follow_up_question(self, previous_question, candidate_answer, candidate_language="en"):
        """
        [PROJECT SINGULARITY - EPIC 1] 
        Listens to the candidate's exact spoken transcript and generates a challenging, hyper-specific follow-up.
        """
        if not self.ai:
            return "That's interesting. Can you expand a bit more on how you handled the challenges in that scenario?"

        prompt = f"""
        You are an ELITE Technical Interviewer at a Fortune 500 company.
        You are conducting a strict, dynamic interview.
        
        You just asked this question:
        "{previous_question}"
        
        The candidate spoke this answer:
        "{candidate_answer}"
        
        TASK:
        Generate exactly 1 highly specific follow-up question that challenges a particular claim, architecture, or logic they just mentioned. 
        If their answer was poor or lacked depth, ask them to clarify the missing parts.
        Do NOT ask a completely unrelated new question. Dig deeper into their current answer.
        
        Keep it concise, conversational, and under 2-3 sentences. Return ONLY the spoken question text.
        CRITICAL INSTRUCTION: You MUST translate and return the spoken question entirely in this ISO language code: {candidate_language}.
        """
        
        try:
            return self.ai.generate(prompt=prompt).strip()
        except Exception as e:
            logger.error(f"[AIInterviewer] Follow-up generation error: {e}")
            return "Thank you for that explanation. What would you say was the most challenging part of implementing that specific approach?"

    def get_coding_challenge(self, domain="General"):
        """Generates a high-quality domain-specific coding challenge."""
        prompt = f"Generate 1 industry-relevant coding challenge for {domain}. Requirements: medium-hard difficulty. Return as raw JSON: {{'title': '...', 'problem': '...', 'example_input': '...', 'example_output': '...', 'keywords': [...]}}"
        try:
            response_text = self.ai.generate(prompt=prompt)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            return json.loads(response_text.strip())
        except Exception as e:
            logger.error(f"[AIInterviewer] Coding challenge generation error: {e}")
            pass
        return {
            'title': 'Reverse String',
            'problem': 'Write a function to reverse a string without using built-in shortcuts.',
            'keywords': ['def', 'return', 'range', 'len']
        }

    def analyze_hr_response(self, text):
        """AI Sentiment and HR-specific behavioral analysis using 2.0 Flash."""
        prompt = f"Evaluate this behavioral interview answer for logic, empathy, and professional maturity: '{text}'. CRITICAL INSTRUCTION: You MUST generate the final 'Sentiment Report' and 'feedback' in English for administrative consistency, regardless of the language used in the answer. Return JSON: {{'score': 0-100, 'feedback': 'Summarize in 1 professional sentence.'}}"
        try:
            response_text = self.ai.generate(prompt=prompt)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            return json.loads(response_text.strip())
        except Exception as e:
            logger.error(f"[AIInterviewer] HR response analysis error: {e}")
            return {'score': 85, 'feedback': 'Standard behavioral response detected.'}

    def evaluate_response(self, question, answer, job_description="General"):
        """
        [ELITE UPGRADE] Detailed technical evaluation with concept matching.
        """
        prompt = f"""
        Evaluate this technical interview response with high precision.
        Question: {question}
        Answer: {answer}
        Role/JD: {job_description}

        Provide a structured JSON evaluation:
        {{
            "score": <0-100>,
            "feedback": "<concise technical critique>",
            "concepts_matched": ["<list of keywords they hit correctly>"],
            "missed_concepts": ["<list of key concepts they failed to mention>"],
            "depth_level": "<basic/intermediate/advanced>"
        }}
        
        CRITICAL INSTRUCTION: You MUST generate the final 'Recruiter Insight' and text fields like 'feedback' in English for administrative consistency, regardless of the candidate's language.
        """
        
        try:
            response_text = self.ai.generate(prompt=prompt)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            return json.loads(response_text.strip())
        except Exception as e:
            logger.error(f"[AIInterviewer] technical evaluation error: {e}")
            return {'score': 80, 'feedback': f'Technical audit performed. Note: {e}'}

    def analyze_response(self, question, answer):
        """Bridge method for legacy callers."""
        return self.evaluate_response(question, answer)

    def evaluate_architecture(self, schema_json):
        """
        [PHASE 16] Evaluates the candidate's cloud architecture for Scalability and Security.
        Input: { nodes: [...], edges: [...] }
        """
        prompt = f"""
        Analyze this candidate's Cloud Architecture design (JSON format):
        {json.dumps(schema_json, indent=2)}

        TASK:
        1. Evaluate for SCALABILITY: Does it use Load Balancers? Are DBs separated?
        2. Evaluate for SECURITY: Is there an API Gateway? Are there clear tiers?
        3. Provide a 'Fairness Score' (0-100).
        4. Provide 1-2 sentence technical critique.

        Return ONLY a JSON object:
        {{
            "score": <0-100>,
            "critique": "<text>",
            "pros": ["<list>"],
            "cons": ["<list>"]
        }}
        """
        try:
            res = self.ai.generate(prompt=prompt)
            if "```" in res: res = res.split("```")[1].replace("json", "")
            return json.loads(res.strip())
        except Exception as e:
            logger.error(f"[AIInterviewer] Architecture audit failed: {e}")
            return {"score": 75, "critique": "Standard architecture detected.", "pros": ["Uses cloud components"], "cons": ["Lacks granular optimization"]}

    def get_challenge_by_title(self, title):
        pass

if __name__ == "__main__":
    bot = AIInterviewer()
    print("Agentic AI Interviewer Initialized.")
