import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from .security import get_authorized_application
from django.contrib.auth.decorators import login_required
from .models import Application
from .views_advanced import _gemini

def candidate_offer_portal(request, application_id):
    """
    A hyper-personalized landing page for hired candidates.
    Uses AI to craft a welcome message based on their specific strengths.
    """
    application = get_authorized_application(request, application_id)
    candidate   = application.candidate
    job         = application.job

    # AI Personalization
    prompt = f"""
    Candidate {candidate.full_name} has just been offered the role of {job.title}.
    Their top strengths identified in the interview: {candidate.technical_skills}.
    They will be joining the 'Engineering Excellence' team.
    
    Craft a hyper-personalized, high-energy 'Welcome' message.
    Include:
    1. A personal greeting.
    2. Why we chose them (mention a specific skill like {random.choice(candidate.skills_list)}).
    3. What they will achieve in their first 90 days.
    
    Return ONLY valid JSON:
    {{
      "headline": "Welcome to the Future, [Name]",
      "welcome_message": "...",
      "team_vibe": "Collaborative, fast-paced, and coffee-fueled.",
      "first_30_days_goal": "Mastering our distributed systems architecture."
    }}
    """
    fallback = {
        'headline': f"Welcome to the Team, {candidate.full_name}!",
        'welcome_message': f"We are thrilled to have you join us as a {job.title}. Your expertise in {candidate.technical_skills} stood out to everyone on the panel.",
        'team_vibe': "Innovative & Collaborative",
        'first_30_days_goal': "System integration and team syncing."
    }
    content = _gemini(prompt, fallback)
    if not isinstance(content, dict): content = fallback

    return render(request, 'jobs/offer_portal.html', {
        'application': application,
        'candidate': candidate,
        'job': job,
        'content': content
    })
