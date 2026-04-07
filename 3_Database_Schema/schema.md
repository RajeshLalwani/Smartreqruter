# SmartRecruit Database Schema Documentation

## Overview
The application uses a relational database (SQLite for Dev, PostgreSQL recommended for Prod) to manage the recruitment lifecycle.
The schema is built around two main apps: `core` (Authentication) and `jobs` (Recruitment Process).

## Entity Relationship Diagram (Description)
- **User** (Recruiters/Candidates) -> 1:N -> **JobPosting** (Recruiters post Jobs)
- **User** -> 1:1 -> **Candidate** (Profile details)
- **Candidate** -> 1:N -> **Application** (Candidate applies to Jobs)
- **JobPosting** -> 1:N -> **Application**
- **Application** -> 1:N -> **Assessment** (Round 1 & 2 Scores)
- **Application** -> 1:N -> **Interview** (Round 3 & 4 Records)
- **Application** -> 1:1 -> **Offer** (Final Stage)

## Tables & Fields

### 1. Users (`core_user`)
| Field | Type | Description |
|---|---|---|
| `id` | Integer | Primary Key |
| `username` | String | Unique Identifier |
| `is_candidate` | Boolean | Role Flag |
| `is_recruiter` | Boolean | Role Flag |
| `profile_pic` | File | User Avatar |

### 2. Job Postings (`jobs_jobposting`)
| Field | Type | Description |
|---|---|---|
| `recruiter_id` | FK (User) | Who posted the job |
| `title` | String | Job Title |
| `status` | String | OPEN / CLOSED |
| `job_type` | String | Full Time/Part Time etc. |
| `required_skills` | Text | Comma-separated tags |
| `created_at` | DateTime | Timestamp |
| **Optimization** | **Index** | `status`, `created_at` recommended |

### 3. Candidates (`jobs_candidate`)
| Field | Type | Description |
|---|---|---|
| `user_id` | OneToOne (User) | Link to Auth User |
| `full_name` | String | Display Name |
| `skills_extracted` | Text | AI Parsed Skills |
| `resume_file` | File | Original Resume |

### 4. Applications (`jobs_application`)
Central hub for the recruitment flow.
| Field | Type | Description |
|---|---|---|
| `job_id` | FK (JobPosting) | Target Job |
| `candidate_id` | FK (Candidate) | Applicant |
| `status` | String | Current Stage (e.g. `ROUND_1_PASSED`) |
| `ai_score` | Float | Resume Match Score |
| `unique_together` | Constraint | (job, candidate) |
| **Optimization** | **Index** | `status` recommended |

### 5. Assessments (`jobs_assessment`)
Stores scores for Round 1 (Aptitude) and Round 2 (Practical).
| Field | Type | Description |
|---|---|---|
| `application_id` | FK (Application) | Link to application |
| `test_type` | String | APTITUDE / PRACTICAL |
| `score` | Float | Result |
| `passed` | Boolean | Pass/Fail Flag |

### 6. Interviews (`jobs_interview`)
Stores AI Interview (Round 3/4) transcripts and scores.
| Field | Type | Description |
|---|---|---|
| `application_id` | FK (Application) | Link to application |
| `interview_type` | String | AI_BOT / AI_HR |
| `ai_confidence_score`| Float | NLP Analysis Score |
| `feedback` | Text | Generated Feedback |

### 7. Offers (`jobs_offer`)
| Field | Type | Description |
|---|---|---|
| `application_id` | OneToOne (Application)| Final result |
| `salary_offered` | String | Compensation details |
| `status` | String | GENERATED / ACCEPTED |

## Recommended PostgreSQL Configuration
For production deployment, update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'smartrecruit_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```
**Note:** `psycopg2` driver installation is required.
