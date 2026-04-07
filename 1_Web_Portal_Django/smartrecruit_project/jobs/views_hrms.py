from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Application

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_hired_candidates_api(request):
    """
    Enterprise HRMS Integration API Endpoint.
    Returns a secure JSON list of candidates who are marked as HIRED or OFFER_ACCEPTED.
    Requires Standard Token Authentication.
    """
    if not (request.user.is_superuser or getattr(request.user, 'is_recruiter', False)):
        return JsonResponse({"detail": "Recruiter access required."}, status=403)

    # Specifically target candidates ready for HRMS ingestion
    applications = Application.objects.filter(
        status__in=['HIRED', 'OFFER_ACCEPTED']
    ).select_related('candidate', 'job')

    if not request.user.is_superuser:
        applications = applications.filter(job__recruiter=request.user)
    
    # Optional parameters for filtering
    job_id = request.GET.get('job_id')
    if job_id:
        applications = applications.filter(job_id=job_id)
        
    start_date = request.GET.get('start_date')
    if start_date:
        applications = applications.filter(updated_at__gte=start_date)
        
    results = []
    for app in applications:
        candidate_data = {
            "application_id": app.id,
            "status": app.status,
            "last_updated": app.updated_at.isoformat(),
            "candidate": {
                "name": app.candidate.full_name,
                "email": app.candidate.email,
                "phone": app.candidate.phone,
                "experience_years": app.candidate.experience_years,
                "current_location": app.candidate.current_location,
                "skills_extracted": app.candidate.skills_extracted,
                "resume_url": request.build_absolute_uri(app.candidate.resume_file.url) if app.candidate.resume_file else None,
            },
            "job": {
                "id": app.job.id,
                "title": app.job.title,
                "department": getattr(app.job, 'department', 'N/A'),
                "location": app.job.location,
                "job_type": app.job.job_type,
            }
        }
        
        # Add offer details if present
        if hasattr(app, 'offer_letter'):
            candidate_data["offer"] = {
                "salary_offered": app.offer_letter.salary_offered,
                "designation": app.offer_letter.designation,
                "joining_date": str(app.offer_letter.joining_date) if app.offer_letter.joining_date else None,
            }
            
        results.append(candidate_data)

    return JsonResponse({
        "count": len(results),
        "results": results
    })
