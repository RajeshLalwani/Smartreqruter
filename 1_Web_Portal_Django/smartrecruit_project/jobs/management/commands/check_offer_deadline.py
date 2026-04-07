"""
management/commands/check_offer_deadline.py
============================================
Flow C: 3-Day Offer Acknowledgement Tracker.
Finds offers past response_deadline and auto-closes them.
Run via cron: python manage.py check_offer_deadline
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Flow C: Auto-close offers past 3-day response deadline'

    def handle(self, *args, **kwargs):
        from jobs.models import Offer

        now = timezone.now()
        expired_offers = Offer.objects.filter(
            status='SENT',
            response_deadline__lt=now
        ).select_related('application__candidate', 'application__job')

        count = expired_offers.count()
        if count == 0:
            self.stdout.write('✅ No expired offers found.')
            return

        self.stdout.write(f'⚠️  Found {count} offers past deadline. Auto-closing...')

        for offer in expired_offers:
            app = offer.application
            offer.status = 'REJECTED'
            offer.save(update_fields=['status'])

            # WhatsApp alert to candidate
            try:
                from core.utils.twilio_api import send_whatsapp_alert
                if app.candidate.phone:
                    msg = (
                        f"Hi {app.candidate.full_name}, your offer for "
                        f"*{app.job.title}* has expired as no response was received "
                        f"within 3 days. Please contact HR if this was an error. — SmartRecruit"
                    )
                    send_whatsapp_alert(app.candidate.phone, msg)
            except Exception as e:
                self.stdout.write(f'   [Twilio] Alert failed: {e}')

            self.stdout.write(
                f'   ⏰ Offer #{offer.id} for {app.candidate.full_name} → REJECTED (deadline passed)'
            )

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Flow C complete. {count} offers auto-closed.'
        ))
