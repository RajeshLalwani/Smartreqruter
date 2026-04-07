

# --- RESTORED VIEWS ---

@login_required
def recruiter_analytics(request):
    if not request.user.is_recruiter:
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    jobs = JobPosting.objects.filter(recruiter=request.user)
    total_jobs = jobs.count()
    active_jobs = jobs.filter(status='OPEN').count()
    
    applications = Application.objects.filter(job__in=jobs)
    total_applications = applications.count()
    shortlisted = applications.filter(status__in=['ROUND_1_PASSED', 'ROUND_2_PASSED', 'RESUME_SELECTED', 'SOURCED']).count()
    hired = applications.filter(status='HIRED').count()
    
    # Calculate Velocity (Avg days from Apply to Hire)
    from django.db.models import Avg, F
    velocity = applications.filter(status='HIRED').annotate(
         days=F('updated_at') - F('applied_at')
    ).aggregate(avg=Avg('days'))['avg']
    avg_velocity = velocity.days if velocity else "N/A"
    
    # Source ROI
    from django.db.models import Count
    sources = applications.values('source_of_hire').annotate(count=Count('id'))
    
    # Funnel Drop-off (AI Insights vs Manual)
    ai_rejected = applications.filter(status='RESUME_REJECTED').count()
    offer_rejected = applications.filter(status='OFFER_REJECTED').count()

    context = {
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'shortlisted': shortlisted,
        'hired': hired,
        'avg_velocity': avg_velocity,
        'sources': sources,
        'ai_rejected': ai_rejected,
        'offer_rejected': offer_rejected,
    }
    return render(request, 'jobs/recruiter_analytics.html', context)


@login_required
def interview_list(request):
    """
    Shows a list of all upcoming interviews for the recruiter OR the candidate.
    """
    if request.user.is_recruiter:
        # Fetch interviews for applications belonging to jobs posted by this recruiter
        interviews = Interview.objects.filter(
            application__job__recruiter=request.user,
            status='SCHEDULED'
        ).order_by('scheduled_time')
        
        pending_applications = Application.objects.filter(
            job__recruiter=request.user,
            status__in=['ROUND_1_PASSED', 'ROUND_2_PASSED']
        )
    else:
        interviews = Interview.objects.filter(
            candidate__user=request.user,
            status='SCHEDULED'
        ).order_by('scheduled_time')
        pending_applications = None
        
    return render(request, 'jobs/interview_list.html', {
        'interviews': interviews,
        'pending_applications': pending_applications
    })


@login_required
def interview_calendar(request):
    """
    Renders the FullCalendar page for recruiters.
    """
    if not request.user.is_recruiter:
        messages.error(request, "Access denied. Recruiters only.")
        return redirect('dashboard')
        
    return render(request, 'jobs/calendar.html')


@login_required
def calendar_api(request):
    """
    Returns JSON data for FullCalendar showing all scheduled interviews.
    """
    if not request.user.is_recruiter:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    interviews = Interview.objects.filter(
        application__job__recruiter=request.user,
        status='SCHEDULED'
    )
    
    events = []
    for interview in interviews:
        end_time = interview.scheduled_time + timezone.timedelta(hours=1)
        events.append({
            'id': interview.id,
            'title': f"Interview: {interview.candidate.full_name} ({interview.application.job.title})",
            'start': interview.scheduled_time.isoformat(),
            'end':   end_time.isoformat(),
            'url':   f"/jobs/application/{interview.application.id}/",
            'backgroundColor': '#6366f1',
            'borderColor': '#4f46e5',
            'textColor': 'white'
        })
        
    return JsonResponse(events, safe=False)


@login_required
def kanban_view(request, job_id=None):
    if not request.user.is_recruiter:
         messages.error(request, "Access denied.")
         return redirect('dashboard')
         
    jobs = JobPosting.objects.filter(recruiter=request.user)
    if job_id:
        selected_job = get_object_or_404(JobPosting, id=job_id, recruiter=request.user)
    else:
        selected_job = jobs.first()
        
    columns = {
        'SOURCED': [],
        'APPLIED': [],
        'SCREENED': [],
        'INTERVIEW': [],
        'OFFERED': [],
        'HIRED': []
    }
    
    if selected_job:
        apps = Application.objects.filter(job=selected_job).select_related('candidate')
        for app in apps:
            # Sourced phase
            if app.status == 'SOURCED':
                columns['SOURCED'].append(app)
            # Application received phase (pre-AI or failed AI but still active)
            elif app.status in ['RESUME_SCREENING']:
                columns['APPLIED'].append(app)
            # AI Screened and Passed
            elif app.status in ['RESUME_SELECTED', 'ROUND_1_PASSED']:
                columns['SCREENED'].append(app)
            # Interview phase
            elif app.status in ['ROUND_2_PASSED', 'FINAL_SELECTED']:
                columns['INTERVIEW'].append(app)
            # Offer Phase
            elif app.status in ['OFFER_SENT', 'OFFER_ACCEPTED']:
                columns['OFFERED'].append(app)
            # Hired
            elif app.status == 'HIRED':
                columns['HIRED'].append(app)

    return render(request, 'jobs/kanban_board.html', {
        'jobs': jobs,
        'selected_job': selected_job,
        'columns': columns
    })


from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@login_required
def kanban_update_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            app_id = data.get('application_id')
            new_stage = data.get('new_stage')
            
            application = get_object_or_404(Application, id=app_id, job__recruiter=request.user)
            
            # Map canonical UI stages to underlying Database status
            status_map = {
                'SOURCED': 'SOURCED',
                'APPLIED': 'RESUME_SCREENING',
                'SCREENED': 'RESUME_SELECTED',
                'INTERVIEW': 'ROUND_2_PASSED',
                'OFFERED': 'OFFER_SENT',
                'HIRED': 'HIRED'
            }
            
            if new_stage in status_map:
                application.status = status_map[new_stage]
                application.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid stage'})
                
        except Exception as e:
             return JsonResponse({'success': False, 'error': str(e)})
             
    return JsonResponse({'success': False, 'error': 'Invalid Request'})
