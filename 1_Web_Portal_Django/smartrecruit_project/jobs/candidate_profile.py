"""
Candidate Profile and Skills Management
Utilities for managing candidate profiles, skills, and preferences
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


def get_or_create_candidate_profile(user):
    """
    Get or create a candidate profile for the user
    Returns a dictionary with profile information
    """
    if user.is_recruiter:
        return None
    
    # Get user's applications to build profile
    from .models import Application
    applications = Application.objects.filter(candidate__user=user)
    
    # Extract skills from applications and user data
    skills = set()
    technologies = set()
    
    for app in applications:
        if app.job.required_skills:
            skills.update([s.strip() for s in app.job.required_skills.split(',')])
        if app.job.technology_stack:
            technologies.update([t.strip() for t in app.job.technology_stack.split(',')])
    
    # Calculate profile completeness
    completeness = calculate_profile_completeness(user, applications)
    
    # Get application statistics
    total_applications = applications.count()
    active_applications = applications.exclude(
        status__in=['RESUME_REJECTED', 'ROUND_1_FAILED', 'ROUND_2_FAILED', 
                    'ROUND_3_FAILED', 'REJECTED', 'OFFER_REJECTED']
    ).count()
    
    offers_received = applications.filter(status='OFFER_GENERATED').count()
    offers_accepted = applications.filter(status='OFFER_ACCEPTED').count()
    
    return {
        'user': user,
        'skills': list(skills),
        'technologies': list(technologies),
        'total_applications': total_applications,
        'active_applications': active_applications,
        'offers_received': offers_received,
        'offers_accepted': offers_accepted,
        'completeness': completeness,
        'success_rate': calculate_success_rate(applications)
    }


def calculate_profile_completeness(user, applications):
    """
    Calculate profile completeness percentage
    """
    score = 0
    max_score = 100
    
    # Basic info (40 points)
    if user.first_name and user.last_name:
        score += 20
    if user.email:
        score += 10
    if hasattr(user, 'phone') and user.phone:
        score += 10
    
    # Application history (30 points)
    if applications.exists():
        score += 15
    if applications.count() >= 3:
        score += 15
    
    # Resume uploaded (30 points)
    if applications.filter(candidate__resume_file__isnull=False).exclude(candidate__resume_file='').exists():
        score += 30
    
    return min(int((score / max_score) * 100), 100)


def calculate_success_rate(applications):
    """
    Calculate candidate's success rate
    """
    if not applications.exists():
        return 0
    
    successful = applications.filter(
        status__in=['OFFER_GENERATED', 'OFFER_ACCEPTED']
    ).count()
    
    total = applications.count()
    return round((successful / total) * 100, 1) if total > 0 else 0


def get_candidate_skills_analysis(user):
    """
    Analyze candidate's skills based on application history
    Returns skill proficiency and recommendations
    """
    from .models import Application
    applications = Application.objects.filter(candidate__user=user)
    
    skill_scores = {}
    skill_frequency = {}
    
    for app in applications:
        if app.job.required_skills:
            skills = [s.strip() for s in app.job.required_skills.split(',')]
            
            for skill in skills:
                if skill not in skill_frequency:
                    skill_frequency[skill] = 0
                    skill_scores[skill] = []
                
                skill_frequency[skill] += 1
                
                # Add scores if available
                if app.ai_score:
                    skill_scores[skill].append(app.ai_score)
    
    # Calculate average scores per skill
    skill_analysis = []
    for skill, frequencies in skill_frequency.items():
        avg_score = sum(skill_scores[skill]) / len(skill_scores[skill]) if skill_scores[skill] else 0
        
        skill_analysis.append({
            'skill': skill,
            'frequency': frequencies,
            'avg_score': round(avg_score, 1),
            'proficiency': get_proficiency_level(avg_score, frequencies)
        })
    
    # Sort by frequency and score
    skill_analysis.sort(key=lambda x: (x['frequency'], x['avg_score']), reverse=True)
    
    return skill_analysis


def get_proficiency_level(score, frequency):
    """
    Determine proficiency level based on score and frequency
    """
    if score >= 80 and frequency >= 3:
        return 'Expert'
    elif score >= 70 and frequency >= 2:
        return 'Advanced'
    elif score >= 60:
        return 'Intermediate'
    else:
        return 'Beginner'


def get_application_timeline(user):
    """
    Get candidate's application timeline with status changes
    """
    from .models import Application
    applications = Application.objects.filter(
        candidate__user=user
    ).select_related('job').order_by('-applied_at')[:10]
    
    timeline = []
    for app in applications:
        timeline.append({
            'date': app.applied_at,
            'job_title': app.job.title,
            'company': app.job.recruiter.get_full_name() if app.job.recruiter else 'Unknown',
            'status': app.get_status_display(),
            'status_code': app.status,
            'score': app.ai_score or 0
        })
    
    return timeline


def get_saved_jobs(user):
    """
    Get jobs that match candidate's profile
    This is a placeholder for future saved jobs feature
    """
    from .recommendations import get_job_recommendations
    return get_job_recommendations(user, limit=5)


def get_candidate_statistics(user):
    """
    Get comprehensive candidate statistics
    """
    from .models import Application
    applications = Application.objects.filter(candidate__user=user)
    
    # Status distribution
    status_dist = {}
    for app in applications:
        status = app.get_status_display()
        status_dist[status] = status_dist.get(status, 0) + 1
    
    # Average AI score from applications
    from django.db.models import Avg
    avg_ai_score = applications.filter(ai_score__gt=0).aggregate(avg=Avg('ai_score'))['avg'] or 0
    
    # Get assessment scores from Assessment model
    from .models import Assessment
    assessments = Assessment.objects.filter(application__candidate__user=user)
    avg_r1 = assessments.filter(test_type='APTITUDE').aggregate(avg=Avg('score'))['avg'] or 0
    avg_r2 = assessments.filter(test_type='PRACTICAL').aggregate(avg=Avg('score'))['avg'] or 0
    
    # Get interview scores from Interview model
    from .models import Interview
    interviews = Interview.objects.filter(application__candidate__user=user, status='COMPLETED')
    avg_ai_interview = interviews.filter(interview_type='AI_BOT').aggregate(avg=Avg('ai_confidence_score'))['avg'] or 0
    avg_hr_interview = interviews.filter(interview_type='AI_HR').aggregate(avg=Avg('ai_confidence_score'))['avg'] or 0
    
    avg_scores = {
        'ai_score': round(avg_ai_score, 1),
        'round1_score': round(avg_r1, 1),
        'round2_score': round(avg_r2, 1),
        'ai_interview_score': round(avg_ai_interview, 1),
        'hr_interview_score': round(avg_hr_interview, 1),
    }
    
    return {
        'status_distribution': status_dist,
        'average_scores': avg_scores,
        'total_applications': applications.count(),
        'success_rate': calculate_success_rate(applications)
    }


def update_candidate_preferences(user, preferences):
    """
    Update candidate job preferences
    This is a placeholder for future preferences feature
    """
    # In a real implementation, this would update a CandidatePreferences model
    # For now, we'll just validate the preferences structure
    
    valid_keys = [
        'preferred_locations',
        'preferred_technologies',
        'min_salary',
        'max_salary',
        'job_types',
        'remote_preference'
    ]
    
    validated_prefs = {}
    for key in valid_keys:
        if key in preferences:
            validated_prefs[key] = preferences[key]
    
    return validated_prefs
