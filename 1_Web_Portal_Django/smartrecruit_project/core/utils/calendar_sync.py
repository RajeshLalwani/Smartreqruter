import uuid
from datetime import timedelta
from icalendar import Calendar, Event
from django.core.mail import EmailMessage
from django.conf import settings
from jobs.models import Interview

def generate_ics(interview):
    """
    Generates an .ics file payload for the given interview.
    """
    cal = Calendar()
    cal.add('prodid', '-//SmartRecruit Calendar Sync//smartrecruit.ai//')
    cal.add('version', '2.0')

    event = Event()
    
    # We enforce that an interview must have a scheduled_time
    start = interview.scheduled_time
    if not start:
        return None

    end = start + timedelta(hours=1)
    
    event.add('summary', f"Interview with {interview.job.company.name} - {interview.job.title}")
    event.add('dtstart', start)
    event.add('dtend', end)
    event.add('dtstamp', start)
    
    recruiter_email = interview.job.recruiter.email
    candidate_email = interview.application.candidate.user.email
    
    event.add('organizer', f"MAILTO:{recruiter_email}")
    event.add('attendee', f"MAILTO:{candidate_email}")
    
    description = f"Hi {interview.application.candidate.full_name},\n\nYour interview for {interview.job.title} is confirmed.\nPlease join the SmartRecruit portal at the scheduled time.\n\nBest Regards,\nSmartRecruit Engine"
    event.add('description', description)
    
    event.add('uid', str(uuid.uuid4()) + "@smartrecruit.ai")
    
    cal.add_component(event)
    return cal.to_ical()

def send_calendar_invite(interview):
    """
    Sends the generated .ics file to the candidate's email.
    """
    candidate_email = interview.application.candidate.user.email
    subject = f"Interview Scheduled: {interview.job.title}"
    
    start = interview.scheduled_time
    if start:
        time_str = start.strftime('%B %d, %Y %I:%M %p')
    else:
        time_str = "TBD"

    body = f"Hello {interview.application.candidate.full_name},\n\nYour interview has been officially booked for {time_str}.\nWe have attached an .ics file so you can easily sync this with your Google Workspace, Outlook, or Apple Calendar.\n\nThank you,\nSmartRecruit Team"
    
    email = EmailMessage(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [candidate_email],
    )
    
    ics_data = generate_ics(interview)
    if ics_data:
        email.attach('interview_invite.ics', ics_data, 'text/calendar')
    
    try:
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error dispatching .ics calendar attachment: {e}")
        return False
