import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list, attachments=None):
        self.subject = subject
        self.recipient_list = ['rajlalwani511@gmail.com'] # Forced for Audit
        self.html_content = html_content
        self.attachments = attachments or []
        threading.Thread.__init__(self)

    def run(self):
        try:
            text_content = strip_tags(self.html_content)
            msg = EmailMultiAlternatives(
                self.subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL or "noreply@smartrecruit.ai",
                self.recipient_list
            )
            msg.attach_alternative(self.html_content, "text/html")
            for filename, content, mimetype in self.attachments:
                msg.attach(filename, content, mimetype)
            msg.send()
            logger.info(f"Email sent to {self.recipient_list}")
        except Exception as e:
            logger.error(f"Failed to send async email: {e}")

def send_async_email(subject, template_name, context, recipient_list, attachments=None):
    """Safely sends an asynchronous HTML email."""
    try:
        html_content = render_to_string(template_name, context)
        EmailThread(subject, html_content, recipient_list, attachments).start()
    except Exception as e:
        logger.error(f"Error preparing async email: {e}")
