# SmartRecruit - AI-Powered Recruitment Portal

SmartRecruit is a next-generation recruitment platform that leverages Artificial Intelligence to streamline the hiring process. It features an automated resume parser, intelligent candidate screening, AI-driven technical interviews, and a secure proctoring system for online assessments.

## 🚀 Key Features

*   **Smart Resume Parsing**: Automatically extracts skills, experience, and contact info from resumes (PDF/DOCX) using NLP (SpaCy).
*   **AI Screening & Scoring**: Ranks candidates based on job description relevance using TF-IDF and keyword matching.
*   **Automated Assessments**:
    *   **Round 1 (Aptitude)** & **Round 2 (Practical)**: Online tests with auto-grading.
    *   **Proctoring**: Detects tab switching and enforces fullscreen mode to ensure integrity.
*   **AI Interview Bot (Round 3)**: A conversational AI agent that conducts technical interviews, asks dynamic questions, and evaluates answers with sentiment analysis.
*   **Recruiter Dashboard**: Post jobs, view analytics, manage applications, and generate offer letters.
*   **Candidate Dashboard**: Track application status, take tests, and view feedback.
*   **Email Notifications**: Automated updates for shortlisting, assessment results, and offer letters.

## 🛠️ Tech Stack

*   **Backend**: Python, Django, Django REST Framework
*   **Frontend**: HTML5, CSS3, JavaScript (Vanilla + Bootstrap 5)
*   **AI/ML**: SpaCy (NLP), Scikit-learn (Ranking), PyPDF (Text Extraction), OpenCV (Proctoring/Monitoring logic)
*   **Database**: SQLite (Dev) / PostgreSQL (Prod)

## ⚙️ Setup & Installation

### 1. Prerequisites
*   Python 3.10 or higher
*   Git

### 2. Clone the Repository
```bash
git clone https://github.com/your-repo/smartrecruit.git
cd smartrecruit
```

### 3. Create Virtual Environment
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Download Language Model
The resume parser requires the English language model from SpaCy:
```bash
python -m spacy download en_core_web_sm
```

### 6. Database Setup
```bash
cd 1_Web_Portal_Django/smartrecruit_project
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Admin User
```bash
python manage.py createsuperuser
```

### 8. Run the Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

## 📂 Project Structure

*   `1_Web_Portal_Django/`: Main web application code.
    *   `core/`: Authentication and dashboard logic.
    *   `jobs/`: Recruitment workflow (Jobs, Applications, Interviews).
*   `2_AI_Modules/`: Standalone AI components.
    *   `Resume_Parser/`: Script for text extraction and scoring.
    *   `Interview_Bot/`: Logic for generating questions and analyzing responses.
    *   `Proctoring_System/`: JavaScript/Python logic for exam monitoring.
*   `3_Database_Schema/`: ERD and schema documentation.
*   `4_Docs_and_Diagrams/`: Architecture diagrams and guides.

## 📧 Email Configuration
To enable email notifications, update the following in `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## 🤝 Contribution
1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes.
4.  Push `git push origin feature/AmazingFeature`.
5.  Open a Pull Request.

## 📄 License
Distributed under the MIT License.
