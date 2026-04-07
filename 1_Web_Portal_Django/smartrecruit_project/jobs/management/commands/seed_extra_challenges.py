from django.core.management.base import BaseCommand
from django.utils.text import slugify
from jobs.models import CodingChallenge
import random

EXTRA_CHALLENGES = []

categories = ['python', 'arrays', 'dp', 'data_science', 'sql', 'trees', 'sorting']
difficulties = ['easy', 'medium', 'hard']

for i in range(1, 41):
    cat = random.choice(categories)
    diff = random.choice(difficulties)
    title = f"Algorithm Challenge {i+10}"
    desc = f"""## {title}

Given the input constraints, write an optimal algorithm to solve this {diff} level problem.
This tests your fundamental understanding of {cat}.

Please implement the solution considering edge cases.
"""
    starter = {
        'python': f'def solve_challenge_{i+10}(nums: list) -> int:\n    # Write your solution here\n    pass\n',
        'javascript': f'function solveChallenge{i+10}(nums) {{\n    // Write your solution here\n}}\n'
    }

    EXTRA_CHALLENGES.append({
        'title': title,
        'category': cat,
        'difficulty': diff,
        'xp_reward': random.choice([30, 50, 80, 100, 150]),
        'description': desc,
        'constraints': '0 <= N <= 10^5',
        'examples': [{'input': 'nums = [1,2,3]', 'output': 'True', 'explanation': 'Sample explanation'}],
        'hints': ['Think about the time complexity.', 'Can you do this in O(N)?'],
        'test_cases': [{'input': '1,2,3', 'expected': 'True'}],
        'starter_code': starter,
    })

class Command(BaseCommand):
    help = 'Seeds 40 extra challenges to reach 50 total'

    def handle(self, *args, **options):
        created = 0
        for i, data in enumerate(EXTRA_CHALLENGES):
            slug = slugify(data['title'])
            obj, is_new = CodingChallenge.objects.get_or_create(
                slug=slug,
                defaults={
                    'title':       data['title'],
                    'category':    data['category'],
                    'difficulty':  data['difficulty'],
                    'xp_reward':   data['xp_reward'],
                    'description': data['description'],
                    'constraints': data.get('constraints', ''),
                    'examples':    data.get('examples', []),
                    'hints':       data.get('hints', []),
                    'test_cases':  data.get('test_cases', []),
                    'starter_code':data.get('starter_code', {}),
                    'order':       i + 15,
                }
            )
            if is_new:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Done! {created} extra challenges created.'))
