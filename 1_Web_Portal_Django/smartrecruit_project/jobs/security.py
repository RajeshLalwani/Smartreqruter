from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from .models import Application

def get_authorized_application(request, application_id, require_role=None):
    """
    Fetches an Application securely by enforcing RBAC and verifying ownership.
    require_role: 'recruiter' (only recruiter access), 'candidate' (only candidate access), 
                  or None (either candidate or recruiter can access their own data).
    """
    application = get_object_or_404(Application, pk=application_id)
    
    # Identify if the user owns this record in the respective roles
    is_owner_recruiter = (request.user == application.job.recruiter)
    is_owner_candidate = (application.candidate and request.user == application.candidate.user)
    
    if require_role == 'recruiter' and not is_owner_recruiter:
        raise PermissionDenied("Only the job recruiter can access this application.")
    
    if require_role == 'candidate' and not is_owner_candidate:
        raise PermissionDenied("Only the candidate can access this application.")
        
    if not require_role and not (is_owner_recruiter or is_owner_candidate):
        raise PermissionDenied("You do not have permission to view this application.")
        
    return application
