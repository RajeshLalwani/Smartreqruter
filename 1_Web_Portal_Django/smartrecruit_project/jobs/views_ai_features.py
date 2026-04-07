"""
AI Features Views for SmartRecruit
────────────────────────────────────────────────────
Endpoints for:
1. Skill Gap Analysis Page
2. Predictive Hiring Score API
3. AI Candidate Rankings API
4. Application Trend API (for analytics dashboard)
"""
import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Avg, Q

from .models import JobPosting, Application, Candidate
from .ai_features import (
    get_skill_gap_analysis,
    calculate_predictive_hiring_score,
    get_application_trend,
    get_score_distribution,
    get_top_candidates_ranking,
)
from .resume_intelligence import extract_resume_entities
from .bias_detection import get_blind_screening_batch, analyze_jd_bias, anonymize_application
from .sentiment_analysis import analyze_interview_sentiment, analyze_all_interviews
from .talent_intelligence import estimate_salary, calculate_cultural_fit, estimate_offer_acceptance


# ──────────────────────────────────────────────────────
# 1. SKILL GAP ANALYSIS PAGE (Recruiter view per application)
# ──────────────────────────────────────────────────────
@login_required
def skill_gap_analysis(request, application_id):
    """
    Full skill gap analysis page for a specific candidate application.
    Shows matched/missing skills, importance-weighted score, and recommendations.
    """
    application = get_object_or_404(
        Application, id=application_id, job__recruiter=request.user
    )
    
    candidate_skills = application.candidate.skills_extracted or ''
    skill_data = get_skill_gap_analysis(application.job, candidate_skills)
    
    # Also compute predictive score
    try:
        predictive = calculate_predictive_hiring_score(application)
    except Exception as e:
        predictive = {
            'composite_score': 0,
            'likelihood': 'Insufficient Data',
            'likelihood_color': 'secondary',
            'likelihood_icon': 'fas fa-question-circle',
            'components': {},
            'skill_analysis': skill_data,
            'stage_bonus': 0,
        }
    
    context = {
        'application': application,
        'skill_data': skill_data,
        'predictive': predictive,
        'matched_json': json.dumps(skill_data['matched_skills']),
        'missing_json': json.dumps(skill_data['missing_skills']),
        'breakdown_json': json.dumps(skill_data['skill_breakdown']),
    }
    return render(request, 'jobs/skill_gap_analysis.html', context)


# ──────────────────────────────────────────────────────
# 2. PREDICTIVE HIRING SCORE API (JSON endpoint)
# ──────────────────────────────────────────────────────
@login_required
def predictive_score_api(request, application_id):
    """
    Returns JSON of the predictive hiring score for a given application.
    Used by frontend for dynamic score display without page reload.
    """
    application = get_object_or_404(
        Application, id=application_id, job__recruiter=request.user
    )
    
    try:
        data = calculate_predictive_hiring_score(application)
        return JsonResponse({
            'success': True,
            'composite_score': data['composite_score'],
            'likelihood': data['likelihood'],
            'likelihood_color': data['likelihood_color'],
            'likelihood_icon': data['likelihood_icon'],
            'components': data['components'],
            'stage_bonus': data['stage_bonus'],
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ──────────────────────────────────────────────────────
# 3. AI CANDIDATE RANKINGS  (Per Job)
# ──────────────────────────────────────────────────────
@login_required
def candidate_rankings(request, job_id):
    """
    Show AI-ranked candidates for a specific job,
    ordered by predictive composite hiring score.
    """
    from .models import Assessment, Interview
    
    job = get_object_or_404(JobPosting, id=job_id, recruiter=request.user)
    applications = Application.objects.filter(job=job).select_related(
        'candidate', 'job'
    ).prefetch_related('assessments', 'interviews')
    
    # Get rankings
    rankings = get_top_candidates_ranking(job, applications, limit=20)
    
    # Score distribution across all candidates
    score_dist = get_score_distribution(applications)
    
    context = {
        'job': job,
        'rankings': rankings,
        'score_distribution': json.dumps(score_dist),
        'total_applicants': applications.count(),
    }
    return render(request, 'jobs/candidate_rankings.html', context)


# ──────────────────────────────────────────────────────
# 4. ANALYTICS TREND API (for enhanced analytics charts)
# ──────────────────────────────────────────────────────
@login_required
def analytics_trend_api(request):
    """
    Returns application trend data (day-by-day counts) for the authenticated recruiter.
    Used by the analytics dashboard timeline chart.
    """
    from .models import Application
    days = int(request.GET.get('days', 30))
    applications = Application.objects.filter(job__recruiter=request.user)
    trend = get_application_trend(applications, days=days)
    
    return JsonResponse({
        'success': True,
        'labels': trend['labels'],
        'values': trend['values'],
        'period': f'Last {days} days',
    })


# ──────────────────────────────────────────────────────
# 5. SKILL GAP API (JSON — for inline checks)
# ──────────────────────────────────────────────────────
@login_required
def skill_gap_api(request, application_id):
    """
    Quick JSON endpoint for skill gap analysis.
    Can be called inline from the candidate list for AJAX updates.
    """
    application = get_object_or_404(
        Application, id=application_id, job__recruiter=request.user
    )
    
    candidate_skills = application.candidate.skills_extracted or ''
    data = get_skill_gap_analysis(application.job, candidate_skills)
    
    return JsonResponse({
        'success': True,
        'match_percentage': data['match_percentage'],
        'importance_weighted_score': data['importance_weighted_score'],
        'matched': data['matched_skills'],
        'missing': data['missing_skills'],
        'recommendations': data['recommendations'],
    })


# ──────────────────────────────────────────────────────
# 6. RESUME INTELLIGENCE REPORT
# ──────────────────────────────────────────────────────
@login_required
def resume_intelligence_view(request, application_id):
    """
    NLP-powered resume entity extraction report with Deep RAG Scoring.
    """
    application = get_object_or_404(
        Application, id=application_id, job__recruiter=request.user
    )
    candidate = application.candidate

    # 1. Base Heuristic Extraction
    resume_text = candidate.skills_extracted or ''
    report = extract_resume_entities(resume_text, candidate=candidate)
    ats = report.pop('ats_score')

    # 2. Deep RAG Intelligence Pass
    try:
        from core.utils.rag_engine import RAGEngine
        rag = RAGEngine()
        
        jd_text = application.job.description or ""
        rag_data = rag.get_contextual_evaluation(resume_text, jd_text)
        
        # Merge RAG score if it's high confidence, otherwise stick to heuristic
        if rag_data.get('score'):
            ats['rag_score'] = rag_data['score']
            ats['justification'] = rag_data.get('justification')
            ats['rag_reasoning'] = rag_data.get('rag_reasoning')
            ats['critical_gaps'] = rag_data.get('critical_gaps', [])
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[ResumeIntelligence] RAG pass failed: {e}")

    context = {
        'application': application,
        'report': report,
        'ats': ats,
    }
    return render(request, 'jobs/resume_intelligence.html', context)


# ──────────────────────────────────────────────────────
# 7. BLIND HIRING MODE (Per Job)
# ──────────────────────────────────────────────────────
@login_required
def blind_hiring_view(request, job_id):
    """
    Blind Hiring Mode: shows anonymized candidates for a job
    to reduce unconscious bias during shortlisting.
    Also analyzes the JD for biased language.
    """
    job = get_object_or_404(JobPosting, id=job_id, recruiter=request.user)
    applications = Application.objects.filter(job=job).select_related('candidate', 'job')

    # Anonymize all candidates
    blind_candidates = get_blind_screening_batch(applications)

    # Analyze JD for bias
    jd_bias = analyze_jd_bias(job.description)

    context = {
        'job': job,
        'blind_candidates': blind_candidates,
        'jd_bias': jd_bias,
        'total': len(blind_candidates),
        # Pass real IDs in a separate map for recruiter to reveal if needed
        'reveal_map': json.dumps({str(i): c['id'] for i, c in enumerate(blind_candidates)}),
    }
    return render(request, 'jobs/blind_hiring.html', context)


# ──────────────────────────────────────────────────────
# 8. INTERVIEW SENTIMENT ANALYSIS
# ──────────────────────────────────────────────────────
@login_required
def sentiment_analysis_view(request, application_id):
    """
    Sentiment analysis of all completed interview feedback for an application.
    Shows overall tone, dimension breakdown, and AI-recommended action.
    """
    application = get_object_or_404(
        Application, id=application_id, job__recruiter=request.user
    )

    # Analyze all rounds
    all_sentiment = analyze_all_interviews(application)

    # Also run on latest AI interview directly
    from .models import Interview
    latest_ai = Interview.objects.filter(
        application=application, interview_type='AI_BOT', status='COMPLETED'
    ).last()
    latest_hr = Interview.objects.filter(
        application=application, interview_type='AI_HR', status='COMPLETED'
    ).last()

    ai_sentiment = analyze_interview_sentiment(
        latest_ai.feedback if latest_ai else '',
        latest_ai
    )
    hr_sentiment = analyze_interview_sentiment(
        latest_hr.feedback if latest_hr else '',
        latest_hr
    )

    # Aggregate overall from all rounds
    scores = [s['overall_score'] for s in all_sentiment.values() if s['overall_score'] > 0]
    aggregate_score = round(sum(scores) / len(scores)) if scores else 0

    context = {
        'application': application,
        'all_sentiment': all_sentiment,
        'ai_sentiment': ai_sentiment,
        'hr_sentiment': hr_sentiment,
        'aggregate_score': aggregate_score,
        'dimensions_json': json.dumps(ai_sentiment['dimensions']),
        'hr_dimensions_json': json.dumps(hr_sentiment['dimensions']),
    }
    return render(request, 'jobs/sentiment_analysis.html', context)


# ──────────────────────────────────────────────────────
# 9. TALENT INTELLIGENCE DASHBOARD
#    (Salary Estimator + Cultural Fit + Offer Acceptance)
# ──────────────────────────────────────────────────────
@login_required
def talent_intelligence_view(request, application_id):
    """
    Combined: Salary Estimate, Cultural Fit Score, Offer Acceptance Probability.
    All three data-science features on one premium dashboard.
    """
    application = get_object_or_404(
        Application, id=application_id, job__recruiter=request.user
    )
    candidate = application.candidate
    job = application.job

    resume_text = candidate.skills_extracted or ''
    location    = candidate.current_location or 'India'
    years       = float(candidate.experience_years or 0)
    ai_score    = float(application.ai_score or 0)

    # ── Salary Estimation ──────────────────────────────────────────
    salary = estimate_salary(
        job_title=job.title,
        experience_years=years,
        skills_text=resume_text,
        location=location,
        ai_score=ai_score,
    )

    # ── Cultural Fit Score ─────────────────────────────────────────
    candidate_combined = resume_text
    # If there are interview feedbacks, include them for richer culture signal
    from .models import Interview
    interviews = Interview.objects.filter(application=application, status='COMPLETED')
    all_feedback = ' '.join([iv.feedback for iv in interviews if iv.feedback])
    candidate_combined += ' ' + all_feedback

    culture = calculate_cultural_fit(
        candidate_text=candidate_combined,
        job_description=job.description or '',
    )

    # ── Offer Acceptance Probability ──────────────────────────────
    # Estimate days since application was submitted
    from django.utils import timezone
    days_elapsed = (timezone.now() - application.applied_at).days

    predictive_score = ai_score  # Use AI score as proxy if composite not cached

    offer = estimate_offer_acceptance(
        ai_score=ai_score,
        predictive_score=predictive_score,
        days_to_offer=days_elapsed,
        rounds_completed=interviews.count(),
        offered_salary=None,  # No offer made yet — use null
        estimated_salary_mid=salary['salary_mid'],
        culture_fit_score=float(culture['overall_score']),
    )

    # ── JSON for Charts ───────────────────────────────────────────
    culture_radar = {k: v['score'] for k, v in culture['category_scores'].items()}

    context = {
        'application': application,
        'salary': salary,
        'culture': culture,
        'offer': offer,
        'salary_factors_json': json.dumps(salary['factors']),
        'culture_radar_json': json.dumps(culture_radar),
    }
    return render(request, 'jobs/talent_intelligence.html', context)
# ──────────────────────────────────────────────────────
# 10. PROCTORING SUSPICION HEATMAP API
# ──────────────────────────────────────────────────────
@login_required
def proctoring_heatmap_api(request, application_id):
    """
    Returns a 'Suspicion Heatmap' for a given application.
    Aggregates log weights into time-buckets for visualization.
    """
    from Proctoring_System.anomaly_detector import AdvancedProctoringAnalyzer
    
    # Security check: Recruiter must own the job
    application = get_object_or_404(
        Application, id=application_id, job__recruiter=request.user
    )
    
    analyzer = AdvancedProctoringAnalyzer()
    heatmap = analyzer.generate_suspicion_heatmap(application_id)
    
    return JsonResponse({
        'success': True,
        'application_id': application_id,
        'heatmap': heatmap,
        'max_suspicion': max([h['score'] for h in heatmap]) if heatmap else 0,
        'average_suspicion': sum([h['score'] for h in heatmap]) / len(heatmap) if heatmap else 0
    })
