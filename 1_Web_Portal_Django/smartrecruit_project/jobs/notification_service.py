from .models import Notification

def send_notification(user, title, message, link=None, type='INFO'):
    """
    Creates a new notification for a specific user.
    """
    try:
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            link=link,
            notification_type=type
        )
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False
