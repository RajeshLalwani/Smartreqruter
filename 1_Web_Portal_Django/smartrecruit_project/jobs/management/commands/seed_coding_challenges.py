"""
Management command to seed the CodingChallenge database with
high-quality curated problems across all categories.

Usage:
    python manage.py seed_coding_challenges
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from jobs.models import CodingChallenge


CHALLENGES = [

    # ─── PYTHON BASICS ────────────────────────────────────────────
    {
        'title': 'Reverse a String',
        'category': 'python',
        'difficulty': 'easy',
        'xp_reward': 30,
        'description': """## Reverse a String

Write a function `reverse_string(s)` that takes a string `s` as input and returns it reversed.

**Note:** Do not use the built-in `.reverse()` method or slicing `[::-1]` — implement it manually using a loop.
""",
        'constraints': '0 <= len(s) <= 10^5\nString contains only ASCII characters',
        'examples': [
            {'input': '"hello"', 'output': '"olleh"', 'explanation': 'Each character position is swapped from front to back.'},
            {'input': '"SmartRecruit"', 'output': '"tiurceRtramS"', 'explanation': ''},
        ],
        'hints': [
            'Think about using two pointers — one at the start and one at the end.',
            'You can build the result by looping from the last index to 0.',
            'Convert the string to a list, swap elements, then join back.',
        ],
        'test_cases': [
            {'input': 'hello',        'expected': 'olleh'},
            {'input': 'SmartRecruit', 'expected': 'tiurceRtramS'},
            {'input': 'a',            'expected': 'a'},
            {'input': '',             'expected': ''},
        ],
        'starter_code': {
            'python': 'def reverse_string(s: str) -> str:\n    # Write your solution here\n    pass\n\n# Test it\nprint(reverse_string("hello"))',
            'javascript': 'function reverseString(s) {\n    // Write your solution here\n}\n\nconsole.log(reverseString("hello"));',
            'java': 'public class Solution {\n    public static String reverseString(String s) {\n        // Write your solution here\n        return "";\n    }\n    public static void main(String[] args) {\n        System.out.println(reverseString("hello"));\n    }\n}',
        },
    },

    {
        'title': 'FizzBuzz',
        'category': 'python',
        'difficulty': 'easy',
        'xp_reward': 25,
        'description': """## FizzBuzz

Print numbers from 1 to `n`, but:
- For multiples of 3, print **"Fizz"**
- For multiples of 5, print **"Buzz"**
- For multiples of both 3 and 5, print **"FizzBuzz"**
- Otherwise, print the number itself

Return the result as a **list of strings**.
""",
        'constraints': '1 <= n <= 10^4',
        'examples': [
            {'input': 'n = 5', 'output': '["1","2","Fizz","4","Buzz"]', 'explanation': '3 → Fizz, 5 → Buzz'},
            {'input': 'n = 15', 'output': '["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"]', 'explanation': '15 is divisible by both'},
        ],
        'hints': [
            'Check divisibility by 15 FIRST (both 3 and 5), then 3, then 5.',
            'Use `%` (modulo) to check if a number is divisible evenly.',
        ],
        'test_cases': [
            {'input': '5',  'expected': '["1","2","Fizz","4","Buzz"]'},
            {'input': '3',  'expected': '["1","2","Fizz"]'},
            {'input': '15', 'expected': '["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"]'},
        ],
        'starter_code': {
            'python': 'def fizz_buzz(n: int) -> list:\n    result = []\n    for i in range(1, n + 1):\n        # Your logic here\n        pass\n    return result\n\nprint(fizz_buzz(15))',
            'javascript': 'function fizzBuzz(n) {\n    const result = [];\n    for (let i = 1; i <= n; i++) {\n        // Your logic here\n    }\n    return result;\n}\nconsole.log(fizzBuzz(15));',
        },
    },

    # ─── ARRAYS & STRINGS ─────────────────────────────────────────
    {
        'title': 'Two Sum',
        'category': 'arrays',
        'difficulty': 'easy',
        'xp_reward': 50,
        'description': """## Two Sum

Given an array of integers `nums` and an integer `target`, return the **indices** of the two numbers that add up to `target`.

You may assume each input has exactly one solution. You may not use the same element twice.
""",
        'constraints': '2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9',
        'examples': [
            {'input': 'nums=[2,7,11,15], target=9', 'output': '[0,1]', 'explanation': 'nums[0] + nums[1] = 2 + 7 = 9'},
            {'input': 'nums=[3,2,4], target=6', 'output': '[1,2]', 'explanation': 'nums[1] + nums[2] = 2 + 4 = 6'},
        ],
        'hints': [
            'Brute force: use two nested loops — O(n²).',
            'Optimal: use a HashMap to store each number\'s index. Look up `target - current` in the map.',
            'Hash map approach runs in O(n) time.',
        ],
        'test_cases': [
            {'input': '[2,7,11,15] 9',  'expected': '[0,1]'},
            {'input': '[3,2,4] 6',      'expected': '[1,2]'},
            {'input': '[3,3] 6',        'expected': '[0,1]'},
        ],
        'starter_code': {
            'python': 'def two_sum(nums: list, target: int) -> list:\n    # Write your solution here\n    pass\n\nprint(two_sum([2, 7, 11, 15], 9))',
            'javascript': 'function twoSum(nums, target) {\n    // Write your solution here\n}\nconsole.log(twoSum([2,7,11,15], 9));',
            'java': 'import java.util.*;\npublic class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        // Write your solution here\n        return new int[]{};\n    }\n}',
        },
    },

    {
        'title': 'Valid Palindrome',
        'category': 'arrays',
        'difficulty': 'easy',
        'xp_reward': 40,
        'description': """## Valid Palindrome

A phrase is a **palindrome** if it reads the same forward and backward after converting all uppercase letters to lowercase and removing non-alphanumeric characters.

Given a string `s`, return `True` if it is a palindrome, or `False` otherwise.
""",
        'constraints': '1 <= s.length <= 2 * 10^5',
        'examples': [
            {'input': '"A man, a plan, a canal: Panama"', 'output': 'True', 'explanation': '"amanaplanacanalpanama" is a palindrome.'},
            {'input': '"race a car"', 'output': 'False', 'explanation': '"raceacar" is not a palindrome.'},
        ],
        'hints': [
            'First clean the string: keep only alphanumeric, lowercase everything.',
            'Use two pointers from both ends to compare characters.',
        ],
        'test_cases': [
            {'input': 'A man, a plan, a canal: Panama', 'expected': 'True'},
            {'input': 'race a car',                    'expected': 'False'},
            {'input': ' ',                             'expected': 'True'},
        ],
        'starter_code': {
            'python': 'def is_palindrome(s: str) -> bool:\n    # Step 1: Clean the string\n    # Step 2: Check if it reads the same both ways\n    pass\n\nprint(is_palindrome("A man, a plan, a canal: Panama"))',
        },
    },

    {
        'title': 'Maximum Subarray (Kadane\'s Algorithm)',
        'category': 'arrays',
        'difficulty': 'medium',
        'xp_reward': 80,
        'description': """## Maximum Subarray

Given an integer array `nums`, find the **subarray** with the largest sum, and return its sum.

**Hint:** Kadane's Algorithm solves this in O(n) — can you figure it out?
""",
        'constraints': '1 <= nums.length <= 10^5\n-10^4 <= nums[i] <= 10^4',
        'examples': [
            {'input': 'nums=[-2,1,-3,4,-1,2,1,-5,4]', 'output': '6', 'explanation': 'Subarray [4,-1,2,1] has the largest sum = 6.'},
            {'input': 'nums=[1]', 'output': '1', 'explanation': 'Single element.'},
        ],
        'hints': [
            'Keep track of the current running sum. If it goes negative, reset to 0.',
            'Maintain a `max_sum` variable to track the global maximum seen so far.',
            'Kadane\'s idea: max_ending_here = max(num, max_ending_here + num)',
        ],
        'test_cases': [
            {'input': '[-2,1,-3,4,-1,2,1,-5,4]', 'expected': '6'},
            {'input': '[1]',                      'expected': '1'},
            {'input': '[5,4,-1,7,8]',             'expected': '23'},
        ],
        'starter_code': {
            'python': 'def max_subarray(nums: list) -> int:\n    # Implement Kadane\'s Algorithm\n    max_sum = nums[0]\n    current = nums[0]\n    # Your logic here...\n    return max_sum\n\nprint(max_subarray([-2,1,-3,4,-1,2,1,-5,4]))',
        },
    },

    # ─── DYNAMIC PROGRAMMING ─────────────────────────────────────
    {
        'title': 'Fibonacci (Memoization)',
        'category': 'dp',
        'difficulty': 'easy',
        'xp_reward': 45,
        'description': """## Fibonacci with Memoization

Write a function `fib(n)` that returns the nth Fibonacci number.

The Fibonacci sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, ...

**Challenge:** Use memoization (top-down DP) to make it O(n) instead of O(2^n).
""",
        'constraints': '0 <= n <= 30',
        'examples': [
            {'input': 'n=6', 'output': '8', 'explanation': 'fib(6) = fib(5)+fib(4) = 5+3 = 8'},
        ],
        'hints': [
            'Use a dictionary to cache already-computed results.',
            'Check: if n is in the cache, return it immediately — no recomputation.',
        ],
        'test_cases': [
            {'input': '6',  'expected': '8'},
            {'input': '10', 'expected': '55'},
            {'input': '0',  'expected': '0'},
            {'input': '1',  'expected': '1'},
        ],
        'starter_code': {
            'python': 'def fib(n: int, memo={}) -> int:\n    if n <= 1:\n        return n\n    if n in memo:\n        return memo[n]\n    # Complete the memoization logic here\n    pass\n\nfor i in range(7): print(f"fib({i}) =", fib(i))',
        },
    },

    {
        'title': 'Climbing Stairs',
        'category': 'dp',
        'difficulty': 'easy',
        'xp_reward': 50,
        'description': """## Climbing Stairs

You are climbing a staircase with `n` steps. Each time you can climb **1 or 2 steps**.

How many **distinct ways** can you climb to the top?
""",
        'constraints': '1 <= n <= 45',
        'examples': [
            {'input': 'n=2', 'output': '2', 'explanation': '1+1 or 2.'},
            {'input': 'n=3', 'output': '3', 'explanation': '1+1+1, 1+2, or 2+1.'},
        ],
        'hints': [
            'This is essentially the Fibonacci problem!',
            'ways(n) = ways(n-1) + ways(n-2)',
        ],
        'test_cases': [
            {'input': '2',  'expected': '2'},
            {'input': '3',  'expected': '3'},
            {'input': '5',  'expected': '8'},
            {'input': '10', 'expected': '89'},
        ],
        'starter_code': {
            'python': 'def climb_stairs(n: int) -> int:\n    # Think about base cases: n=1 and n=2\n    # Then build up from bottom\n    pass\n\nprint(climb_stairs(5))',
        },
    },

    {
        'title': 'Longest Common Subsequence',
        'category': 'dp',
        'difficulty': 'hard',
        'xp_reward': 150,
        'description': """## Longest Common Subsequence

Given two strings `text1` and `text2`, return the **length of their longest common subsequence**. If there is no common subsequence, return 0.

A **subsequence** is a sequence derived from a string by deleting some or no characters without changing the order.

Example: "ace" is a subsequence of "**a**b**c**d**e**".
""",
        'constraints': '1 <= text1.length, text2.length <= 1000',
        'examples': [
            {'input': 'text1="abcde", text2="ace"', 'output': '3', 'explanation': 'The LCS is "ace".'},
            {'input': 'text1="abc", text2="abc"', 'output': '3', 'explanation': 'The LCS is "abc".'},
        ],
        'hints': [
            'Create a 2D DP table: dp[i][j] = LCS length for text1[:i] and text2[:j].',
            'If text1[i-1] == text2[j-1]: dp[i][j] = dp[i-1][j-1] + 1',
            'Else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])',
        ],
        'test_cases': [
            {'input': 'abcde ace',  'expected': '3'},
            {'input': 'abc abc',    'expected': '3'},
            {'input': 'abc def',    'expected': '0'},
        ],
        'starter_code': {
            'python': 'def lcs(text1: str, text2: str) -> int:\n    m, n = len(text1), len(text2)\n    # Create a DP table of size (m+1) x (n+1)\n    dp = [[0] * (n + 1) for _ in range(m + 1)]\n    # Fill in the table\n    # Your code here...\n    return dp[m][n]\n\nprint(lcs("abcde", "ace"))',
        },
    },

    # ─── DATA SCIENCE ─────────────────────────────────────────────
    {
        'title': 'Calculate Mean, Median, Mode',
        'category': 'data_science',
        'difficulty': 'easy',
        'xp_reward': 40,
        'description': """## Calculate Mean, Median, Mode

Given a list of numbers, compute:
1. **Mean** — average of all numbers
2. **Median** — middle value when sorted
3. **Mode** — most frequently occurring value

Return a dictionary with keys `mean`, `median`, `mode`.
""",
        'constraints': '1 <= len(nums) <= 10^4\nAll values are integers',
        'examples': [
            {'input': '[1,2,2,3,4]', 'output': '{"mean": 2.4, "median": 2, "mode": 2}', 'explanation': 'Mode = 2 (appears twice); median = 2 (middle of sorted list)'},
        ],
        'hints': [
            'Mean = sum(nums) / len(nums)',
            'Sort the list; median is nums[len//2] for odd length, average of two middle for even.',
            'Use Counter from collections to find the mode.',
        ],
        'test_cases': [
            {'input': '[1,2,2,3,4]',    'expected': 'mean=2.4 median=2 mode=2'},
            {'input': '[5,5,5,5]',      'expected': 'mean=5.0 median=5 mode=5'},
            {'input': '[1,2,3,4,5,6]',  'expected': 'mean=3.5 median=3 mode=1'},
        ],
        'starter_code': {
            'python': 'from collections import Counter\n\ndef stats(nums: list) -> dict:\n    # Calculate mean\n    mean = 0  # fix this\n    # Calculate median\n    median = 0  # fix this\n    # Calculate mode\n    mode = 0  # fix this\n    return {"mean": mean, "median": median, "mode": mode}\n\nprint(stats([1, 2, 2, 3, 4]))',
        },
    },

    {
        'title': 'Linear Regression from Scratch',
        'category': 'data_science',
        'difficulty': 'medium',
        'xp_reward': 120,
        'description': """## Simple Linear Regression

Implement **simple linear regression** from scratch using the least squares formula. Given lists `X` (features) and `Y` (labels), compute the slope `m` and intercept `b` such that `Y ≈ m*X + b`.

**Formulas:**
```
m = (n * Σ(x*y) - Σx * Σy) / (n * Σ(x²) - (Σx)²)
b = (Σy - m * Σx) / n
```

Return `(m, b)` rounded to 4 decimal places.
""",
        'constraints': '2 <= len(X) = len(Y) <= 10^4\nAll values are floats',
        'examples': [
            {'input': 'X=[1,2,3,4,5], Y=[2,4,5,4,5]', 'output': '(0.6, 2.2)', 'explanation': 'Best fit line through the data points.'},
        ],
        'hints': [
            'Compute: n = len(X), sum_x, sum_y, sum_xy, sum_x2',
            'Plug into the formula directly — no library imports needed!',
        ],
        'test_cases': [
            {'input': '[1,2,3,4,5] [2,4,5,4,5]', 'expected': 'm=0.6 b=2.2'},
            {'input': '[1,2,3] [1,2,3]',          'expected': 'm=1.0 b=0.0'},
        ],
        'starter_code': {
            'python': 'def linear_regression(X: list, Y: list):\n    n = len(X)\n    # Compute required sums\n    sum_x  = sum(X)\n    sum_y  = sum(Y)\n    sum_xy = sum(x * y for x, y in zip(X, Y))\n    sum_x2 = sum(x ** 2 for x in X)\n    # Compute slope and intercept\n    m = 0  # fix this\n    b = 0  # fix this\n    return round(m, 4), round(b, 4)\n\nprint(linear_regression([1,2,3,4,5], [2,4,5,4,5]))',
        },
    },

    # ─── SQL ──────────────────────────────────────────────────────
    {
        'title': 'Find Employees with Salary > Average',
        'category': 'sql',
        'difficulty': 'easy',
        'xp_reward': 40,
        'description': """## SQL: Above Average Salary

Given an `employees` table with columns `id`, `name`, `salary`, `department`:

Write a query to return the **name** and **salary** of all employees whose salary is **above the company average**.

Sort the results by salary in **descending order**.
""",
        'constraints': 'Table: employees(id, name, salary, department)',
        'examples': [
            {'input': 'employees with salaries: [50k, 60k, 80k, 45k]', 'output': 'Returns employees with 60k and 80k (avg=58.75k)', 'explanation': 'Only employees earning above average.'},
        ],
        'hints': [
            'Use a subquery: WHERE salary > (SELECT AVG(salary) FROM employees)',
            'Add ORDER BY salary DESC at the end.',
        ],
        'test_cases': [
            {'input': 'sql_query', 'expected': 'SELECT name, salary FROM employees WHERE salary > (SELECT AVG(salary) FROM employees) ORDER BY salary DESC'},
        ],
        'starter_code': {
            'sql': '-- Write your SQL query below\nSELECT name, salary\nFROM employees\nWHERE salary > (\n    -- Subquery to get average salary\n    \n)\nORDER BY salary DESC;',
        },
    },

    # ─── TREES ────────────────────────────────────────────────────
    {
        'title': 'Binary Tree Inorder Traversal',
        'category': 'trees',
        'difficulty': 'easy',
        'xp_reward': 60,
        'description': """## Binary Tree Inorder Traversal

Given the `root` of a binary tree, return the **inorder traversal** of its nodes' values.

**Inorder traversal:** Left → Root → Right

```
      1
       \\
        2
       /
      3
```
Output: [1, 3, 2]
""",
        'constraints': '0 <= Number of nodes <= 100',
        'examples': [
            {'input': 'root = [1,null,2,3]', 'output': '[1,3,2]', 'explanation': 'Inorder: visit left, then root, then right.'},
        ],
        'hints': [
            'Use recursion: inorder(node.left) → append node.val → inorder(node.right)',
            'Base case: if node is None, return.',
        ],
        'test_cases': [
            {'input': 'tree: 1->2->3', 'expected': '[1, 3, 2]'},
        ],
        'starter_code': {
            'python': 'class TreeNode:\n    def __init__(self, val=0, left=None, right=None):\n        self.val = val\n        self.left = left\n        self.right = right\n\ndef inorder_traversal(root):\n    result = []\n    def helper(node):\n        if node is None:\n            return\n        # Left, Root, Right\n        helper(node.left)\n        result.append(node.val)\n        helper(node.right)\n    helper(root)\n    return result',
        },
    },

    # ─── SORTING ──────────────────────────────────────────────────
    {
        'title': 'Merge Sort Implementation',
        'category': 'sorting',
        'difficulty': 'medium',
        'xp_reward': 90,
        'description': """## Implement Merge Sort

Implement **merge sort** to sort a list in ascending order. Merge sort is a divide-and-conquer algorithm with O(n log n) time complexity.

**Algorithm:**
1. Divide the list in half
2. Recursively sort both halves
3. Merge the two sorted halves
""",
        'constraints': '0 <= len(nums) <= 10^5',
        'examples': [
            {'input': '[38,27,43,3,9,82,10]', 'output': '[3,9,10,27,38,43,82]', 'explanation': 'Divide and merge recursively.'},
        ],
        'hints': [
            'Split: left = arr[:mid], right = arr[mid:]',
            'In the merge step: compare first elements of both halves, pick the smaller one.',
            'Don\'t modify the input array directly — create new lists.',
        ],
        'test_cases': [
            {'input': '[38,27,43,3,9,82,10]', 'expected': '[3,9,10,27,38,43,82]'},
            {'input': '[5,4,3,2,1]',          'expected': '[1,2,3,4,5]'},
            {'input': '[1]',                  'expected': '[1]'},
        ],
        'starter_code': {
            'python': 'def merge_sort(arr: list) -> list:\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(left, right):\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        # Compare and append the smaller element\n        pass\n    # Append remaining elements\n    return result\n\nprint(merge_sort([38, 27, 43, 3, 9, 82, 10]))',
        },
    },
]


class Command(BaseCommand):
    help = 'Seeds the database with curated coding challenges'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for i, data in enumerate(CHALLENGES):
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
                    'order':       i,
                }
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {obj.title}'))
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(f'  Skipped: {obj.title}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {created} challenges created, {skipped} already existed.'
        ))
