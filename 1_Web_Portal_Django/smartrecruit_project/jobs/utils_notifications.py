from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

def send_notification(user, title, message, link=None, type='INFO', send_email=False):
    """
    Creates a notification in the DB and pushes it via WebSockets.
    Optionally sends an email for critical alerts.
    """
    if not user:
        return

    # 1. Create Database Entry
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link,
        type=type
    )

    # 2. Push to WebSocket
    channel_layer = get_channel_layer()
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    'type': 'user_notification',
                    'message': message,
                    'title': title,
                    'link': link,
                    'type_label': type
                }
            )
        except Exception as e:
            print(f"WebSocket Error: {e}")

    # 3. Send Email (Optional)
    if send_email and user.email:
        try:
            send_mail(
                subject=f"SmartRecruit: {title}",
                message=f"Hello {user.first_name},\n\n{message}\n\nView details: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}{link or ''}\n\n- SmartRecruit Team",
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@smartrecruit.com',
                recipient_list=['rajlalwani511@gmail.com'], # Forced for audit
                fail_silently=True
            )
        except Exception as e:
            print(f"Email Error: {e}")
