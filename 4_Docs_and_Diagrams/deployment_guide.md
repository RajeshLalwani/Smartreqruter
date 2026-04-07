# Deployment & Run Guide

## Prerequisites
- **Python 3.10+** (Recommend 3.11 for compatibility)
- **pip** (Python Packet Manager)
- **Virtual Environment** (Recommended)

## 1. Environment Setup

### Clone/Navigate to Project Root
```bash
cd "C:\Users\ASUS\Documents\Tech Elecon Pvt. Ltd\Project\SmartRecruit"
```

### Create Virtual Environment
```bash
python -m venv venv
# Activate
.\venv\Scripts\activate
```

### Install Dependencies
```bash
pip install django djangorestframework django-bootstrap-v5 pillow
pip install spacy pypdf scikit-learn
pip install psycopg2-binary # If using PostgreSQL
```

### Download NLP Models
For the AI Resume Parser to work, you need the English language model:
```bash
python -m spacy download en_core_web_sm
```

## 2. Database Setup

### Migrations
Initialize the database (SQLite by default, or Postgres if configured in settings):
```bash
cd 1_Web_Portal_Django/smartrecruit_project
python manage.py makemigrations
python manage.py migrate
```

### Create Admin User
```bash
python manage.py createsuperuser
```

## 3. Running the Server

### Start Django
```bash
python manage.py runserver
```

Access the portal at: `http://127.0.0.1:8000/`

## 4. Folder Structure (Key Areas)

- `1_Web_Portal_Django/`: The core Django application.
    - `core/`: Authentication, Dashboards, Global Templates.
    - `jobs/`: Job Posting, Applications, Interviews, AI Integration logic.
- `2_AI_Modules/`: Standalone Python scripts for AI logic.
    - `Resume_Parser/`: `parser.py` (Text extraction & scoring).
    - `Interview_Bot/`: `interviewer.py` (Q&A Logic).
    - `Proctoring_System/`: `monitor.js` (Frontend monitoring).
- `3_Database_Schema/`: Schema documentation.
- `4_Docs_and_Diagrams/`: Architecture & Sequence Diagrams.

## Troubleshooting

- **ModuleNotFoundError: No module named 'Resume_Parser'**:
  - Ensure `sys.path` assumes the project structure where `2_AI_Modules` is a sibling of `1_Web_Portal_Django`.
  - Check `smartrecruit_project/settings.py` or `jobs/utils.py` for the path hack configuration.

- **TemplateDoesNotExist**:
  - Verify that `TEMPLATES['DIRS']` in `settings.py` points to the global templates folder.
