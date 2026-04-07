"""
Advanced Recruiter Tools
Bulk actions, candidate comparison, and automated screening
"""

from django.db.models import Q, Avg, Count
from .models import Application, JobPosting
from django.core.mail import send_mass_mail


def bulk_update_status(application_ids, new_status, recruiter):
    """
    Update status for multiple applications at once
    """
    applications = Application.objects.filter(
        id__in=application_ids,
        job__recruiter=recruiter
    )
    
    updated_count = applications.update(status=new_status)
    return updated_count


def bulk_send_emails(application_ids, subject, message, recruiter):
    """
    Send emails to multiple candidates
    """
    applications = Application.objects.filter(
        id__in=application_ids,
        job__recruiter=recruiter
    ).select_related('candidate')
    
    messages = []
    for app in applications:
        messages.append((
            subject,
            message,
            'noreply@smartrecruit.com',
            [app.candidate.email]
        ))
    
    send_mass_mail(messages, fail_silently=False)
    return len(messages)


def compare_candidates(application_ids):
    """
    Compare multiple candidates side-by-side
    """
    applications = Application.objects.filter(
        id__in=application_ids
    ).select_related('candidate', 'job')
    
    comparison_data = []
    for app in applications:
        comparison_data.append({
            'application_id': app.id,
            'candidate_name': app.candidate.get_full_name(),
            'candidate_email': app.candidate.email,
            'job_title': app.job.title,
            'ai_score': app.ai_score or 0,
            'round1_score': app.round1_score or 0,
            'round2_score': app.round2_score or 0,
            'ai_interview_score': app.ai_interview_score or 0,
            'hr_interview_score': app.hr_interview_score or 0,
            'overall_score': calculate_overall_score(app),
            'status': app.get_status_display(),
            'applied_date': app.applied_at,
        })
    
    # Sort by overall score
    comparison_data.sort(key=lambda x: x['overall_score'], reverse=True)
    return comparison_data


def calculate_overall_score(application):
    """
    Calculate weighted overall score for an application
    """
    scores = []
    weights = []
    
    if application.ai_score:
        scores.append(application.ai_score)
        weights.append(0.15)
    
    if application.round1_score:
        scores.append(application.round1_score)
        weights.append(0.20)
    
    if application.round2_score:
        scores.append(application.round2_score)
        weights.append(0.25)
    
    if application.ai_interview_score:
        scores.append(application.ai_interview_score)
        weights.append(0.20)
    
    if application.hr_interview_score:
        scores.append(application.hr_interview_score)
        weights.append(0.20)
    
    if not scores:
        return 0
    
    # Normalize weights
    total_weight = sum(weights)
    if total_weight > 0:
        weights = [w / total_weight for w in weights]
    
    # Calculate weighted average
    overall = sum(s * w for s, w in zip(scores, weights))
    return round(overall, 1)


def create_automated_screening_rule(job, rules):
    """
    Create automated screening rules for a job
    Rules format:
    {
        'min_ai_score': 60,
        'min_experience': 2,
        'required_skills': ['Python', 'Django'],
        'auto_reject_below': 40,
        'auto_shortlist_above': 80
    }
    """
    # This would typically be stored in a database
    # For now, we'll return a function that applies the rules
    
    def apply_rules(application):
        actions = []
        
        # Auto-reject if AI score too low
        if application.ai_score and application.ai_score < rules.get('auto_reject_below', 0):
            actions.append(('reject', 'AI score below threshold'))
        
        # Auto-shortlist if AI score high enough
        elif application.ai_score and application.ai_score >= rules.get('auto_shortlist_above', 100):
            actions.append(('shortlist', 'AI score above threshold'))
        
        # Check required skills
        required_skills = rules.get('required_skills', [])
        if required_skills:
            # This would need to check candidate's resume/profile
            pass
        
        return actions
    
    return apply_rules


def get_candidate_pipeline_stats(recruiter):
    """
    Get statistics about candidates in the pipeline
    """
    applications = Application.objects.filter(job__recruiter=recruiter)
    
    stats = {
        'total_candidates': applications.count(),
        'by_status': {},
        'avg_scores': {
            'ai_score': applications.aggregate(Avg('ai_score'))['ai_score__avg'] or 0,
            'round1': applications.aggregate(Avg('round1_score'))['round1_score__avg'] or 0,
            'round2': applications.aggregate(Avg('round2_score'))['round2_score__avg'] or 0,
            'ai_interview': applications.aggregate(Avg('ai_interview_score'))['ai_interview_score__avg'] or 0,
            'hr_interview': applications.aggregate(Avg('hr_interview_score'))['hr_interview_score__avg'] or 0,
        },
        'by_job': {},
    }
    
    # Count by status
    status_counts = applications.values('status').annotate(count=Count('id'))
    for item in status_counts:
        stats['by_status'][item['status']] = item['count']
    
    # Count by job
    job_counts = applications.values('job__title').annotate(count=Count('id'))
    for item in job_counts:
        stats['by_job'][item['job__title']] = item['count']
    
    return stats


def find_top_candidates(job, limit=10):
    """
    Find top candidates for a specific job based on overall score
    """
    applications = Application.objects.filter(job=job)
    
    # Calculate overall score for each
    candidates_with_scores = []
    for app in applications:
        overall_score = calculate_overall_score(app)
        candidates_with_scores.append((app, overall_score))
    
    # Sort by score
    candidates_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    return [app for app, score in candidates_with_scores[:limit]]


def get_recruiter_performance_metrics(recruiter, days=30):
    """
    Calculate performance metrics for a recruiter
    """
    from datetime import timedelta
    from django.utils import timezone
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    applications = Application.objects.filter(
        job__recruiter=recruiter,
        applied_at__gte=cutoff_date
    )
    
    metrics = {
        'total_applications': applications.count(),
        'applications_reviewed': applications.exclude(status='RESUME_SCREENING').count(),
        'candidates_hired': applications.filter(status='OFFER_ACCEPTED').count(),
        'avg_time_to_review': 0,  # Would need to track review timestamps
        'conversion_rate': 0,
        'active_jobs': JobPosting.objects.filter(recruiter=recruiter, status='OPEN').count(),
    }
    
    # Calculate conversion rate
    if metrics['total_applications'] > 0:
        metrics['conversion_rate'] = (metrics['candidates_hired'] / metrics['total_applications']) * 100
    
    return metrics


# ─── Feature 11: Agentic JD Optimizer (Generative AI) ─────────────

def optimize_jd_for_ai(jd_text: str, job_title: str) -> dict:
    """
    Analyzes and optimizes a Job Description for better AI matching.
    Simulates Generative AI reasoning for structural and keyword improvements.
    """
    import re
    
    suggestions = []
    missing_keywords = []
    
    # ── 1. Structural Analysis ───────────────
    if len(jd_text) < 300:
        suggestions.append("Job description is too short. AI models prefer 500-1000 characters for rich context.")
    
    if "responsibilities" not in jd_text.lower() and "requirements" not in jd_text.lower():
        suggestions.append("Missing clear section headers (Responsibilities, Requirements). Use markdown headers for better parsing.")

    # ── 2. Keyword Intelligence ──────────────
    # Identify title-specific missing keywords
    title_lower = job_title.lower()
    tech_stack = {
        'python': ['FastAPI', 'Django', 'PyTest', 'Asyncio'],
        'data scientist': ['Scikit-Learn', 'Pandas', 'Feature Engineering', 'AB Testing'],
        'frontend': ['TypeScript', 'Next.js', 'Redux', 'Unit Testing'],
        'devops': ['CI/CD', 'Kubernetes', 'Terraform', 'SRE'],
    }
    
    for category, keywords in tech_stack.items():
        if category in title_lower:
            for kw in keywords:
                if kw.lower() not in jd_text.lower():
                    missing_keywords.append(kw)
    
    if missing_keywords:
        suggestions.append(f"Essential skills like {', '.join(missing_keywords[:3])} are missing. Adding these will improve the matching score for top candidates.")

    # ── 3. Bias & Clarity ───────────────
    if "rockstar" in jd_text.lower() or "ninja" in jd_text.lower():
        suggestions.append("Avoid 'Rockstar' or 'Ninja' terminology. Use professional roles to attract a diverse talent pool.")

    # ── 4. Generative Content (Simulated) ─────────
    optimized_snippet = f"### Key Responsibilities\n- Design and implement scalable {job_title} solutions.\n- Collaborate with cross-functional teams to deliver high-impact features.\n- Write clean, maintainable, and well-documented code."
    
    return {
        'optimization_score': 100 - (len(suggestions) * 10),
        'suggestions': suggestions,
        'missing_keywords': missing_keywords,
        'generative_enhancement': optimized_snippet,
        'seo_rating': 'Excellent' if not missing_keywords else 'Moderate'
    }
