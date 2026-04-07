"""
management/commands/check_application_expiry.py
================================================
Flow B: 7-Day Rule — auto-reject timed-out applications.
Marks as REJECTED_TIMEOUT (not generic REJECTED) and fires Twilio WhatsApp alert.
Run via cron: python manage.py check_application_expiry
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from jobs.models import Application
from datetime import timedelta


class Command(BaseCommand):
    help = 'Flow B: Auto-reject timed-out applications (7-day rule) and send WhatsApp alerts'

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # --- Round 1 Pending > 7 days ---
        threshold_r1 = now - timedelta(days=7)
        expired_r1 = list(Application.objects.filter(
            status='ROUND_1_PENDING',
            updated_at__lt=threshold_r1
        ).select_related('candidate', 'job'))

        # --- Rounds 2/3/HR Pending > 3 days ---
        threshold_other = now - timedelta(days=3)
        expired_other = list(Application.objects.filter(
            status__in=['ROUND_2_PENDING', 'ROUND_3_PENDING', 'HR_ROUND_PENDING'],
            updated_at__lt=threshold_other
        ).select_related('candidate', 'job'))

        expired_apps = expired_r1 + expired_other
        count = len(expired_apps)

        if count == 0:
            self.stdout.write("✅ No expired applications found.")
            return

        self.stdout.write(f"⚠️  Found {count} timed-out applications. Processing...")

        for app in expired_apps:
            # ← FLOW B: Use REJECTED_TIMEOUT (not generic REJECTED)
            app.status = 'REJECTED_TIMEOUT'
            app.save(update_fields=['status', 'updated_at'])

            # WhatsApp alert to candidate
            try:
                from core.utils.twilio_api import send_whatsapp_alert
                if app.candidate.phone:
                    msg = (
                        f"Hi {app.candidate.full_name}, your application for "
                        f"*{app.job.title}* has been automatically closed "
                        f"as the assessment window expired. "
                        f"Please apply again for future openings. — SmartRecruit"
                    )
                    send_whatsapp_alert(app.candidate.phone, msg)
            except Exception as wa_err:
                self.stdout.write(f"   [Twilio] Alert failed for {app.candidate.full_name}: {wa_err}")

            # Email via pipeline
            try:
                from jobs.email_utils import send_auto_rejection
                send_auto_rejection(app)
            except Exception:
                pass

            self.stdout.write(
                f"   ⏰ REJECTED_TIMEOUT: #{app.id} {app.candidate.full_name} → {app.job.title}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Flow B complete. {count} applications marked REJECTED_TIMEOUT."
        ))

