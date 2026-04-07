import os
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from jobs.models import Application, Candidate, ActivityLog

class Command(BaseCommand):
    help = 'Purges or anonymizes candidate data older than 6 months for GDPR compliance.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the purge without deleting data',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        # Threshold: 6 months ago (approx 180 days)
        threshold = timezone.now() - timedelta(days=180)
        
        expired_apps = Application.objects.filter(applied_at__lt=threshold)
        count = expired_apps.count()

        self.stdout.write(self.style.WARNING(f"Found {count} applications older than 6 months (Threshold: {threshold.date()})"))

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No data to purge."))
            return

        for app in expired_apps:
            candidate = app.candidate
            job_title = app.job.title
            
            if dry_run:
                self.stdout.write(f"[DRY-RUN] Would purge application #{app.id} for {candidate.full_name} ({job_title})")
            else:
                # 1. Delete sensitive files (Resumes, Proctoring Images)
                if candidate.resume_file:
                    file_path = candidate.resume_file.path
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    candidate.resume_file = None
                    candidate.save()
                
                # 2. Delete Proctoring Violations (Photos)
                for log in app.proctoring_logs.all():
                    if log.frame_data: # If stored as file path
                        # Assuming frame_data is a FileField/ImageField
                        try:
                             log.frame_data.delete()
                        except:
                             pass
                
                # 3. Anonymize Candidate (Optional based on business rules)
                # Here we just mark the application as 'PURGED' and clear the score
                app.status = 'PURGED'
                app.ai_score = 0
                app.save()
                
                self.stdout.write(self.style.SUCCESS(f"Purged application #{app.id} for {candidate.full_name}"))

        if not dry_run:
            ActivityLog.objects.create(
                user=None, # System action
                action="Data Retention Purge",
                details=f"Automatically purged/anonymized {count} records older than 6 months."
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully processed {count} records."))
