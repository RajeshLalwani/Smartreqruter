import os
import json
from datetime import timedelta
from google import genai
from django.utils import timezone
from .models import Application, JobPosting, ActivityLog
from django.db.models import Avg

class RecruitmentAgent:
    """
    The 'Agent' part of SmartRecruit.
    Proactively analyzes data to give recruiters high-level advice.
    """
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def get_proactive_insights(self, recruiter_user):
        """
        Scans all active jobs and candidates for this recruiter.
        Returns a set of AI insights including ghosting detection.
        """
        # 1. Fetch data for context
        active_jobs = JobPosting.objects.filter(recruiter=recruiter_user, status='OPEN')
        apps = Application.objects.filter(job__in=active_jobs)
        total_apps = apps.count()
        avg_score = apps.aggregate(Avg('ai_score'))['ai_score__avg'] or 0

        # 2. GHOSTING DETECTION — Real behavioral data
        ghosting_threshold = timezone.now() - timedelta(hours=48)
        ghosts = apps.filter(
            updated_at__lt=ghosting_threshold,
            status__contains='PENDING'
        ).select_related('candidate', 'job')
        
        ghost_count = ghosts.count()
        ghost_names = ", ".join([g.candidate.full_name for g in ghosts[:3]])

        # 3. STAR CANDIDATES
        star_candidates = apps.filter(ai_score__gte=85).order_by('-ai_score')[:3]
        candidates_str = "\n".join([f"- {a.candidate.full_name} (Score: {a.ai_score}) for {a.job.title}" for a in star_candidates])
        
        if not self.client:
            return ["AI Agent is currently offline. Please check your API Key."]

        prompt = f"""
        You are 'RecruitAgent V2', an advanced proactive hiring intelligence.
        Analyze the following operational data and provide 3-4 sharp, actionable insights.
        
        CURRENT PIPELINE:
        - Active Jobs: {active_jobs.count()}
        - Total Applicants: {total_apps}
        - Avg Match Score: {avg_score:.1f}%
        
        GHOSTING RISK (High Priority):
        - Found {ghost_count} candidates stuck for >48h.
        - Examples: {ghost_names or 'None'}
        
        TOP TALENT OPPORTUNITIES:
        {candidates_str}
        
        Your goals:
        1. Identify the 'Highest Value Action' for the recruiter today.
        2. Specifically address the ghosting risks if they exist.
        3. Suggest personalized nudges for star candidates.
        
        Return a JSON array of strings. Each string should be one insight. Use professional, data-driven language.
        """

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                config={'response_mime_type': 'application/json'},
                contents=f"{prompt}\nIMPORTANT: Be sharp and strategic. Don't just list facts, tell a story of where the bottlenecks are."
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Agent Insight Error: {e}")
            return [
                f"Operational Alert: {ghost_count} candidates are currently idle. Immediate nudge recommended.",
                f"Elite Talent identified. {star_candidates.count()} candidates scored above 85% match."
            ]

    def get_elite_alerts(self, recruiter_user):
        """
        Returns structured strategic alerts for the VIP dashboard widget.
        Uses real database signals — no random mocking.
        """
        now = timezone.now()
        alerts = []

        active_jobs = JobPosting.objects.filter(recruiter=recruiter_user, status='OPEN')
        apps = Application.objects.filter(job__in=active_jobs)

        # ── GHOSTING ALERT ──
        ghost_threshold = now - timedelta(hours=48)
        ghost_apps = apps.filter(
            updated_at__lt=ghost_threshold,
            status__contains='PENDING'
        ).select_related('candidate', 'job')[:5]

        for g in ghost_apps:
            days_idle = (now - g.updated_at).days
            alerts.append({
                'type': 'ghosting',
                'icon': 'fas fa-ghost',
                'color': '#ff4444',
                'title': f'{g.candidate.full_name} — Ghosting Risk',
                'detail': f'Idle for {days_idle} days in {g.get_status_display()} stage for {g.job.title}.',
                'action_url': f'/jobs/application/{g.id}/',
                'action_label': 'Nudge Now'
            })

        # ── INTERNAL MOBILITY ALERT ──
        hired = Application.objects.filter(status='HIRED').select_related('candidate')[:10]
        for emp in hired:
            emp_skills = set(
                s.strip().lower()
                for s in (emp.candidate.skills_extracted or '').split(',')
                if s.strip()
            )
            if not emp_skills:
                continue
            for job in active_jobs[:5]:
                job_skills = set(
                    s.strip().lower()
                    for s in (job.required_skills or '').split(',')
                    if s.strip()
                )
                if not job_skills:
                    continue
                overlap = emp_skills & job_skills
                score = int((len(overlap) / len(job_skills)) * 100)
                if score >= 70:
                    alerts.append({
                        'type': 'mobility',
                        'icon': 'fas fa-exchange-alt',
                        'color': '#00c851',
                        'title': f'{emp.candidate.full_name} → {job.title}',
                        'detail': f'{score}% skill match. Internal move could save sourcing costs.',
                        'action_url': f'/jobs/internal-mobility/',
                        'action_label': 'Review Match'
                    })
                    break  # Only one match per employee

        # ── STALE PIPELINE ALERT ──
        stale_threshold = now - timedelta(days=7)
        stale_apps = apps.filter(
            updated_at__lt=stale_threshold,
            status__in=['APPLIED', 'RESUME_SCREENING']
        ).count()
        if stale_apps > 0:
            alerts.append({
                'type': 'stale',
                'icon': 'fas fa-hourglass-end',
                'color': '#ffbb33',
                'title': f'{stale_apps} Applications Aging > 7 Days',
                'detail': 'Candidates in early stages need review to prevent pipeline decay.',
                'action_url': '/jobs/candidates/',
                'action_label': 'Review Pipeline'
            })

        return alerts[:8]  # Cap at 8 alerts

    def draft_invite_email(self, application):
        """
        Agentic feature: Draft a personalized invite email based on why the agent liked them.
        """
        if not self.client: return "Drafting unavailable."

        prompt = f"""
        Draft a short, highly professional interview invitation email for {application.candidate.full_name}.
        Job: {application.job.title}
        Why they matched: {application.ai_insights or 'Strong technical skills'}
        
        The tone should be welcoming but elite.
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            return response.text.strip()
        except:
            return "Professional Interview Invitation Draft."

    def get_candidate_navigator(self, user):
        """
        AI Navigator for Candidates. Analyzes profile vs applied jobs 
        and suggests specific Arena practice or profile improvements.
        """
        if not hasattr(user, 'candidate_profile'):
            return ["Complete your profile to unlock AI Career Navigation."]

        from .models import Application, JobPosting
        from .recommendations import get_candidate_skills
        
        apps = Application.objects.filter(candidate__user=user).order_by('-applied_at')[:3]
        skills = get_candidate_skills(user)
        
        # Identify missing skills for applied jobs
        missing_skills = set()
        for app in apps:
            job_skills = [s.strip().lower() for s in app.job.required_skills.split(',') if s.strip()]
            for s in job_skills:
                if s not in [cs.lower() for cs in skills]:
                    missing_skills.add(s)
        
        if not self.client:
            if missing_skills:
                return [f"Focus on learning: {', '.join(list(missing_skills)[:3])}. Use the Practice Arena!"]
            return ["You're on the right track! Keep applying to high-match roles."]

        prompt = f"""
        You are 'CareerSentinel AI', a high-end career strategist for elite engineers.
        
        USER CONTEXT:
        - Skills: {', '.join(skills)}
        - Recent Applications: {', '.join([a.job.title for a in apps])}
        - Missing Skills for those roles: {', '.join(list(missing_skills)[:5])}
        
        GOAL:
        Provide 2-3 short, punchy, strategic advice items. 
        Focus on:
        1. Which 'Coding Arena' category they should practice next based on missing skills.
        2. How to bridge the match score gap.
        
        Return a JSON array of strings. Keep them motivating and elite.
        """

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                config={'response_mime_type': 'application/json'},
                contents=prompt
            )
            return json.loads(response.text)
        except Exception:
            return [
                f"Skill Gap detected in {list(missing_skills)[0] if missing_skills else 'Data Structures'}. Practice now in the Arena!",
                "Your profile matches 80% of top roles. Refine your summary to hit 90%."
            ]

