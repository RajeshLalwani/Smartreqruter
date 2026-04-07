import json
from django.shortcuts import render, get_object_or_404, redirect
from .security import get_authorized_application
from django.contrib.auth.decorators import login_required
from .models import Application
from .views_advanced import _gemini, _recruiter_required

@login_required
def generative_lab_challenge(request, application_id):
    """
    The 'Assessment Lab' generates a one-of-a-kind coding challenge 
    based on the candidate's public project footprint or primary stack.
    """
    application = get_authorized_application(request, application_id)
    candidate   = application.candidate
    
    # Check if a lab result already exists in session to prevent regeneration
    session_key = f'lab_challenge_{application_id}'
    lab_data = request.session.get(session_key)
    
    if not lab_data:
        # Contextual prompt for the AI Lab Engineer
        public_context = candidate.github_url if candidate.github_url else f"Skills: {candidate.skills_extracted}"
        
        prompt = f"""
        Role: AI Lab Architect.
        Context: Candidate {candidate.full_name} is being evaluated for {application.job.title}.
        Public Project Pointer: {public_context}
        
        Task: Create a HYPER-PERSONALIZED coding challenge.
        If they have a GitHub URL, pretend you've analyzed their Top Repo and found a hypothetical architectural flaw.
        If not, create a challenge based on their primary skills.
        
        Challenge Type: Bug Fix / Refactoring of a specific complex function.
        
        Return ONLY valid JSON:
        {{
          "lab_id": "LAB-DYN-X7",
          "title": "Decoupling Service Logic",
          "scenario": "While reviewing your project [Project Name], I noticed a tight coupling in the database layer.",
          "task": "Refactor the provided 'OrderService' to use a Repository Pattern and implement a basic retry mechanism for transient failures.",
          "starting_code": "class OrderService:\\n    def create_order(self, data):\\n        # High-coupling code here...",
          "test_cases": ["Should handle DB timeout", "Should not duplicate orders"]
        }}
        """
        fallback = {
            'lab_id': 'LAB-DYN-GENERIC',
            'title': 'System Design Implementation',
            'scenario': 'Your profile indicates strong Python skills. We need you to implement a rate-limiter.',
            'task': 'Implement a sliding-window rate limiter using Redis (mocked) or a local dict.',
            'starting_code': 'class RateLimiter:\n    def is_allowed(self, user_id):\n        pass',
            'test_cases': ['Allow 5 req/sec', 'Block 6th req']
        }
        lab_data = _gemini(prompt, fallback)
        if not isinstance(lab_data, dict): lab_data = fallback
        
        request.session[session_key] = lab_data
        request.session.modified = True

    return render(request, 'jobs/assessment_lab.html', {
        'application': application,
        'lab': lab_data
    })

@login_required
def submit_lab_solution(request, application_id):
    """
    Submits the Assessment Lab solution and uses AI to grade it.
    Updates the application status based on the AI feedback.
    """
    application = get_authorized_application(request, application_id)
    
    if request.method == 'POST':
        try:
            solution_code = request.POST.get('lab_solution', '').strip()
            lab_data = request.session.get(f'lab_challenge_{application_id}', {})
            
            if not solution_code:
                messages.error(request, "Please provide a solution before submitting.")
                return redirect('generative_lab_challenge', application_id=application_id)

            ai = AIEngine()
            prompt = f"""
            Grade this coding challenge solution.
            Challenge Title: {lab_data.get('title')}
            Challenge Task: {lab_data.get('task')}
            Candidate Solution:
            {solution_code}
            
            Return ONLY a valid JSON object:
            {{
              "score": <0-100>,
              "feedback": "Concise technical feedback",
              "passed": <true/false>
            }}
            """
            
            response_text = ai.generate(prompt=prompt)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            grade = json.loads(response_text.strip())
            
            # Save results (you might want a specific model for this, but let's use the session/message for now)
            # Or update application status
            if grade.get('passed'):
                application.status = 'Assessment Lab Passed'
                messages.success(request, f"Lab Evaluation Complete! Score: {grade.get('score')}%. Feedback: {grade.get('feedback')}")
            else:
                messages.warning(request, f"Lab Evaluation Complete. Score: {grade.get('score')}%. You didn't meet the passing criteria.")
            
            application.save()
            return redirect('dashboard')
            
        except Exception as e:
            logger.error(f"[LabSubmit] AI Error: {e}")
            messages.error(request, "Evaluation engine error. Please try again.")
            return redirect('generative_lab_challenge', application_id=application_id)
            
    return redirect('generative_lab_challenge', application_id=application_id)
