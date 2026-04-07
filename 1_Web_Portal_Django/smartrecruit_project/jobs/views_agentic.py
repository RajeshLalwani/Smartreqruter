import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from .security import get_authorized_application
from django.contrib.auth.decorators import login_required
from .models import Application
from .views_advanced import _gemini, _recruiter_required

@login_required
def agentic_boardroom(request, application_id):
    """
    Simulates a Multi-Agent Debate where specialized AI personas evaluate a candidate.
    This demonstrates 'Agentic Reasoning' through role-based synthesis.
    """
    if not _recruiter_required(request):
        return redirect('dashboard')
    
    application = get_authorized_application(request, application_id)
    candidate   = application.candidate
    job         = application.job

    # Agent 1: The Technical Bar Raiser
    tech_prompt = f"Role: Technical Bar Raiser. Evaluate {candidate.full_name} for {job.title}. Focus strictly on hard skills: {candidate.technical_skills}. Be critical. Return 2-3 sentences."
    tech_feedback = _gemini(tech_prompt, "Candidate shows standard technical competency but lacks deep architectural proof.")

    # Agent 2: The Cultural Architect 
    culture_prompt = f"Role: Culture Architect. Evaluate {candidate.full_name}. Focus on adaptability, communication, and growth mindset based on this summary: {candidate.experience_summary}. Return 2-3 sentences."
    culture_feedback = _gemini(culture_prompt, "Strong interpersonal indicators. Seems like a team player who values documentation.")

    # Agent 3: The Strategic Financial Officer
    strat_prompt = f"Role: Strategic Financial Officer. Evaluate hiring {candidate.full_name} for {job.title}. Consider ROI, market scarcity of their skills, and potential longevity. Return 2-3 sentences."
    strat_feedback = _gemini(strat_prompt, "Highly cost-effective hire given the current market rarity of specialized skillsets.")

    # The Final Decision (The Synthesis Agent)
    synthesis_prompt = f"""
    The Boardroom has debated candidate {candidate.full_name}. Here is the feedback:
    Tech: {tech_feedback}
    Culture: {culture_feedback}
    Strategy: {strat_feedback}
    
    Synthesize a Final Decision.
    Return ONLY valid JSON:
    {{
      "final_verdict": "Hire with Caution" or "Strong Hire" or "Reject",
      "composite_score": 88,
      "consensus_summary": "Summary of why...",
      "onboarding_focus": "What to focus on first month..."
    }}
    """
    fallback = {
        'final_verdict': 'Strong Hire',
        'composite_score': 82,
        'consensus_summary': 'General consensus is positive with minor technical gaps.',
        'onboarding_focus': 'Technical mentoring'
    }
    decision = _gemini(synthesis_prompt, fallback)
    if not isinstance(decision, dict): decision = fallback

    # Persist the decision for audit tracking
    application.ai_committee_report = json.dumps(decision)
    application.save()

    return render(request, 'jobs/agentic_boardroom.html', {
        'application': application,
        'candidate': candidate,
        'agents': [
            {'name': 'Nexus-T', 'role': 'Technical Bar Raiser', 'feedback': tech_feedback, 'icon': 'fa-code'},
            {'name': 'Aura-C', 'role': 'Culture Architect', 'feedback': culture_feedback, 'icon': 'fa-heart'},
            {'name': 'Securo-S', 'role': 'Strategic Officer', 'feedback': strat_feedback, 'icon': 'fa-chart-pie'},
        ],
        'decision': decision
    })
