# API & Route Documentation

## Core App Routes (Authentication & Dashboard)

| HTTP Method | URL Pattern | View Name | Description |
|---|---|---|---|
| `GET` | `/` | `login` | Redirects to Login or Dashboard |
| `GET/POST` | `/login/` | `login_view` | User Authentication |
| `GET/POST` | `/register/` | `register_view` | New User Registration |
| `GET` | `/logout/` | `logout_view` | Logs out user |
| `GET` | `/dashboard/` | `dashboard` | User dashboard based on role |

## Jobs App Routes (Recruitment Process)

| HTTP Method | URL Pattern | View Name | Description |
|---|---|---|---|
| `GET` | `/jobs/` | `job_list` | List all available jobs |
| `GET` | `/jobs/<int:job_id>/` | `job_detail` | View job details |
| `POST` | `/jobs/<int:job_id>/apply/` | `apply_job` | Submit application & Resume |
| `GET` | `/my-applications/` | `candidate_applications` | List candidate's applications |
| `GET` | `/manage-jobs/` | `manage_jobs` | Recruiter: List posted jobs |
| `GET` | `/manage-jobs/<int:job_id>/candidates/` | `candidate_list` | Recruiter: View applicants for a job |

## AI Module Integration Routes

| HTTP Method | URL Pattern | View Name | Description |
|---|---|---|---|
| `GET/POST` | `/interview/ai-bot/` | `ai_interview` | AI Technical Interview (Round 3) |
| `GET/POST` | `/interview/ai-hr/` | `ai_hr_interview` | AI HR Interview (Round 4) |
| `GET` | `/interviews/` | `interview_list` | List scheduled interviews |
| `GET` | `/assessment/<int:application_id>/` | `take_assessment` | Round 1 & 2 Assessments (Proctored) |

## Offer Management

| HTTP Method | URL Pattern | View Name | Description |
|---|---|---|---|
| `GET/POST` | `/offer/generate/<int:app_id>/` | `generate_offer` | Recruiter: Create Offer |
| `GET` | `/offer/view/<int:offer_id>/` | `view_offer` | Candidate: View/Accept/Reject Offer |
