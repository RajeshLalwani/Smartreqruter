from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


from core.utils.email_service import send_async_email

def _send_email(subject, template_name, context, recipient_list, attachments=None):
    """
    Helper to send HTML emails.
    Utilizes core EmailThread for asynchronous, non-blocking delivery.
    attachments: list of tuples (filename, content, mimetype)
    """
    try:
        send_async_email(subject, template_name, context, recipient_list, attachments)
        print(f"Async email '{subject}' queued for {recipient_list}")
        return True
    except Exception as e:
        print(f"Failed to queue async email '{subject}' to {recipient_list}: {e}")
        return False

# --- Generic Helper ---
def send_html_email(subject, template_name, context, recipient_email):
    return _send_email(subject, template_name, context, [recipient_email])

# --- New Scheduler Emails ---

def send_interview_confirmation(interview):
    from .utils import generate_ics_content
    
    subject = f"Interview Scheduled: {interview.application.job.title}"
    context = {
        'candidate_name': interview.application.candidate.full_name,
        'job_title': interview.application.job.title,
        'round_name': interview.get_interview_type_display(),
        'scheduled_time': interview.scheduled_time.strftime('%A, %B %d, %Y at %I:%M %p'),
        'meeting_link': interview.meeting_link,
    }
    
    # Generate ICS
    ics_content = generate_ics_content(interview)
    attachments = [('invite.ics', ics_content, 'text/calendar')]
    
    _send_email(subject, 'emails/interview_confirmation.html', context, [interview.application.candidate.user.email], attachments=attachments)

def send_auto_rejection(application):
    subject = f"Application Update: {application.job.title}"
    context = {
        'candidate_name': application.candidate.full_name,
        'job_title': application.job.title,
    }
    _send_email(subject, 'emails/rejection_notification.html', context, [application.candidate.user.email])

# --- Legacy/Existing Emails ---

def send_application_received_email(user, job, application):
    from django.urls import reverse
    
    subject = f"Application Received: {job.title}"
    portal_url = settings.SITE_URL + reverse('dashboard') if hasattr(settings, 'SITE_URL') else "http://localhost:8000" + reverse('dashboard')
    
    context = {
        'candidate_name': user.first_name or user.username,
        'job_title': job.title,
        'application_id': application.id,
        'submitted_date': application.applied_at.strftime('%B %d, %Y') if application.applied_at else 'Today',
        'ai_score': application.ai_score,
        'dashboard_url': portal_url,
    }
    
    _send_email(
        subject,
        'emails/application_received.html',
        context,
        [user.email]
    )

def send_resume_shortlisted_email(user, job, application):
    """
    Sends the branded 'Thunder Strike Shortlisted' email once a candidate passes AI screening.
    """
    from django.urls import reverse
    dashboard_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000') + reverse('dashboard')
    final_score = application.ai_score or 0
    
    context = {
        'candidate_name': user.first_name or user.username,
        'job_title': job.title,
        'match_percentage': int(final_score),
        'company_name': getattr(settings, 'COMPANY_NAME', 'IR Info Tech'),
        'dashboard_url': dashboard_url,
    }
    
    return _send_email(
        subject=f"⚡ Your Career Strike! You've been Shortlisted for {job.title}",
        template_name='emails/resume_shortlisted.html',
        context=context,
        recipient_list=[user.email]
    )

def send_assessment_result_email(application, score, passed):
    from django.urls import reverse
    
    status = "Passed" if passed else "Failed"
    subject = f"Assessment Result: {status} - {application.job.title}"
    portal_url = settings.SITE_URL + reverse('dashboard') if hasattr(settings, 'SITE_URL') else "http://localhost:8000" + reverse('dashboard')
    
    context = {
        'candidate_name': application.candidate.user.first_name or application.candidate.full_name,
        'job_title': application.job.title,
        'score': score,
        'status': status,
        'dashboard_url': portal_url,
    }
    
    _send_email(
        subject,
        'emails/assessment_result.html',
        context,
        [application.candidate.user.email]
    )

def send_interview_invitation_email(application, round_name, interview=None):
    from django.urls import reverse
    
    subject = f"📅 Confirmed: Your AI Interview is Scheduled – {application.job.title}"
    interview_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000') + reverse('dashboard')
    scheduled_time = None
    if interview and interview.scheduled_time:
        scheduled_time = interview.scheduled_time.strftime('%A, %B %d, %Y at %I:%M %p')
    
    context = {
        'candidate_name': application.candidate.user.first_name or application.candidate.full_name,
        'job_title': application.job.title,
        'round_name': round_name,
        'scheduled_time': scheduled_time or 'To be confirmed',
        'company_name': getattr(settings, 'COMPANY_NAME', 'IR Info Tech'),
        'interview_url': interview_url,
    }
    
    return _send_email(
        subject,
        'emails/interview_invite.html',
        context,
        [application.candidate.user.email]
    )

def send_offer_letter_email(offer):
    """
    Sends the official offer letter as a professional PDF attachment.
    """
    from .utils import render_to_pdf
    from django.core.files.base import ContentFile
    
    subject = f"Official Offer of Employment: {offer.application.job.title} | IR Info Tech"
    
    # Context for the professional template
    import os
    from django.conf import settings
    
    logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'images', 'ir_logo.png')
    signature_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'images', 'signature.png')

    context = {
        'candidate_name': offer.application.candidate.full_name,
        'designation': offer.designation,
        'salary': offer.salary_offered,
        'joining_date': offer.joining_date,
        'application': offer.application,
        'logo_url': logo_path,
        'signature_url': signature_path,
    }
    
    # Generate PDF content
    pdf_content = render_to_pdf('jobs/offer_letter_pdf.html', context)
    
    if pdf_content:
        # Save the file to the model if not already saved (or to update it)
        filename = f"Offer_{offer.application.candidate.id}_{offer.id}.pdf"
        offer.offer_file.save(filename, ContentFile(pdf_content), save=True)
        
        # Prepare email
        html_body = render_to_string('emails/offer_letter.html', context)
        attachments = [(filename, pdf_content, 'application/pdf')]
        
        return _send_email(
            subject, 
            'emails/offer_letter.html', 
            context, 
            [offer.application.candidate.user.email], 
            attachments=attachments
        )
    
    return False

def send_status_email(user, subject, body):
    try:
        msg = EmailMultiAlternatives(subject, body, settings.DEFAULT_FROM_EMAIL, ['rajlalwani511@gmail.com'])
        msg.attach_alternative(f"<p>{body}</p>", "text/html")
        msg.send()
        return True
    except:
        return False

def send_status_update_email(application, action_type):
    """
    Sends the dynamically generated AI HTML email on Shortlist or Reject.
    """
    from django.urls import reverse
    import sys
    import os
    import json
    
    # Try importing the AI Email Generator
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        ai_modules_dir = os.path.join(parent_dir, '2_AI_Modules')
        sys.path.append(ai_modules_dir)
        from Email_Drafter.ai_email_generator import generate_personalized_email
    except ImportError as e:
        generate_personalized_email = None
        print(f"[Email Utils] Error importing AI Email Generator: {e}")

    # Gather Context
    candidate_name = application.candidate.user.first_name or application.candidate.full_name
    job_title = application.job.title
    
    # Extract AI Insights if present, else fallback to raw score
    try:
        feedback_data = json.loads(application.ai_insights)
    except:
        feedback_data = {"ai_score": application.ai_score}
        
    # Check if there's interview feedback
    latest_interview = application.interviews.filter(status='COMPLETED').order_by('-created_at').first()
    if latest_interview and latest_interview.feedback:
        feedback_data['latest_interview_feedback'] = latest_interview.feedback

    if action_type == 'shortlist':
        subject = f"Update on your application: {job_title} - Shortlisted!"
        status_type = 'success'
    elif action_type == 'reject':
        subject = f"Update on your application: {job_title}"
        status_type = 'error'
    else:
        return False
        
    # GENERATE MAGICAL AI EMAIL BODY
    if generate_personalized_email:
        email_body = generate_personalized_email(candidate_name, job_title, action_type, feedback_data)
    else:
        # Fallback if module fails to load entirely
        if action_type == 'shortlist':
            email_body = f"Congratulations! Your profile has been selected for the next round of interviews for the <strong>{job_title}</strong> role."
        else:
            email_body = f"Thank you for taking the time to apply for the <strong>{job_title}</strong> role. Unfortunately, we have decided to move forward with other candidates who more closely align with our current needs."
        
    portal_url = settings.SITE_URL + reverse('dashboard') if hasattr(settings, 'SITE_URL') else "http://localhost:8000" + reverse('dashboard')
        
    context = {
        'candidate_name': application.candidate.user.first_name or application.candidate.full_name,
        'job_title': application.job.title,
        'email_body': email_body,
        'status_type': status_type,
        'portal_url': portal_url,
    }
    
    return _send_email(
        subject,
        'emails/status_update.html',
        context,
        [application.candidate.user.email]
    )

def send_onboarding_email(user, job):
    subject = f"Welcome to the Team! Onboarding Next Steps"
    context = {
        'user': user,
        'job': job
    }
    _send_email(subject, 'emails/onboarding_welcome.html', context, [user.email])


def send_auto_rejection(application):
    """
    Send an automatic rejection email to a candidate whose resume score
    fell below the threshold. Called when application.status = 'REJECTED'.
    """
    try:
        candidate_email = application.candidate.user.email
        candidate_name = (
            application.candidate.full_name
            or application.candidate.user.get_full_name()
            or application.candidate.user.email
        )
        job_title = application.job.title
        subject = f"Application Update: {job_title}"
        context = {
            'candidate_name': candidate_name,
            'job_title': job_title,
            'ai_score': application.ai_score,
            'portal_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
        }
        # Use status_update template with a rejection tone, or plain text fallback
        try:
            return _send_email(
                subject,
                'emails/auto_rejection.html',
                context,
                [candidate_email]
            )
        except Exception:
            # Plain-text fallback
            from django.core.mail import send_mail
            from django.conf import settings as django_settings
            send_mail(
                subject,
                f"Dear {candidate_name},\n\nThank you for applying for {job_title}. "
                f"After reviewing your profile, we regret that your application did not meet "
                f"our criteria at this time.\n\nWe encourage you to apply again in the future.\n\n"
                f"Best regards,\nSmartRecruit Team",
                django_settings.DEFAULT_FROM_EMAIL,
                ['rajlalwani511@gmail.com'], # Forced for audit
                fail_silently=True,
            )
            return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"send_auto_rejection failed: {e}")
        return False


def send_final_decision_email(application, request, is_hired=True):
    # Retrieve the logger locally since it might not be globally imported here
    import logging
    logger = logging.getLogger(__name__)

    candidate_user = application.candidate.user
    if not candidate_user or not candidate_user.email:
        logger.warning(f"No valid email found for application {application.id}")
        return

    company_name = getattr(settings, 'COMPANY_NAME', 'IR Info Tech (SmartRecruit)')
    job_title = application.job.title
    
    # HARDCODED TEST IDENTITY
    test_email = 'rajlalwani511@gmail.com'
    
    if is_hired:
        subject = f"⚡ Welcome to the Multiverse! Offer Letter from {company_name}"
        template_name = 'emails/offer_letter.html'
    else:
        subject = f"Update regarding your application for {job_title}"
        template_name = 'emails/polite_rejection.html'

    context = {
        'candidate_name': application.candidate.full_name,
        'job_title': job_title,
        'company_name': company_name,
        'dashboard_url': request.build_absolute_uri('/')
    }

    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[test_email]  # Using Raj's explicit test identity
        )
        email.attach_alternative(html_message, "text/html")
        
        # Attach the Offer Letter PDF if hired
        if is_hired:
            if hasattr(application, 'offer_letter') and application.offer_letter.offer_file:
                email.attach(
                    application.offer_letter.offer_file.name,
                    application.offer_letter.offer_file.read(),
                    'application/pdf'
                )

        email.send()
        action_name = "Selection" if is_hired else "Rejection"
        logger.info(f"Final {action_name} email sent to {test_email} for Job: {job_title}")
    except Exception as e:
        logger.error(f"Failed to send final decision email to {test_email}: {str(e)}")
