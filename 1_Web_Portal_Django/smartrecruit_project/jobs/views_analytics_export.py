import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Application

@login_required # Should be recruiter only
def export_candidates_csv(request):
    """
    Export candidate data to CSV for the recruiter's jobs.
    """
    if not (request.user.is_recruiter or request.user.is_superuser):
        return HttpResponse("Unauthorized", status=403)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="candidates_export.csv"'

    writer = csv.writer(response)
    # Header
    writer.writerow(['Candidate Name', 'Email', 'Applied For', 'Status', 'AI Score', 'Applied Date'])

    # Data
    applications = Application.objects.filter(job__recruiter=request.user).select_related('candidate', 'job')
    
    for app in applications:
        writer.writerow([
            app.candidate.full_name,
            app.candidate.email,
            app.job.title,
            app.get_status_display(),
            app.ai_score,
            app.applied_at.strftime("%Y-%m-%d %H:%M")
        ])

    return response

# =========================================
# ANALYTICS API & EXPORTS
# =========================================
from django.http import JsonResponse
from django.db.models import Count
from .models import JobPosting

@login_required
def analytics_api(request):
    """
    API to provide data for Dashboard Charts (Chart.js)
    """
    if not (request.user.is_recruiter or request.user.is_superuser):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    # 1. Pipeline Data (Funnel)
    # Applications by Status
    pipeline_data = list(Application.objects.filter(job__recruiter=request.user)
                         .values('status')
                         .annotate(count=Count('id'))
                         .order_by('status'))
    
    # Map status codes to readable labels if needed, or do it in JS
    
    # 2. Technology Distribution
    tech_data = list(JobPosting.objects.filter(recruiter=request.user)
                     .values('technology_stack')
                     .annotate(count=Count('id')))
                     
    return JsonResponse({
        'pipeline': pipeline_data,
        'tech_distribution': tech_data
    })

@login_required
def export_analytics_csv_view(request):
    """
    Export Comprehensive Analytics Data to CSV.
    Uses the same aggregation logic as the dashboard.
    """
    if not (request.user.is_recruiter or request.user.is_superuser):
        return HttpResponse("Unauthorized", status=403)

    # Date Filters from GET
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    from .utils_analytics import get_analytics_context
    data = get_analytics_context(request.user, start_date, end_date)

    response = HttpResponse(content_type='text/csv')
    filename = f"analytics_report_{start_date or 'all'}_{end_date or 'all'}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    
    # 1. SUMMARY
    writer.writerow(['--- SUMMARY METRICS ---'])
    writer.writerow(['Metric', 'Value'])
    for k, v in data['summary'].items():
        writer.writerow([k.replace('_', ' ').title(), v])
    writer.writerow([])

    # 2. FUNNEL
    writer.writerow(['--- HIRING FUNNEL ---'])
    writer.writerow(['Stage', 'Count'])
    for k, v in data['simplified_funnel'].items():
        writer.writerow([k, v])
    writer.writerow([])

    # 3. PASS RATES
    writer.writerow(['--- PASS RATES (%) ---'])
    writer.writerow(['Round', 'Pass Rate'])
    for k, v in data['pass_rates'].items():
        writer.writerow([k, f"{v}%"])
    writer.writerow([])

    # 4. SOURCE OF HIRE
    writer.writerow(['--- SOURCE OF HIRE ---'])
    writer.writerow(['Source', 'Count'])
    for k, v in data['source_data'].items():
        writer.writerow([k, v])
    writer.writerow([])
    
    # 5. LOCATIONS
    writer.writerow(['--- TOP LOCATIONS ---'])
    writer.writerow(['Location', 'Count'])
    for k, v in data['location_data'].items():
        writer.writerow([k, v])
    writer.writerow([])
    
    return response

@login_required
def export_analytics_pdf_view(request):
    """
    Renders a print-friendly HTML page for analytics, 
    intended to be saved as PDF via browser print.
    """
    if not (request.user.is_recruiter or request.user.is_superuser):
        return HttpResponse("Unauthorized", status=403)
        
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    from .utils_analytics import get_analytics_context
    data = get_analytics_context(request.user, start_date, end_date)
    
    html = f"""
    <html>
    <head>
        <title>Recruitment Analytics Report</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            h1, h2 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .metric-card {{ border: 1px solid #eee; padding: 15px; margin-bottom: 10px; break-inside: avoid; }}
        </style>
    </head>
    <body onload="window.print()">
        <h1>Recruitment Analytics Report</h1>
        <p>Generated on: {request.GET.get('start_date', 'All Time')} to {request.GET.get('end_date', 'Present')}</p>
        
        <h2>Summary Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            {''.join(f'<tr><td>{k.replace("_", " ").title()}</td><td>{v}</td></tr>' for k, v in data['summary'].items())}
        </table>
        
        <h2>Hiring Funnel</h2>
        <table>
            <tr><th>Stage</th><th>Count</th></tr>
            {''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in data['simplified_funnel'].items())}
        </table>
        
        <h2>Pass Rates</h2>
        <table>
            <tr><th>Round</th><th>Rate</th></tr>
            {''.join(f'<tr><td>{k}</td><td>{v}%</td></tr>' for k, v in data['pass_rates'].items())}
        </table>
        
        <h2>Source of Hire</h2>
        <table>
            <tr><th>Source</th><th>Count</th></tr>
            {''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in data['source_data'].items())}
        </table>
    </body>
    </html>
    """
    return HttpResponse(html)
