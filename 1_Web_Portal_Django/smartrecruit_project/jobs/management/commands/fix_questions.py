from django.core.management.base import BaseCommand
from jobs.models import Question
from jobs.utils import SmartFallbackGenerator
import json

class Command(BaseCommand):
    help = 'Fixes existing questions with lazy mock data by replacing them with realistic technical content.'

    def handle(self, *args, **options):
        # 1. Identify lazy questions
        # Matches "Mock Question X" or options containing "Answer A"
        lazy_questions = Question.objects.filter(
            text__icontains="Mock Question"
        ) | Question.objects.filter(
            options__icontains="Answer A"
        )

        count = lazy_questions.count()
        self.stdout.write(self.style.WARNING(f"Found {count} lazy questions in database."))

        repaired_count = 0
        for q in lazy_questions:
            # Generate one realistic question for the same category
            realistic_qs = SmartFallbackGenerator(domain=q.category, amount=1)
            if realistic_qs:
                real_q = realistic_qs[0]
                q.text = real_q['question']
                q.options = real_q['options']
                q.correct_answer = real_q['correct']
                q.save()
                repaired_count += 1
                self.stdout.write(self.style.SUCCESS(f"Repaired: {q.id} - {q.text[:40]}..."))

        self.stdout.write(self.style.SUCCESS(f"Successfully repaired {repaired_count} questions."))
