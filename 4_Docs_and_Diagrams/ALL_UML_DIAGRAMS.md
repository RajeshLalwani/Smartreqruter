# SmartRecruit — Complete UML Diagrams (System-Analyzed)
> Auto-generated from codebase analysis — March 2026

---

## 1. USE CASE DIAGRAM

```mermaid
graph TD
    subgraph SmartRecruit_System["SmartRecruit AI Recruitment Platform"]
        UC1["Post Job Opening"]
        UC2["Generate JD with AI"]
        UC3["View All Applications"]
        UC4["Shortlist / Reject Resume"]
        UC5["Schedule Assessment"]
        UC6["Preview AI Assessment"]
        UC7["Launch AI Interview (R3)"]
        UC8["Launch HR Interview (R4)"]
        UC9["Launch Botanist Voice Interview"]
        UC10["Live Code Session with Candidate"]
        UC11["Generate Offer Letter"]
        UC12["Send Broadcast Notification"]
        UC13["View Analytics Dashboard"]
        UC14["Manage Platform Settings"]
        UC15["Blind Hiring Mode"]
        UC16["Kanban Pipeline View"]
        UC17["Coding Arena Management"]
        UC18["View Recruiter Performance"]
        UC19["Manage Users"]
        UC20["Biometric Proctoring"]
        UC21["Register Account"]
        UC22["Login / SSO"]
        UC23["Apply for Job"]
        UC24["Take Aptitude Test (R1)"]
        UC25["Take Practical Test (R2)"]
        UC26["Attend AI Interview (R3)"]
        UC27["View / Accept Offer"]
        UC28["Track Application Status"]
        UC29["Use AI Prep Lab"]
        UC30["Solve Coding Challenges"]
        UC31["Build Resume with AI"]
        UC32["Score Cover Letter"]
        UC33["Verify Credentials (Blockchain)"]
    end

    Recruiter["👤 Recruiter"]
    Candidate["👤 Candidate"]
    Admin["👤 Admin"]

    Recruiter -->|performs| UC1
    Recruiter -->|performs| UC2
    Recruiter -->|performs| UC3
    Recruiter -->|performs| UC4
    Recruiter -->|performs| UC5
    Recruiter -->|performs| UC6
    Recruiter -->|performs| UC7
    Recruiter -->|performs| UC8
    Recruiter -->|performs| UC9
    Recruiter -->|performs| UC10
    Recruiter -->|performs| UC11
    Recruiter -->|performs| UC15
    Recruiter -->|performs| UC16
    Recruiter -->|performs| UC20

    Candidate -->|performs| UC21
    Candidate -->|performs| UC22
    Candidate -->|performs| UC23
    Candidate -->|performs| UC24
    Candidate -->|performs| UC25
    Candidate -->|performs| UC26
    Candidate -->|performs| UC27
    Candidate -->|performs| UC28
    Candidate -->|performs| UC29
    Candidate -->|performs| UC30
    Candidate -->|performs| UC31
    Candidate -->|performs| UC32
    Candidate -->|performs| UC33

    Admin -->|manages| UC12
    Admin -->|manages| UC13
    Admin -->|manages| UC14
    Admin -->|manages| UC17
    Admin -->|manages| UC18
    Admin -->|manages| UC19
    Admin -->|performs| UC22
```

---

## 2. DATA FLOW DIAGRAM — Level 0 (Context Diagram)

```mermaid
flowchart LR
    Recruiter(["👤 Recruiter"]) -->|"Job data, assessment rules"| SYS[["⬛ SmartRecruit\nAI Platform"]]
    Candidate(["👤 Candidate"]) -->|"Resume, answers, code"| SYS
    Admin(["👤 Admin"]) -->|"Config, user management"| SYS
    SYS -->|"Shortlist results, scores, offers"| Recruiter
    SYS -->|"Application status, interview invites"| Candidate
    GeminiAI(["🤖 Google Gemini"]) <-->|"Prompts / AI responses"| SYS
    Groq(["⚡ Groq API"]) <-->|"Low-latency fallback"| SYS
    N8N(["🔗 n8n Webhooks"]) <-->|"Automation events"| SYS
    Blockchain(["🔒 Blockchain Ledger"]) <-->|"Credential hashes"| SYS
```

---

## 3. DATA FLOW DIAGRAM — Level 1 (Major Processes)

```mermaid
flowchart TD
    D1[(Job Postings DB)]
    D2[(Candidates DB)]
    D3[(Applications DB)]
    D4[(Assessments DB)]
    D5[(Interviews DB)]
    D6[(Offers DB)]
    D7[(Notifications DB)]

    P1["P1: Job Management\n(create, edit, publish)"]
    P2["P2: Resume Intelligence\n(parse, score, shortlist)"]
    P3["P3: Assessment Engine\n(aptitude, practical MCQs)"]
    P4["P4: AI Interview Engine\n(R3 bot, HR bot, Botanist)"]
    P5["P5: Offer & Onboarding\n(generate PDF, e-sign)"]
    P6["P6: Analytics Engine\n(funnel, retention, bias)"]
    P7["P7: Notification Hub\n(email, in-app, webhook)"]

    Recruiter(["👤 Recruiter"]) --> P1
    P1 --> D1
    Candidate(["👤 Candidate"]) --> P2
    P2 --> D2
    P2 --> D3
    D3 --> P3
    P3 --> D4
    D4 --> P4
    P4 --> D5
    D5 --> P5
    P5 --> D6
    D3 & D4 & D5 --> P6
    P6 --> Recruiter
    P2 & P3 & P4 & P5 --> P7
    P7 --> D7
    P7 --> Candidate
    P7 --> Recruiter
```

---

## 4. DATA FLOW DIAGRAM — Level 2 (Resume Screening Process)

```mermaid
flowchart TD
    C(["👤 Candidate"]) -->|"Upload PDF/DOCX"| P2_1["Extract Text\n(pdfplumber / python-docx)"]
    P2_1 -->|"Raw text"| P2_2["Multi-lingual\nDetection\n(langdetect)"]
    P2_2 -->|"Detected lang + text"| P2_3["Semantic Embedding\n(Sentence-Transformers\nor Gemini embed)"]
    P2_3 --> P2_4["Cosine Similarity\nvs Job Description\nEmbedding"]
    P2_4 -->|"Score 0–100"| P2_5["Threshold Decision\n≥ 60 → Shortlist\n< 60 → Reject"]
    P2_5 -->|"AI Insights JSON"| D_APP[(Application DB\nai_score, ai_insights)]
    P2_5 -->|"Trigger"| P2_6["Email + Notification\n(send_async_email)"]
    D_JD[(Job Description DB)] --> P2_3
```

---

## 5. ACTIVITY DIAGRAM — Full 4-Round Hiring Pipeline

```mermaid
flowchart TD
    A([▶ Start: Candidate Applies]) --> B["Resume Uploaded\n& Parsed by AI"]
    B --> C{AI Score ≥ 60?}
    C -- No --> Z1(["❌ Resume Rejected\n+ Email Sent"])
    C -- Yes --> D["Status: RESUME_SELECTED\n+ Email Sent"]
    D --> E["Recruiter Reviews\nApplication Details"]
    E --> F{Manual Override?}
    F -- Reject --> Z2(["❌ Rejected by Recruiter"])
    F -- Proceed --> G["Round 1: Aptitude Test\n(AI-Generated MCQs)"]
    G --> H{Score ≥ 70%?}
    H -- No --> Z3(["❌ Round 1 Failed"])
    H -- Yes --> I["Round 2: Practical Test\n(Domain-Specific MCQs)"]
    I --> J{Score ≥ 70%?}
    J -- No --> Z4(["❌ Round 2 Failed"])
    J -- Yes --> K["Round 3: AI Technical Interview\n(Voice + Code + Sentiment)"]
    K --> L{Confidence Score ≥ 75?}
    L -- No --> Z5(["❌ Round 3 Failed\n(ROUND_3_FAILED)"])
    L -- Yes --> M["Round 4: HR Interview\n(Botanist/AI HR)"]
    M --> N{HR Approved?}
    N -- No --> Z6(["❌ HR Round Failed"])
    N -- Yes --> O["Offer Letter Generated\n(PDF + Email)"]
    O --> P{Candidate Response\nwithin 3 days?}
    P -- Decline --> Z7(["❌ Offer Rejected"])
    P -- Accept --> Q(["✅ HIRED\n+ Onboarding Plan Generated"])
```

---

## 6. CLASS DIAGRAM — Core Data Models

```mermaid
classDiagram
    class User {
        +id: BigAutoField
        +email: EmailField
        +username: CharField
        +is_recruiter: BooleanField
        +is_candidate: BooleanField
        +is_superuser: BooleanField
        +professional_title: CharField
        +blind_hiring: BooleanField
        +voice_preference: CharField
        +model_preference: CharField
    }

    class JobPosting {
        +id: BigAutoField
        +title: CharField
        +job_type: CharField
        +technology_stack: CharField
        +location: CharField
        +salary_range: CharField
        +required_skills: TextField
        +min_experience: FloatField
        +passing_score_r1: FloatField
        +passing_score_r2: FloatField
        +time_limit_r1: IntegerField
        +time_limit_r2: IntegerField
        +aptitude_difficulty: CharField
        +practical_difficulty: CharField
        +status: CharField
        +deadline: DateField
        +skills_list(): list
    }

    class Candidate {
        +id: BigAutoField
        +full_name: CharField
        +email: EmailField
        +phone: CharField
        +experience_years: FloatField
        +skills_extracted: TextField
        +resume_file: FileField
        +github_url: URLField
        +portfolio_url: URLField
        +is_verified_on_chain: BooleanField
        +blockchain_hash: CharField
        +detected_language: CharField
        +skills_list(): list
    }

    class Application {
        +id: BigAutoField
        +ai_score: FloatField
        +ai_insights: TextField
        +status: CharField
        +technical_score: FloatField
        +communication_score: FloatField
        +confidence_score: FloatField
        +integrity_score: FloatField
        +hr_summary: TextField
        +candidate_feedback: TextField
        +applied_at: DateTimeField
    }

    class Assessment {
        +id: BigAutoField
        +test_type: CharField
        +score: FloatField
        +max_score: FloatField
        +passed: BooleanField
        +details: JSONField
        +time_taken: DurationField
    }

    class Interview {
        +id: BigAutoField
        +interview_type: CharField
        +scheduled_time: DateTimeField
        +ai_confidence_score: FloatField
        +feedback: TextField
        +status: CharField
        +code_final: TextField
        +architecture_schema: TextField
        +architecture_score: FloatField
        +is_flagged: BooleanField
        +flag_count: IntegerField
    }

    class SentimentLog {
        +emotion: CharField
        +score: FloatField
        +confidence_score: FloatField
        +stress_level: FloatField
        +vocal_confidence_score: FloatField
        +speech_rate: FloatField
        +hesitation_count: IntegerField
        +proctoring_flags: JSONField
        +frame: TextField
    }

    class Offer {
        +salary_offered: CharField
        +designation: CharField
        +joining_date: DateField
        +offer_file: FileField
        +status: CharField
        +response_deadline: DateTimeField
    }

    class Notification {
        +title: CharField
        +message: TextField
        +type: CharField
        +is_read: BooleanField
        +link: CharField
        +created_at: DateTimeField
    }

    class NegotiationSession {
        +current_salary_offer: FloatField
        +max_budget: FloatField
        +candidate_counter_offer: FloatField
        +status: CharField
        +chat_history: JSONField
    }

    class CodingChallenge {
        +title: CharField
        +slug: SlugField
        +difficulty: CharField
        +category: CharField
        +xp_reward: IntegerField
        +starter_code: JSONField
        +test_cases: JSONField
    }

    User "1" --> "*" JobPosting : posts
    User "1" --> "1" Candidate : has_profile
    JobPosting "1" --> "*" Application : receives
    Candidate "1" --> "*" Application : submits
    Application "1" --> "*" Assessment : takes
    Application "1" --> "*" Interview : has
    Application "1" --> "0..1" Offer : receives
    Application "1" --> "0..1" NegotiationSession : negotiates
    Interview "1" --> "*" SentimentLog : generates
    User "1" --> "*" Notification : receives
```

---

## 7. SEQUENCE DIAGRAM — End-to-End Hiring Flow

```mermaid
sequenceDiagram
    actor C as Candidate
    actor R as Recruiter
    participant Web as Django Views
    participant AI as AI Engine (Gemini/Groq)
    participant DB as Database (SQLite)
    participant Email as Email Service

    C->>Web: POST /jobs/<id>/apply/ (Resume PDF)
    Web->>AI: parse_resume(text) + embed(skills)
    AI-->>Web: {ai_score, skills, insights}
    Web->>DB: Create Application (status=RESUME_SELECTED/REJECTED)
    Web->>Email: send_resume_shortlisted_email() [async thread]
    Email-->>C: "Resume Shortlisted" email

    R->>Web: GET /application/<id>/
    Web->>DB: Fetch Application + Assessments + Interviews
    Web-->>R: ApplicationDetails page (AI Score, Insights)

    R->>Web: POST /status/update/<id>/ROUND_1_PENDING/
    Web->>DB: Update status to ROUND_1_PENDING

    C->>Web: GET /assessment/<id>/APTITUDE/
    Web->>AI: fetch_questions(job, difficulty)
    AI-->>Web: [50 AI-generated MCQ questions]
    Web-->>C: Render take_assessment.html (timed)

    C->>Web: POST /assessment/<id>/APTITUDE/ (answers)
    Web->>DB: Create Assessment (score, passed)
    alt Score >= 70
        Web->>DB: Update status ROUND_1_PASSED
        Web->>Email: send_assessment_result_email() [PASS, async]
    else Score < 70
        Web->>DB: Update status ROUND_1_FAILED
        Web->>Email: send_assessment_result_email() [FAIL, async]
    end

    Note over C,Email: Round 2 (Practical) follows same pattern

    R->>Web: GET /interview/ai/<id>/
    Web->>AI: AIInterviewer.generate_question()
    Web-->>R: Render live interview session

    C->>Web: GET /interview/ai/<id>/
    Web->>AI: generate_content(context, job_desc)
    AI-->>Web: question_text + TTS audio
    Web-->>C: Render AI Interview page (mic + camera + code editor)

    loop Each Answer
        C->>Web: POST answer + frame + code
        Web->>AI: analyze_response(question, answer)
        AI-->>Web: {score, feedback}
        Web->>DB: Save SentimentLog + Interview progress
    end

    Web->>DB: Update Interview (status=COMPLETED, ai_confidence_score)
    Web->>DB: Update Application (status=ROUND_3_PASSED/FAILED)
    Web->>Email: send_interview_invitation_email() [async]

    R->>Web: POST generate_offer/<id>/
    Web->>AI: Generate offer letter PDF
    Web->>DB: Create Offer (status=GENERATED)
    Web->>Email: send_offer_letter_email() [async]
    Email-->>C: "You have a Job Offer" email

    C->>Web: POST /offer/<id>/accept/
    Web->>DB: Update Offer (status=ACCEPTED) + Application (status=HIRED)
    Web->>AI: Generate OnboardingRoadmap (30-60-90 day plan)
    Web->>DB: Save OnboardingRoadmap
```
