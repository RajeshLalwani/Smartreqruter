import json
import os
import logging
from .models import Application, JobPosting
from .utils import advanced_ai_candidate_ranking

logger = logging.getLogger(__name__)

class DecisionMatrixAgent:
    """
    Elite Decision Suite: Compares multiple candidates side-by-side.
    Uses the SmartRecruit Intelligence Engine for multi-dimensional analysis.
    """

    @staticmethod
    def generate_matrix(job_id):
        """
        Gathers top applications for a job and generates a comparative matrix.
        """
        job = JobPosting.objects.get(pk=job_id)
        applications = Application.objects.filter(job=job).exclude(status='REJECTED')[:5]
        
        candidates_data = []
        for app in applications:
            # Aggregate 3-round AI results for holistic evaluation
            candidates_data.append({
                "id": app.id,
                "name": app.candidate.full_name,
                "r1_resume_score": app.ai_score or 0,
                "r2_technical_score": app.technical_score or 0,
                "r3_behavioral_score": app.communication_score or 0,
                "overall_confidence": app.confidence_score or 0,
                "experience": app.candidate.experience_years or 0,
                "skills": app.candidate.skills_extracted or ""
            })

        if not candidates_data:
            return None

        prompt = f"""
        Role: Senior Talent Acquisition Director & Strategic Hiring Agent.
        Task: Perform a multi-dimensional comparative analysis for the role: '{job.title}'.
        
        JOB DESCRIPTION SCOPE: {job.description[:1000]}
        
        CANDIDATES PERFORMANCE DATA (3-ROUND AI PIPELINE):
        {json.dumps(candidates_data, indent=2)}
        
        ANALYSIS CRITERIA:
        1. Technical Dominance: Weigh R1 and R2 heavily.
        2. Leadership & Communication: Analyze R3 Behavioral scores.
        3. Strategic Fit: Innovation vs Sustainability.
        4. Churn Risk: Predictive based on experience vs role seniority.
        
        You must rank them 1 to {len(candidates_data)}.
        
        Return RAW JSON ONLY:
        {{
            "rankings": [
                {{
                    "application_id": ...,
                    "rank": 1,
                    "cultural_fit": 0-100,
                    "churn_risk": "Low/Medium/High",
                    "innovation_index": 0-100,
                    "uvp": "Unique Value Proposition (1 impactful sentence)"
                }}
            ],
            "hiring_recommendation": "Executive summary of the top tier selection and strategic rationale."
        }}
        """

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {"rankings": [], "hiring_recommendation": "Decision Matrix requires AI connectivity."}

        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                config=types.GenerateContentConfig(response_mime_type='application/json'),
                contents=prompt
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Matrix Error: {e}")
            return {"rankings": [], "hiring_recommendation": "Failed to generate comparative analysis."}
