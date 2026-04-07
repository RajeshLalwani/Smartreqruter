"""
core/utils/rag_engine.py — Advanced Retrieval-Augmented Generation Engine
=====================================================================
SmartRecruit's primary vector intelligence layer.
Uses all-MiniLM-L6-v2 (local, 100% free) for semantic embeddings.
Uses Gemini Flash (free tier) for high-quality reasoning generation.
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict

logger = logging.getLogger(__name__)

# Lazy-load SentenceTransformer to avoid import errors on startup
_sentence_model = None


def _get_sentence_model():
    """Lazy-load paraphrase-multilingual-MiniLM-L12-v2 — cached after first call."""
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Using multi-lingual model for cross-lingual semantic mapping
            _sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("[RAGEngine] paraphrase-multilingual-MiniLM-L12-v2 loaded successfully.")
        except Exception as e:
            logger.error(f"[RAGEngine] SentenceTransformer load failed: {e}")
            _sentence_model = None
    return _sentence_model


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for better semantic coverage."""
    if not text:
        return []
    words = text.split()
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks


def _embed(texts: List[str]) -> np.ndarray:
    """Generate embeddings using all-MiniLM-L6-v2 (local, free, fast)."""
    model = _get_sentence_model()
    if model is None or not texts:
        return np.array([])
    try:
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings
    except Exception as e:
        logger.error(f"[RAGEngine] Embedding failed: {e}")
        return np.array([])


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    if vec_a.size == 0 or vec_b.size == 0:
        return 0.0
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def _call_gemini(prompt: str) -> str:
    """Call Centralized AIEngine (with multi-tier fallback) for reasoning."""
    from core.ai_engine import AIEngine
    ai = AIEngine()
    try:
        return ai.generate(user_prompt=prompt, system_prompt="You are an elite RAG Reasoning Engine.")
    except Exception as e:
        logger.warning(f"[RAGEngine] AI call failed: {e}")
        return ""


class RAGEngine:
    """
    Handles vectorization, context retrieval, and grounded evaluations.
    Embeddings: all-MiniLM-L6-v2 (local, 100% free).
    Reasoning: Gemini Flash (free tier).
    """

    def get_contextual_evaluation(self, resume_text: str, jd_text: str) -> Dict:
        """
        Deep Semantic Match with RAG citations and Reasoning Summary.
        Returns: score, justification (cited), critical_gaps, rag_reasoning.
        """
        if not resume_text or not jd_text:
            return {
                "score": 0,
                "justification": "Incomplete data: resume or job description is missing.",
                "critical_gaps": ["Resume or JD is empty"],
                "rag_reasoning": "Cannot perform semantic matching without both inputs.",
            }

        # 1. Chunk the documents
        resume_chunks = _chunk_text(resume_text)
        jd_chunks = _chunk_text(jd_text)

        if not resume_chunks or not jd_chunks:
            return {"score": 0, "justification": "Text chunking failed.", "critical_gaps": [], "rag_reasoning": ""}

        # 2. Embed with all-MiniLM-L6-v2
        resume_embeddings = _embed(resume_chunks)
        jd_embeddings = _embed(jd_chunks)

        if resume_embeddings.size == 0 or jd_embeddings.size == 0:
            return {
                "score": 0,
                "justification": "Embedding engine offline. Check sentence-transformers installation.",
                "critical_gaps": ["Vector engine unavailable"],
                "rag_reasoning": "Unable to compute semantic similarity without embeddings.",
            }

        # 3. Cross-attention semantic matching
        matches = []
        gaps = []
        for i, jd_vec in enumerate(jd_embeddings):
            sims = [_cosine_similarity(jd_vec, res_vec) for res_vec in resume_embeddings]
            max_idx = int(np.argmax(sims))
            max_sim = sims[max_idx]

            if max_sim > 0.55:
                matches.append({
                    "requirement": jd_chunks[i][:200],
                    "citation": resume_chunks[max_idx][:300],
                    "confidence": round(max_sim, 3),
                })
            elif max_sim < 0.40:
                gaps.append(jd_chunks[i][:150])

        # 4. Compute aggregate score
        if jd_embeddings.shape[0] > 0:
            # Average max similarity across all JD chunks
            avg_scores = []
            for jd_vec in jd_embeddings:
                sims = [_cosine_similarity(jd_vec, res_vec) for res_vec in resume_embeddings]
                avg_scores.append(max(sims) if sims else 0.0)
            raw_score = round(np.mean(avg_scores) * 100, 1)
        else:
            raw_score = 0.0

        score = max(0, min(100, raw_score))

        # 5. Build evidence stream for Gemini
        evidence_stream = "\n".join([
            f"[REQ]: {m['requirement'][:180]}\n[EVIDENCE]: \"{m['citation'][:250]}\"\n[STRENGTH]: {m['confidence']:.2f}\n"
            for m in matches[:8]
        ])
        gaps_text = "\n".join([f"- {g}" for g in gaps[:5]])

        # 6. Cross-Lingual Prompt Engineering
        # If chunks contain non-Latin or evidence is in another language, 
        # we instruct Gemini to reason across scripts.
        prompt = f"""
You are Sentinel Prime, an elite Multi-Lingual AI Recruitment Auditor.
Perform a cross-lingual RAG-grounded evaluation of a candidate based on cited evidence.
Note: Evidence might be in a different language (e.g., Hindi, Spanish, etc.) than the requirements. 
Evaluate semantic overlap regardless of the original script.

SEMANTIC MATCHES (resume citations for JD requirements):
{evidence_stream if evidence_stream else "No strong matches found."}

POTENTIAL GAPS (low semantic match areas):
{gaps_text if gaps_text else "None detected."}

JOB DESCRIPTION (first 800 chars):
{jd_text[:800]}

COMPUTED SIMILARITY SCORE: {score}%

INSTRUCTIONS:
- Write a "justification" of 2-3 sentences referencing the evidence above.
- Write "rag_reasoning" explaining why the score is {score}% based on semantic overlap.
- ⚡ MANDATORY: The entire response (justification, rag_reasoning, critical_gaps) MUST be in English.
- If the original evidence was in a non-English language (e.g., Hindi, Spanish, etc.), translate the core concepts into English in your reasoning.
- List up to 3 "critical_gaps" as short strings.
- Return STRICTLY valid JSON only (no markdown code blocks).

JSON FORMAT:
{{
    "score": {int(score)},
    "justification": "Based on the cited evidence, the candidate demonstrates...",
    "critical_gaps": ["Gap 1", "Gap 2"],
    "rag_reasoning": "The semantic match density indicates..."
}}
"""
        try:
            raw = _call_gemini(prompt)
            if raw:
                cleaned = raw.replace("```json", "").replace("```", "").strip()
                result = json.loads(cleaned)
                result["score"] = max(0, min(100, int(result.get("score", score))))
                return result
        except Exception as e:
            logger.warning(f"[RAGEngine] Gemini reasoning parse failed: {e}")

        # Fallback if Gemini fails
        return {
            "score": int(score),
            "justification": f"Semantic analysis achieved {score:.0f}% match. {len(matches)} requirements validated with evidence from resume.",
            "critical_gaps": [g[:100] for g in gaps[:3]],
            "rag_reasoning": f"Vector similarity using all-MiniLM-L6-v2 found {len(matches)} strong semantic overlaps across {len(jd_chunks)} JD segments.",
        }

    def generate_reasoning_summary(self, resume_text: str, jd_text: str) -> Dict:
        """
        Public wrapper — always returns a full reasoning dict.
        Used by ATS scoring pipeline to attach to every Application.
        """
        return self.get_contextual_evaluation(resume_text, jd_text)

    def find_skill_gaps(self, resume_text: str, jd_text: str) -> List[str]:
        """Identifies JD requirements with NO semantic match in resume."""
        resume_chunks = _chunk_text(resume_text)
        jd_chunks = _chunk_text(jd_text)

        if not resume_chunks or not jd_chunks:
            return []

        resume_embeddings = _embed(resume_chunks)
        jd_embeddings = _embed(jd_chunks)

        if resume_embeddings.size == 0 or jd_embeddings.size == 0:
            return []

        gaps = []
        for i, jd_vec in enumerate(jd_embeddings):
            sims = [_cosine_similarity(jd_vec, res_vec) for res_vec in resume_embeddings]
            if max(sims, default=0) < 0.40:
                gaps.append(jd_chunks[i][:150])

        return gaps[:6]

    def generate_gap_based_questions(self, resume_text: str, jd_text: str, amount: int = 5) -> List[Dict]:
        """Generate targeted technical questions for detected skill gaps."""
        gaps = self.find_skill_gaps(resume_text, jd_text)
        gap_context = ", ".join(gaps[:3]) if gaps else "General Software Mastery"

        prompt = f"""
Candidate Skill Gaps: {gap_context}
JD Context: {jd_text[:500]}

Generate {amount} professional technical MCQ questions targeting these gaps.
Return ONLY valid JSON array:
[
    {{
        "question": "question text here",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct": "Option A",
        "explanation": "Brief explanation why."
    }}
]
"""
        try:
            raw = _call_gemini(prompt)
            if raw:
                cleaned = raw.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned)
        except Exception as e:
            logger.error(f"[RAGEngine] Gap question generation failed: {e}")
        return []


# Singleton instance
_rag_engine_instance = None


def get_rag_engine() -> RAGEngine:
    """Return a singleton RAGEngine. Thread-safe enough for Django views."""
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance
