import logging
from django.utils import timezone
from django.db.models import Sum, F
from jobs.models import Badge, Candidate, Application, Assessment, Interview, SentimentLog

logger = logging.getLogger(__name__)

def check_assessment_milestones(candidate, assessment, request=None):
    """
    Checks and awards badges related to Aptitude and Practical assessments.
    """
    # 1. "Speed Demon": Solve code in < 40% time
    if assessment.test_type == 'PRACTICAL' and assessment.time_taken:
        # Assuming job.time_limit_r2 is in minutes
        time_limit_seconds = assessment.application.job.time_limit_r2 * 60
        time_taken_seconds = assessment.time_taken.total_seconds()
        
        if time_taken_seconds < (0.4 * time_limit_seconds):
            award_badge(candidate, "Speed Demon", request=request)

    # 2. "First Blood": Complete the first tier with 100% accuracy
    if assessment.test_type == 'APTITUDE' and assessment.score >= 100:
        award_badge(candidate, "First Blood", request=request)

def check_interview_milestones(candidate, interview, request=None):
    """
    Checks and awards badges related to AI interviews.
    """
    # 3. "Zen Master": Complete an interview with zero "Stressed" sentiment flags
    from jobs.models import SentimentLog
    stressed_logs = SentimentLog.objects.filter(interview=interview, emotion='stressed').count()
    
    if stressed_logs == 0:
        award_badge(candidate, "Zen Master", request=request)

def award_badge(candidate, badge_name, request=None):
    """
    Safely awards a badge to a candidate if they don't already have it.
    """
    try:
        badge = Badge.objects.get(name=badge_name)
        if badge not in candidate.earned_badges.all():
            candidate.earned_badges.add(badge)
            logger.info(f"🏆 Achievement Unlocked: {badge_name} for {candidate.full_name}")
            
            if request:
                from django.contrib import messages
                # Specialized tag for 'Thunder Toast'
                messages.success(request, f"ACHIEVEMENT_UNLOCKED|{badge.name}|{badge.icon_class}|{badge.rarity}", extra_tags='gamification')
            return True
    except Badge.DoesNotExist:
        logger.warning(f"Badge '{badge_name}' does not exist in the database.")
    return False

def get_leaderboard_data():
    """
    Calculates rankings based on Technical Score + Sentiment Points + Speed Bonus.
    """
    candidates = Candidate.objects.all()
    leaderboard = []
    
    for candidate in candidates:
        # Aggregate scores from all applications
        apps = Application.objects.filter(candidate=candidate)
        total_tech_score = apps.aggregate(total=Sum('ai_score'))['total'] or 0
        
        # Sentiment Points (e.g., number of 'happy' logs)
        sentiment_points = SentimentLog.objects.filter(interview__application__candidate=candidate, emotion='happy').count() * 5
        
        # Speed Bonus (from assessment details)
        speed_bonus = 0
        assessments = Assessment.objects.filter(application__candidate=candidate)
        for ass in assessments:
            if isinstance(ass.details, dict):
                speed_bonus += ass.details.get('speed_bonus', 0)
        
        aggregate_score = total_tech_score + sentiment_points + speed_bonus
        
        # Privacy: Use Pseudonym
        display_name = candidate.pseudonym if candidate.pseudonym else f"CyberRunner_{candidate.id}"
        
        leaderboard.append({
            'name': display_name,
            'score': aggregate_score,
            'badges_count': candidate.earned_badges.count(),
            'rank': 0 # Will be set after sorting
        })
    
    # Sort by score descending
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry['rank'] = i + 1
        
    return leaderboard[:10] # Top 10
