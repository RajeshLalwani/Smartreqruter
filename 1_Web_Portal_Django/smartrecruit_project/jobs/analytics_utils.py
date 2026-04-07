"""
Advanced Analytics Utilities for SmartRecruit
Provides export, time-to-hire calculations, and advanced metrics
"""

import csv
from io import BytesIO, StringIO
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.db.models import Avg, Count, Q, F
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def calculate_time_to_hire(application):
    """
    Calculate time-to-hire for an application
    Returns days from application to offer acceptance
    """
    if application.status == 'OFFER_ACCEPTED':
        try:
            offer = application.offer_letter
            # Use offer created_at as the acceptance proxy (no accepted_at field)
            time_delta = offer.created_at - application.applied_at
            return time_delta.days
        except Exception:
            pass
    return None


def calculate_average_time_to_hire(applications):
    """
    Calculate average time-to-hire across multiple applications
    """
    times = []
    for app in applications:
        time = calculate_time_to_hire(app)
        if time is not None:
            times.append(time)
    
    if times:
        return sum(times) / len(times)
    return 0


def get_conversion_rates(applications):
    """
    Calculate conversion rates between stages
    """
    total = applications.count()
    if total == 0:
        return {}
    
    return {
        'resume_to_r1': (applications.filter(
            Q(status='ROUND_1_PASSED') | Q(status='ROUND_2_PASSED') | 
            Q(status='ROUND_3_PASSED') | Q(status='OFFER_GENERATED') | 
            Q(status='OFFER_ACCEPTED')
        ).count() / total) * 100,
        'r1_to_r2': (applications.filter(
            Q(status='ROUND_2_PASSED') | Q(status='ROUND_3_PASSED') | 
            Q(status='OFFER_GENERATED') | Q(status='OFFER_ACCEPTED')
        ).count() / max(applications.filter(status='ROUND_1_PASSED').count(), 1)) * 100,
        'r2_to_r3': (applications.filter(
            Q(status='ROUND_3_PASSED') | Q(status='OFFER_GENERATED') | 
            Q(status='OFFER_ACCEPTED')
        ).count() / max(applications.filter(status='ROUND_2_PASSED').count(), 1)) * 100,
        'r3_to_offer': (applications.filter(
            Q(status='OFFER_GENERATED') | Q(status='OFFER_ACCEPTED')
        ).count() / max(applications.filter(status='ROUND_3_PASSED').count(), 1)) * 100,
        'offer_to_hired': (applications.filter(
            status='OFFER_ACCEPTED'
        ).count() / max(applications.filter(status='OFFER_GENERATED').count(), 1)) * 100,
    }


def export_analytics_csv(applications, filename='analytics_export.csv'):
    """
    Export analytics data to CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'Application ID', 'Candidate Name', 'Job Title', 'Applied Date',
        'Status', 'AI Score', 'Round 1 Score', 'Round 2 Score',
        'AI Interview Score', 'HR Interview Score', 'Time to Hire (days)'
    ])
    
    # Import models once outside the loop
    from .models import Assessment, Interview
    
    # Write data
    for app in applications:
        # Fetch scores from Assessment & Interview models
        r1_assessment = Assessment.objects.filter(application=app, test_type='APTITUDE').first()
        r2_assessment = Assessment.objects.filter(application=app, test_type='PRACTICAL').first()
        ai_interview = Interview.objects.filter(application=app, interview_type='AI_BOT', status='COMPLETED').first()
        hr_interview = Interview.objects.filter(application=app, interview_type='AI_HR', status='COMPLETED').first()
        
        writer.writerow([
            app.id,
            app.candidate.full_name,
            app.job.title,
            app.applied_at.strftime('%Y-%m-%d'),
            app.get_status_display(),
            f"{app.ai_score:.1f}" if app.ai_score else 'N/A',
            f"{r1_assessment.score:.1f}" if r1_assessment else 'N/A',
            f"{r2_assessment.score:.1f}" if r2_assessment else 'N/A',
            f"{ai_interview.ai_confidence_score:.1f}" if ai_interview else 'N/A',
            f"{hr_interview.ai_confidence_score:.1f}" if hr_interview else 'N/A',
            calculate_time_to_hire(app) or 'N/A'
        ])
    
    return response


def export_analytics_pdf(applications, recruiter_name, filename='analytics_report.pdf'):
    """
    Export analytics data to PDF with charts and summaries
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    title = Paragraph("SmartRecruit Analytics Report", title_style)
    elements.append(title)
    
    # Metadata
    meta_data = [
        ['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
        ['Recruiter:', recruiter_name],
        ['Total Applications:', str(applications.count())],
    ]
    
    meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))
    
    # Summary Statistics
    elements.append(Paragraph("Summary Statistics", heading_style))
    
    total_apps = applications.count()
    hired = applications.filter(status='OFFER_ACCEPTED').count()
    avg_time = calculate_average_time_to_hire(applications)
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Applications', str(total_apps)],
        ['Candidates Hired', str(hired)],
        ['Hiring Rate', f"{(hired/total_apps*100):.1f}%" if total_apps > 0 else 'N/A'],
        ['Average Time to Hire', f"{avg_time:.1f} days" if avg_time > 0 else 'N/A'],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Application Details
    elements.append(Paragraph("Application Details", heading_style))
    
    app_data = [['ID', 'Candidate', 'Job', 'Status', 'AI Score']]
    for app in applications[:20]:  # Limit to first 20
        app_data.append([
            str(app.id),
            app.candidate.full_name[:20],
            app.job.title[:25],
            app.get_status_display()[:20],
            f"{app.ai_score:.1f}" if app.ai_score else 'N/A'
        ])
    
    app_table = Table(app_data, colWidths=[0.5*inch, 1.5*inch, 2*inch, 1.5*inch, 1*inch])
    app_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    elements.append(app_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def get_technology_breakdown(applications):
    """
    Get breakdown of applications by technology stack
    """
    tech_counts = applications.values('job__technology_stack').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return {item['job__technology_stack']: item['count'] for item in tech_counts}


def get_source_tracking(applications):
    """
    Track where candidates are coming from
    (This would require adding a 'source' field to Application model)
    """
    # Placeholder - would need model changes
    return {
        'Direct Application': applications.count(),
        'Referral': 0,
        'LinkedIn': 0,
        'Job Board': 0,
    }
