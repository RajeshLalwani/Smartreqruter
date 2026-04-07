
from jobs.models import CodingChallenge
import json

challenges = [
    {
        "title": "Validate Binary Search Tree",
        "slug": "validate-bst",
        "description": "Given the root of a binary tree, determine if it is a valid binary search tree (BST).",
        "difficulty": "medium",
        "category": "trees",
        "xp_reward": 100,
        "starter_code": {"python": "class TreeNode:\n    def __init__(self, val=0, left=None, right=None):\n        self.val = val\n        self.left = left\n        self.right = right\n\ndef isValidBST(root):\n    # Write your solution here\n    pass"},
        "test_cases": [{"input": "[2,1,3]", "expected": "true"}],
    },
    {
        "title": "Kth Largest Element in an Array",
        "slug": "kth-largest",
        "description": "Find the kth largest element in an unsorted array.",
        "difficulty": "medium",
        "category": "sorting",
        "xp_reward": 80,
        "starter_code": {"python": "def findKthLargest(nums, k):\n    # Write your solution here\n    pass"},
        "test_cases": [{"input": "[3,2,1,5,6,4], 2", "expected": "5"}],
    },
    {
        "title": "Word Search",
        "slug": "word-search",
        "description": "Given an m x n board and a word, find if the word exists in the grid.",
        "difficulty": "hard",
        "category": "recursion",
        "xp_reward": 150,
        "starter_code": {"python": "def exist(board, word):\n    # Write your solution here\n    pass"},
        "test_cases": [{"input": "[['A','B','C','E'],['S','F','C','S'],['A','D','E','E']], 'ABCCED'", "expected": "true"}],
    },
    {
        "title": "Coin Change",
        "slug": "coin-change",
        "description": "Find the fewest number of coins that you need to make up a given amount.",
        "difficulty": "medium",
        "category": "dp",
        "xp_reward": 120,
        "starter_code": {"python": "def coinChange(coins, amount):\n    # Write your solution here\n    pass"},
        "test_cases": [{"input": "[1,2,5], 11", "expected": "3"}],
    },
    {
        "title": "Merge Intervals",
        "slug": "merge-intervals",
        "description": "Given an array of intervals, merge all overlapping intervals.",
        "difficulty": "medium",
        "category": "arrays",
        "xp_reward": 90,
        "starter_code": {"python": "def merge(intervals):\n    # Write your solution here\n    pass"},
        "test_cases": [{"input": "[[1,3],[2,6],[8,10],[15,18]]", "expected": "[[1,6],[8,10],[15,18]]"}],
    },
    {
        "title": "Trapping Rain Water",
        "slug": "trapping-rain-water",
        "description": "Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.",
        "difficulty": "hard",
        "category": "arrays",
        "xp_reward": 200,
        "starter_code": {"python": "def trap(height):\n    # Write your solution here\n    pass"},
        "test_cases": [{"input": "[0,1,0,2,1,0,1,3,2,1,2,1]", "expected": "6"}],
    },
    {
        "title": "Course Schedule",
        "slug": "course-schedule",
        "description": "There are a total of numCourses courses you have to take, labeled from 0 to numCourses - 1. Some courses may have prerequisites. Return true if you can finish all courses.",
        "difficulty": "medium",
        "category": "trees",
        "xp_reward": 130,
        "starter_code": {"python": "def canFinish(numCourses, prerequisites):\n    # Write your solution here\n    pass"},
        "test_cases": [{"input": "2, [[1,0]]", "expected": "true"}],
    }
]

for ch in challenges:
    CodingChallenge.objects.get_or_create(
        slug=ch['slug'],
        defaults={
            "title": ch['title'],
            "description": ch['description'],
            "difficulty": ch['difficulty'],
            "category": ch['category'],
            "xp_reward": ch['xp_reward'],
            "starter_code": ch['starter_code'],
            "test_cases": ch['test_cases'],
            "is_active": True
        }
    )

print("Added more challenges successfully.")
