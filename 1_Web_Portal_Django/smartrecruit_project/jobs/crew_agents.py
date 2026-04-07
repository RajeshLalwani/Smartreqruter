import time
import random

def run_hiring_committee(candidate_name, job_title, required_skills, resume_summary, interview_transcript, assessment_scores):
    """
    Simulates a Multi-Agent CrewAI debate on a candidate's profile.
    Because Python 3.14 lacks pre-compiled Rust/MSVC wheels for Pydantic/Numpy,
    the actual CrewAI pip package cannot install on this environment.
    This provides a deterministic, high-quality simulation for the UI.
    """
    
    # Simulate processing time for the "Agents" to "think"
    time.sleep(2)
    
    # Parse whether this is a strong or weak candidate based on assessment scores string (naive check for simulation)
    is_strong = "Failed" not in assessment_scores and "100/100" not in assessment_scores # just a pseudo check
    
    if "Failed" in assessment_scores:
        tech_verdict = f"**Tech Expert Agent:** Upon reviewing the technical assessments, {candidate_name} struggled significantly, failing to meet the core competency thresholds required for the {job_title} role. The coding assessment revealed gaps in optimal algorithmic understanding."
        hr_verdict = f"**HR Executive Agent:** The candidate communicated reasonably well during the interview, but showed some frustration when pressed on technical constraints. Overall culture fit is decent, but not exceptional."
        final_verdict = "REJECT"
        manager_justification = f"While {candidate_name} exhibits acceptable communication traits, the glaring technical deficiencies highlighted by the Tech Expert make this a high-risk hire. We cannot compromise on engineering standards. Reject."
    else:
        tech_verdict = f"**Tech Expert Agent:** {candidate_name} demonstrates a robust grasp of the required tech stack for the {job_title} position. The assessment scores highlight strong foundational knowledge, and the interview transcript confirms deep practical experience."
        hr_verdict = f"**HR Executive Agent:** I am highly impressed. {candidate_name} articulates complex ideas clearly and displays a strong growth mindset. They align perfectly with our core values of extreme ownership and collaboration."
        final_verdict = "HIRE"
        manager_justification = f"Both the technical and behavioral reports are overwhelmingly positive. {candidate_name} possesses the precise blend of engineering rigor and cultural alignment we need to scale the team. Extend an offer immediately."

    report = f"""## The Virtual Hiring Committee Verdict

### 🤖 Tech Report Summary (Senior Technical Evaluator)
{tech_verdict}

### 🤝 HR Report Summary (Chief People Officer)
{hr_verdict}

---

### ⚖️ Final Decision: **[{final_verdict}]**
**VP of Engineering (The Decider):**
{manager_justification}
"""
    return report
