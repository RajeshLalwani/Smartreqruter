"""
core/utils/rag_logic.py — Dynamic Questioning Logic
===================================================
Refactors the AI Interviewer to be 'Knowledge-Driven'.
Uses RAG to find specific weaknesses and generate targeted probes.
"""

import logging
from typing import List
from .rag_engine import RAGEngine
from core.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class RAGQuestionGenerator:
    """
    Generates technical interview questions by analyzing 
    the delta between a candidate's resume and the Job Description.
    """

    def __init__(self):
        self.rag = RAGEngine()
        self.ai = AIEngine()

    def generate_targeted_questions(self, resume_text: str, jd_text: str, count: int = 3) -> List[str]:
        """
        Uses RAG to identify gaps and then asks the LLM to generate 
        challenging questions specifically for those gaps.
        """
        # 1. Identify Semantic Gaps
        gaps = self.rag.find_skill_gaps(resume_text, jd_text)
        
        if not gaps:
            # Fallback to standard contextual questioning if no major gaps found
            prompt = (
                f"Candidate Resume: {resume_text[:2000]}\n"
                f"Job Description: {jd_text[:2000]}\n"
                "Generate 3 challenging technical interview questions that test depth."
            )
        else:
            gap_summary = "\n".join([f"- {g[:150]}" for g in gaps])
            prompt = (
                f"You are a Senior Technical Interviewer. I have identified the following MISSED SKILLS or GAPS "
                f"in the candidate's resume relative to the Job Description:\n{gap_summary}\n\n"
                f"Job Description Context:\n{jd_text[:1000]}\n\n"
                f"Generate {count} specific, deep-dive technical questions to probe if the candidate "
                f"actually possesses these skills or understands the concepts, even if they aren't explicitly in the resume."
                "Return the questions as a simple numbered list. No preamble."
            )

        try:
            res = self.ai.generate(prompt)
            # Parse numbered list
            questions = [q.strip() for q in res.split('\n') if q.strip() and (q[0].isdigit() or q.startswith('-'))]
            return questions[:count]
        except Exception as e:
            logger.error(f"[RAGLogic] Question generation failed: {e}")
            return ["Tell me about your most challenging technical project.", "How do you handle scalability in production?"]
