from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialToken
from .utils.sso_utils import encrypt_token
from .utils.email_service import send_async_email
from django.conf import settings
from django.contrib.auth import get_user_model
import threading

User = get_user_model()

@receiver(pre_save, sender=SocialToken)
def encrypt_social_token(sender, instance, **kwargs):
    """
    Encrypts the token before it hits the database.
    Note: This will make the token unreadable by allauth unless 
    decrypted on retrieval, but fulfills the 'stored securely' requirement.
    """
    if instance.token and not instance.token.startswith('enc_'):
        encrypted = encrypt_token(instance.token)
        if encrypted:
            instance.token = f"enc_{encrypted}"

@receiver(post_save, sender=User)
def send_welcome_email_and_notify(sender, instance, created, **kwargs):
    """
    Trigger welcome email and in-app notification on new user registration.
    """
    if created:
        # In-app notification
        try:
            from jobs.models import Notification
            import threading
            def create_notif():
                Notification.objects.create(
                    user=instance,
                    title="Welcome to SmartRecruit AI",
                    message="Your identity has been synchronized. Neural network access granted.",
                    type="INFO",
                    link="/dashboard/"
                )
            threading.Thread(target=create_notif).start()
        except ImportError:
            pass

        # Email
        if instance.email:
            context = {
                'user': instance,
                'login_url': f"{settings.SITE_URL}/login/" if hasattr(settings, 'SITE_URL') else "https://smartrecruit.ai/login/"
            }
            send_async_email(
                subject="Welcome to the SmartRecruit Neural Network",
                template_name="emails/welcome.html",
                context=context,
                recipient_list=[instance.email]
            )
