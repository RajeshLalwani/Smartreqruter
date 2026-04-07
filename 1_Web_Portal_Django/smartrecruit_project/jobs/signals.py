import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Assessment, SentimentLog, Interview, Notification
from core.utils.analytics_engine import RetentionAnalyticsEngine
from core.utils.email_service import send_async_email
from django.conf import settings

@receiver(post_save, sender=Assessment)
def trigger_retention_on_assessment(sender, instance, created, **kwargs):
    """
    Trigger attrition prediction and send result notification when an assessment is saved.
    Runs in a background thread to avoid slowing down the UI.
    """
    if created:
        candidate = instance.application.candidate
        thread = threading.Thread(target=RetentionAnalyticsEngine.run_prediction, args=(candidate,))
        thread.start()

        # In-app notification and email
        if candidate.user:
            def notify_assessment():
                Notification.objects.create(
                    user=candidate.user,
                    title="Assessment Result Processed",
                    message=f"Your recent assessment for {instance.application.job.title} has been evaluated.",
                    type="SUCCESS" if instance.passed else "INFO",
                    link=f"/candidate/applications/"
                )
                if candidate.user.email:
                    context = {
                        'user': candidate.user,
                        'job_title': instance.application.job.title,
                        'report_url': f"{settings.SITE_URL}/candidate/applications/" if hasattr(settings, 'SITE_URL') else "https://smartrecruit.ai/candidate/applications/"
                    }
                    send_async_email(
                        subject="SmartRecruit Neural Engine Result",
                        template_name="emails/result.html",
                        context=context,
                        recipient_list=[candidate.user.email]
                    )
            threading.Thread(target=notify_assessment).start()

@receiver(post_save, sender=SentimentLog)
def trigger_retention_on_sentiment(sender, instance, created, **kwargs):
    """
    Trigger attrition prediction when new sentiment data arrives.
    """
    if created and instance.interview:
        candidate = instance.interview.application.candidate
        thread = threading.Thread(target=RetentionAnalyticsEngine.run_prediction, args=(candidate,))
        thread.start()

@receiver(post_save, sender=Interview)
def trigger_interview_invite(sender, instance, created, **kwargs):
    """
    Trigger interview invite email and notification.
    """
    if created:
        candidate = instance.application.candidate
        if candidate.user:
            def notify_interview():
                Notification.objects.create(
                    user=candidate.user,
                    title="Interview Session Scheduled",
                    message=f"Neural assessment scheduled for {instance.application.job.title}.",
                    type="INFO",
                    link=instance.meeting_link or f"/candidate/applications/"
                )
                if candidate.user.email:
                    context = {
                        'user': candidate.user,
                        'job_title': instance.application.job.title,
                        'mode': instance.get_interview_type_display(),
                        'interview_url': instance.meeting_link or (f"{settings.SITE_URL}/interviews/" if hasattr(settings, 'SITE_URL') else "https://smartrecruit.ai/interviews/")
                    }
                    
                    # Generate rudimentary .ics attachment
                    import datetime
                    start_time = instance.scheduled_time or datetime.datetime.now(datetime.timezone.utc)
                    end_time = start_time + datetime.timedelta(hours=1)
                    dtstamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    dtstart = start_time.strftime("%Y%m%dT%H%M%SZ")
                    dtend = end_time.strftime("%Y%m%dT%H%M%SZ")
                    
                    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//SmartRecruit AI//Neural Link//EN
BEGIN:VEVENT
UID:smartrecruit-{instance.id}@smartrecruit.ai
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:SmartRecruit Interview - {instance.application.job.title}
DESCRIPTION:Your secure neural assessment session has been scheduled. Link: {context['interview_url']}
END:VEVENT
END:VCALENDAR"""

                    attachments = [('invite.ics', ics_content, 'text/calendar')]
                    
                    send_async_email(
                        subject="SmartRecruit Neural Link Requested",
                        template_name="emails/interview_invite.html",
                        context=context,
                        recipient_list=[candidate.user.email],
                        attachments=attachments
                    )
            threading.Thread(target=notify_interview).start()

from .models import Application

@receiver(post_save, sender=Application)
def trigger_pipeline_on_application(sender, instance, created, **kwargs):
    """
    Triggers the PipelineOrchestrator (which includes the Rule Engine)
    whenever an application is updated.
    """
    from .pipeline import PipelineOrchestrator
    # We pass the instance to orchestrator to route status changes
    # and trigger Rule Engine (Module 3)
    PipelineOrchestrator.on_status_change(instance)
