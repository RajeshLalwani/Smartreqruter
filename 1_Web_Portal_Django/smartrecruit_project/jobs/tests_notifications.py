from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from jobs.models import Notification
from django.urls import reverse
import json

User = get_user_model()

class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password', email='test@example.com')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
    def test_create_notification(self):
        # Test Model
        Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test",
            type="INFO"
        )
        self.assertEqual(Notification.objects.count(), 1)
        
    def test_get_notifications_api(self):
        # Create dummy notification
        Notification.objects.create(
            user=self.user,
            title="Test Notif",
            message="Test Msg"
        )
        
        response = self.client.get(reverse('get_notifications_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['unread_count'], 1)
        self.assertEqual(len(data['notifications']), 1)
        self.assertEqual(data['notifications'][0]['title'], "Test Notif")

    def test_mark_read_api(self):
        notif = Notification.objects.create(
            user=self.user,
            title="Read Me",
            message="Msg"
        )
        
        response = self.client.post(reverse('mark_notification_read_api', args=[notif.id]))
        self.assertEqual(response.status_code, 200)
        
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_read(self):
        # Create multiple notifications
        Notification.objects.create(user=self.user, title="N1", message="M1")
        Notification.objects.create(user=self.user, title="N2", message="M2")
        
        response = self.client.post(reverse('mark_all_notifications_read_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_delete_notification(self):
        n = Notification.objects.create(user=self.user, title="N1", message="M1")
        
        response = self.client.post(reverse('delete_notification_api', args=[n.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Notification.objects.filter(id=n.id).exists())

    def test_email_notification(self):
        # Verify email is sent when flag is True
        from django.core import mail
        from jobs.utils_notifications import send_notification
        
        send_notification(self.user, "Email Test", "Message", send_email=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Email Test", mail.outbox[0].subject)
