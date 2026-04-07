"""
AI Interview Prep Tips - A new AI-powered feature
Generates personalized interview tips + question bank for candidates
based on their applied job and skill gaps.
"""
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Application

try:
    from google import genai as google_genai
    from django.conf import settings
    _genai_client = google_genai.Client(api_key=settings.GEMINI_API_KEY)
    _genai_active = bool(settings.GEMINI_API_KEY)
except Exception:
    _genai_client = None
    _genai_active = False


def _generate_tips(job_title: str, skills: str, job_desc: str) -> dict:
    """Generate AI interview tips using Gemini."""
    if not _genai_active:
        return _fallback_tips(job_title, job_desc)

    prompt = f"""
You are an expert career coach. A candidate is preparing for a "{job_title}" interview.
Their skills: {skills or 'Not specified'}
Job description excerpt: {(job_desc or '')[:400]}

Return ONLY valid JSON with this structure (no markdown, no code fences):
{{
  "quick_tips": ["tip1", "tip2", "tip3", "tip4", "tip5"],
  "technical_questions": [
    {{"q": "Q1", "hint": "H1"}}, {{"q": "Q2", "hint": "H2"}}, {{"q": "Q3", "hint": "H3"}}, {{"q": "Q4", "hint": "H4"}}, {{"q": "Q5", "hint": "H5"}}, {{"q": "Q6", "hint": "H6"}}, {{"q": "Q7", "hint": "H7"}}, {{"q": "Q8", "hint": "H8"}}, {{"q": "Q9", "hint": "H9"}}, {{"q": "Q10", "hint": "H10"}}, {{"q": "Q11", "hint": "H11"}}, {{"q": "Q12", "hint": "H12"}}, {{"q": "Q13", "hint": "H13"}}, {{"q": "Q14", "hint": "H14"}}, {{"q": "Q15", "hint": "H15"}}, {{"q": "Q16", "hint": "H16"}}, {{"q": "Q17", "hint": "H17"}}, {{"q": "Q18", "hint": "H18"}}, {{"q": "Q19", "hint": "H19"}}, {{"q": "Q20", "hint": "H20"}}, {{"q": "Q21", "hint": "H21"}}, {{"q": "Q22", "hint": "H22"}}, {{"q": "Q23", "hint": "H23"}}, {{"q": "Q24", "hint": "H24"}}, {{"q": "Q25", "hint": "H25"}}, {{"q": "Q26", "hint": "H26"}}, {{"q": "Q27", "hint": "H27"}}, {{"q": "Q28", "hint": "H28"}}, {{"q": "Q29", "hint": "H29"}}, {{"q": "Q30", "hint": "H30"}}, {{"q": "Q31", "hint": "H31"}}, {{"q": "Q32", "hint": "H32"}}, {{"q": "Q33", "hint": "H33"}}, {{"q": "Q34", "hint": "H34"}}, {{"q": "Q35", "hint": "H35"}}, {{"q": "Q36", "hint": "H36"}}, {{"q": "Q37", "hint": "H37"}}, {{"q": "Q38", "hint": "H38"}}, {{"q": "Q39", "hint": "H39"}}, {{"q": "Q40", "hint": "H40"}}, {{"q": "Q41", "hint": "H41"}}, {{"q": "Q42", "hint": "H42"}}, {{"q": "Q43", "hint": "H43"}}, {{"q": "Q44", "hint": "H44"}}, {{"q": "Q45", "hint": "H45"}}, {{"q": "Q46", "hint": "H46"}}, {{"q": "Q47", "hint": "H47"}}, {{"q": "Q48", "hint": "H48"}}, {{"q": "Q49", "hint": "H49"}}, {{"q": "Q50", "hint": "H50"}}
  ],
  "hr_questions": [
    {{"q": "Q1", "hint": "H1"}}, {{"q": "Q2", "hint": "H2"}}, {{"q": "Q3", "hint": "H3"}}, {{"q": "Q4", "hint": "H4"}}, {{"q": "Q5", "hint": "H5"}}, {{"q": "Q6", "hint": "H6"}}, {{"q": "Q7", "hint": "H7"}}, {{"q": "Q8", "hint": "H8"}}, {{"q": "Q9", "hint": "H9"}}, {{"q": "Q10", "hint": "H10"}}, {{"q": "Q11", "hint": "H11"}}, {{"q": "Q12", "hint": "H12"}}, {{"q": "Q13", "hint": "H13"}}, {{"q": "Q14", "hint": "H14"}}, {{"q": "Q15", "hint": "H15"}}, {{"q": "Q16", "hint": "H16"}}, {{"q": "Q17", "hint": "H17"}}, {{"q": "Q18", "hint": "H18"}}, {{"q": "Q19", "hint": "H19"}}, {{"q": "Q20", "hint": "H20"}}, {{"q": "Q21", "hint": "H21"}}, {{"q": "Q22", "hint": "H22"}}, {{"q": "Q23", "hint": "H23"}}, {{"q": "Q24", "hint": "H24"}}, {{"q": "Q25", "hint": "H25"}}, {{"q": "Q26", "hint": "H26"}}, {{"q": "Q27", "hint": "H27"}}, {{"q": "Q28", "hint": "H28"}}, {{"q": "Q29", "hint": "H29"}}, {{"q": "Q30", "hint": "H30"}}, {{"q": "Q31", "hint": "H31"}}, {{"q": "Q32", "hint": "H32"}}, {{"q": "Q33", "hint": "H33"}}, {{"q": "Q34", "hint": "H34"}}, {{"q": "Q35", "hint": "H35"}}, {{"q": "Q36", "hint": "H36"}}, {{"q": "Q37", "hint": "H37"}}, {{"q": "Q38", "hint": "H38"}}, {{"q": "Q39", "hint": "H39"}}, {{"q": "Q40", "hint": "H40"}}, {{"q": "Q41", "hint": "H41"}}, {{"q": "Q42", "hint": "H42"}}, {{"q": "Q43", "hint": "H43"}}, {{"q": "Q44", "hint": "H44"}}, {{"q": "Q45", "hint": "H45"}}, {{"q": "Q46", "hint": "H46"}}, {{"q": "Q47", "hint": "H47"}}, {{"q": "Q48", "hint": "H48"}}, {{"q": "Q49", "hint": "H49"}}, {{"q": "Q50", "hint": "H50"}}
  ],
  "skills_to_brush_up": ["skill1", "skill2", "skill3"],
  "confidence_score": 72,
  "preparation_time": "3-5 days"
}}

[IMPORTANT: Provide exactly 50 Technical and 50 HR questions. Ensure high variety and depth.]
"""
    try:
        response = _genai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={"max_output_tokens": 8192}
        )
        text = response.text.strip()
        # Robustly strip markdown fences if present
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
            
        return json.loads(text.strip())
    except Exception:
        return _fallback_tips(job_title, job_desc)


def _fallback_tips(job_title: str, custom_focus: str = "") -> dict:
    """Fallback tips when Gemini is unavailable."""
    focus = custom_focus.replace("Focus on: ", "").strip() if custom_focus else job_title
    
    return {
        "quick_tips": [
            f"Research the specific tech stack for {job_title} thoroughly.",
            f"Refresh your core concepts around {focus} before the technical rounds.",
            "Mock code on a whiteboard if it is a technical lead role.",
            "Prepare 5 deep STAR method stories highlighting technical resolution.",
            "Investigate the company's recent engineering blogs or public GitHub.",
        ],
        "technical_questions": [
            {"q": f"Explain the core architecture and fundamental principles of {focus}.", "hint": "Differentiate between theoretical concepts and practical application."},
            {"q": f"What are the most common performance bottlenecks when working with {focus}?", "hint": "Discuss optimization techniques and caching."},
            {"q": f"Describe a complex problem you solved involving {focus}. What was the outcome?", "hint": "Use the STAR method emphasizing your technical decisions."},
            {"q": f"How do you handle edge cases and security vulnerabilities typically associated with {focus}?", "hint": "Mention industry standards and best practices."},
            {"q": "What is the difference between an Abstract Class and an Interface?", "hint": "State vs. Contractual behavior."},
            {"q": "Explain the difference between supervised and unsupervised learning.", "hint": "Labeled vs unlabeled data applications."},
            {"q": "How would you handle missing data in a large dataset for training?", "hint": "Imputation types and bias considerations."},
            {"q": "What is Big O notation and how do you analyze a recursive function?", "hint": "Time/Space complexity and recurrence relations."}
        ] + [{"q": f"Advanced {focus} Technical Question #{i}", "hint": "Consult internal system documentation for deep dive."} for i in range(9, 51)],
        "hr_questions": [
            {"q": "Tell me about a time you led a project with conflicting stakeholder interests.", "hint": "Show negotiation and data-driven prioritization."},
            {"q": "Why should we hire you over other candidates with similar technical skills?", "hint": "Highlight unique cultural value and adaptability."},
            {"q": "Describe your ideal working environment and team culture.", "hint": "Self-awareness and alignment with company mission."},
            {"q": "How do you handle rapid technological changes and stay updated?", "hint": "Continuous learning habits and community involvement."}
        ] + [{"q": f"Professional HR Scenario #{i}", "hint": "Reflect on past behavioral experiences."} for i in range(5, 51)],
        "skills_to_brush_up": ["Advanced Algorithms", "System Architecture", "Cloud Infrastructure", "Soft Skills", "DevOps basics"],
        "confidence_score": 65,
        "preparation_time": "5-10 days",
    }


@login_required
def interview_prep_tips(request, application_id=None):
    """Show AI-powered interview preparation tips for a specific job or generic."""
    application = None
    job_title = "Software Engineer"
    skills = ""
    job_desc = ""

    if application_id:
        application = get_object_or_404(
            Application,
            id=application_id,
            candidate__user=request.user
        )
        job_title = application.job.title
        job_desc = application.job.description or ""

    # Get candidate skills
    try:
        profile = request.user.candidate
        skills = profile.skills_extracted or ""
    except Exception:
        skills = ""

    # Generate tips
    tips = _generate_tips(job_title, skills, job_desc)

    context = {
        'application': application,
        'job_title': job_title,
        'tips': tips,
        'quick_tips': tips.get('quick_tips', []),
        'technical_questions': tips.get('technical_questions', []),
        'hr_questions': tips.get('hr_questions', []),
        'skills_to_brush': tips.get('skills_to_brush_up', []),
        'confidence_score': tips.get('confidence_score', 70),
        'prep_time': tips.get('preparation_time', '3-5 days'),
    }
    return render(request, 'jobs/interview_prep.html', context)


@csrf_exempt
@login_required
@require_POST
def regenerate_prep_tips_api(request):
    """AJAX endpoint to regenerate tips with optional custom focus area."""
    try:
        body = json.loads(request.body)
        job_title = body.get('job_title', 'Software Engineer')
        skills = body.get('skills', '')
        focus = body.get('focus', '')
        job_desc = f"Focus on: {focus}" if focus else ''
        tips = _generate_tips(job_title, skills, job_desc)
        return JsonResponse({'ok': True, 'tips': tips})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
