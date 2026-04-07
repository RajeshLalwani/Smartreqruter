import os
import sys
import requests
import html
import random
import asyncio
import edge_tts
import json
import logging
import tempfile
import uuid
import threading
from datetime import timedelta
from io import BytesIO
from uuid import uuid4

from django.conf import settings
from django.utils import timezone
from django.template.loader import get_template
from xhtml2pdf import pisa

from core.ai_engine import AIEngine
import PyPDF2
import logging

logger = logging.getLogger(__name__)


# ===========================================================================
# ⚡ STEP 4: AUTOMATED n8n WEBHOOK TRIGGER (Zero-Latency, Async Implementation)
# ===========================================================================

def _send_n8n_payload(payload: dict):
    """
    Internal thread target. Sends the candidate evaluation payload to the
    n8n Workflow Engine. Runs in a background daemon thread so the HTTP
    round-trip NEVER blocks the user's request-response cycle.
    """
    webhook_url = os.getenv('N8N_WEBHOOK_URL') or getattr(settings, 'N8N_WEBHOOK_URL', None)
    if not webhook_url:
        logger.warning("[n8n] N8N_WEBHOOK_URL is not configured. Skipping automation trigger.")
        return

    try:
        logger.info(f"[n8n] Triggering workflow for candidate: {payload.get('candidate_email')}")
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=15,
            headers={'Content-Type': 'application/json', 'X-Source': 'SmartRecruit-ATS'}
        )
        response.raise_for_status()
        logger.info(f"[n8n] Webhook delivered successfully. Status: {response.status_code}")
    except requests.exceptions.Timeout:
        logger.error("[n8n] Webhook timed out. The n8n server took too long to respond.")
    except requests.exceptions.ConnectionError:
        logger.error("[n8n] Webhook connection failed. Is the n8n server reachable?")
    except requests.exceptions.HTTPError as e:
        logger.error(f"[n8n] Webhook returned an error response: {e}")
    except Exception as e:
        logger.error(f"[n8n] Unexpected webhook error: {e}")


def trigger_n8n_workflow(
    candidate_name: str,
    candidate_email: str,
    applied_role: str,
    ats_score: float,
    key_strengths: list,
    threshold: float = 75.0
):
    """
    Public API for the n8n trigger.

    Evaluates whether the candidate's ATS score meets the threshold and, if so,
    dispatches the automation payload in a non-blocking background thread.

    Usage (in views.py):
        from .utils import trigger_n8n_workflow
        trigger_n8n_workflow(
            candidate_name=candidate_profile.full_name,
            candidate_email=candidate_profile.email,
            applied_role=job.title,
            ats_score=final_score,
            key_strengths=ai_insights.get('strengths', [])
        )
    """
    if ats_score < threshold:
        logger.info(
            f"[n8n] Score {ats_score}% is below threshold {threshold}%. "
            f"Skipping workflow trigger for {candidate_email}."
        )
        return

    payload = {
        "candidate_name":  candidate_name,
        "candidate_email": candidate_email,
        "applied_role":    applied_role,
        "ats_score":       ats_score,
        "key_strengths":   key_strengths,
        "source":          "SmartRecruit-ATS",
        "triggered_at":    timezone.now().isoformat(),
    }

    # Fire-and-forget: background daemon thread — zero UI latency
    thread = threading.Thread(target=_send_n8n_payload, args=(payload,), daemon=True)
    thread.start()
    logger.info(
        f"[n8n] Background trigger dispatched for {candidate_email} "
        f"(ATS Score: {ats_score}%)."
    )


# --- 1. Question Generation Logic ---

def SmartFallbackGenerator(domain='general', amount=10, difficulty='medium'):
    """Elite Fallback Mechanism: Generates realistic technical questions when AI is offline."""
    FALLBACK_BANK = {
        'PYTHON': [
            {"question": "What is the primary difference between a list and a tuple in Python?", "correct": "Lists are mutable while tuples are immutable", "options": ["Lists are mutable while tuples are immutable", "Tuples are faster for all operations", "Lists can only store strings", "Tuples do not support indexing"]},
            {"question": "How does Python handle memory management?", "correct": "Via reference counting and a cyclic garbage collector", "options": ["Via reference counting and a cyclic garbage collector", "Manual allocation by the developer", "Strictly using stack-based allocation", "It does not have a garbage collector"]},
        ],
        'GENERAL': [
            {"question": "What is the main goal of Agile methodology?", "correct": "Iterative development and rapid response to change", "options": ["Iterative development and rapid response to change", "Strict adherence to a 2-year project plan", "Eliminating all meetings", "Reducing the number of developers needed"]}
        ]
    }
    
    domain_key = str(domain).upper()
    questions = FALLBACK_BANK.get(domain_key, FALLBACK_BANK['GENERAL'])
    
    results = []
    for i in range(amount):
        base = random.choice(questions)
        q = {
            'id': str(uuid4()),
            'question': base['question'],
            'correct': base['correct'],
            'options': random.sample(base['options'], len(base['options']))
        }
        results.append(q)
    return results

def generate_ai_mcqs(amount=10, domain='general', difficulty='medium', resume_text=None, jd_text=None):
    """
    Generates high-quality MCQs using the Centralized AIEngine and RAGEngine.
    If resume_text and jd_text are provided, it performs gap-based generation.
    """
    from core.utils.rag_engine import RAGEngine
    rag = RAGEngine()
    
    if resume_text and jd_text:
        logger.info(f"[RAG] Generating {amount} gap-based questions for candidate.")
        questions = rag.generate_gap_based_questions(resume_text, jd_text, amount=amount)
        if questions:
            return format_questions(questions)

    ai = AIEngine()
    prompt = f"""
    Generate exactly {amount} high-fidelity {difficulty} MCQs for the domain: "{domain}". 
    Return strictly as a raw JSON array.
    Schema: [{{"question": "...", "correct_answer": "...", "incorrect_answers": ["...", "...", "..."]}}]
    """
    try:
        response = ai.generate(user_prompt=prompt, system_prompt="You are an ELITE Senior Lead Architect and Industry Examiner.")
        # Clean potential markdown
        response = response.replace("```json", "").replace("```", "").strip()
        raw_questions = json.loads(response)
        return format_questions(raw_questions)
    except Exception as e:
        logger.error(f"MCQ Generation Error: {e}")
        return SmartFallbackGenerator(domain=domain, amount=amount, difficulty=difficulty)

def fetch_questions(amount=50, category=18, difficulty=None, resume_text=None, jd_text=None):
    """
    Fetches questions from external APIs or delegates to AIEngine for domain-specific questions.
    Now supports RAG context for gap-based generation.
    """
    try:
        if isinstance(category, str):
            diff = difficulty if difficulty else 'medium'
            return generate_ai_mcqs(amount=amount, domain=category, difficulty=diff, resume_text=resume_text, jd_text=jd_text)
            
        fetch_amount = min(amount, 50)
        url = f"https://opentdb.com/api.php?amount={fetch_amount}&category={category}&type=multiple"
        if difficulty:
            url += f"&difficulty={difficulty}"
            
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['response_code'] == 0:
            return format_questions(data['results'])
            
        return []
    except Exception as e:
        logger.error(f"Error fetching questions: {e}")
        return []

def format_questions(raw_questions):
    """Utility to normalize question format for the platform."""
    formatted = []
    for q in raw_questions:
        if isinstance(q, dict) and 'correct' in q and 'options' in q:
            if 'id' not in q: q['id'] = str(uuid4())
            formatted.append(q)
            continue
            
        correct_answer = html.unescape(q.get('correct_answer', q.get('correct', '')))
        incorrect_answers = q.get('incorrect_answers', [])
        
        if not incorrect_answers and 'options' in q:
            options = [html.unescape(opt) for opt in q['options']]
        else:
            options = [html.unescape(opt) for opt in incorrect_answers]
            options.append(correct_answer)
        
        random.shuffle(options)
        formatted.append({
            'id': str(uuid4()),
            'question': html.unescape(q.get('question', '')),
            'options': options,
            'correct': correct_answer,
            'correct_answer': correct_answer
        })
    return formatted

# --- 2. THE CORE RESUME RAG PIPELINE (Step 3 Implementation) ---

def parse_resume(resume_file, job_description=None):
    """
    Overhauled Resume Parser & RAG Pipeline Bridge.
    Uses PyPDF2 to extract text from PDF, then delegates to Gemini-RAG engine 
    (AIEngine) for extracting Skills, Experience, Education, and match score.
    """
    try:
        # Extract text directly using PyPDF2
        resume_text = ""
        pdf_reader = PyPDF2.PdfReader(resume_file)
        for page in pdf_reader.pages:
            resume_text += page.extract_text() + "\n"
        
        # Determine language (Phase 11)
        detected_lang = 'en'
        try:
            from langdetect import detect
            detected_lang = detect(resume_text)
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")

        # Integrate Gemini-RAG engine
        ai = AIEngine()
        system_prompt = (
            "You are Rajesh Lalwani, an elite AI/ML Engineering Lead and Technical Recruiter for SmartRecruit. "
            "Your task is to analyze candidate resumes using advanced RAG and yield precise JSON data."
        )
        
        user_prompt = f"""
        Extract professional data from the following resume text.
        If a Job Description is provided, calculate a strict 'Match Score' (0-100) based on alignment. 
        If no JD is provided, base the Match Score on general technical proficiency.
        
        Return strictly valid JSON with the following schema:
        {{
            "score": <int>,
            "skills": ["<skill1>", "<skill2>", ...],
            "experience_summary": "<A comprehensive summary of work experience>",
            "education": "<Extracted education details>",
            "missing_skills": ["<missing1>", ...],
            "recommendation": "<'Shortlist' or 'Reject' based on match score>",
            "rajesh_insight": "<A 1-2 sentence professional insight from Rajesh Lalwani explaining the score>"
        }}

        Job Description: {job_description or 'Evaluate based on general software engineering standards.'}
        
        Resume Text:
        {resume_text}
        """

        response = ai.generate(user_prompt=user_prompt, system_prompt=system_prompt)
        
        # Robust Response Cleaning
        if not response:
            raise ValueError("Empty response from AI Engine")
            
        clean_response = response.strip()
        if "```" in clean_response:
             # Handle markdown code blocks
             if "```json" in clean_response:
                 clean_response = clean_response.split("```json")[1].split("```")[0].strip()
             else:
                 clean_response = clean_response.split("```")[1].split("```")[0].strip()

        data = json.loads(clean_response)

        return {
            'score': data.get('score', 0),
            'skills': data.get('skills', []),
            'experience_summary': data.get('experience_summary', ''),
            'education': data.get('education', ''),
            'matched_skills': data.get('skills', []),
            'missing_skills': data.get('missing_skills', []),
            'recommendation': data.get('recommendation', 'Reject'),
            'rajesh_insight': data.get('rajesh_insight', ''),
            'email': '',  # Handled by candidate object
            'phone': '',  # Handled by candidate object
            'text': resume_text,
            'detected_language': detected_lang
        }
    except Exception as e:
        logger.error(f"Advanced Resume Parsing Error: {e}")
        return {
            'score': 0,
            'recommendation': 'Reject',
            'error': str(e),
            'skills': [],
            'matched_skills': [],
            'missing_skills': [],
            'experience_summary': '',
            'education': '',
            'rajesh_insight': "Analysis system error. Rajesh Lalwani."
        }

def match_resume_with_ai(resume_file, job_description):
    """
    Semantic Resume-JD Matcher.
    Delegates to the overhauled parse_resume (RAG pipeline) for consistency.
    """
    result = parse_resume(resume_file, job_description)
    return {
        'score': result.get('score', 0),
        'insights': {
            'strengths': result.get('skills', []),
            'missing': result.get('missing_skills', []),
            'recommendation': result.get('recommendation', 'Pending')
        }
    }

def advanced_ai_candidate_ranking(resume_text, job_description):
    """
    Advanced candidate evaluation using Centralized AIEngine.
    """
    ai = AIEngine()
    prompt = f"""
    Evaluate candidate resume against JD. Return strictly valid JSON.
    Schema: {{
        "score": <int>, "strengths": [...], "weaknesses": [...], 
        "summary": "...", "dimensions": {{"Technical": <int>, "Communication": <int>, "Leadership": <int>, "Cultural": <int>}}
    }}
    JD: {job_description}
    Resume: {resume_text}
    """
    try:
        res = ai.generate(user_prompt=prompt, system_prompt="You are an expert technical recruiter.")
        res = res.replace("```json", "").replace("```", "").strip()
        return json.loads(res)
    except Exception as e:
        logger.error(f"Ranking Error: {e}")
        return {'score': 0, 'strengths': [], 'weaknesses': [], 'summary': str(e), 'dimensions': {'Technical': 0, 'Communication': 0, 'Leadership': 0, 'Cultural': 0}}

# --- 3. Roadmap & Learning Logic ---

def generate_growth_roadmap_data(candidate, job):
    """
    Generates a personalized learning roadmap via AIEngine.
    """
    ai = AIEngine()
    prompt = f"""
    Create a 'Skill Bridge Roadmap' for candidate. Return raw JSON.
    Role: {job.title} | Candidate Skills: {candidate.skills_extracted or 'Generic'}
    Schema: {{"summary": "...", "milestones": [{{"title": "...", "weeks": "...", "resources": ["..."], "goal": "..."}}], "poc_project": {{"title": "...", "description": "..."}}}}
    """
    try:
        res = ai.generate(user_prompt=prompt, system_prompt="You are an ELITE Career Architect.")
        res = res.replace("```json", "").replace("```", "").strip()
        return json.loads(res)
    except Exception as e:
        logger.error(f"Roadmap Error: {e}")
        return {"summary": "Offline fallback.", "milestones": []}

# --- 4. Utility Helpers (Voice, JD, ICS, PDF) ---

def generate_voice_file(text):
    """Generates MP3 via Edge TTS."""
    try:
        filename = f"voice_{uuid4()}.mp3"
        media_root = getattr(settings, 'MEDIA_ROOT', 'media')
        voice_dir = os.path.join(media_root, 'voice_questions')
        os.makedirs(voice_dir, exist_ok=True)
        output_path = os.path.join(voice_dir, filename)
        
        async def _save():
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
            await communicate.save(output_path)
        
        asyncio.run(_save())
        return os.path.join('voice_questions', filename)
    except Exception as e:
        logger.error(f"Voice Generation Error: {e}")
        return None

def generate_ai_job_description(title, skills, tone='professional'):
    """Generates a structured JD via AIEngine."""
    ai = AIEngine()
    prompt = f"Generate a {tone} Job Description for {title} with skills: {', '.join(skills)}. Use Markdown."
    try:
        return ai.generate(user_prompt=prompt, system_prompt="You are a professional HR specialist.")
    except Exception:
        return f"**Role**: {title}\n**Skills**: {', '.join(skills)}\n**Tone**: {tone}"

def generate_ics_content(interview):
    """Generates VCALENDAR content."""
    start_time = interview.scheduled_time
    end_time = start_time + timedelta(hours=1)
    def f(dt): return dt.strftime('%Y%m%dT%H%M%SZ')
    
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//SmartRecruit//EN
BEGIN:VEVENT
UID:{interview.id}@smartrecruit.com
DTSTAMP:{f(timezone.now())}
DTSTART:{f(start_time)}
DTEND:{f(end_time)}
SUMMARY:Interview for {interview.application.job.title}
LOCATION:{interview.meeting_link}
END:VEVENT
END:VCALENDAR"""

def render_to_pdf(template_src, context_dict={}):
    """Renders HTML template to PDF."""
    try:
        template = get_template(template_src)
        html_content = template.render(context_dict)
        result = BytesIO()
        pisa.pisaDocument(BytesIO(html_content.encode("utf-8")), result)
        return result.getvalue()
    except Exception as e:
        logger.error(f"PDF Render Error: {e}")
        return None


def run_system_housekeeping():
    """
    Autonomously sweep the database for expired assessment links and offers.
    Ensures 100% adherence to Flow B (7-day timeout) and Flow C (3-day timeout).
    """
    from .models import Application, Offer
    from django.utils import timezone
    from datetime import timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    now = timezone.now()

    # --- Flow B: 7-Day Assessment Inactivity Housekeeping ---
    # Triggered if a candidate stays in 'RESUME_SELECTED' (Shortlisted) 
    # or 'ROUND_1_PENDING' for more than 7 days.
    assessment_threshold = now - timedelta(days=7)
    expired_apps = Application.objects.filter(
        status__in=['RESUME_SELECTED', 'ROUND_1_PENDING'],
        updated_at__lt=assessment_threshold
    )
    
    for app in expired_apps:
        app.status = 'REJECTED_TIMEOUT'
        app.save()
        logger.info(f"[Housekeeping] Flow B: App #{app.id} REJECTED due to 7-day assessment timeout.")

    # --- Flow C: 3-Day Offer Acknowledgement Tracker ---
    # Triggered if an offer in 'SENT' status hasn't been handled by the deadline.
    expired_offers = Offer.objects.filter(
        status='SENT',
        response_deadline__lt=now
    )
    
    for offer in expired_offers:
        offer.status = 'REJECTED' # Mark as rejected due to non-response
        offer.save()
        
        # Link back to application
        app = offer.application
        app.status = 'OFFER_REJECTED'
        app.save()
        logger.info(f"[Housekeeping] Flow C: Offer #{offer.id} for App #{app.id} REJECTED due to 3-day deadline.")
