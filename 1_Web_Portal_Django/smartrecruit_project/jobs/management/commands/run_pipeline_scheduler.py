"""
Management Command: run_pipeline_scheduler
==========================================
Usage:
    python manage.py run_pipeline_scheduler --task all
    python manage.py run_pipeline_scheduler --task expire_offers
    python manage.py run_pipeline_scheduler --task ghosting_nudges
    python manage.py run_pipeline_scheduler --task offer_reminders

Schedule this via Windows Task Scheduler (or a cron job on Linux) to run every 30 minutes.

Windows Task Scheduler command:
    python manage.py run_pipeline_scheduler --task all
    
Cron (Linux):
    */30 * * * * cd /path/to/project && python manage.py run_pipeline_scheduler --task all
"""

import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger('pipeline')


class Command(BaseCommand):
    help = 'Run SmartRecruit Pipeline Scheduler tasks (offer expiry, ghosting nudges, reminders)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            default='all',
            choices=['all', 'expire_offers', 'ghosting_nudges', 'offer_reminders'],
            help='Which scheduler task to run'
        )

    def handle(self, *args, **options):
        from jobs.pipeline import PipelineScheduler
        task = options['task']

        self.stdout.write(self.style.SUCCESS(f'[SmartRecruit Pipeline] Running task: {task}'))

        if task in ('all', 'expire_offers'):
            count = PipelineScheduler.expire_offer_deadlines()
            self.stdout.write(f'  [OK] Expired offers processed: {count}')

        if task in ('all', 'ghosting_nudges'):
            count = PipelineScheduler.send_ghosting_nudges()
            self.stdout.write(f'  [OK] Ghosting nudges sent: {count}')

        if task in ('all', 'offer_reminders'):
            count = PipelineScheduler.offer_reminder_3day()
            self.stdout.write(f'  [OK] Offer reminders sent: {count}')

        self.stdout.write(self.style.SUCCESS('[SmartRecruit Pipeline] Scheduler run complete.'))
