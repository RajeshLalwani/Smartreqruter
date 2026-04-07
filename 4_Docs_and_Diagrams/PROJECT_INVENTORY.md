# SmartRecruit — Project Inventory & Feature Matrix

## 1. Core AI Suite

| Feature | Description | Key Files |
| :--- | :--- | :--- |
| **AI Interviewer** | Real-time audio/text interview engine with dynamic question generation. | `jobs/sentiment_analysis.py`, `jobs/views_candidate.py`, `core/templates/jobs/interview_session.html` |
| **Neural Sentiment tracking** | Camera-based real-time emotion analysis (Confident, Focused, Stressed). | `core/utils/ai_logic.py`, `core/views.py` (`save_sentiment_data`), `core/templates/base.html` |
| **Global AI Chatbot** | Sitewide assistant for candidates and recruiters with TTS capabilities. | `core/views.py` (`chatbot_api`), `core/templates/base.html` (JS + Widget) |
| **Voice Assistant** | Native Text-to-Speech (TTS) for AI responses. | `core/views.py` (`voice_assistant_api`), `core/templates/base.html` |
| **Text Sentiment Analysis** | NLP analysis of interview transcripts to detect honesty and clarity. | `jobs/sentiment_analysis.py`, `jobs/models.py` (`SentimentLog`) |

## 2. Assessment & Technical Testing

| Feature | Description | Key Files |
| :--- | :--- | :--- |
| **Code Execution (Piston)** | Secure, real-time code execution for 20+ programming languages. | `jobs/piston_api.py` (integrated in views), `jobs/views_candidate.py` |
| **Question Bank API** | Automated fetching and scaling of 150+ categorized questions per domain. | `jobs/utils.py`, `jobs/api_views.py` |
| **Assessment Dashboard** | Recruiters can preview, categorize, and manage large-scale tests. | `core/templates/jobs/preview_assessment.html`, `jobs/views.py` |
| **Automatic Grading** | System-wide scoring of assessments and interviews. | `jobs/models.py` (`AssessmentResult`, `Interview`) |

## 3. Communication & Automation

| Feature | Description | Key Files |
| :--- | :--- | :--- |
| **WhatsApp Integration** | Real-time event notifications via Twilio (New application, Interviews). | `core/utils/twilio_api.py`, `core/utils/webhooks.py` |
| **Email Notifier** | SMTP-based transactional emails for registration and status updates. | `core/views.py` (`register_view`, `forgot_password_view`) |
| **Offer Letter PDF** | Dynamic generation of professional Offer Letters with branding. | `core/templates/jobs/offer_letter_pdf.html`, `jobs/views.py` |
| **Document Scanning** | OCR tracking for candidate resumes and documents. | `jobs/candidate_profile.py` (pytesseract/pdf2image) |

## 4. UI/UX Design System

| Component | Description | Key Files |
| :--- | :--- | :--- |
| **"Smart Glass" System** | Modern glassmorphism UI language applied sitewide. | `static/css/professional_ui.css`, `static/css/base.css` |
| **Midnight Dark Theme** | Premium dark mode fully implemented across all portals. | `core/templates/base.html` (Theme Engine logic) |
| **Thunder Preloader** | High-performance system-wide loading animations. | `static/css/preloader.css`, `core/templates/base.html` |
| **Responsive Portals** | Mobile-optimized views for Career Multiverse and Job Tracking. | `core/templates/jobs/career_multiverse.html`, `core/templates/jobs/apply_job.html` |

## 5. System Administration & Security

| Feature | Description | Key Files |
| :--- | :--- | :--- |
| **REST API (v1)** | Secure API endpoints for mobile apps and third-party integrations. | `jobs/api_urls.py`, `jobs/api_views.py` |
| **Auth Shield** | Standardized Login, Registration, and Password Reset workflows. | `core/views.py`, `core/templates/registration/` |
| **Database Architecture** | Robust schema with 30+ tables for applications, jobs, and AI logs. | `jobs/models.py` |
| **Automation Scripts** | Maintenance scripts for template sanitization and data population. | `scripts/sweep_templates.py`, `scripts/seed_questions.py` |

## 6. Documentation Assets
- **Location**: `4_Docs_and_Diagrams/`
- **Key Files**: 
    - `COLLEGE_REPORT_MAR05_MAR18.md` (Latest Progress)
    - `2_Smart_Recruit_Doc.docx` (Full Tech Spec)
    - `sequence_diagrams.md` (System Flow)
    - `DFD_Diagrams.md` (Data Flow)
