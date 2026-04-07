import os
import sys
import django
from io import BytesIO
from django.core.files.base import ContentFile

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartrecruit_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from jobs.models import Candidate
from xhtml2pdf import pisa

User = get_user_model()

def generate_pdf_resume(html_content, filename):
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("utf-8")), result)
    if not pdf.err:
         return ContentFile(result.getvalue(), name=filename)
    return None

def create_sample_candidate():
    print("Creating sample candidate profiles and resumes...")
    
    # Candidate 1: Strong Python/Django Developer
    html_1 = """
    <html>
    <head><style>body { font-family: Helvetica, sans-serif; }</style></head>
    <body>
        <h1>Jane Doe</h1>
        <p>Email: jane.doe@example.com | Phone: 555-0100</p>
        <h2>Professional Summary</h2>
        <p>Senior Backend Engineer with 5+ years of experience specializing in Python, Django, and RESTful APIs. Proven track record of architecting scalable web applications and optimizing database performance.</p>
        <h2>Technical Skills</h2>
        <p><strong>Languages:</strong> Python, JavaScript, SQL</p>
        <p><strong>Frameworks:</strong> Django, Django Rest Framework (DRF), React</p>
        <p><strong>Databases:</strong> PostgreSQL, MySQL, Redis</p>
        <p><strong>DevOps:</strong> AWS, Docker, Kubernetes, CI/CD</p>
        <h2>Experience</h2>
        <h3>Backend Developer | TechCorp (2020 - Present)</h3>
        <ul>
            <li>Developed scalable microservices using Python and Django.</li>
            <li>Designed and implemented RESTful APIs consumed by millions of users.</li>
            <li>Optimized PostgreSQL queries reducing latency by 40%.</li>
        </ul>
        <h2>Education</h2>
        <p>B.S. in Computer Science, University of Technology (2018)</p>
    </body>
    </html>
    """
    
    # Create or update User
    user1, created1 = User.objects.get_or_create(username='janedoe', defaults={
        'first_name': 'Jane',
        'last_name': 'Doe',
        'email': 'jane.doe@example.com'
    })
    if created1:
        user1.set_password('TestPass123!')
        user1.save()
        
    candidate1, created_cand1 = Candidate.objects.get_or_create(user=user1, defaults={
        'full_name': 'Jane Doe',
        'email': 'jane.doe@example.com',
        'phone': '555-0100',
        'experience_years': 5.0,
        'current_location': 'New York, NY'
    })
    
    pdf1 = generate_pdf_resume(html_1, 'janedoe_resume.pdf')
    if pdf1:
        candidate1.resume_file = pdf1
        candidate1.save()
        print("Created Jane Doe (Python/Django Candidate)")

    # Candidate 2: Data Scientist / ML Engineer
    html_2 = """
    <html>
    <head><style>body { font-family: Helvetica, sans-serif; }</style></head>
    <body>
        <h1>John Smith</h1>
        <p>Email: john.smith@example.com | Phone: 555-0200</p>
        <h2>Professional Summary</h2>
        <p>Data Scientist and Machine Learning Engineer passionate about building intelligent systems. Experienced in predictive modeling, NLP, and implementing ML pipelines.</p>
        <h2>Technical Skills</h2>
        <p><strong>Languages:</strong> Python, R, SQL</p>
        <p><strong>ML/AI:</strong> Scikit-Learn, TensorFlow, PyTorch, Pandas, NumPy</p>
        <p><strong>Tools:</strong> Jupyter, Git, AWS SageMaker</p>
        <h2>Experience</h2>
        <h3>Data Scientist | DataAI Inc (2021 - Present)</h3>
        <ul>
            <li>Built predictive models increasing customer retention by 20%.</li>
            <li>Developed NLP models for sentiment analysis on product reviews.</li>
            <li>Deployed machine learning models to production using FastAPI and Docker.</li>
        </ul>
        <h2>Education</h2>
        <p>M.S. in Data Science, AI State University (2021)</p>
    </body>
    </html>
    """
    
    user2, created2 = User.objects.get_or_create(username='johnsmith', defaults={
        'first_name': 'John',
        'last_name': 'Smith',
        'email': 'john.smith@example.com'
    })
    if created2:
        user2.set_password('TestPass123!')
        user2.save()
        
    candidate2, created_cand2 = Candidate.objects.get_or_create(user=user2, defaults={
        'full_name': 'John Smith',
        'email': 'john.smith@example.com',
        'phone': '555-0200',
        'experience_years': 3.0,
        'current_location': 'San Francisco, CA'
    })
    
    pdf2 = generate_pdf_resume(html_2, 'johnsmith_resume.pdf')
    if pdf2:
        candidate2.resume_file = pdf2
        candidate2.save()
        print("Created John Smith (Data Science / ML Candidate)")

if __name__ == "__main__":
    create_sample_candidate()
    print("Done generating sample data.")
