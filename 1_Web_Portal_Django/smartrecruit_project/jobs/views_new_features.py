"""
Feature A: Hiring Funnel Analytics Dashboard
Feature B: AI Cover Letter Scorer
Feature C: Offer Acceptance Predictor
Feature D: Early Churn / Retention Risk Score
Feature E: AI JD Enhancer
Feature F: Score Trend Chart data API
Feature G: Resume ATS Live Checker (candidate-side)
Feature H: Job Recommendation Engine
Feature I: Upskilling Roadmap
Feature J: Application Analytics for Candidate
"""

import json
import math
from collections import defaultdict, Counter
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .security import get_authorized_application
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Application, JobPosting, Candidate

try:
    from google import genai
    from django.conf import settings
    _genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception:
    _genai_client = None


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE A — Hiring Funnel Analytics Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

# Ordered funnel stages with labels and grouping
FUNNEL_STAGES = [
    ('applied',    'Applied',       ['APPLIED']),
    ('screening',  'Screening',     ['RESUME_SCREENING', 'RESUME_SELECTED', 'RESUME_REJECTED']),
    ('round1',     'Round 1',       ['ROUND_1_PENDING', 'ROUND_1_PASSED', 'ROUND_1_FAILED']),
    ('round2',     'Round 2',       ['ROUND_2_PENDING', 'ROUND_2_PASSED', 'ROUND_2_FAILED']),
    ('round3',     'AI Interview',  ['ROUND_3_PENDING', 'ROUND_3_PASSED', 'ROUND_3_FAILED']),
    ('hr',         'HR Round',      ['HR_ROUND_PENDING', 'OFFER_GENERATED', 'OFFER_ACCEPTED', 'OFFER_REJECTED']),
    ('hired',      'Hired',         ['HIRED']),
]

PASS_STATUSES  = {'RESUME_SELECTED', 'ROUND_1_PASSED', 'ROUND_2_PASSED', 'ROUND_3_PASSED',
                  'OFFER_ACCEPTED', 'HIRED', 'OFFER_GENERATED', 'HR_ROUND_PENDING', 'ROUND_1_PENDING',
                  'ROUND_2_PENDING', 'ROUND_3_PENDING', 'RESUME_SCREENING'}
REJECT_STATUSES = {'RESUME_REJECTED', 'ROUND_1_FAILED', 'ROUND_2_FAILED', 'ROUND_3_FAILED',
                   'OFFER_REJECTED', 'REJECTED'}


@login_required
def hiring_funnel_dashboard(request):
    """Feature A – Hiring Funnel Dashboard (Recruiter only)."""
    if not request.user.is_recruiter:
        from django.shortcuts import redirect
        return redirect('dashboard')

    # Job filter
    job_id = request.GET.get('job_id')
    jobs = JobPosting.objects.filter(recruiter=request.user).order_by('-created_at')
    qs = Application.objects.filter(job__recruiter=request.user)
    if job_id:
        qs = qs.filter(job_id=job_id)

    # ── Funnel counts ──────────────────────────────────────────────────────────
    status_counts = dict(qs.values_list('status').annotate(cnt=Count('id')))
    funnel_data = []
    for key, label, statuses in FUNNEL_STAGES:
        cnt = sum(status_counts.get(s, 0) for s in statuses)
        funnel_data.append({'key': key, 'label': label, 'count': cnt})

    # Conversion rates between consecutive stages
    for i in range(1, len(funnel_data)):
        prev = funnel_data[i - 1]['count']
        curr = funnel_data[i]['count']
        funnel_data[i]['conversion'] = round((curr / prev * 100), 1) if prev else 0
    funnel_data[0]['conversion'] = 100

    # ── Time-in-stage (avg days between status transitions) ───────────────────
    total = qs.count()
    hired  = qs.filter(status='HIRED').count()
    rejected = qs.filter(status__in=REJECT_STATUSES).count()
    active   = total - hired - rejected

    # Avg time to hire (days)
    hired_apps = qs.filter(status='HIRED')
    avg_days = None
    if hired_apps.exists():
        delta_sum = sum((a.updated_at - a.applied_at).days for a in hired_apps)
        avg_days = round(delta_sum / hired_apps.count(), 1)

    # ── Source of hire breakdown ───────────────────────────────────────────────
    source_data = list(qs.values('source_of_hire').annotate(cnt=Count('id')).order_by('-cnt'))

    # ── Weekly application trend (last 8 weeks) ────────────────────────────────
    from django.utils.timezone import now
    eight_weeks_ago = now() - timedelta(weeks=8)
    weekly_apps = (
        qs.filter(applied_at__gte=eight_weeks_ago)
          .extra(select={'week': "strftime('%%W', applied_at)"})
          .values('week')
          .annotate(cnt=Count('id'))
          .order_by('week')
    )
    trend_labels = [r['week'] for r in weekly_apps]
    trend_values = [r['cnt'] for r in weekly_apps]

    # ── Bottleneck: stage with highest drop-off ────────────────────────────────
    bottleneck = None
    min_conv = 100
    for d in funnel_data[1:]:
        if d['conversion'] < min_conv:
            min_conv = d['conversion']
            bottleneck = d['label']

    # ── AI Score distribution buckets ─────────────────────────────────────────
    buckets = {'0-25': 0, '26-50': 0, '51-75': 0, '76-100': 0}
    for app in qs.values_list('ai_score', flat=True):
        if app <= 25:   buckets['0-25'] += 1
        elif app <= 50: buckets['26-50'] += 1
        elif app <= 75: buckets['51-75'] += 1
        else:           buckets['76-100'] += 1

    context = {
        'jobs': jobs,
        'selected_job_id': int(job_id) if job_id else None,
        'funnel_data': funnel_data,
        'funnel_json': json.dumps([{'label': d['label'], 'count': d['count'], 'conversion': d['conversion']}
                                   for d in funnel_data]),
        'total': total,
        'hired': hired,
        'rejected': rejected,
        'active': active,
        'avg_days': avg_days,
        'hire_rate': round(hired / total * 100, 1) if total else 0,
        'source_data': source_data,
        'source_json': json.dumps([{'source': r['source_of_hire'], 'count': r['cnt']} for r in source_data]),
        'trend_labels': json.dumps(trend_labels),
        'trend_values': json.dumps(trend_values),
        'bottleneck': bottleneck,
        'score_buckets': json.dumps(list(buckets.keys())),
        'score_values': json.dumps(list(buckets.values())),
        'summary_stats': [
            ('Total Applications', total,    'primary', 'fas fa-users'),
            ('Hired',             hired,     'success', 'fas fa-trophy'),
            ('Rejected',          rejected,  'danger',  'fas fa-times-circle'),
            ('Active / Pending',  active,    'warning', 'fas fa-spinner'),
        ],
    }
    return render(request, 'jobs/hiring_funnel.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE B — AI Cover Letter Scorer
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def cover_letter_scorer(request):
    """Feature B – Score cover letter vs JD with AI feedback."""
    jobs = JobPosting.objects.filter(status='OPEN').order_by('-created_at')[:20]
    result = None

    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '').strip()
        job_id = request.POST.get('job_id')
        job_desc = ''

        if job_id:
            try:
                posting = JobPosting.objects.get(pk=job_id)
                job_desc = posting.description or ''
                job_title = posting.title
            except JobPosting.DoesNotExist:
                job_title = 'Software Engineer'
        else:
            job_title = request.POST.get('job_title', 'Software Engineer')
            job_desc  = request.POST.get('job_desc', '')

        result = _score_cover_letter(cover_letter, job_title, job_desc)
        result['cover_letter'] = cover_letter
        result['job_title'] = job_title

    return render(request, 'jobs/cover_letter_scorer.html', {
        'jobs': jobs,
        'result': result,
    })


def _score_cover_letter(cover_letter: str, job_title: str, job_desc: str) -> dict:
    """Score cover letter using Gemini or heuristic fallback."""
    if _genai_client:
        prompt = f"""You are an expert ATS recruiter. Score this cover letter for the role "{job_title}".

Job Description excerpt:
{job_desc[:500]}

Cover Letter:
{cover_letter[:1000]}

Return ONLY valid JSON (no markdown):
{{
  "overall_score": 72,
  "relevance_score": 75,
  "tone_score": 80,
  "specificity_score": 65,
  "ats_keywords_found": ["python", "machine learning"],
  "missing_keywords": ["sql", "data pipeline"],
  "strengths": ["Clear opening", "Relevant experience mentioned"],
  "improvements": ["Add quantified achievements", "Mention specific company values"],
  "rewritten_opening": "A more compelling opening sentence here...",
  "verdict": "Good"
}}
Verdict must be one of: Excellent / Good / Average / Needs Work"""
        try:
            resp = _genai_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = resp.text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'): text = text[4:]
            return json.loads(text.strip())
        except Exception:
            pass

    # Heuristic fallback
    words = set(cover_letter.lower().split())
    jd_words = set(job_desc.lower().split()) if job_desc else set()
    overlap = len(words & jd_words)
    score = min(100, 40 + overlap * 2)
    return {
        'overall_score': score,
        'relevance_score': score,
        'tone_score': 70,
        'specificity_score': 60,
        'ats_keywords_found': list(words & jd_words)[:5],
        'missing_keywords': [],
        'strengths': ['Cover letter submitted successfully.'],
        'improvements': ['Add more role-specific keywords.', 'Include quantified achievements.'],
        'rewritten_opening': 'I am excited to apply for this position and bring my expertise in...',
        'verdict': 'Good' if score >= 60 else 'Needs Work',
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE C — Offer Acceptance Predictor
# ═══════════════════════════════════════════════════════════════════════════════

def predict_offer_acceptance(application: Application) -> dict:
    """Feature C – Rule-based classification: probability candidate accepts offer."""
    score = 0
    reasons_good = []
    reasons_risk = []

    # Factor 1: AI match score (higher = more interested)
    ai = application.ai_score or 0
    if ai >= 80:
        score += 30; reasons_good.append('Strong AI match score (≥80%)')
    elif ai >= 60:
        score += 20; reasons_good.append('Good AI match score')
    elif ai >= 40:
        score += 10
    else:
        reasons_risk.append('Low AI match score — candidate may prefer other offers')

    # Factor 2: Time to offer (days from apply to current stage)
    days = (timezone.now() - application.applied_at).days
    if days <= 14:
        score += 25; reasons_good.append('Fast process (<14 days) — candidate still engaged')
    elif days <= 30:
        score += 15; reasons_good.append('Moderate process time (14-30 days)')
    elif days <= 60:
        score += 5
    else:
        reasons_risk.append(f'Slow process ({days} days) — candidate may have moved on')

    # Factor 3: Round performance
    r1 = getattr(application, 'round1_score', 0) or 0
    r2 = getattr(application, 'round2_score', 0) or 0
    overall = getattr(application, 'overall_score', 0) or 0

    if overall >= 75:
        score += 25; reasons_good.append('Excellent overall performance — candidate is confident')
    elif (r1 + r2) / 2 >= 60 if (r1 or r2) else False:
        score += 15; reasons_good.append('Good assessment performance')

    # Factor 4: Application source
    src = application.source_of_hire
    if src == 'REFERRAL':
        score += 15; reasons_good.append('Referred candidate — higher loyalty')
    elif src == 'LINKEDIN':
        score += 5
    elif src == 'AGENCY':
        score -= 5; reasons_risk.append('Agency-sourced — may have competing offers')

    score = max(0, min(100, score))

    if score >= 75:   verdict = 'Very Likely to Accept'
    elif score >= 55: verdict = 'Likely to Accept'
    elif score >= 35: verdict = 'Uncertain'
    else:             verdict = 'At Risk — May Decline'

    return {
        'probability': score,
        'verdict': verdict,
        'reasons_good': reasons_good,
        'reasons_risk': reasons_risk,
        'recommendation': (
            'Send offer promptly with strong compensation.' if score >= 55
            else 'Consider increasing offer value or accelerating timeline.'
        )
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE D — Early Churn / Retention Risk Score
# ═══════════════════════════════════════════════════════════════════════════════

def predict_churn_risk(application: Application) -> dict:
    """Feature D – Predict if a hired candidate is a flight risk in 6 months."""
    risk = 0
    flags = []
    positives = []

    # Factor 1: Long hiring process → frustration
    days = (timezone.now() - application.applied_at).days
    if days > 60:
        risk += 20; flags.append(f'Hiring took {days} days — may indicate process frustration')
    elif days < 20:
        positives.append('Fast onboarding — positive first impression')

    # Factor 2: Low AI score but hired → potential misalignment
    ai = application.ai_score or 0
    if ai < 50:
        risk += 25; flags.append('Low resume-JD fit score — possible role mismatch')
    elif ai >= 75:
        positives.append('High JD fit — strong role alignment')

    # Factor 3: Overall performance
    overall = getattr(application, 'overall_score', 0) or 0
    if overall < 55 and overall > 0:
        risk += 15; flags.append('Borderline performance scores — may struggle in role')
    elif overall >= 80:
        positives.append('High overall performance — confident in role')

    # Factor 4: Source of hire
    if application.source_of_hire == 'AGENCY':
        risk += 15; flags.append('Agency hire — statistically higher turnover')
    elif application.source_of_hire == 'REFERRAL':
        risk -= 10; positives.append('Referral hire — higher retention rate')

    risk = max(0, min(100, risk))

    if risk >= 60:   level = 'High Risk'
    elif risk >= 35: level = 'Moderate Risk'
    else:            level = 'Low Risk'

    return {
        'risk_score': risk,
        'risk_level': level,
        'flags': flags,
        'positives': positives,
        'recommendation': (
            'Schedule 30/60/90 day check-ins and consider mentorship program.'
            if risk >= 40 else
            'Standard onboarding should suffice. Monitor during probation.'
        )
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE E — AI JD Enhancer / Analyser
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@require_POST
def jd_enhancer_api(request):
    """Refactored Feature E – Analyse & enhance a job description using recruiter_tools."""
    from .recruiter_tools import optimize_jd_for_ai
    try:
        body = json.loads(request.body)
        jd_text = body.get('jd_text', '').strip()
        job_title = body.get('job_title', 'Software Engineer')
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid request'}, status=400)

    if not jd_text:
        return JsonResponse({'ok': False, 'error': 'JD text required'}, status=400)

    result = optimize_jd_for_ai(jd_text, job_title)
    return JsonResponse({'ok': True, 'result': result})


def _enhance_jd(jd_text: str, job_title: str) -> dict:
    if _genai_client:
        prompt = f"""You are an expert HR consultant. Analyse this job description for "{job_title}".

JD:
{jd_text[:1500]}

Return ONLY valid JSON:
{{
  "bias_score": 35,
  "gendered_words": ["rockstar", "aggressive"],
  "vague_phrases": ["fast-paced environment", "team player"],
  "seo_score": 60,
  "missing_sections": ["Salary Range", "Remote Policy", "Growth Opportunities"],
  "clarity_score": 70,
  "top_improvements": ["Add salary range", "Remove gendered language", "Specify tech stack versions"],
  "enhanced_summary": "A rewritten, improved 3-sentence summary of the role...",
  "overall_grade": "B"
}}
overall_grade must be A/B/C/D/F"""
        try:
            resp = _genai_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = resp.text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'): text = text[4:]
            return json.loads(text.strip())
        except Exception:
            pass

    # Heuristic fallback
    jd_lower = jd_text.lower()
    bias_words = [w for w in ['rockstar', 'ninja', 'aggressive', 'dominant', 'competitive']
                  if w in jd_lower]
    vague = [w for w in ['fast-paced', 'team player', 'self-starter', 'synergy'] if w in jd_lower]
    return {
        'bias_score': len(bias_words) * 20,
        'gendered_words': bias_words,
        'vague_phrases': vague,
        'seo_score': 55,
        'missing_sections': ['Salary Range', 'Remote Policy'],
        'clarity_score': 65,
        'top_improvements': ['Add salary range', 'Specify tech stack', 'Include team size'],
        'enhanced_summary': f'We are seeking a talented {job_title} to join our growing team...',
        'overall_grade': 'C',
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE F — Score Trend Data API (for application_details chart)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def score_trend_api(request, application_id):
    """Feature F – Return scores across all rounds for Chart.js line chart."""
    application = get_authorized_application(request, application_id)

    # Access check
    if request.user.is_recruiter:
        if application.job.recruiter != request.user:
            return JsonResponse({'error': 'Forbidden'}, status=403)
    else:
        if application.candidate.user != request.user:
            return JsonResponse({'error': 'Forbidden'}, status=403)

    labels, values = [], []

    if application.ai_score:
        labels.append('Resume Match'); values.append(round(application.ai_score))

    r1 = getattr(application, 'round1_score', None)
    if r1: labels.append('Round 1'); values.append(round(r1))

    r2 = getattr(application, 'round2_score', None)
    if r2: labels.append('Round 2'); values.append(round(r2))

    ov = getattr(application, 'overall_score', None)
    if ov: labels.append('Overall'); values.append(round(ov))

    return JsonResponse({
        'labels': labels,
        'values': values,
        'avg': round(sum(values) / len(values)) if values else 0,
        'trend': 'improving' if len(values) >= 2 and values[-1] > values[0] else 'declining',
    })


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE G — Resume ATS Live Checker (Candidate-facing)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def resume_ats_checker(request):
    """Feature G – Candidate pastes resume text; get instant ATS score + tips."""
    result = None
    if request.method == 'POST':
        resume_text = request.POST.get('resume_text', '').strip()
        job_id = request.POST.get('job_id', '')
        job_desc = ''
        job_title = 'Software Engineer'

        if job_id:
            try:
                posting = JobPosting.objects.get(pk=job_id)
                job_desc = posting.description or ''
                job_title = posting.title
            except JobPosting.DoesNotExist:
                pass

        result = _check_ats(resume_text, job_title, job_desc)

    jobs = JobPosting.objects.filter(status='OPEN').order_by('-created_at')[:20]
    scores_list = None
    if result:
        scores_list = [
            ('ATS Score',          result.get('ats_score', 0),          'primary'),
            ('Keyword Match',      result.get('keyword_match_score', 0), 'info'),
            ('Format Score',       result.get('format_score', 0),        'success'),
            ('Completeness',       result.get('completeness_score', 0),  'warning'),
        ]
    tips_list = [
        ('Keyword Optimised', 'Match job description terms', 'fas fa-key', 'primary'),
        ('Sections Complete', 'Include all standard sections', 'fas fa-list-check', 'success'),
        ('ATS Friendly', 'Clean format, no tables/images', 'fas fa-robot', 'info'),
    ]
    return render(request, 'jobs/resume_ats_checker.html', {
        'result': result,
        'jobs': jobs,
        'scores_list': scores_list,
        'tips_list': tips_list,
    })


def _check_ats(resume_text: str, job_title: str, job_desc: str) -> dict:
    if _genai_client:
        prompt = f"""You are an ATS expert. Analyse this resume for the "{job_title}" role.

Job Description:
{job_desc[:400]}

Resume Text:
{resume_text[:1500]}

Return ONLY valid JSON:
{{
  "ats_score": 68,
  "keyword_match_score": 72,
  "format_score": 80,
  "completeness_score": 65,
  "found_keywords": ["python", "machine learning", "sql"],
  "missing_keywords": ["docker", "kubernetes", "aws"],
  "sections_found": ["Experience", "Education", "Skills"],
  "sections_missing": ["Summary", "Certifications", "Projects"],
  "formatting_issues": ["Use bullet points", "Add contact info section"],
  "quick_wins": ["Add 3 missing keywords", "Write a 3-line summary", "Add 2 project descriptions"],
  "verdict": "Interview Ready"
}}
verdict options: ATS Ready / Interview Ready / Needs Improvement / Major Revision Needed"""
        try:
            resp = _genai_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = resp.text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'): text = text[4:]
            return json.loads(text.strip())
        except Exception:
            pass

    # Heuristic fallback
    words = set(resume_text.lower().split())
    jd_words = set(job_desc.lower().split()) if job_desc else set()
    found = list(words & jd_words)[:6]
    score = min(95, 40 + len(found) * 4)

    sections_found = []
    for sec in ['experience', 'education', 'skills', 'summary', 'projects', 'certifications']:
        if sec in resume_text.lower():
            sections_found.append(sec.title())

    return {
        'ats_score': score,
        'keyword_match_score': score,
        'format_score': 75,
        'completeness_score': len(sections_found) * 15,
        'found_keywords': found,
        'missing_keywords': [],
        'sections_found': sections_found,
        'sections_missing': [s for s in ['Summary', 'Projects', 'Certifications'] if s not in sections_found],
        'formatting_issues': ['Use consistent bullet points', 'Keep to 1-2 pages'],
        'quick_wins': ['Add a professional summary', 'List 5+ technical skills', 'Quantify achievements'],
        'verdict': 'Interview Ready' if score >= 65 else 'Needs Improvement',
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE H — Job Recommendation Engine (Candidate-facing)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def job_recommendations(request):
    """Feature H – Recommend open jobs based on candidate skill profile."""
    if request.user.is_recruiter:
        from django.shortcuts import redirect
        return redirect('dashboard')

    try:
        candidate = request.user.candidate
        skills_text = (candidate.skills_extracted or '').lower()
    except Exception:
        skills_text = ''

    open_jobs = JobPosting.objects.filter(status='OPEN').select_related('recruiter')

    # Already applied job IDs
    applied_ids = set(
        Application.objects.filter(candidate__user=request.user)
        .values_list('job_id', flat=True)
    )

    skill_words = set(skills_text.replace(',', ' ').split())

    scored_jobs = []
    for job in open_jobs:
        if job.id in applied_ids:
            continue
        jd_text = ((job.description or '') + ' ' + (job.technology_stack or '') + ' ' + job.title).lower()
        jd_words = set(jd_text.split())
        matched = skill_words & jd_words
        match_pct = min(99, int(len(matched) / max(len(skill_words), 1) * 100)) if skill_words else 40
        scored_jobs.append({
            'job': job,
            'match_score': match_pct,
            'matched_skills': list(matched)[:6],
            'why': f"Matches {len(matched)} of your skills" if matched else "Explore a new opportunity",
        })

    # Sort by match score desc
    scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    top_jobs = scored_jobs[:12]

    return render(request, 'jobs/job_recommendations.html', {
        'recommendations': top_jobs,
        'skills_text': skills_text,
        'total_open': open_jobs.count(),
        'total_applied': len(applied_ids),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE I — Upskilling Roadmap (Candidate, after skill gap)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def upskilling_roadmap(request, application_id):
    """Feature I – Personalised learning roadmap based on Elite Bridge-Skilling."""
    application = get_object_or_404(Application, pk=application_id, candidate__user=request.user)
    
    from .utils import generate_growth_roadmap_data
    roadmap_data = generate_growth_roadmap_data(application.candidate, application.job)
    
    return render(request, 'jobs/upskilling_roadmap.html', {
        'application': application,
        'job_title': application.job.title,
        'roadmap': roadmap_data,
        'milestones': roadmap_data.get('milestones', []),
        'poc_project': roadmap_data.get('poc_project', {}),
        'summary': roadmap_data.get('summary', '')
    })


def _build_roadmap(skills: list, job_title: str) -> list:
    """Build a learning roadmap for each missing skill with resources."""
    if _genai_client and skills:
        prompt = f"""Create a learning roadmap for someone applying for {job_title}.
They need to learn: {', '.join(skills)}.

Return ONLY valid JSON array:
[
  {{
    "skill": "Python",
    "priority": "Critical",
    "weeks_to_learn": 4,
    "resources": [
      {{"title": "Python for Everybody", "platform": "Coursera", "url": "https://coursera.org/learn/python", "free": true}},
      {{"title": "Automate the Boring Stuff", "platform": "Book/Free", "url": "https://automatetheboringstuff.com", "free": true}}
    ],
    "milestones": ["Week 1: Basics", "Week 2: OOP", "Week 4: Projects"]
  }}
]"""
        try:
            resp = _genai_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = resp.text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'): text = text[4:]
            return json.loads(text.strip())
        except Exception:
            pass

    # Fallback static map
    resource_map = {
        'python':     [{'title': 'Python for Everybody', 'platform': 'Coursera', 'url': 'https://www.coursera.org/specializations/python', 'free': True}],
        'sql':        [{'title': 'SQL for Data Science', 'platform': 'Coursera', 'url': 'https://www.coursera.org/learn/sql-for-data-science', 'free': True}],
        'machine learning': [{'title': 'ML Crash Course', 'platform': 'Google', 'url': 'https://developers.google.com/machine-learning/crash-course', 'free': True}],
        'pandas':     [{'title': 'Pandas Documentation', 'platform': 'Official Docs', 'url': 'https://pandas.pydata.org/docs/', 'free': True}],
        'docker':     [{'title': 'Docker for Beginners', 'platform': 'YouTube', 'url': 'https://www.youtube.com/watch?v=3c-iBn73dDE', 'free': True}],
        'react':      [{'title': 'React Official Tutorial', 'platform': 'React.dev', 'url': 'https://react.dev/learn', 'free': True}],
        'aws':        [{'title': 'AWS Cloud Practitioner', 'platform': 'AWS Training', 'url': 'https://aws.amazon.com/training/', 'free': True}],
    }
    result = []
    for i, skill in enumerate(skills):
        key = skill.lower()
        resources = resource_map.get(key, [
            {'title': f'Learn {skill}', 'platform': 'YouTube', 'url': f'https://www.youtube.com/results?search_query=learn+{skill.replace(" ", "+")}', 'free': True}
        ])
        result.append({
            'skill': skill,
            'priority': 'Critical' if i < 2 else ('Important' if i < 5 else 'Nice-to-have'),
            'weeks_to_learn': 4 if i < 2 else (3 if i < 5 else 2),
            'resources': resources,
            'milestones': [f'Week 1: Fundamentals of {skill}', f'Week 2-3: Practice projects', f'Week 4: Apply in portfolio'],
        })
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE J — Application Analytics Dashboard (Candidate)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def candidate_analytics(request):
    """Feature J – Candidate sees charts of their own application performance."""
    if request.user.is_recruiter:
        from django.shortcuts import redirect
        return redirect('dashboard')

    apps = Application.objects.filter(
        candidate__user=request.user
    ).select_related('job').order_by('-applied_at')

    total = apps.count()
    hired = apps.filter(status='HIRED').count()
    rejected = apps.filter(status__in=['RESUME_REJECTED', 'ROUND_1_FAILED',
                                        'ROUND_2_FAILED', 'ROUND_3_FAILED', 'REJECTED']).count()
    active = total - hired - rejected

    # AI score trend over time
    score_trend = list(
        apps.filter(ai_score__gt=0)
            .values('applied_at', 'ai_score', 'job__title')
            .order_by('applied_at')
    )
    trend_labels = [f"{r['job__title'][:15]} ({r['applied_at'].strftime('%b %d')})" for r in score_trend]
    trend_values = [round(r['ai_score']) for r in score_trend]

    # Status distribution
    status_counts = dict(apps.values_list('status').annotate(cnt=Count('id')))

    # Category: group by pass/fail/active
    category_data = {
        'Active': active,
        'Hired': hired,
        'Rejected': rejected,
    }

    # Avg scores
    avg_ai = apps.filter(ai_score__gt=0).aggregate(a=Avg('ai_score'))['a'] or 0

    # Top matched jobs (by AI score)
    top_matches = list(apps.filter(ai_score__gt=0).order_by('-ai_score')[:5].values(
        'job__title', 'ai_score', 'status'
    ))

    # Monthly application activity
    from django.utils.timezone import now
    monthly = defaultdict(int)
    for app in apps:
        key = app.applied_at.strftime('%b %Y')
        monthly[key] += 1
    monthly_labels = list(monthly.keys())
    monthly_values = list(monthly.values())

    return render(request, 'jobs/candidate_analytics.html', {
        'total': total,
        'hired': hired,
        'rejected': rejected,
        'active': active,
        'avg_ai': round(avg_ai, 1),
        'hit_rate': round(hired / total * 100, 1) if total else 0,
        'trend_labels': json.dumps(trend_labels),
        'trend_values': json.dumps(trend_values),
        'category_json': json.dumps(category_data),
        'top_matches': top_matches,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_values': json.dumps(monthly_values),
        'applications': apps[:5],
    })
