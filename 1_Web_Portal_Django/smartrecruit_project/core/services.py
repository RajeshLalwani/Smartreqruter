from django.utils import timezone
from django.db.models import Avg, Count, Q
from jobs.models import Application, JobPosting, Interview, ActivityLog, ATSSyncLog
from jobs.recommendations import get_job_recommendations

class DashboardService:
    @staticmethod
    def get_candidate_context(user):
        """
        Prepares context data for the Candidate Dashboard with analytical stats.
        """
        from jobs.models import Application, JobPosting, Interview
        
        # 1. Applications & Stats
        my_applications = Application.objects.filter(candidate__user=user).order_by('-applied_at')
        
        stats = {
            'total_applied': my_applications.count(),
            'active': my_applications.filter(status__in=['APPLIED', 'RESUME_SELECTED', 'ROUND_1_PASSED', 'ROUND_2_PASSED', 'ROUND_3_PASSED']).count(),
            'interviews': Interview.objects.filter(application__candidate__user=user, status='SCHEDULED').count(),
            'offers': my_applications.filter(status='OFFER_GENERATED').count(),
        }

        # 2. Upcoming Interviews
        upcoming_interviews = Interview.objects.filter(
            application__candidate__user=user, 
            status='SCHEDULED',
            scheduled_time__gte=timezone.now()
        ).order_by('scheduled_time')[:3]

        # 3. Smart Recommendations (Elite Matching Engine)
        recommended_jobs = get_job_recommendations(user, limit=6)
        
        # 4. Market Standing & Skill Readiness (Strategic Insights)
        # Average AI Score for the most applied category/job to see where they stand
        market_standing = 0
        if my_applications.exists():
            top_job = my_applications.first().job
            market_standing = Application.objects.filter(job=top_job).aggregate(Avg('ai_score'))['ai_score__avg'] or 0
        
        # Skill overlap for top trending skills in their tech stack
        skill_readiness = 0
        if hasattr(user, 'candidate_profile'):
            from jobs.recommendations import get_candidate_skills
            candidate_skills = get_candidate_skills(user)
            # Find common skills in jobs they applied to or are recommended
            target_skills = set()
            for rec in recommended_jobs:
                target_skills.update(rec['job'].skills_list)
            
            if target_skills:
                match_count = sum(1 for s in target_skills if s.lower() in [cs.lower() for cs in candidate_skills])
                skill_readiness = int((match_count / len(target_skills)) * 100)

        from django.conf import settings
        auto_send_feedback = getattr(settings, 'AUTO_SEND_FEEDBACK_TO_CANDIDATE', False)

        return {
            'user': user,
            'today_date': timezone.now(),
            'my_applications': my_applications,
            'stats': stats,
            'upcoming_interviews': upcoming_interviews,
            'recent_jobs': recommended_jobs,
            'market_standing': round(market_standing, 1),
            'skill_readiness': skill_readiness,
            'auto_send_feedback': auto_send_feedback,
        }

    @staticmethod
    def get_recruiter_context(user):
        """
        Prepares context data for the Recruiter Dashboard.
        """
        # Stats
        active_jobs = JobPosting.objects.select_related('recruiter').filter(recruiter=user, status='OPEN')
        recent_jobs = active_jobs.order_by('-created_at')[:5]
        total_jobs = active_jobs.count()
        
        # Candidates for THIS recruiter's jobs
        recruiter_apps = Application.objects.select_related('candidate', 'job', 'candidate__user').filter(job__recruiter=user)
        total_candidates = recruiter_apps.count()
        
        # Interviews
        recruiter_interviews = Interview.objects.select_related('application', 'application__candidate').filter(application__job__recruiter=user)
        total_interviews = recruiter_interviews.filter(status='SCHEDULED').count()
        flagged_sessions = recruiter_interviews.filter(is_flagged=True).count()
        
        # Urgent Job (Nearest deadline)
        urgent_job = active_jobs.filter(deadline__gte=timezone.now()).order_by('deadline').first()
        
        # 3. Hiring Velocity (Avg Days to Move)
        # Calculate delta between APPLIED and HIRED/OFFER_ACCEPTED for history
        avg_velocity = 0
        closed_apps = recruiter_apps.filter(status__in=['HIRED', 'OFFER_ACCEPTED', 'OFFER_REJECTED'])
        if closed_apps.exists():
            days_sum = 0
            for app in closed_apps:
                delta = app.updated_at - app.applied_at
                days_sum += delta.days
            avg_velocity = days_sum / closed_apps.count()

        # 4. Sourcing Mix (Distribution)
        sourcing_mix = recruiter_apps.values('source_of_hire').annotate(count=Count('id')).order_by('-count')
        
        # 5. Activity Log
        recent_activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')[:10]

        # 6. Pipeline Data (Funnel)
        pipeline_data = {
            'screening': recruiter_apps.filter(status='APPLIED').count(),
            'assessment': recruiter_apps.filter(status__in=['RESUME_SELECTED', 'ROUND_1_PASSED']).count(),
            'interview': recruiter_apps.filter(status__in=['ROUND_2_PASSED', 'ROUND_3_PASSED']).count(),
            'offered': recruiter_apps.filter(status='OFFER_GENERATED').count()
        }

        # 7. Sentiment Pulse (Phase 3 Integration)
        from jobs.models import SentimentLog
        sentiment_metrics = SentimentLog.objects.filter(interview__in=recruiter_interviews).aggregate(
            avg_score=Avg('score'),
            count=Count('id')
        )
        
        dominant_emotion_data = SentimentLog.objects.filter(interview__in=recruiter_interviews).values('emotion').annotate(
            count=Count('emotion')
        ).order_by('-count').first()
        
        avg_sentiment = int((sentiment_metrics['avg_score'] or 0) * 100)
        dominant_emotion = (dominant_emotion_data['emotion'] or 'Neutral').capitalize() if dominant_emotion_data else 'Neutral'
        
        # 8. Turnover Prediction Data (Phase 7 Integration)
        from jobs.models import TurnoverPrediction
        from core.utils.analytics_engine import RetentionAnalyticsEngine
        
        # Trigger predictive run for recent applicants if not already done
        for app in recruiter_apps.order_by('-applied_at')[:10]:
            if not TurnoverPrediction.objects.filter(candidate=app.candidate).exists():
                RetentionAnalyticsEngine.run_prediction(app.candidate)
        
        predictions = TurnoverPrediction.objects.filter(
            candidate__applications__job__recruiter=user
        ).distinct().order_by('-retention_score')
        
        at_risk_candidates = predictions.filter(retention_score__lte=50)[:5]
        stable_candidates = predictions.filter(retention_score__gte=80)[:5]
        
        # Get the very latest prediction for the radar chart (fallback or featured)
        featured_prediction = predictions.first()

        # 9. ATS Sync Health (Phase 12 Integration)
        last_sync = ATSSyncLog.objects.filter(application__job__recruiter=user).first()
        sync_logs = ATSSyncLog.objects.filter(application__job__recruiter=user)[:5]

        return {
            'user': user,
            'today_date': timezone.now(),
            'recent_jobs': recent_jobs,
            'total_jobs': total_jobs,
            'total_candidates': total_candidates,
            'total_interviews': total_interviews,
            'urgent_job': urgent_job,
            'recent_activities': recent_activities,
            'recruiter_apps': recruiter_apps.order_by('-ai_score')[:20],
            'flagged_sessions': flagged_sessions,
            'pipeline_screening': pipeline_data['screening'],
            'pipeline_assessment': pipeline_data['assessment'],
            'pipeline_interview': pipeline_data['interview'],
            'pipeline_offered': pipeline_data['offered'],
            'total_offers': pipeline_data['offered'],
            'avg_velocity': round(avg_velocity, 1),
            'sourcing_mix': list(sourcing_mix),
            'avg_sentiment': avg_sentiment,
            'dominant_emotion': dominant_emotion,
            'sentiment_count': sentiment_metrics['count'] or 0,
            # Phase 7
            'at_risk_candidates': at_risk_candidates,
            'stable_candidates': stable_candidates,
            'featured_prediction': featured_prediction,
            # Phase 12
            'last_sync': last_sync,
            'sync_logs': sync_logs,
        }
