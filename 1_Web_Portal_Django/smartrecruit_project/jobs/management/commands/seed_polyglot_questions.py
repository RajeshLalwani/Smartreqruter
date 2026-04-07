import json
from django.core.management.base import BaseCommand
from jobs.models import QuestionBank

class Command(BaseCommand):
    help = 'Seeds the QuestionBank with multi-language (Polyglot) coding challenges'

    def handle(self, *args, **options):
        challenges = [
            {
                'round': 'R2_PRACTICAL',
                'category': 'GOLANG_CODING',
                'language': 'go',
                'difficulty': 'medium',
                'question_text': 'Implement a function that calculates the factorial of a number using recursion.',
                'starter_code': '',
                'expected_output': '120', # For input 5
                'is_coding': True,
                'is_active': True
            },
            {
                'round': 'R2_PRACTICAL',
                'category': 'RUST_CODING',
                'language': 'rust',
                'difficulty': 'hard',
                'question_text': 'Write a Rust program to find the first non-repeating character in a string.',
                'starter_code': '',
                'expected_output': 's', # For "smartrecruit"
                'is_coding': True,
                'is_active': True
            },
            {
                'round': 'R2_PRACTICAL',
                'category': 'JAVA_CODING',
                'language': 'java',
                'difficulty': 'medium',
                'question_text': 'Implement a basic LRU Cache with get and put methods.',
                'starter_code': '',
                'expected_output': 'Successfully implemented',
                'is_coding': True,
                'is_active': True
            },
            {
                'round': 'R2_PRACTICAL',
                'category': 'JS_CODING',
                'language': 'javascript',
                'difficulty': 'easy',
                'question_text': 'Write a function that reverses a string in-place.',
                'starter_code': '',
                'expected_output': 'tiurcer-trams',
                'is_coding': True,
                'is_active': True
            }
        ]

        for chunk in challenges:
            qb, created = QuestionBank.objects.get_or_create(
                question_text=chunk['question_text'],
                defaults=chunk
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {chunk['language']} challenge: {chunk['question_text'][:30]}..."))
            else:
                self.stdout.write(self.style.WARNING(f"Challenge already exists: {chunk['question_text'][:30]}..."))

        self.stdout.write(self.style.SUCCESS("Successfully seeded polyglot challenges."))
