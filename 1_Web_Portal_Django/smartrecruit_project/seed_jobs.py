import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
from jobs.models import JobPosting, Technology

def seed():
    # Find or create a default recruiter
    recruiter = User.objects.filter(is_staff=True).first()
    if not recruiter:
        try:
            # Maybe the user custom model has recruiter flag
            recruiter = User.objects.filter(is_recruiter=True).first()
        except:
            pass
            
    if not recruiter:
        print("No recruiter found. Creating a generic 'hr_admin' user.")
        recruiter = User.objects.create_user(username='hr_admin', password='password123', email='hr@irinfotech.com', first_name='HR', last_name='Admin')
        try:
            recruiter.is_recruiter = True
            recruiter.save()
        except:
            pass

    # Ensure technologies exist
    python_tech, _ = Technology.objects.get_or_create(name='Python')
    react_tech, _ = Technology.objects.get_or_create(name='React')
    java_tech, _ = Technology.objects.get_or_create(name='Java')
    aws_tech, _ = Technology.objects.get_or_create(name='AWS / Cloud computing')

    # Wipe existing generic/test jobs (for example, jobs with 'test' in title)
    deleted, _ = JobPosting.objects.filter(title__icontains='test').delete()
    print(f"Deleted {deleted} test jobs.")

    jobs_data = [
        {
            'title': 'Senior Python Backend Engineer',
            'description': '''<p>IR Info Tech is seeking an experienced Backend Engineer to architect, build, and scale our core API services. You will join our high-performance infrastructure team to drive the evolution of our Neural Recruitment platform.</p>
<h4>Key Responsibilities:</h4>
<ul>
<li>Design and implement highly available and scalable backend microservices.</li>
<li>Collaborate with Data Science teams to integrate ML pipelines directly into our Django ecosystems.</li>
<li>Optimize PostgreSQL databases and query performance for big data workloads.</li>
<li>Write clean, tested, and maintainable code adhering to PEP8 standards.</li>
</ul>
<h4>Requirements:</h4>
<ul>
<li>Strong foundation in Python and Django/FastAPI frameworks.</li>
<li>Experience with Redis, Celery, and asynchronous messaging queues.</li>
<li>Understanding of containerization (Docker, Kubernetes).</li>
</ul>''',
            'job_type': 'FT',
            'status': 'OPEN',
            'location': 'Mumbai, India (Hybrid)',
            'salary_range': '₹ 18,00,000 - ₹ 32,00,000 PA',
            'min_experience': 4,
            'required_skills': 'Python, Django, PostgreSQL, Redis, Celery, Docker, REST APIs, System Architecture',
            'technology': python_tech,
            'aptitude_difficulty': 'HARD',
            'practical_difficulty': 'HARD',
            'deadline': timezone.now() + timedelta(days=30),
        },
        {
            'title': 'Frontend React Developer (UI/UX Focused)',
            'description': '''<p>We are looking for a creative Frontend Engineer who is obsessed with delivering pixel-perfect user experiences and writing modular components.</p>
<h4>Key Responsibilities:</h4>
<ul>
<li>Translate Figma designs into responsive, beautiful React components.</li>
<li>Manage global application state using Redux Toolkit or Context API.</li>
<li>Optimize application load times and Web Core Vitals.</li>
<li>Implement sophisticated UI animations and glassmorphic designs.</li>
</ul>
<h4>Requirements:</h4>
<ul>
<li>Deep expertise in React.js and modern JavaScript (ES6+).</li>
<li>Experience with modern CSS structures (Tailwind, SCSS).</li>
<li>A keen eye for design aesthetics and UI/UX principles.</li>
</ul>''',
            'job_type': 'FT',
            'status': 'OPEN',
            'location': 'Bangalore, India (Remote allowed)',
            'salary_range': '₹ 12,00,000 - ₹ 20,00,000 PA',
            'min_experience': 2,
            'required_skills': 'React, JavaScript, TypeScript, CSS3, Redux, UI/UX, Webpack',
            'technology': react_tech,
            'aptitude_difficulty': 'MEDIUM',
            'practical_difficulty': 'MEDIUM',
            'deadline': timezone.now() + timedelta(days=15),
        },
        {
            'title': 'Cloud Infrastructure Architect (AWS)',
            'description': '''<p>Join our Cloud Operations division to design and maintain our fault-tolerant AWS infrastructure supporting thousands of concurrent AI evaluations.</p>
<h4>Key Responsibilities:</h4>
<ul>
<li>Design and deploy scalable cloud architectures on AWS.</li>
<li>Implement continuous integration and deployment (CI/CD) pipelines.</li>
<li>Maintain strict security protocols and automate infrastructure provisioning using Terraform.</li>
</ul>
<h4>Requirements:</h4>
<ul>
<li>AWS Certified Solutions Architect (Preferred).</li>
<li>Strong scripting skills in Bash or Python.</li>
<li>Experience with ECS, EKS, RDS, and CloudFront.</li>
</ul>''',
            'job_type': 'CT',
            'status': 'OPEN',
            'location': 'Remote (Global)',
            'salary_range': 'Competitive / Based on experience',
            'min_experience': 5,
            'required_skills': 'AWS, DevOps, CI/CD, Terraform, Kubernetes, Bash, Cloud Security',
            'technology': aws_tech,
            'aptitude_difficulty': 'HARD',
            'practical_difficulty': 'EXPERT',
            'deadline': timezone.now() + timedelta(days=45),
        },
        {
            'title': 'Machine Learning Intern',
            'description': '''<p>Looking to kickstart your career in Artificial Intelligence? Join us for a 6-month intensive internship where you'll work alongside our lead AI researchers.</p>
<h4>Key Responsibilities:</h4>
<ul>
<li>Assist in training and fine-tuning robust NLP models.</li>
<li>Perform extensive data cleaning and dataset augmentation.</li>
<li>Write scripts to evaluate model precision and recall.</li>
</ul>
<h4>Requirements:</h4>
<ul>
<li>Enrolled in or recently graduated with a B.Tech/M.Tech in Computer Science.</li>
<li>Familiarity with Pandas, NumPy, and basic PyTorch/TensorFlow.</li>
<li>A passion for deep learning and continuous research.</li>
</ul>''',
            'job_type': 'IN',
            'status': 'OPEN',
            'location': 'Pune, India (On-site)',
            'salary_range': '₹ 30,000 / month stipend',
            'min_experience': 0,
            'required_skills': 'Python, Machine Learning, Data Science, NLP, Mathematics',
            'technology': python_tech,
            'aptitude_difficulty': 'MEDIUM',
            'practical_difficulty': 'EASY',
            'deadline': timezone.now() + timedelta(days=7),
        }
    ]

    for data in jobs_data:
        # Avoid duplicates based on title
        if not JobPosting.objects.filter(title=data['title']).exists():
            data['recruiter'] = recruiter
            JobPosting.objects.create(**data)
            print(f"Created job: {data['title']}")
        else:
            print(f"Job already exists: {data['title']}")

    print("Database seeding completed.")

if __name__ == '__main__':
    seed()
