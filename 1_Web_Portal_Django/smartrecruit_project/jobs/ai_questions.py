"""
Enhanced AI Interview Question Database
Organized by domain, difficulty level, and technology stack
"""

AI_INTERVIEW_QUESTIONS = {
    # ===== PYTHON & BACKEND =====
    'python': {
        'easy': [
            "What are the key differences between lists and tuples in Python?",
            "Explain what a decorator is in Python and give an example use case.",
            "What is the difference between '==' and 'is' in Python?",
            "How does Python's garbage collection work?",
            "What are Python's built-in data types?",
        ],
        'medium': [
            "Explain the concept of generators in Python and when you would use them.",
            "What is the Global Interpreter Lock (GIL) and how does it affect multithreading?",
            "Describe the difference between deep copy and shallow copy.",
            "How would you implement a singleton pattern in Python?",
            "Explain Python's context managers and the 'with' statement.",
        ],
        'hard': [
            "Explain metaclasses in Python and provide a practical use case.",
            "How would you optimize a Python application for performance?",
            "Describe the difference between multiprocessing and multithreading in Python.",
            "Explain how Python's memory management works in detail.",
            "How would you implement a custom iterator and iterable class?",
        ]
    },
    
    # ===== MACHINE LEARNING & AI =====
    'machine_learning': {
        'easy': [
            "What is the difference between supervised and unsupervised learning?",
            "Explain what overfitting is and how to prevent it.",
            "What is the purpose of train-test split in machine learning?",
            "Describe the difference between classification and regression.",
            "What is a confusion matrix and what does it tell you?",
        ],
        'medium': [
            "Explain the bias-variance tradeoff in machine learning.",
            "How does gradient descent work? What are its variants?",
            "Describe the architecture of a convolutional neural network (CNN).",
            "What is regularization and why is it important?",
            "Explain the difference between bagging and boosting.",
        ],
        'hard': [
            "How would you design a recommendation system for an e-commerce platform?",
            "Explain the attention mechanism in transformer models.",
            "How would you handle class imbalance in a dataset?",
            "Describe the architecture and training process of GANs.",
            "How would you deploy a machine learning model to production?",
        ]
    },
    
    # ===== WEB DEVELOPMENT =====
    'web_development': {
        'easy': [
            "What is the difference between GET and POST HTTP methods?",
            "Explain what RESTful APIs are and their key principles.",
            "What is CORS and why is it important?",
            "Describe the difference between cookies and sessions.",
            "What is the purpose of HTTP status codes?",
        ],
        'medium': [
            "How would you implement authentication and authorization in a web application?",
            "Explain the concept of middleware in web frameworks.",
            "What is SQL injection and how do you prevent it?",
            "Describe the MVC (Model-View-Controller) pattern.",
            "How would you optimize a web application's performance?",
        ],
        'hard': [
            "Design a scalable architecture for a high-traffic web application.",
            "How would you implement real-time features using WebSockets?",
            "Explain database sharding and when you would use it.",
            "How would you implement a microservices architecture?",
            "Describe strategies for handling distributed transactions.",
        ]
    },
    
    # ===== DATA STRUCTURES & ALGORITHMS =====
    'algorithms': {
        'easy': [
            "Explain the difference between an array and a linked list.",
            "What is the time complexity of binary search?",
            "Describe how a stack works and give a use case.",
            "What is a hash table and how does it work?",
            "Explain the concept of Big O notation.",
        ],
        'medium': [
            "How would you detect a cycle in a linked list?",
            "Explain different tree traversal algorithms.",
            "What is dynamic programming? Provide an example.",
            "How would you implement a LRU cache?",
            "Describe the difference between BFS and DFS.",
        ],
        'hard': [
            "Design an algorithm to find the shortest path in a weighted graph.",
            "How would you implement a trie data structure?",
            "Explain the A* pathfinding algorithm.",
            "How would you solve the traveling salesman problem?",
            "Design a data structure for a social network's friend suggestions.",
        ]
    },
    
    # ===== DATABASES =====
    'database': {
        'easy': [
            "What is the difference between SQL and NoSQL databases?",
            "Explain what database normalization is.",
            "What is a primary key and a foreign key?",
            "Describe the ACID properties of databases.",
            "What is an index and why is it useful?",
        ],
        'medium': [
            "Explain different types of database joins.",
            "What is database denormalization and when would you use it?",
            "How do database transactions work?",
            "Describe the CAP theorem.",
            "What are database triggers and stored procedures?",
        ],
        'hard': [
            "How would you design a database schema for a social media platform?",
            "Explain database replication and its different strategies.",
            "How would you optimize slow database queries?",
            "Describe the differences between OLTP and OLAP systems.",
            "How would you implement database partitioning?",
        ]
    },
    
    # ===== CLOUD & DEVOPS =====
    'cloud_devops': {
        'easy': [
            "What is the difference between IaaS, PaaS, and SaaS?",
            "Explain what containerization is.",
            "What is CI/CD and why is it important?",
            "Describe what Docker is and its benefits.",
            "What is version control and why do we use it?",
        ],
        'medium': [
            "How would you set up a CI/CD pipeline?",
            "Explain the concept of infrastructure as code.",
            "What is Kubernetes and what problems does it solve?",
            "Describe different cloud deployment models.",
            "How would you implement monitoring and logging for a production system?",
        ],
        'hard': [
            "Design a highly available and fault-tolerant cloud architecture.",
            "How would you implement zero-downtime deployments?",
            "Explain service mesh architecture and when to use it.",
            "How would you handle disaster recovery in the cloud?",
            "Describe strategies for cost optimization in cloud infrastructure.",
        ]
    },
    
    # ===== SYSTEM DESIGN =====
    'system_design': {
        'easy': [
            "What is load balancing and why is it important?",
            "Explain what caching is and its benefits.",
            "What is horizontal vs vertical scaling?",
            "Describe the concept of a CDN (Content Delivery Network).",
            "What is an API gateway?",
        ],
        'medium': [
            "How would you design a URL shortening service like bit.ly?",
            "Explain different caching strategies.",
            "How would you design a rate limiting system?",
            "Describe the publish-subscribe pattern.",
            "How would you implement a distributed cache?",
        ],
        'hard': [
            "Design a system like Twitter/X that can handle millions of users.",
            "How would you design a distributed file storage system?",
            "Explain how you would design a real-time messaging system.",
            "How would you design a search engine?",
            "Design a video streaming platform like YouTube.",
        ]
    },
}


# Follow-up questions based on initial responses
FOLLOW_UP_QUESTIONS = {
    'clarification': [
        "Can you elaborate on that point?",
        "What would be the trade-offs of that approach?",
        "How would you handle edge cases?",
        "Can you provide a specific example?",
    ],
    'deeper': [
        "How would you optimize that solution?",
        "What are the time and space complexity considerations?",
        "How would this scale with large datasets?",
        "What alternatives did you consider?",
    ],
    'practical': [
        "How would you implement this in a production environment?",
        "What testing strategy would you use?",
        "How would you monitor this in production?",
        "What security considerations are there?",
    ]
}


def get_questions_by_domain(domain, difficulty='medium', count=5):
    """
    Get random questions for a specific domain and difficulty
    """
    import random
    
    domain_questions = AI_INTERVIEW_QUESTIONS.get(domain, {})
    difficulty_questions = domain_questions.get(difficulty, [])
    
    if not difficulty_questions:
        # Fallback to medium if difficulty not found
        difficulty_questions = domain_questions.get('medium', [])
    
    # Return random sample
    return random.sample(difficulty_questions, min(count, len(difficulty_questions)))


def get_mixed_difficulty_questions(domain, count=5):
    """
    Get a mix of questions across different difficulty levels
    """
    import random
    
    domain_questions = AI_INTERVIEW_QUESTIONS.get(domain, {})
    
    questions = []
    # 2 easy, 2 medium, 1 hard
    questions.extend(random.sample(domain_questions.get('easy', []), min(2, len(domain_questions.get('easy', [])))))
    questions.extend(random.sample(domain_questions.get('medium', []), min(2, len(domain_questions.get('medium', [])))))
    questions.extend(random.sample(domain_questions.get('hard', []), min(1, len(domain_questions.get('hard', [])))))
    
    random.shuffle(questions)
    return questions[:count]


def get_follow_up_question(category='clarification'):
    """
    Get a random follow-up question
    """
    import random
    return random.choice(FOLLOW_UP_QUESTIONS.get(category, FOLLOW_UP_QUESTIONS['clarification']))
