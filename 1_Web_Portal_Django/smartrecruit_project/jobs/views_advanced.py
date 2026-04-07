"""
Advanced Features — All 18 new features
1.  Diversity & Inclusion Dashboard        (Recruiter)
2.  Time-to-Hire Predictor                 (Recruiter)
3.  Smart Interview Question Generator     (Recruiter)
4.  AI Email Drafter                       (Recruiter)
5.  Talent Pool Manager                    (Recruiter)
6.  Department-wise Analytics              (Recruiter)
7.  Reference Check Automation             (Recruiter)
8.  AI Resume Builder                      (Candidate)
9.  Mock Psychometric Test                 (Candidate)
10. Video Pitch Analyser                   (Candidate)
11. Leaderboard / Competitive Standing     (Candidate)
12. Salary Expectation Calibrator          (Candidate)
13. Job Application Tracker / Kanban       (Candidate)
14. Job Market Intelligence                (Platform)
15. AI Onboarding Plan Generator           (Platform)
16. Enhanced Proctoring Dashboard          (Platform)
17. Anonymous Feedback System              (Platform)
18. Knowledge Base / FAQ Bot               (Platform)
"""
import json
import random
from collections import defaultdict, Counter
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Max, Min, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .security import get_authorized_application
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .models import Application, JobPosting, Candidate
try:
    from core.ai_engine import AIEngine
except ImportError:
    AIEngine = None
    import logging
    logger = logging.getLogger(__name__)

def _gemini(prompt: str, fallback: dict | list) -> dict | list:
    """Call Centralized AIEngine and parse JSON; return fallback on any error."""
    if not AIEngine:
        return fallback
    try:
        system_prompt = "You are a professional AI Assistant for the SmartRecruit Enterprise Portal. Follow formatting requests exactly."
        json_response = "valid json" in prompt.lower() or "json array" in prompt.lower()
        
        ai = AIEngine()
        text = ai.generate(system_prompt=system_prompt, user_prompt=prompt, json_response=json_response)
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
                
        return json.loads(text.strip())
    except Exception as e:
        if 'logger' in globals():
            logger.warning(f"[_gemini list/dict parser fallback]: {e}")
        return fallback

def _recruiter_required(request):
    return request.user.is_authenticated and getattr(request.user, 'is_recruiter', False)

def _candidate_required(request):
    return request.user.is_authenticated and not getattr(request.user, 'is_recruiter', False)

REJECT_SET = {'RESUME_REJECTED','ROUND_1_FAILED','ROUND_2_FAILED','ROUND_3_FAILED',
              'OFFER_REJECTED','REJECTED'}
HIRED_SET  = {'HIRED','OFFER_ACCEPTED'}


# ══════════════════════════════════════════════════════════════════════════════
# 1. DIVERSITY & INCLUSION DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def diversity_dashboard(request):
    if not _recruiter_required(request):
        return redirect('dashboard')

    qs = Application.objects.filter(job__recruiter=request.user).select_related('job', 'candidate')
    total = qs.count()

    # Source distribution (proxy for diversity channel)
    source_counts = dict(qs.values_list('source_of_hire').annotate(c=Count('id')))

    # Hired vs rejected by source — proxy for bias across channel
    channel_pass = {}
    for src, label in Application.SOURCE_CHOICES:
        apps  = qs.filter(source_of_hire=src)
        total_src = apps.count()
        hired_src = apps.filter(status__in=HIRED_SET).count()
        if total_src:
            channel_pass[label] = round(hired_src / total_src * 100, 1)

    # AI Score gap analysis (fairness check)
    score_data = qs.filter(ai_score__gt=0).values('source_of_hire').annotate(avg=Avg('ai_score'))
    score_by_source = {r['source_of_hire']: round(r['avg'], 1) for r in score_data}

    # Stage drop-off — are any sources hitting a particular stage?
    screening_pass = {}
    for src, label in Application.SOURCE_CHOICES:
        total_src = qs.filter(source_of_hire=src).count()
        passed    = qs.filter(source_of_hire=src).exclude(status__in=REJECT_SET).count()
        if total_src:
            screening_pass[label] = round(passed / total_src * 100, 1)

    # Monthly diversity trend (unique sources per month)
    months = defaultdict(set)
    for app in qs:
        months[app.applied_at.strftime('%b %Y')].add(app.source_of_hire)
    month_diversity = {m: len(s) for m, s in months.items()}

    # D&I score (heuristic: more sources = more diverse)
    unique_sources_used = len(source_counts)
    di_score = min(100, unique_sources_used * 17)   # 6 sources max → 100

    context = {
        'total': total,
        'di_score': di_score,
        'unique_sources': unique_sources_used,
        'source_counts': source_counts,
        'source_json': json.dumps([{'src': k, 'count': v} for k, v in source_counts.items()]),
        'channel_pass': channel_pass,
        'channel_pass_json': json.dumps(channel_pass),
        'score_by_source': score_by_source,
        'score_by_source_json': json.dumps(score_by_source),
        'screening_pass': screening_pass,
        'month_diversity_json': json.dumps(month_diversity),
        'hired': qs.filter(status__in=HIRED_SET).count(),
    }
    return render(request, 'jobs/diversity_dashboard.html', context)


# ══════════════════════════════════════════════════════════════════════════════
# 2. TIME-TO-HIRE PREDICTOR
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def time_to_hire_predictor(request):
    if not _recruiter_required(request):
        return redirect('dashboard')

    prediction = None
    jobs = JobPosting.objects.filter(recruiter=request.user)

    # Historical averages from actual data
    hired_apps  = Application.objects.filter(job__recruiter=request.user, status__in=HIRED_SET)
    hist_avg    = None
    if hired_apps.exists():
        deltas   = [(a.updated_at - a.applied_at).days for a in hired_apps]
        hist_avg = round(sum(deltas) / len(deltas))

    if request.method == 'POST':
        job_id   = request.POST.get('job_id')
        job_type = request.POST.get('job_type', 'FULL_TIME')
        exp_req  = float(request.POST.get('exp_required', 2))
        skill_count = int(request.POST.get('skill_count', 5))

        # Base estimate (heuristic regression)
        base = 21  # avg days
        if exp_req >= 5:   base += 14
        elif exp_req >= 3: base += 7
        if skill_count >= 8: base += 10
        elif skill_count >= 5: base += 5
        if job_type == 'INTERNSHIP': base -= 7
        elif job_type == 'CONTRACT': base -= 3

        # Adjust by historical average
        if hist_avg:
            base = round((base + hist_avg) / 2)

        # Confidence band
        low  = max(7, base - 7)
        high = base + 14

        # Stage breakdown
        stages = [
            ('Sourcing',           round(base * 0.15)),
            ('Resume Screening',   round(base * 0.20)),
            ('Round 1 (Aptitude)', round(base * 0.15)),
            ('Round 2 (Practical)',round(base * 0.15)),
            ('AI Interview',       round(base * 0.10)),
            ('HR Round',           round(base * 0.15)),
            ('Offer & Decision',   round(base * 0.10)),
        ]

        prediction = {
            'days': base,
            'low': low,
            'high': high,
            'stages': stages,
            'stages_json': json.dumps([{'stage': s, 'days': d} for s, d in stages]),
            'tip': ('Consider streamlining assessment rounds to speed up hiring.'
                    if base > 30 else 'Your predicted pipeline is efficient!'),
        }

    return render(request, 'jobs/time_to_hire.html', {
        'jobs': jobs,
        'prediction': prediction,
        'hist_avg': hist_avg,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 3. SMART INTERVIEW QUESTION GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def smart_question_generator(request):
    if not _recruiter_required(request):
        return redirect('dashboard')

    result = None
    jobs = JobPosting.objects.filter(recruiter=request.user, status='OPEN')

    if request.method == 'POST':
        job_id       = request.POST.get('job_id')
        app_id       = request.POST.get('application_id', '')
        focus        = request.POST.get('focus', 'all')
        difficulty   = request.POST.get('difficulty', 'medium')
        count        = int(request.POST.get('count', 10))

        candidate_name = 'Candidate'
        candidate_skills = ''
        job_title = 'Software Engineer'
        job_desc  = ''

        if job_id:
            try:
                job = JobPosting.objects.get(pk=job_id, recruiter=request.user)
                job_title = job.title
                job_desc  = job.description or ''
            except JobPosting.DoesNotExist:
                pass

        if app_id:
            try:
                app = Application.objects.get(pk=app_id, job__recruiter=request.user)
                candidate_name   = app.candidate.full_name
                candidate_skills = app.candidate.skills_extracted or ''
            except Application.DoesNotExist:
                pass

        prompt = f"""Generate {count} {difficulty}-level interview questions for a {job_title} role.
Focus: {focus} (technical/hr/behavioral/all).
Candidate skills: {candidate_skills[:300]}
Job description excerpt: {job_desc[:400]}

Return ONLY valid JSON array:
[
  {{
    "question": "Explain the GIL in Python...",
    "category": "Technical",
    "difficulty": "Medium",
    "expected_answer_points": ["Point 1", "Point 2"],
    "follow_up": "How would you work around it?"
  }}
]"""

        fallback = [
            {"question": f"Tell me about your experience with the core technologies for {job_title}.",
             "category": "Technical", "difficulty": difficulty.title(),
             "expected_answer_points": ["Depth of knowledge", "Real project examples", "Problem-solving approach"],
             "follow_up": "What was the most complex project you worked on?"},
            {"question": "Describe a situation where you had to learn a new technology quickly.",
             "category": "Behavioral", "difficulty": "Medium",
             "expected_answer_points": ["Learning strategy", "Time to proficiency", "Outcome"],
             "follow_up": "What resources helped you most?"},
            {"question": "How do you handle conflicting priorities?",
             "category": "HR", "difficulty": "Easy",
             "expected_answer_points": ["Prioritisation method", "Communication", "Outcome example"],
             "follow_up": "Give a specific example."},
        ]

        questions = _gemini(prompt, fallback)
        if not isinstance(questions, list):
            questions = fallback

        result = {
            'questions': questions,
            'candidate_name': candidate_name,
            'job_title': job_title,
            'total': len(questions),
        }

    applications = Application.objects.filter(
        job__recruiter=request.user
    ).select_related('candidate', 'job').order_by('-applied_at')[:50]

    return render(request, 'jobs/smart_question_gen.html', {
        'jobs': jobs,
        'applications': applications,
        'result': result,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 4. AI EMAIL DRAFTER
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def ai_email_drafter(request):
    if not _recruiter_required(request):
        return redirect('dashboard')

    result = None
    apps = Application.objects.filter(
        job__recruiter=request.user
    ).select_related('candidate', 'job').order_by('-applied_at')[:100]

    if request.method == 'POST':
        app_id    = request.POST.get('application_id')
        email_type = request.POST.get('email_type', 'shortlist')
        custom_note = request.POST.get('custom_note', '')

        candidate_name = 'Candidate'
        job_title = 'the Role'
        company = 'SmartRecruit AI'
        ai_score = 0

        if app_id:
            try:
                app = Application.objects.get(pk=app_id, job__recruiter=request.user)
                candidate_name = app.candidate.full_name
                job_title      = app.job.title
                ai_score       = round(app.ai_score)
            except Application.DoesNotExist:
                pass

        email_type_labels = {
            'shortlist': 'Shortlisting',
            'rejection': 'Rejection',
            'interview_invite': 'Interview Invitation',
            'offer': 'Job Offer',
            'onboarding': 'Onboarding Welcome',
        }

        prompt = f"""Write a professional {email_type_labels.get(email_type, email_type)} email for:
Candidate: {candidate_name}
Role: {job_title}
Company: SmartRecruit AI
AI Match Score: {ai_score}%
Custom note: {custom_note}

Return ONLY valid JSON:
{{
  "subject": "Email subject line here",
  "body": "Full email body with proper greeting and sign-off...",
  "tone": "Professional & Warm",
  "word_count": 120
}}"""

        fallback = {
            'subject': f"{'We loved your profile' if 'shortlist' in email_type else 'Update on your application'} — {job_title} at SmartRecruit AI",
            'body': f"Dear {candidate_name},\n\nThank you for your interest in the {job_title} position at SmartRecruit AI.\n\n{'We are pleased to inform you that your profile has been shortlisted for the next round.' if email_type == 'shortlist' else 'After careful consideration, we regret to inform you that we will not be moving forward with your application at this time.'}\n\n{'We will reach out shortly with next steps.' if email_type != 'rejection' else 'We encourage you to apply to future openings that match your profile.'}\n\nBest regards,\nHR Team\nSmartRecruit AI",
            'tone': 'Professional',
            'word_count': 80,
        }

        result = _gemini(prompt, fallback)
        if not isinstance(result, dict):
            result = fallback
        result['email_type'] = email_type
        result['candidate_name'] = candidate_name
        result['job_title'] = job_title

    return render(request, 'jobs/ai_email_drafter.html', {
        'applications': apps,
        'result': result,
        'email_types': [
            ('shortlist', 'Shortlist Notification', 'fas fa-thumbs-up', 'success'),
            ('rejection', 'Rejection Email', 'fas fa-times-circle', 'danger'),
            ('interview_invite', 'Interview Invitation', 'fas fa-calendar-check', 'primary'),
            ('offer', 'Job Offer Letter', 'fas fa-trophy', 'warning'),
            ('onboarding', 'Onboarding Welcome', 'fas fa-door-open', 'info'),
        ],
    })


# ══════════════════════════════════════════════════════════════════════════════
# 5. TALENT POOL MANAGER
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def talent_pool(request):
    if not _recruiter_required(request):
        return redirect('dashboard')

    # Rejected but high-scoring candidates = talent pool
    pool = Application.objects.filter(
        job__recruiter=request.user,
        status__in=REJECT_SET,
        ai_score__gte=55,
    ).select_related('candidate', 'job').order_by('-ai_score')

    # Get currently open jobs for matching
    open_jobs = JobPosting.objects.filter(recruiter=request.user, status='OPEN')

    # For each pool candidate, find best matching open jobs
    pool_with_matches = []
    for app in pool[:50]:
        c_skills = set((app.candidate.skills_extracted or '').lower().replace(',', ' ').split())
        matches = []
        for job in open_jobs:
            jd_words = set((job.description or job.required_skills or '').lower().split())
            overlap  = len(c_skills & jd_words)
            if overlap >= 2:
                matches.append({'job': job, 'overlap': overlap})
        matches.sort(key=lambda x: x['overlap'], reverse=True)
        pool_with_matches.append({
            'app': app,
            'matches': matches[:3],
        })

    return render(request, 'jobs/talent_pool.html', {
        'pool': pool_with_matches,
        'total': pool.count(),
        'open_jobs_count': open_jobs.count(),
    })


# ══════════════════════════════════════════════════════════════════════════════
# 6. DEPARTMENT-WISE ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def department_analytics(request):
    if not _recruiter_required(request):
        return redirect('dashboard')

    # Group by technology_stack (acts as department proxy)
    dept_data = (
        Application.objects.filter(job__recruiter=request.user)
        .values('job__technology_stack')
        .annotate(
            total=Count('id'),
            hired=Count('id', filter=Q(status__in=HIRED_SET)),
            rejected=Count('id', filter=Q(status__in=REJECT_SET)),
            avg_score=Avg('ai_score'),
        )
        .order_by('-total')
    )

    # Job-level breakdown
    job_data = (
        JobPosting.objects.filter(recruiter=request.user)
        .annotate(
            app_count=Count('applications'),
            hired_count=Count('applications', filter=Q(applications__status__in=HIRED_SET)),
            avg_ai=Avg('applications__ai_score'),
        )
        .order_by('-app_count')[:15]
    )

    dept_list = list(dept_data)
    for d in dept_list:
        t = d['total'] or 1
        d['hire_rate'] = round(d['hired'] / t * 100, 1)
        d['avg_score'] = round(d['avg_score'] or 0, 1)
        d['dept_label'] = d['job__technology_stack'] or 'General'

    context = {
        'dept_data': dept_list,
        'dept_labels_json': json.dumps([d['dept_label'] for d in dept_list]),
        'dept_totals_json': json.dumps([d['total'] for d in dept_list]),
        'dept_hired_json': json.dumps([d['hired'] for d in dept_list]),
        'dept_scores_json': json.dumps([d['avg_score'] for d in dept_list]),
        'job_data': job_data,
        'total_apps': Application.objects.filter(job__recruiter=request.user).count(),
        'total_jobs': JobPosting.objects.filter(recruiter=request.user).count(),
    }
    return render(request, 'jobs/department_analytics.html', context)


# ══════════════════════════════════════════════════════════════════════════════
# 7. REFERENCE CHECK AUTOMATION
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def reference_check(request, application_id):
    if not _recruiter_required(request):
        return redirect('dashboard')

    application = get_object_or_404(Application, pk=application_id, job__recruiter=request.user)
    candidate   = application.candidate
    job_title   = application.job.title

    questions = _gemini(
        f"""Generate 10 professional reference check questions for a {job_title} candidate named {candidate.full_name}.
Skills: {candidate.skills_extracted[:200]}
Return ONLY valid JSON array of objects:
[{{"question": "...", "category": "Performance|Teamwork|Leadership|Technical|Character", "red_flag_if": "..."}}]""",
        [
            {"question": f"How long did {candidate.full_name} work with you and in what capacity?",
             "category": "Background", "red_flag_if": "Evasive or contradicts resume"},
            {"question": "How would you rate their technical skills on a scale of 1-10?",
             "category": "Technical", "red_flag_if": "Below 6 or hesitation"},
            {"question": "Would you rehire this person?",
             "category": "Character", "red_flag_if": "Hesitation or 'no'"},
            {"question": "How did they handle pressure and deadlines?",
             "category": "Performance", "red_flag_if": "Mentions missed deadlines without explanation"},
            {"question": "How did they work within the team?",
             "category": "Teamwork", "red_flag_if": "Mentions conflicts or isolation"},
        ]
    )
    if not isinstance(questions, list): questions = []

    return render(request, 'jobs/reference_check.html', {
        'application': application,
        'candidate':   candidate,
        'job_title':   job_title,
        'questions':   questions,
        'questions_json': json.dumps(questions),
    })


# ══════════════════════════════════════════════════════════════════════════════
# 8. AI RESUME BUILDER
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def ai_resume_builder(request):
    if _recruiter_required(request):
        return redirect('dashboard')

    result = None
    if request.method == 'POST':
        name       = request.POST.get('full_name', '')
        email      = request.POST.get('email', '')
        phone      = request.POST.get('phone', '')
        role       = request.POST.get('target_role', '')
        experience = request.POST.get('experience', '')
        skills     = request.POST.get('skills', '')
        education  = request.POST.get('education', '')
        projects   = request.POST.get('projects', '')

        prompt = f"""Create a professional ATS-optimised resume for:
Name: {name}
Target Role: {role}
Experience: {experience}
Skills: {skills}
Education: {education}
Projects: {projects}

Return ONLY valid JSON:
{{
  "professional_summary": "3-sentence compelling summary...",
  "experience_bullets": ["• Led team of 5 engineers...", "• Built ML pipeline..."],
  "skills_formatted": ["Python", "Machine Learning", "SQL"],
  "projects_formatted": [{{"title": "Proj", "description": "...impact..."}}],
  "education_formatted": "B.Tech CS, XYZ University, 2023",
  "ats_keywords": ["python", "machine learning", "data analysis"],
  "tips": ["Add quantified achievements", "Include more action verbs"]
}}"""

        fallback = {
            'professional_summary': f"Results-driven {role} with hands-on experience in {skills[:60]}. Proven ability to deliver impactful solutions and collaborate effectively. Passionate about continuous learning and innovation.",
            'experience_bullets': [
                f"• Developed and maintained software solutions using {skills[:30]}",
                "• Collaborated with cross-functional teams to deliver projects on time",
                "• Implemented best practices improving code quality and performance by 20%",
            ],
            'skills_formatted': [s.strip() for s in skills.split(',')][:10],
            'projects_formatted': [{'title': p.strip(), 'description': 'Developed and deployed a complete solution.'} for p in projects.split('\n') if p.strip()][:3],
            'education_formatted': education,
            'ats_keywords': [s.strip().lower() for s in skills.split(',')][:8],
            'tips': ['Add quantified achievements', 'Use strong action verbs', 'Keep to 1-2 pages', 'Tailor for each application'],
        }

        result = _gemini(prompt, fallback)
        if not isinstance(result, dict):
            result = fallback
        result.update({'name': name, 'email': email, 'phone': phone,
                       'target_role': role, 'education': education})

    return render(request, 'jobs/ai_resume_builder.html', {'result': result})


# ══════════════════════════════════════════════════════════════════════════════
# 9. MOCK PSYCHOMETRIC TEST
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def psychometric_test(request):
    if _recruiter_required(request):
        return redirect('dashboard')

    # Static psychometric question bank (5 dimensions × 5 questions)
    QUESTIONS = [
        # Openness
        {'id': 1, 'text': 'I enjoy trying new and unfamiliar experiences.',         'trait': 'Openness'},
        {'id': 2, 'text': 'I am curious about many different things.',              'trait': 'Openness'},
        {'id': 3, 'text': 'I have a vivid imagination.',                            'trait': 'Openness'},
        {'id': 4, 'text': 'I enjoy abstract thinking and complex ideas.',           'trait': 'Openness'},
        {'id': 5, 'text': 'I appreciate art, music, or literature.',                'trait': 'Openness'},
        # Conscientiousness
        {'id': 6,  'text': 'I am always prepared and organised.',                  'trait': 'Conscientiousness'},
        {'id': 7,  'text': 'I pay attention to details.',                           'trait': 'Conscientiousness'},
        {'id': 8,  'text': 'I follow a schedule and stick to it.',                 'trait': 'Conscientiousness'},
        {'id': 9,  'text': 'I do not leave tasks incomplete.',                      'trait': 'Conscientiousness'},
        {'id': 10, 'text': 'I get chores done right away.',                         'trait': 'Conscientiousness'},
        # Extraversion
        {'id': 11, 'text': 'I feel comfortable in large groups of people.',        'trait': 'Extraversion'},
        {'id': 12, 'text': 'I start conversations easily.',                         'trait': 'Extraversion'},
        {'id': 13, 'text': 'I am the life of the party.',                           'trait': 'Extraversion'},
        {'id': 14, 'text': 'I feel energised after spending time with people.',    'trait': 'Extraversion'},
        {'id': 15, 'text': 'I like to be the center of attention sometimes.',      'trait': 'Extraversion'},
        # Agreeableness
        {'id': 16, 'text': 'I sympathise with others\' feelings.',                 'trait': 'Agreeableness'},
        {'id': 17, 'text': 'I take time out for others.',                          'trait': 'Agreeableness'},
        {'id': 18, 'text': 'I feel others\' emotions.',                             'trait': 'Agreeableness'},
        {'id': 19, 'text': 'I make people feel at ease.',                          'trait': 'Agreeableness'},
        {'id': 20, 'text': 'I am interested in people.',                           'trait': 'Agreeableness'},
        # Neuroticism (low = stable)
        {'id': 21, 'text': 'I get stressed out easily.',                           'trait': 'Emotional Stability'},
        {'id': 22, 'text': 'I worry about things.',                                'trait': 'Emotional Stability'},
        {'id': 23, 'text': 'I get irritated easily.',                              'trait': 'Emotional Stability'},
        {'id': 24, 'text': 'I often feel blue or down.',                           'trait': 'Emotional Stability'},
        {'id': 25, 'text': 'I have frequent mood swings.',                         'trait': 'Emotional Stability'},
    ]

    result = None
    if request.method == 'POST':
        scores = defaultdict(int)
        counts = defaultdict(int)
        for q in QUESTIONS:
            val = int(request.POST.get(f'q{q["id"]}', 3))
            trait = q['trait']
            # Neuroticism is reverse-scored for stability
            if trait == 'Emotional Stability':
                val = 6 - val
            scores[trait] += val
            counts[trait]  += 1

        trait_scores = {t: round((scores[t] / (counts[t] * 5)) * 100) for t in scores}

        # MBTI-proxy
        mbti = ''
        mbti += 'E' if trait_scores.get('Extraversion', 50) >= 50 else 'I'
        mbti += 'N' if trait_scores.get('Openness', 50) >= 50 else 'S'
        mbti += 'F' if trait_scores.get('Agreeableness', 50) >= 50 else 'T'
        mbti += 'J' if trait_scores.get('Conscientiousness', 50) >= 50 else 'P'

        MBTI_DESC = {
            'ENTJ': 'Commander — Natural leader, strategic, decisive.',
            'INTJ': 'Architect — Analytical, creative, independent.',
            'ENTP': 'Debater — Innovative, enthusiastic, loves challenges.',
            'INTP': 'Logician — Analytical, objective, loves theory.',
            'ENFJ': 'Protagonist — Charismatic, inspiring, empathetic.',
            'INFJ': 'Advocate — Insightful, principled, determined.',
            'ENFP': 'Campaigner — Enthusiastic, creative, sociable.',
            'INFP': 'Mediator — Idealistic, empathetic, creative.',
            'ESTJ': 'Executive — Organised, loyal, direct.',
            'ISTJ': 'Logistician — Responsible, thorough, dependable.',
            'ESFJ': 'Consul — Caring, social, traditional.',
            'ISFJ': 'Defender — Warm, dedicated, dutiful.',
            'ESTP': 'Entrepreneur — Bold, practical, action-oriented.',
            'ISTP': 'Virtuoso — Practical, observant, hands-on.',
            'ESFP': 'Entertainer — Spontaneous, energetic, fun.',
            'ISFP': 'Adventurer — Flexible, charming, artistic.',
        }
        mbti_desc = MBTI_DESC.get(mbti, 'Unique personality blend.')

        result = {
            'trait_scores': trait_scores,
            'trait_scores_json': json.dumps(trait_scores),
            'mbti': mbti,
            'mbti_desc': mbti_desc,
            'top_trait': max(trait_scores, key=trait_scores.get),
            'strengths': _get_trait_strengths(trait_scores),
        }

    return render(request, 'jobs/psychometric_test.html', {
        'questions': QUESTIONS,
        'result': result,
        'trait_count': 25,
        'psych_range': range(1, 6),
    })

def _get_trait_strengths(scores):
    strengths = []
    if scores.get('Openness', 0) >= 60:       strengths.append('Creative & innovative thinker')
    if scores.get('Conscientiousness', 0) >= 60: strengths.append('Highly organised & reliable')
    if scores.get('Extraversion', 0) >= 60:   strengths.append('Strong communicator & team player')
    if scores.get('Agreeableness', 0) >= 60:  strengths.append('Collaborative & empathetic')
    if scores.get('Emotional Stability', 0) >= 60: strengths.append('Resilient under pressure')
    return strengths or ['Balanced personality with multiple strong traits']


# ══════════════════════════════════════════════════════════════════════════════
# 10. VIDEO PITCH ANALYSER
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def video_pitch_analyser(request):
    if _recruiter_required(request):
        return redirect('dashboard')
    # Renders the recording UI — transcription and analysis happen via AJAX
    return render(request, 'jobs/video_pitch.html', {})


@login_required
@require_POST
def analyse_pitch_api(request):
    """Receives transcript text via AJAX, returns AI analysis."""
    try:
        body = json.loads(request.body)
        transcript = body.get('transcript', '').strip()
        duration   = body.get('duration', 60)
    except Exception:
        return JsonResponse({'ok': False}, status=400)

    if not transcript:
        return JsonResponse({'ok': False, 'error': 'No transcript'})

    prompt = f"""Analyse this {duration}-second video pitch transcript for a job application.
Transcript: "{transcript}"

Return ONLY valid JSON:
{{
  "confidence_score": 72,
  "clarity_score": 68,
  "fluency_score": 75,
  "keyword_richness": 65,
  "overall_score": 70,
  "words_per_minute": 130,
  "filler_words_detected": ["um", "like"],
  "key_strengths": ["Clear articulation of skills", "Good eye contact mentioned"],
  "improvements": ["Reduce filler words", "Add specific examples"],
  "tone": "Professional & Confident",
  "verdict": "Strong Pitch"
}}
verdict: Outstanding / Strong Pitch / Good Start / Needs Practice"""

    fallback = {
        'confidence_score': 65,
        'clarity_score': 70,
        'fluency_score': 68,
        'keyword_richness': 60,
        'overall_score': 66,
        'words_per_minute': round(len(transcript.split()) / max(duration / 60, 1)),
        'filler_words_detected': [w for w in ['um', 'uh', 'like', 'you know'] if w in transcript.lower()],
        'key_strengths': ['Completed the pitch within time', 'Covered relevant experience'],
        'improvements': ['Add specific quantified achievements', 'Slow down for clarity'],
        'tone': 'Neutral',
        'verdict': 'Good Start',
    }

    result = _gemini(prompt, fallback)
    if not isinstance(result, dict):
        result = fallback
    return JsonResponse({'ok': True, 'result': result})


# ══════════════════════════════════════════════════════════════════════════════
# 11. LEADERBOARD / COMPETITIVE STANDING
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def competitive_standing(request, application_id):
    application = get_authorized_application(request, application_id)

    # Access check
    if not _recruiter_required(request):
        if application.candidate.user != request.user:
            return redirect('candidate_applications')

    # All applicants for the same job
    all_apps = Application.objects.filter(
        job=application.job, ai_score__gt=0
    ).order_by('-ai_score')

    total = all_apps.count()
    scores = list(all_apps.values_list('ai_score', flat=True))

    candidate_score = application.ai_score
    rank = sum(1 for s in scores if s > candidate_score) + 1
    percentile = round((1 - rank / max(total, 1)) * 100, 1)

    score_dist = {'0-25': 0, '26-50': 0, '51-75': 0, '76-100': 0}
    for s in scores:
        if s <= 25:   score_dist['0-25'] += 1
        elif s <= 50: score_dist['26-50'] += 1
        elif s <= 75: score_dist['51-75'] += 1
        else:         score_dist['76-100'] += 1

    top_10 = list(all_apps[:10].values('candidate__full_name', 'ai_score', 'status'))

    return render(request, 'jobs/competitive_standing.html', {
        'application': application,
        'rank': rank,
        'total': total,
        'percentile': percentile,
        'candidate_score': round(candidate_score),
        'avg_score': round(sum(scores) / len(scores)) if scores else 0,
        'top_score': round(max(scores)) if scores else 0,
        'score_dist_json': json.dumps(score_dist),
        'top_10': top_10,
        'is_top_25': percentile >= 75,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 12. SALARY EXPECTATION CALIBRATOR
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def salary_calibrator(request):
    if _recruiter_required(request):
        return redirect('dashboard')

    result = None
    if request.method == 'POST':
        role       = request.POST.get('role', 'Software Engineer')
        exp        = float(request.POST.get('experience', 2))
        skills_raw = request.POST.get('skills', '')
        location   = request.POST.get('location', 'India')
        job_type   = request.POST.get('job_type', 'FULL_TIME')

        # Heuristic salary model (INR/year in Lakhs)
        base = 4.0  # fresher base
        base += exp * 1.2
        skill_list = [s.strip().lower() for s in skills_raw.split(',') if s.strip()]
        premium_skills = {'machine learning', 'deep learning', 'ai', 'cloud', 'aws', 'devops',
                          'react', 'node', 'flutter', 'data science', 'blockchain', 'llm', 'mlops'}
        premium_count = len(set(skill_list) & premium_skills)
        base += premium_count * 0.8

        if location.lower() in ['bangalore', 'mumbai', 'delhi', 'pune', 'hyderabad']:
            base *= 1.25
        if job_type == 'INTERNSHIP':
            base = base * 0.15  # monthly stipend logic

        low  = round(base * 0.85, 1)
        high = round(base * 1.20, 1)
        mid  = round(base, 1)

        prompt = f"""Give salary market data for a {role} with {exp} years experience in {location}, India. Skills: {skills_raw[:200]}.
Return ONLY valid JSON:
{{
  "market_low": 6.0, "market_mid": 9.5, "market_high": 14.0,
  "demand_level": "High",
  "top_paying_companies": ["Company A", "Company B", "Company C"],
  "negotiation_tips": ["Tip 1", "Tip 2"],
  "market_insight": "One sentence insight about this role's market."
}}
All values in Indian LPA (Lakhs Per Annum). demand_level: Low/Moderate/High/Very High"""

        market = _gemini(prompt, {
            'market_low': low, 'market_mid': mid, 'market_high': high,
            'demand_level': 'Moderate',
            'top_paying_companies': ['Product companies', 'MNCs', 'Startups'],
            'negotiation_tips': ['Research company salary bands', 'Highlight premium skills', 'Consider total compensation'],
            'market_insight': f'Demand for {role} professionals is growing steadily in {location}.',
        })

        result = {
            'role': role, 'experience': exp, 'skills': skill_list,
            'location': location, 'job_type': job_type,
            'our_low': low, 'our_mid': mid, 'our_high': high,
            **market,
        }

    return render(request, 'jobs/salary_calibrator.html', {'result': result})


# ══════════════════════════════════════════════════════════════════════════════
# 13. JOB APPLICATION TRACKER (Candidate Kanban)
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def application_tracker(request):
    if _recruiter_required(request):
        return redirect('dashboard')

    apps = Application.objects.filter(
        candidate__user=request.user
    ).select_related('job', 'job__recruiter').order_by('-applied_at')

    # Group into kanban columns
    COLUMNS = [
        ('applied',    'Applied',         'applied',     '#2979FF', 'fas fa-paper-plane',
         ['APPLIED']),
        ('screening',  'In Screening',    'screening',   '#7C4DFF', 'fas fa-search',
         ['RESUME_SCREENING', 'RESUME_SELECTED']),
        ('assessment', 'Assessment',      'assessment',  '#FF6D00', 'fas fa-tasks',
         ['ROUND_1_PENDING','ROUND_1_PASSED','ROUND_2_PENDING','ROUND_2_PASSED']),
        ('interview',  'Interview',       'interview',   '#00B0FF', 'fas fa-comments',
         ['ROUND_3_PENDING','ROUND_3_PASSED','HR_ROUND_PENDING']),
        ('offer',      'Offer Stage',     'offer',       '#00C853', 'fas fa-trophy',
         ['OFFER_GENERATED','OFFER_ACCEPTED','HIRED']),
        ('rejected',   'Not Selected',    'rejected',    '#FF4444', 'fas fa-times-circle',
         REJECT_SET),
    ]

    columns = []
    for key, label, col_class, color, icon, statuses in COLUMNS:
        col_apps = apps.filter(status__in=statuses)
        columns.append({
            'key': key, 'label': label, 'color': color, 'icon': icon,
            'apps': col_apps,
            'count': col_apps.count(),
        })

    return render(request, 'jobs/application_tracker.html', {
        'columns': columns,
        'total': apps.count(),
    })


# ══════════════════════════════════════════════════════════════════════════════
# 14. JOB MARKET INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def job_market_intelligence(request):
    role    = request.GET.get('role', 'Data Scientist')
    location = request.GET.get('location', 'India')

    prompt = f"""Provide job market intelligence for {role} in {location} as of 2025.
Return ONLY valid JSON:
{{
  "demand_score": 82,
  "demand_trend": "Rising",
  "avg_salary_lpa": 12.5,
  "salary_range": "8–22 LPA",
  "top_skills_in_demand": ["Python", "Machine Learning", "SQL", "TensorFlow"],
  "emerging_skills": ["LLM Fine-tuning", "MLOps", "Vector Databases"],
  "top_hiring_companies": ["Google", "Amazon", "Flipkart", "Infosys"],
  "growth_rate_percent": 28,
  "job_openings_estimate": "15,000+",
  "competition_level": "High",
  "remote_percentage": 45,
  "insights": [
    "AI/ML roles are growing 28% YoY in India.",
    "Product companies pay 40% more than service companies.",
    "Cloud expertise adds ₹2–4 LPA premium."
  ]
}}"""

    fallback = {
        'demand_score': 75,
        'demand_trend': 'Rising',
        'avg_salary_lpa': 10.0,
        'salary_range': '6–18 LPA',
        'top_skills_in_demand': ['Python', 'Machine Learning', 'SQL', 'Data Analysis'],
        'emerging_skills': ['Generative AI', 'MLOps', 'Cloud Computing'],
        'top_hiring_companies': ['TCS', 'Infosys', 'Wipro', 'Amazon', 'Google'],
        'growth_rate_percent': 22,
        'job_openings_estimate': '10,000+',
        'competition_level': 'Moderate',
        'remote_percentage': 40,
        'insights': [
            f'{role} demand is growing rapidly across India.',
            'Upskilling in cloud and AI unlocks premium salaries.',
            'Tier-1 cities pay 25% more than tier-2 cities.',
        ],
    }

    data = _gemini(prompt, fallback)
    if not isinstance(data, dict):
        data = fallback

    popular_roles = [
        'Data Scientist', 'ML Engineer', 'Software Engineer',
        'DevOps Engineer', 'Full Stack Developer', 'AI Engineer',
        'Data Analyst', 'Cloud Architect',
    ]

    return render(request, 'jobs/job_market_intelligence.html', {
        'data': data,
        'role': role,
        'location': location,
        'popular_roles': popular_roles,
        'skills_json': json.dumps(data.get('top_skills_in_demand', [])),
    })


# ══════════════════════════════════════════════════════════════════════════════
# 15. AI ONBOARDING PLAN GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def onboarding_plan(request, application_id):
    application = get_authorized_application(request, application_id)
    if not (_recruiter_required(request) and application.job.recruiter == request.user):
        return redirect('dashboard')

    candidate = application.candidate
    job_title = application.job.title
    skills    = candidate.skills_extracted or ''

    prompt = f"""Create a 90-day onboarding plan for a new {job_title} hire named {candidate.full_name}.
Their skills: {skills[:300]}
Return ONLY valid JSON:
{{
  "day_30": {{
    "theme": "Foundation & Orientation",
    "goals": ["Goal 1", "Goal 2", "Goal 3"],
    "activities": ["Activity 1", "Activity 2"],
    "success_metrics": ["Metric 1", "Metric 2"]
  }},
  "day_60": {{
    "theme": "Integration & Contribution",
    "goals": ["Goal 1", "Goal 2"],
    "activities": ["Activity 1", "Activity 2"],
    "success_metrics": ["Metric 1", "Metric 2"]
  }},
  "day_90": {{
    "theme": "Independence & Impact",
    "goals": ["Goal 1", "Goal 2"],
    "activities": ["Activity 1", "Activity 2"],
    "success_metrics": ["Metric 1", "Metric 2"]
  }},
  "tools_to_learn": ["Tool 1", "Tool 2"],
  "buddy_program": true,
  "key_stakeholders": ["Manager", "Team Lead", "HR"]
}}"""

    fallback = {
        'day_30': {
            'theme': 'Foundation & Orientation',
            'goals': ['Understand company culture and processes', 'Complete all HR and tool onboarding', 'Meet the entire team'],
            'activities': ['1:1 with manager', 'Team introduction sessions', 'Tool and access setup'],
            'success_metrics': ['All tools configured', 'Team introductions done'],
        },
        'day_60': {
            'theme': 'Integration & First Contribution',
            'goals': [f'Deliver first {job_title} task independently', 'Understand codebase/project structure'],
            'activities': ['Shadow senior team members', 'Complete first assigned project'],
            'success_metrics': ['First PR/deliverable merged', 'Code review participation'],
        },
        'day_90': {
            'theme': 'Independence & Growing Impact',
            'goals': ['Lead a small initiative', 'Provide feedback on processes'],
            'activities': ['Present work to team', 'Participate in sprint planning'],
            'success_metrics': ['Positive peer feedback', 'Independent task execution'],
        },
        'tools_to_learn': ['Jira', 'Confluence', 'Slack', 'GitHub', 'VS Code'],
        'buddy_program': True,
        'key_stakeholders': ['Direct Manager', 'Team Lead', 'HR Partner'],
    }

    plan = _gemini(prompt, fallback)
    if not isinstance(plan, dict):
        plan = fallback

    return render(request, 'jobs/onboarding_plan.html', {
        'application': application,
        'candidate':   candidate,
        'job_title':   job_title,
        'plan':        plan,
        'onboarding_phases': [
            {'key': 'day_30', 'label': 'Day 1-30', 'emoji': '🚀', 'color': '#2979FF', 'data': plan.get('day_30', {})},
            {'key': 'day_60', 'label': 'Day 31-60', 'emoji': '⚡', 'color': '#FF6D00', 'data': plan.get('day_60', {})},
            {'key': 'day_90', 'label': 'Day 61-90', 'emoji': '🏆', 'color': '#00C853', 'data': plan.get('day_90', {})},
        ],
    })


# ══════════════════════════════════════════════════════════════════════════════
# 16. ENHANCED PROCTORING DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def proctoring_dashboard(request):
    if not _recruiter_required(request):
        return redirect('dashboard')

    from .models import ProctoringLog

    job_id = request.GET.get('job_id')
    jobs   = JobPosting.objects.filter(recruiter=request.user)

    qs = ProctoringLog.objects.filter(application__job__recruiter=request.user)
    if job_id:
        qs = qs.filter(application__job_id=job_id)

    # Log type counts (SCREENSHOT / VIOLATION / SUSPICION)
    type_counts = dict(qs.values_list('log_type').annotate(c=Count('id')))
    total_logs  = qs.count()
    flagged_apps = qs.values('application').distinct().count()

    # Violations specifically
    violations = qs.filter(log_type__in=['VIOLATION', 'SUSPICION'])
    total_violations = violations.count()

    # Per-application summary
    app_logs = (
        qs.values('application', 'application__candidate__full_name', 'application__job__title')
          .annotate(cnt=Count('id'))
          .order_by('-cnt')[:20]
    )

    # Recent logs
    recent_logs = qs.select_related(
        'application', 'application__candidate', 'application__job'
    ).order_by('-timestamp')[:30]

    context = {
        'jobs': jobs,
        'selected_job': job_id,
        'total_logs': total_logs,
        'total_violations': total_violations,
        'flagged_apps': flagged_apps,
        'type_counts': type_counts,
        'type_json': json.dumps(type_counts),
        'app_logs': list(app_logs),
        'recent_logs': recent_logs,
    }
    return render(request, 'jobs/proctoring_dashboard.html', context)


# ══════════════════════════════════════════════════════════════════════════════
# 17. ANONYMOUS FEEDBACK SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
@login_required
def submit_feedback(request, application_id):
    application = get_object_or_404(Application, pk=application_id, candidate__user=request.user)
    submitted   = False

    if request.method == 'POST' and application.status in REJECT_SET | HIRED_SET:
        rating     = int(request.POST.get('rating', 3))
        feedback   = request.POST.get('feedback', '').strip()
        category   = request.POST.get('category', 'General')

        # Store in ai_insights as feedback blob (no new migration needed)
        try:
            existing = json.loads(application.ai_insights or '{}')
        except Exception:
            existing = {}
        existing['feedback'] = {
            'rating': rating,
            'text': feedback,
            'category': category,
            'submitted_at': timezone.now().isoformat(),
        }
        application.ai_insights = json.dumps(existing)
        application.save(update_fields=['ai_insights'])
        submitted = True

    return render(request, 'jobs/feedback.html', {
        'application': application,
        'submitted': submitted,
    })


@login_required
def feedback_analytics(request):
    """Recruiter view — aggregated anonymous feedback."""
    if not _recruiter_required(request):
        return redirect('dashboard')

    apps = Application.objects.filter(
        job__recruiter=request.user,
        status__in=REJECT_SET | HIRED_SET,
    )

    feedbacks = []
    ratings   = []
    for app in apps:
        try:
            insights = json.loads(app.ai_insights or '{}')
            fb = insights.get('feedback')
            if fb:
                feedbacks.append(fb)
                ratings.append(fb.get('rating', 3))
        except Exception:
            pass

    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
    rating_dist = Counter(ratings)

    return render(request, 'jobs/feedback_analytics.html', {
        'total_feedback': len(feedbacks),
        'avg_rating': avg_rating,
        'rating_dist_json': json.dumps({str(k): v for k, v in rating_dist.items()}),
        'feedbacks': feedbacks[:20],
    })


# ══════════════════════════════════════════════════════════════════════════════
# 18. KNOWLEDGE BASE / FAQ BOT
# ══════════════════════════════════════════════════════════════════════════════
@login_required
@require_POST
def faq_bot_api(request):
    """AI-powered FAQ bot — answers questions about SmartRecruit platform."""
    try:
        body = json.loads(request.body)
        question = body.get('question', '').strip()
    except Exception:
        return JsonResponse({'ok': False}, status=400)

    if not question:
        return JsonResponse({'ok': False, 'error': 'Empty question'})

    context_info = """
SmartRecruit is an AI-powered ATS (Applicant Tracking System) by IR Info Tech Pvt Ltd.
Features: Job Posting, AI Resume Screening, Skill Gap Analysis, Coding Arena (Practice),
Predictive Hiring Score, Blind Hiring, Interview Sentiment Analysis, AI Interview Prep,
Cover Letter Scorer, ATS Resume Checker, Job Recommendations, Upskilling Roadmap,
Candidate Analytics, Hiring Funnel, D&I Dashboard, Proctoring, Psychometric Tests,
Video Pitch Analyser, Salary Calibrator, AI Email Drafter, Onboarding Plan Generator.
Roles: Recruiter (posts jobs, manages pipeline), Candidate (applies, practices, tracks).
AI: Uses Google Gemini API for all generative features.
"""

    prompt = f"""You are SmartRecruit's helpful AI assistant. Answer this question clearly and concisely.

Platform context:
{context_info}

User question: {question}

Return ONLY valid JSON:
{{"answer": "Clear helpful answer in 2-3 sentences.", "related_features": ["feature1", "feature2"], "action_url": "/jobs/arena/"}}
action_url should be a relevant page path on the platform."""

    fallback = {
        'answer': 'SmartRecruit offers comprehensive AI-powered recruitment tools. Please explore the sidebar to discover features like Interview Prep, Coding Arena, ATS Checker, and more.',
        'related_features': ['Interview Prep', 'ATS Resume Checker', 'Job Recommendations'],
        'action_url': '/jobs/',
    }
    result = _gemini(prompt, fallback)
    if not isinstance(result, dict):
        result = fallback
    return JsonResponse({'ok': True, **result})
