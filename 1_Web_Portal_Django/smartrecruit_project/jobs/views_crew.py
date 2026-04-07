from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Application, Assessment, Interview
from .crew_agents import run_hiring_committee
from .views_advanced import _recruiter_required

@login_required
def execute_virtual_committee_api(request, application_id):
    """
    Triggers the CrewAI Multi-Agent Hiring Committee.
    Aggregates data, runs the debate, saves the output, and returns it.
    """
    if not _recruiter_required(request):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    application = get_object_or_404(Application, id=application_id, job__recruiter=request.user)
    
    # 1. Gather Candidate Data
    candidate_name = application.candidate.full_name
    job_title = application.job.title
    required_skills = application.job.required_skills
    
    resume_summary = application.ai_insights if application.ai_insights else "No advanced resume insights available. Extracted skills: " + application.candidate.skills_extracted
    
    # 2. Gather Assessment Scores
    assessments = Assessment.objects.filter(application=application)
    assessment_scores = ""
    for score in assessments:
        assessment_scores += f"- {score.get_test_type_display()}: {score.score}/{score.max_score} (Passed: {score.passed})\n"
        
    if not assessment_scores:
        assessment_scores = "No technical assessments completed yet."
        
    # 3. Gather Interview Transcripts (Round 3 AI Interview)
    interviews = Interview.objects.filter(application=application, status='COMPLETED')
    interview_transcript = ""
    for interview in interviews:
        if interview.transcript:
            interview_transcript += f"[{interview.get_interview_type_display()}]\n{interview.transcript}\n\n"
            
    if not interview_transcript:
        interview_transcript = "No interview transcripts available."
        
    # 4. Trigger CrewAI
    report = run_hiring_committee(
        candidate_name=candidate_name,
        job_title=job_title,
        required_skills=required_skills,
        resume_summary=resume_summary,
        interview_transcript=interview_transcript,
        assessment_scores=assessment_scores
    )
    
    # 5. Save Report to Application
    application.ai_committee_report = report
    application.save()
    
    return JsonResponse({
        'success': True,
        'report': report
    })
