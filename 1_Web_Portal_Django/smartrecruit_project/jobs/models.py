from django.db import models
from django.conf import settings
from django.utils import timezone

# 1.5 TECHNOLOGY (Dynamic Tech Stack)
class Technology(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon_class = models.CharField(max_length=50, default="fas fa-code", help_text="FontAwesome class")
    color = models.CharField(max_length=20, default="#00d2ff")
    
    class Meta:
        verbose_name_plural = "Technologies"
        ordering = ['name']

    def __str__(self): return self.name

# 11. REAL-TIME NOTIFICATIONS
class Notification(models.Model):
    TYPE_CHOICES = [
        ('INFO', 'Info'),
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='INFO')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self): return f"{self.user.username}: {self.title}"

# 1. JOB POSTINGS (Your Existing Model)
class JobPosting(models.Model):
    JOB_TYPES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('INTERNSHIP', 'Internship'),
        ('CONTRACT', 'Contract'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('OPEN', 'Open'), 
        ('CLOSED', 'Closed'),
        ('REJECTED', 'Rejected')
    ]
    
    TECHNOLOGY_CHOICES = [
        ('PYTHON', 'Python/Django'),
        ('DOTNET', '.NET/C#'),
        ('JAVA', 'Java/Spring'),
        ('JAVASCRIPT', 'JavaScript/Node.js'),
        ('REACT', 'React/Frontend'),
        ('ANGULAR', 'Angular'),
        ('VUE', 'Vue.js'),
        ('ANDROID', 'Android/Kotlin'),
        ('FLUTTER', 'Flutter/Dart'),
        ('IOS', 'iOS/Swift'),
        ('DATA_SCIENCE', 'Data Science/ML'),
        ('DEVOPS', 'DevOps/Cloud'),
        ('PHP', 'PHP/Laravel'),
        ('RUBY', 'Ruby/Rails'),
        ('GENERAL', 'General IT'),
    ]

    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='FULL_TIME')
    technology_stack = models.CharField(max_length=20, choices=TECHNOLOGY_CHOICES, default='GENERAL', help_text="Primary technology for this role")
    technology = models.ForeignKey(Technology, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs', help_text="Dynamic Technology Link (Optional)")
    location = models.CharField(max_length=100)
    salary_range = models.CharField(max_length=100, blank=True)
    deadline = models.DateField(null=True, blank=True)
    description = models.TextField()
    
    # YOUR SPECIFIC FIELDS
    required_skills = models.TextField(help_text="Comma-separated skills")
    min_experience = models.FloatField(default=0)
    
    # Automated Round Criteria
    passing_score_r1 = models.FloatField(default=70.0, help_text="Passing score for Round 1 (Aptitude)")
    passing_score_r2 = models.FloatField(default=70.0, help_text="Passing score for Round 2 (Practical)")
    time_limit_r1 = models.IntegerField(default=45, help_text="Time limit for Round 1 in minutes")
    time_limit_r2 = models.IntegerField(default=60, help_text="Time limit for Round 2 in minutes")
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    aptitude_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium', help_text="Difficulty level for Aptitude MCQs")
    practical_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium', help_text="Difficulty level for Practical MCQs")
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    @property
    def skills_list(self):
        if self.required_skills:
            return [s.strip() for s in self.required_skills.split(',') if s.strip()]
        return []

    def __str__(self): return self.title

# 2. CANDIDATE PROFILE (Your Existing Model)
class Candidate(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidate_profile', null=True, blank=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    experience_years = models.FloatField(default=0)
    current_location = models.CharField(max_length=100, default='Remote')
    pseudonym = models.CharField(max_length=100, blank=True, null=True, help_text="Gamification identity (e.g. CyberNinja77)")
    
    # DEMOGRAPHICS (For Bias Auditing - Non-public)
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('NON_BINARY', 'Non-Binary'),
        ('NOT_SAY', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='NOT_SAY')
    date_of_birth = models.DateField(null=True, blank=True)
    institution_type = models.CharField(max_length=100, default='Tier-2', help_text="Analyzed for elitism detection")

    resume_file = models.FileField(upload_to='resumes/', null=True, blank=True)
    github_url = models.URLField(max_length=500, blank=True, null=True, help_text="Public GitHub/GitLab profile")
    portfolio_url = models.URLField(max_length=500, blank=True, null=True, help_text="Personal portfolio or project site")
    
    # AI ENRICHED FIELDS
    skills_extracted = models.TextField(blank=True)
    experience_summary = models.TextField(blank=True, help_text="AI-generated summary of career history")
    current_role = models.CharField(max_length=150, blank=True, default="Specialist")
    detected_language = models.CharField(max_length=50, blank=True, default="English", help_text="Detected language of the resume")
    
    is_passive_sourced = models.BooleanField(default=False, help_text="True if candidate was autonomously sourced via n8n Hunter")
    
    # BLOCKCHAIN VERIFICATION FIELDS
    is_verified_on_chain = models.BooleanField(default=False, help_text="Global verification status across all credentials")
    blockchain_hash = models.CharField(max_length=255, blank=True, help_text="Primary cryptographic link to the decentralized ledger")
    blockchain_tx_id = models.CharField(max_length=255, blank=True, help_text="Simulated Transaction ID on the ledger")
    
    created_at = models.DateTimeField(auto_now_add=True)
    earned_badges = models.ManyToManyField('Badge', blank=True, related_name='winners')

    @property
    def technical_skills(self):
        return self.skills_extracted
    
    @property
    def skills_list(self):
        if self.skills_extracted:
            return [s.strip() for s in self.skills_extracted.split(',') if s.strip()]
        return []

    def __str__(self): return self.full_name

# 2.5 EDUCATION & CERTIFICATIONS (Blockchain-Linked)
class Education(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='education_history')
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Blockchain Details
    is_verified_on_chain = models.BooleanField(default=False)
    blockchain_hash = models.CharField(max_length=255, blank=True, help_text="Transaction hash or Certificate ID on-chain")
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Education History"

    def __str__(self): return f"{self.degree} from {self.institution}"

# 2.6 BLOCKCHAIN AUDIT LOG (Security & Compliance)
class BlockchainAuditLog(models.Model):
    ACTION_CHOICES = [
        ('VERIFY_REQUEST', 'Verification Request Init'),
        ('VERIFY_SUCCESS', 'Verification Successful'),
        ('VERIFY_FAILURE', 'Verification Failed'),
        ('TAMPER_DETECTED', 'Hash Mismatch / Tamper Alert'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    doc_type = models.CharField(max_length=100, default='Degree/Certificate')
    target_hash = models.CharField(max_length=255)
    status_code = models.CharField(max_length=20, default='SUCCESS')
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self): return f"{self.action} - {self.target_hash[:10]}"

# 3. APPLICATION (Enhanced for 4-Round Process)
class Application(models.Model):
    STATUS_CHOICES = [
        ('APPLIED', 'Applied'),
        ('RESUME_SCREENING', 'Resume Screening'),
        ('RESUME_SELECTED', 'Resume Selected'),
        ('RESUME_REJECTED', 'Resume Rejected'),
        
        ('ROUND_1_PENDING', 'Round 1 Pending (Aptitude)'),
        ('ROUND_1_PASSED', 'Round 1 Passed'),
        ('ROUND_1_FAILED', 'Round 1 Failed'),
        
        ('ROUND_2_PENDING', 'Round 2 Pending (Practical)'),
        ('ROUND_2_PASSED', 'Round 2 Passed'),
        ('ROUND_2_FAILED', 'Round 2 Failed'),
        
        ('ROUND_3_PENDING', 'Round 3 Pending (AI Interview)'),
        ('ROUND_3_PASSED', 'Round 3 Passed'),
        ('ROUND_3_FAILED', 'Round 3 Failed'),
        
        ('HR_ROUND_PENDING', 'HR Round Pending'),
        ('OFFER_GENERATED', 'Offer Generated'),
        ('OFFER_ACCEPTED', 'Offer Accepted'),
        ('OFFER_REJECTED', 'Offer Rejected'),
        ('HIRED', 'Hired'),
        ('REJECTED', 'Rejected'),
        ('REJECTED_TIMEOUT', 'Rejected - Timeout'),
        ('SOURCED', 'Sourced (Passive)'),
    ]
    SOURCE_CHOICES = [
        ('LINKEDIN', 'LinkedIn'),
        ('INDEED', 'Indeed'),
        ('WEBSITE', 'Career Site'),
        ('REFERRAL', 'Referral'),
        ('AGENCY', 'Agency'),
        ('AI_HUNTER', 'AI Sourced'),
        ('OTHER', 'Other'),
    ]
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='applications')
    source_of_hire = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='WEBSITE')
    ai_score = models.FloatField(default=0.0) # Resume Score
    ai_insights = models.TextField(blank=True, default="{}", help_text="JSON storing detailed AI analysis (matched/missing keywords)")
    ai_committee_report = models.TextField(blank=True, null=True, help_text="CrewAI multi-agent debate report and final verdict")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED', db_index=True)
    external_ats_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID of this application in the external ATS (Workday/Greenhouse)")
    sync_status = models.CharField(max_length=20, default='PENDING', choices=[('PENDING', 'Pending'), ('SYNCED', 'Synced'), ('FAILED', 'Failed')])
    
    # PHASE 7 FIELDS: AI Summary Engine
    hr_summary = models.TextField(blank=True, null=True, help_text="Executive summary for HR")
    candidate_feedback = models.TextField(blank=True, null=True, help_text="Constructive 'Growth Mindset' feedback for candidate")
    technical_score = models.FloatField(default=0.0)
    communication_score = models.FloatField(default=0.0)
    confidence_score = models.FloatField(default=0.0)
    integrity_score = models.FloatField(default=0.0)
    problem_solving_score = models.FloatField(default=0.0)
    
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: unique_together = ['job', 'candidate']
    def __str__(self): return f"{self.candidate.full_name} -> {self.job.title} ({self.status})"

# 4. ASSESSMENT (For Round 1 & Round 2)
class Assessment(models.Model):
    TEST_TYPES = [
        ('APTITUDE', 'Aptitude Test (Round 1)'),
        ('PRACTICAL', 'Practical/Coding Test (Round 2)'),
    ]
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='assessments')
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    score = models.FloatField(default=0.0)
    max_score = models.FloatField(default=100.0)
    passed = models.BooleanField(default=False)
    details = models.JSONField(default=dict, blank=True) # Store Q&A or code submission links
    time_taken = models.DurationField(null=True, blank=True, help_text="Time taken to complete the assessment")
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.test_type} - {self.application.candidate.full_name}"

# 5. INTERVIEW (For Round 3 & HR)
class Interview(models.Model):
    INTERVIEW_TYPES = [
        ('APTITUDE', 'Aptitude Test (Round 1)'),
        ('PRACTICAL', 'Practical/Coding Test (Round 2)'),
        ('AI_BOT', 'AI Technical Interview (Round 3)'),
        ('AI_HR', 'AI HR Interview (Round 4)'),
        ('BOTANIST', 'Botanist Voice Interview'),
    ]
    INTERVIEW_STATUS = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('TERMINATED', 'Terminated'),
        ('CANCELLED', 'Cancelled'),
    ]
    PROCTORING_STATUS = [
        ('PENDING', 'Pending Review'),
        ('VERIFIED', 'Verified Violation'),
        ('FALSE_POSITIVE', 'False Positive'),
        ('CLEAN', 'No Violation'),
    ]
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES, default='AI_BOT')
    scheduled_time = models.DateTimeField(null=True, blank=True)
    meeting_link = models.URLField(blank=True)
    ai_confidence_score = models.FloatField(default=0.0) # For AI Bot
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=INTERVIEW_STATUS, default='SCHEDULED')
    code_final = models.TextField(blank=True, help_text="Final synchronized code from live session")
    architecture_schema = models.TextField(blank=True, help_text="JSON representation of the visual system architecture")
    architecture_score = models.FloatField(default=0.0, help_text="Score graded by AIEngine for the architecture diagram")
    is_flagged = models.BooleanField(default=False, help_text="Set to True if proctoring violations exceed threshold")
    flag_count = models.IntegerField(default=0, help_text="Number of detected proctoring violations")
    proctoring_status = models.CharField(max_length=20, choices=PROCTORING_STATUS, default='CLEAN')
    proctoring_notes = models.TextField(blank=True, help_text="Admin notes on proctoring review")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"{self.interview_type}: {self.application.candidate.full_name}"

    def save(self, *args, **kwargs):
        # Phase 11: Blockchain Credential Verification
        should_mint = False
        if self.status == 'COMPLETED' and not getattr(self, '_blockchain_minted', False):
            should_mint = True
            self._blockchain_minted = True # Prevent duplicate triggers in memory

        super().save(*args, **kwargs)

        if should_mint:
            from core.utils.blockchain_sync import mint_certificate
            import hashlib
            # Create a unique un-guessable hash
            data_to_hash = f"{self.id}-{self.application.candidate.id}-{self.ai_confidence_score}-{self.created_at.timestamp()}".encode('utf-8')
            cert_hash = "0x" + hashlib.sha256(data_to_hash).hexdigest()

            tx_hash = mint_certificate(cert_hash, str(self.application.candidate.user.username if self.application.candidate.user else self.application.candidate.full_name), str(self.ai_confidence_score))
            
            if tx_hash:
                self.application.candidate.is_verified_on_chain = True
                self.application.candidate.blockchain_hash = cert_hash
                self.application.candidate.blockchain_tx_id = tx_hash
                self.application.candidate.save()


# 5.5 SENTIMENT LOG (Real-time Emotion Tracking)
class SentimentLog(models.Model):
    """Stores facial expression data captured by face-api.js during interviews."""
    EMOTION_CHOICES = [
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
        ('fearful', 'Fearful'),
        ('disgusted', 'Disgusted'),
        ('surprised', 'Surprised'),
        ('neutral', 'Neutral'),
    ]
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='sentiment_logs', null=True, blank=True)
    emotion = models.CharField(max_length=20, choices=EMOTION_CHOICES, default='neutral')
    score = models.FloatField(default=0.0, help_text="Confidence score 0.0 to 1.0")
    raw_expressions = models.JSONField(default=dict, blank=True, help_text="Full face-api.js expression scores")
    proctoring_flags = models.JSONField(default=dict, blank=True, help_text="Violation flags (e.g., {'multiple_faces': True})")
    frame = models.TextField(blank=True, null=True, help_text="Base64 encoded frame for replay")
    
    # --- PHASE 10: BOTANIST VOICE ADDITIONS ---
    voice_transcript = models.TextField(blank=True, null=True, help_text="Transcribed voice response from the candidate")
    behavioral_score = models.FloatField(default=0.0, help_text="AI-calculated behavioral fitment score")
    vocal_metrics = models.JSONField(default=dict, blank=True, help_text="Voice analytics (speech rate, pause density)")
    
    # Expanded analytics for Recruiter Dashboard
    behavioral_fitment_summary = models.TextField(blank=True, null=True, help_text="AI-generated summary of behavioral fitment")
    vocal_confidence_score = models.FloatField(default=0.0, help_text="Confidence percentage based on vocal analysis")
    speech_rate = models.FloatField(default=0.0, help_text="Words per minute")
    hesitation_count = models.IntegerField(default=0, help_text="Detected pauses or fillers")
    volume_consistency = models.FloatField(default=0.0, help_text="Standard deviation of volume levels")
    
    # PHASE 5: Stress Detection markers
    stress_index = models.FloatField(default=0.0, help_text="Calculated stress level (0-100)")
    jitter = models.FloatField(default=0.0, help_text="Micro-tremor frequency variation")
    shimmer = models.FloatField(default=0.0, help_text="Amplitude variation")
    pitch_variance = models.FloatField(default=0.0, help_text="Pitch fluctuation")
    
    # ── Master Prompt 2 Overrides ──
    confidence_score = models.FloatField(default=0.0, help_text="AI estimated confidence (0.0 to 1.0)")
    stress_level = models.FloatField(default=0.0, help_text="AI estimated stress level (0.0 to 1.0)")
    sentiment_label = models.CharField(max_length=50, blank=True, null=True, help_text="Processed sentiment label from AI")
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['interview', 'timestamp']),
        ]

    def __str__(self):
        return f"[{self.emotion}:{self.score:.2f}] @ {self.timestamp:%H:%M:%S}"


# 5.6 INTERVIEW DISCUSSION (Phase 6: Multi-Recruiter Live Chat)
class InterviewDiscussion(models.Model):
    MSG_TYPE_CHOICES = [
        ('chat', 'Standard Chat'),
        ('presence', 'Presence Update'),
        ('vote_up', 'Upvote / Agree'),
        ('vote_down', 'Downvote / Disagree'),
        ('flag', 'Proctoring Flag Alert'),
    ]
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='discussions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview_comments')
    message = models.TextField(blank=True)
    msg_type = models.CharField(max_length=20, choices=MSG_TYPE_CHOICES, default='chat')
    video_timestamp = models.CharField(max_length=10, default="00:00", help_text="Timestamp of the interview when comment was made")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} on {self.interview.application.candidate.full_name}: {self.message[:30]}"


# 6. OFFER LETTER (Final Stage)
class Offer(models.Model):
    OFFER_STATUS = [
        ('GENERATED', 'Generated'),
        ('SENT', 'Sent'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='offer_letter')
    salary_offered = models.CharField(max_length=50, default='Not Specified')
    designation = models.CharField(max_length=100)
    joining_date = models.DateField(null=True, blank=True)
    offer_file = models.FileField(upload_to='offers/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=OFFER_STATUS, default='GENERATED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    response_deadline = models.DateTimeField(null=True, blank=True) # 3 Days logic

    def __str__(self): return f"Offer for {self.application.candidate.full_name}"

# 7. QUESTION BANK (Recruiter Managed)
class Question(models.Model):
    CATEGORY_CHOICES = [
        ('PYTHON', 'Python'),
        ('JAVA', 'Java'),
        ('JAVASCRIPT', 'JavaScript'),
        ('CPP', 'C++'),
        ('GO', 'Go'),
        ('RUST', 'Rust'),
        ('SQL', 'SQL'),
        ('HR', 'HR/Behavioral'),
        ('APTITUDE', 'Aptitude'),
        ('GENERAL', 'General'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    options = models.JSONField(default=list, help_text="List of options for MCQs (JSON format)")
    correct_answer = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    language_requirement = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL', help_text="Specific language required for this question")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.text[:50]

# 8. PROCTORING LOGS (Evidence)
class ProctoringLog(models.Model):
    LOG_TYPE_CHOICES = [
        ('SCREENSHOT', 'Periodic Screenshot'),
        ('VIOLATION', 'Violation Snapshot'),
        ('SUSPICION', 'Suspicious Activity'),
    ]
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='proctoring_logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    image = models.ImageField(upload_to='proctoring_logs/', null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.log_type} - {self.application.candidate.full_name}"

# 8.5 MACHINE VISION ANALYSIS (SecureSight)
class ProctoringAnalysis(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='vision_analysis')
    face_count = models.IntegerField(default=1)
    pose_stability = models.FloatField(default=1.0) # 0 to 1
    eye_status = models.CharField(max_length=50, default='LOOKING_CENTER')
    is_impersonation_risk = models.BooleanField(default=False)
    vision_confidence = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Vision: {self.application.candidate.full_name} ({self.timestamp})"

# 8.6 SKILL LEARNING RESOURCES (SkillForge)
class SkillLearningResource(models.Model):
    skill_name = models.CharField(max_length=100)
    resource_title = models.CharField(max_length=255)
    url = models.URLField()
    difficulty = models.CharField(max_length=20, default='Beginner')
    platform = models.CharField(max_length=50, default='SmartRecruit Academy')

    def __str__(self): return f"{self.skill_name}: {self.resource_title}"


# 9. ACTIVITY LOG (Recruiter Feed)
class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.user.username} - {self.action}"

# 10. EMAIL TEMPLATES (Dynamic)
class EmailTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Internal name used in code (e.g., 'application_received')")
    subject = models.CharField(max_length=255)
    body_content = models.TextField(help_text="HTML content. Use Double Curly Braces for variables.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.name

# 12. SMART SCHEDULER (Availability Slots)
class AvailabilitySlot(models.Model):
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='availability_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']
        unique_together = ['recruiter', 'start_time', 'end_time']

    def __str__(self):
        return f"{self.recruiter.username} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"


# ──────────────────────────────────────────────────────
# 13. CODING PRACTICE ARENA
# ──────────────────────────────────────────────────────
class CodingChallenge(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy',   'Easy'),
        ('medium', 'Medium'),
        ('hard',   'Hard'),
    ]
    CATEGORY_CHOICES = [
        ('arrays',         'Arrays & Strings'),
        ('linked_list',    'Linked Lists'),
        ('trees',          'Trees & Graphs'),
        ('dp',             'Dynamic Programming'),
        ('sorting',        'Sorting & Searching'),
        ('recursion',      'Recursion'),
        ('sql',            'SQL'),
        ('python',         'Python Basics'),
        ('data_science',   'Data Science / ML'),
        ('os_concepts',    'OS & System Design'),
    ]

    title          = models.CharField(max_length=200)
    slug           = models.SlugField(max_length=200, unique=True)
    description    = models.TextField(help_text="Full problem statement (markdown supported)")
    difficulty     = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy', db_index=True)
    category       = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='python', db_index=True)
    xp_reward      = models.IntegerField(default=50, help_text="XP points awarded on solve")

    # Starter code per language (JSON: {"python": "...", "javascript": "...", "java": "..."})
    starter_code   = models.JSONField(default=dict, blank=True)
    # Test cases JSON: [{"input": "...", "expected": "..."}]
    test_cases     = models.JSONField(default=list)
    # Constraints / hints / examples
    constraints    = models.TextField(blank=True)
    examples       = models.JSONField(default=list, blank=True,
                                      help_text='[{"input":"...","output":"...","explanation":"..."}]')
    hints          = models.JSONField(default=list, blank=True,
                                      help_text='["Hint 1", "Hint 2", "Hint 3"]')

    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    order          = models.IntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ['order', 'difficulty', 'title']

    def __str__(self):
        return f"[{self.get_difficulty_display()}] {self.title}"

    @property
    def difficulty_color(self):
        return {'easy': '#00C853', 'medium': '#FFC107', 'hard': '#FF5252'}[self.difficulty]

    @property
    def difficulty_badge(self):
        return {'easy': 'success', 'medium': 'warning', 'hard': 'danger'}[self.difficulty]


class CodingSubmission(models.Model):
    LANG_CHOICES = [
        ('python',      'Python 3'),
        ('javascript',  'JavaScript'),
        ('java',        'Java'),
        ('cpp',         'C++'),
        ('sql',         'SQL'),
    ]
    STATUS_CHOICES = [
        ('ACCEPTED',  'Accepted ✅'),
        ('WRONG',     'Wrong Answer ❌'),
        ('ERROR',     'Runtime Error ⚠️'),
        ('PARTIAL',   'Partial ⚡'),
        ('TIMEOUT',   'Time Limit Exceeded ⏱️'),
    ]

    candidate   = models.ForeignKey(Candidate, on_delete=models.CASCADE,
                                    related_name='coding_submissions', null=True, blank=True)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='coding_submissions', null=True, blank=True)
    challenge   = models.ForeignKey(CodingChallenge, on_delete=models.CASCADE,
                                    related_name='submissions')
    language    = models.CharField(max_length=20, choices=LANG_CHOICES, default='python')
    code        = models.TextField()
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES)
    runtime_ms  = models.IntegerField(null=True, blank=True)
    test_results= models.JSONField(default=list, blank=True)
    xp_earned   = models.IntegerField(default=0)
    hints_used  = models.IntegerField(default=0)
    submitted_at= models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        user_str = self.candidate.full_name if self.candidate else (self.user.username if self.user else 'Anonymous')
        return f"{user_str} → {self.challenge.title} [{self.status}]"


class CandidateXP(models.Model):
    """Gamification: tracks total XP, badges, and streak for each user."""
    user          = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                         related_name='coding_xp')
    total_xp      = models.IntegerField(default=0)
    problems_solved = models.IntegerField(default=0)
    streak_days   = models.IntegerField(default=0)
    last_active   = models.DateField(null=True, blank=True)
    badges        = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.user.username}: {self.total_xp} XP"

    @property
    def level(self):
        if self.total_xp >= 5000: return ('Legend', 'fas fa-crown', '#FFD700')
        if self.total_xp >= 2000: return ('Expert',  'fas fa-gem',   '#AA00FF')
        if self.total_xp >= 800:  return ('Advanced','fas fa-fire',  '#FF5722')
        if self.total_xp >= 300:  return ('Learner', 'fas fa-book',  '#2196F3')
        return ('Beginner', 'fas fa-seedling', '#4CAF50')

# 12. AUTOMATION WEBHOOKS (n8n Bridge)
class WebhookConfig(models.Model):
    EVENT_CHOICES = [
        ('NEW_CANDIDATE', 'New Candidate Applied'),
        ('SHORTLISTED', 'Candidate Shortlisted'),
        ('HIRED', 'Candidate Hired'),
        ('HIGH_RISK_GHOST', 'High Ghosting Risk Found'),
        ('OFFER_ACCEPTED', 'Offer Accepted'),
        ('SENTIMENT_RED_FLAG', 'Sentiment Red Flag Observed'),
    ]
    name = models.CharField(max_length=100)
    url = models.URLField(help_text="n8n or Zapier Webhook URL")
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.name} ({self.event_type})"

# 13. SEMANTIC VECTOR INDEX
class CandidateEmbedding(models.Model):
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name='embedding_record')
    vector_json = models.TextField(help_text="JSON serialized embedding vector")
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self): return f"Vector: {self.candidate.full_name}"

# 14. NEGOTIATION SPARRING (Autonomous Closer)
class NegotiationSession(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Active Negotiation'),
        ('ACCEPTED', 'Offer Agreed'),
        ('REJECTED', 'Offer Declined'),
        ('STALLED', 'Awaiting Human Intervention'),
    ]
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='negotiation')
    current_salary_offer = models.FloatField()
    initial_salary_offer = models.FloatField()
    max_budget = models.FloatField()
    candidate_counter_offer = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    chat_history = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"Negotiation: {self.application.candidate.full_name}"


# 15. STRUCTURED COMPETENCIES
class Competency(models.Model):
    CATEGORY_CHOICES = [
        ('TECHNICAL', 'Technical Skills'),
        ('SOFT_SKILL', 'Soft Skills / Behavioral'),
        ('LEADERSHIP', 'Leadership & Management'),
        ('CULTURE_FIT', 'Culture & Values'),
    ]
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='TECHNICAL')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Competencies"
        ordering = ['category', 'name']

    def __str__(self): return f"{self.name} ({self.get_category_display()})"


# 16. COLLABORATIVE EVALUATION SCORECARDS
class EvaluationScorecard(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='scorecards')
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    overall_comments = models.TextField(blank=True)
    is_final = models.BooleanField(default=False, help_text="Set to true if this is the definitive hiring decision")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Scorecard: {self.application.candidate.full_name} by {self.recruiter.username}"


class EvaluationItem(models.Model):
    scorecard = models.ForeignKey(EvaluationScorecard, on_delete=models.CASCADE, related_name='items')
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE)
    score = models.IntegerField(default=3, help_text="Rating from 1-5")
    comments = models.CharField(max_length=255, blank=True)

    def __str__(self): return f"{self.competency.name}: {self.score}/5"


# 17. AUTOMATED ONBOARDING ROADMAP
class OnboardingRoadmap(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Drafting'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
    ]
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='onboarding_roadmap')
    tasks = models.JSONField(default=list, help_text="List of milestones: [{'title': '...', 'status': 'PENDING/DONE'}]")
    start_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    ai_generated_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Onboarding: {self.application.candidate.full_name}"
# 18. AI INTERVIEW SENTIMENT ANALYSIS (Phase 5)
class SentimentAnalysis(models.Model):
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name='sentiment')
    confidence_score = models.FloatField(default=0.0)
    clarity_score = models.FloatField(default=0.0)
    stress_level = models.FloatField(default=0.0) # 0 to 100
    honesty_index = models.FloatField(default=0.0)
    detailed_emotions = models.JSONField(default=dict, help_text="Breakdown: {'happy': 0.1, 'anxious': 0.4, ...}")
    key_phrases = models.JSONField(default=list, help_text="Detected significant technical or behavioral phrases")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Sentiment: {self.interview.application.candidate.full_name}"


# 20. BOTANIST VOICE INTERVIEW LOGS (Interactive Voice AI)
class VoiceInterviewLog(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='voice_logs')
    transcript = models.TextField(blank=True, help_text="Full transcription of the voice session")
    ai_evaluation = models.TextField(blank=True, help_text="Gemini evaluation of behavioral traits")
    
    # Vocal Analytics
    vocal_confidence_score = models.FloatField(default=0.0, help_text="0-100 score based on speech patterns")
    speech_rate = models.FloatField(default=0.0, help_text="Words per minute")
    hesitation_count = models.IntegerField(default=0, help_text="Number of detected 'um', 'uh', or long silence gaps")
    volume_consistency = models.FloatField(default=0.0, help_text="Stability of volume (0.0=erratic, 1.0=stable)")
    
    behavioral_fitment_summary = models.TextField(blank=True, help_text="Auto-generated summary for the recruiter")
    behavioral_traits = models.JSONField(default=dict, blank=True, help_text="Detected traits like 'Leadership', 'Clarity', etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"VoiceLog: {self.interview.application.candidate.full_name} ({self.vocal_confidence_score}%)"



# 19. AUTONOMOUS SOURCING (The Matchmaker)
class SourcingMatch(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='matchmaker_results')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='matchmaker_hits')
    match_score = models.FloatField()
    fit_rationale = models.TextField()
    is_shortlisted = models.BooleanField(default=False)
    notified_recruiter = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-match_score']
        unique_together = ['job', 'candidate']

    def __str__(self): return f"Match {self.match_score}%: {self.candidate.full_name}"


# 20. OFFER & COMPENSATION

# 20. CANDIDATE GROWTH ROADMAP (Bridge-Skilling)
class GrowthRoadmap(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='growth_roadmap')
    roadmap_data = models.JSONField(default=dict, help_text="AI-generated courses, projects, and milestones")
    summary = models.TextField(blank=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)
    is_shared_with_candidate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Roadmap for {self.application.candidate.full_name}"

# ──────────────────────────────────────────────────────
# Phase 6: ELITE INTELLIGENCE & GLOBAL POLISH (300+ Lines)
# ──────────────────────────────────────────────────────

# 21. AI USAGE MONITORING (Token & Feature tracking)
class AIUsageLog(models.Model):
    FEATURE_CHOICES = [
        ('RESUME_PARSER', 'Resume Parsing'),
        ('JD_ENHANCER', 'JD Enhancement'),
        ('INTERVIEW_GEN', 'Question Generation'),
        ('SENTIMENT', 'Sentiment Analysis'),
        ('MATCHMAKER', 'Matchmaker Bot'),
        ('ROADMAP', 'Growth Roadmap'),
        ('DECISION_MATRIX', 'Decision Matrix'),
        ('CHATBOT', 'Global Assistant'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ai_usage')
    feature = models.CharField(max_length=50, choices=FEATURE_CHOICES)
    model_used = models.CharField(max_length=50, default='gemini-2.0-flash')
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0) # Sum of input + output
    cost_estimate = models.FloatField(default=0.0)
    latency_ms = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='SUCCESS')
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "AI Usage Logs"

    def __str__(self): return f"{self.user.username} - {self.feature} ({self.status})"

# 22. HIRING VELOCITY & BOTTLENECK ANALYSIS
class HiringVelocity(models.Model):
    STAGE_CHOICES = Application.STATUS_CHOICES
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='velocity_logs')
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES)
    entered_at = models.DateTimeField(auto_now_add=True)
    exited_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Hiring Velocities"

    def __str__(self):
        return f"{self.application.candidate.user.username}: {self.stage}"


class PredictiveInsight(models.Model):
    """
    Phase 8: ML Engine - Stores predictive analytics for a candidate's future success.
    """
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='predictive_insight')
    success_probability = models.FloatField(help_text="Expected probability of top performance (0-100)")
    feature_importance_json = models.JSONField(blank=True, null=True, help_text="Impact of each metric on the score")
    gap_analysis_json = models.JSONField(blank=True, null=True, help_text="Benchmarking against ideal top performer profile")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction for {self.application.candidate.user.username}: {self.success_probability}%"

# 23. ADVANCED CANDIDATE INTELLIGENCE (Deeper AI Profile)
class CandidateIntelligence(models.Model):
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name='intelligence')
    growth_potential = models.FloatField(default=0.0, help_text="AI Predicted growth over 2 years")
    leadership_index = models.FloatField(default=0.0, help_text="Detected leadership traits/mentorship")
    technical_breadth = models.FloatField(default=0.0, help_text="Diversity of technology stack")
    churn_risk_score = models.FloatField(default=0.0, help_text="Calculated based on job hopping/skills")
    innovation_score = models.FloatField(default=0.0, help_text="Evidence of problem-solving/patents/projects")
    
    # NLP Insights
    sentiment_baseline = models.FloatField(default=0.0, help_text="Average positivity in communication")
    top_competencies = models.JSONField(default=list)
    missing_critical_skills = models.JSONField(default=list)
    career_trajectory = models.TextField(blank=True, help_text="AI summary of career path")
    
    last_analyzed = models.DateTimeField(auto_now=True)

    def __str__(self): return f"Intelligence: {self.candidate.full_name}"

# 24. RECRUITER PERFORMANCE METRICS
class RecruiterPerformance(models.Model):
    recruiter = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='performance')
    hiring_accuracy = models.FloatField(default=0.0, help_text="Matches vs Retentions")
    avg_time_to_fill = models.FloatField(default=0.0)
    interview_conversion_rate = models.FloatField(default=0.0)
    ai_efficiency_gain = models.FloatField(default=0.0, help_text="Time saved using SmartRecruit features")
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"Stats: {self.recruiter.username}"

# 25. THEME & UI PREFERENCES (Deeper storage)
class UserUIProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ui_profile')
    preferred_bg_theme = models.CharField(max_length=50, default='midnight-nebula')
    preferred_accent_color = models.CharField(max_length=20, default='#ff3366')
    glass_opacity = models.FloatField(default=0.1)
    animation_speed = models.FloatField(default=1.0) # 1.0 is normal
    enable_particles = models.BooleanField(default=True)
    font_family = models.CharField(max_length=50, default='Inter')
    font_scale = models.FloatField(default=1.0)
    
    # Sidebar Collapse state etc
    sidebar_collapsed = models.BooleanField(default=False)
    
    # System Telemetry & Notifications
    smtp_alerts_enabled = models.BooleanField(default=True)
    high_value_ping_enabled = models.BooleanField(default=True)
    
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self): return f"UI: {self.user.username}"

# 26. SYSTEM ANNOUNCEMENTS (Global Feed)
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-bullhorn')
    target_role = models.CharField(max_length=20, choices=[('ALL', 'All Users'), ('RECRUITER', 'Recruiters Only'), ('CANDIDATE', 'Candidates Only')], default='ALL')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.title

# 27. SECURITY LOGS (Compliance & Professionalism)
class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    action = models.CharField(max_length=255)
    resource = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self): return f"{self.timestamp} - {self.user.username if self.user else 'System'} : {self.action}"


# 28. VECTOR INTELLIGENCE (Semantic Hunter)


# ──────────────────────────────────────────────────────
# 29. PROFESSIONAL QUESTION BANK (50 Questions per Round)
# ──────────────────────────────────────────────────────

class QuestionBank(models.Model):
    """
    Enterprise 50-Question Bank — 4 Rounds, 200 questions total.
    System pulls 10-15 randomly per session for variety.
    """
    ROUND_CHOICES = [
        ('R1_APTITUDE',  'Round 1 — Aptitude (Logical, Quantitative, Verbal)'),
        ('R2_PRACTICAL', 'Round 2 — Practical (Coding + Programming MCQs)'),
        ('R3_TECHNICAL', 'Round 3 — Technical (CS, System Design, Django/ML)'),
        ('R4_HR',        'Round 4 — HR / Behavioral (STAR, Culture Fit)'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy',   'Easy'),
        ('medium', 'Medium'),
        ('hard',   'Hard'),
    ]
    CATEGORY_CHOICES = [
        # R1
        ('LOGICAL',       'Logical Reasoning'),
        ('QUANTITATIVE',  'Quantitative Aptitude'),
        ('VERBAL',        'Verbal Ability'),
        # R2
        ('PYTHON_CODING', 'Python / Coding'),
        ('JS_CODING',     'JavaScript Coding'),
        ('GOLANG_CODING', 'Go / Backend'),
        ('RUST_CODING',   'Rust / Systems'),
        ('JAVA_CODING',   'Java / Enterprise'),
        ('DSA',           'Data Structures & Algorithms'),
        ('WEB_CODING',    'Web Programming'),
        # R3
        ('CS_FUNDAMENTALS','CS Fundamentals'),
        ('SYSTEM_DESIGN', 'System Design'),
        ('DJANGO_ML',     'Django / Python / ML'),
        # R4
        ('BEHAVIORAL',    'Behavioral / STAR'),
        ('SITUATIONAL',   'Situational Judgment'),
        ('CULTURE_FIT',   'Culture & Values Fitment'),
    ]
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('java', 'Java'),
    ]
    MODERATION_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]


    round        = models.CharField(max_length=20, choices=ROUND_CHOICES, db_index=True)
    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='LOGICAL')
    language     = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python', help_text="Primary language for this challenge")
    difficulty   = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    question_text= models.TextField()
    # For MCQs: list of option strings e.g. ["Option A", "Option B", ...]
    options      = models.JSONField(default=list, blank=True)
    correct_answer = models.CharField(max_length=500, blank=True,
                                      help_text="Exact text of correct option, or model answer for open-ended")
    explanation  = models.TextField(blank=True, help_text="Why this answer is correct")
    # For R2 coding questions: starter code for Piston execution
    starter_code = models.TextField(blank=True, help_text="Python starter code for coding Qs")
    expected_output = models.CharField(max_length=500, blank=True)
    is_coding    = models.BooleanField(default=False, help_text="True if this is a live code execution Q")
    
    # ⚖️ GOVERNANCE & MODERATION (Module 4)
    moderation_status = models.CharField(max_length=20, choices=MODERATION_CHOICES, default='APPROVED')
    submitted_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_questions')
    
    # 📊 PERFORMANCE ANALYTICS (Bias Detection)
    attempt_count     = models.IntegerField(default=0)
    failure_count     = models.IntegerField(default=0)
    
    is_active    = models.BooleanField(default=True)

    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name      = 'Question Bank Entry'
        verbose_name_plural = 'Question Bank'
        indexes = [
            models.Index(fields=['round', 'difficulty', 'is_active']),
        ]
        ordering = ['round', 'difficulty']

    def __str__(self):
        return f"[{self.get_round_display()}] [{self.difficulty}] {self.question_text[:60]}"

    @property
    def options_list(self) -> list:
        if isinstance(self.options, list):
            return self.options
        return []

# 28. PREDICTIVE RETENTION ANALYTICS (Attrition Forecast)
class TurnoverPrediction(models.Model):
    RISK_LEVELS = [
        ('LOW', 'Low Risk (Stable)'),
        ('MEDIUM', 'Medium Risk (Neutral)'),
        ('HIGH', 'High Risk (At-Risk)'),
    ]
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name='turnover_prediction')
    retention_score = models.FloatField(default=0.0, help_text="Probability of staying with the company (0-100%)")
    
    # Explanatory Metrics
    technical_stability = models.FloatField(default=0.0, help_text="Consistency in technical assessment performance")
    sentiment_stability = models.FloatField(default=0.0, help_text="Stability of emotional response during interviews")
    behavioral_alignment = models.FloatField(default=0.0, help_text="Match with company culture and values")
    time_efficiency = models.FloatField(default=0.0, help_text="Score based on assessment speed vs accuracy")
    
    # Data for Visualization
    radar_data = models.JSONField(default=dict, help_text="JSON data for Chart.js Radar Map")
    
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='MEDIUM')
    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-retention_score']
        verbose_name_plural = "Turnover Predictions"

    def __str__(self):
        return f"Prediction: {self.candidate.full_name} ({self.retention_score}%)"

    def save(self, *args, **kwargs):
        # Auto-set risk level based on score
        if self.retention_score >= 80:
            self.risk_level = 'LOW'
        elif self.retention_score <= 40:
            self.risk_level = 'HIGH'
        else:
            self.risk_level = 'MEDIUM'
        super().save(*args, **kwargs)



# 22. ATS BI-DIRECTIONAL SYNC CONFIG & LOGS
class ATSSyncConfig(models.Model):
    PROVIDER_CHOICES = [('WORKDAY', 'Workday'), ('GREENHOUSE', 'Greenhouse'), ('LEVER', 'Lever'), ('SAP_SUCCESSFACTORS', 'SAP SuccessFactors')]
    
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default='WORKDAY')
    internal_stage = models.CharField(max_length=20, choices=Application.STATUS_CHOICES, unique=True)
    external_ats_stage = models.CharField(max_length=100, help_text="Exact stage name in the external ATS")
    is_active = models.BooleanField(default=True)

    def __str__(self): return f"[{self.provider}] {self.internal_stage} -> {self.external_ats_stage}"

class ExternalATSMapping(models.Model):
    """Links SmartRecruit entities to external Enterprise IDs."""
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ats_mappings')
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='ats_mapping', null=True, blank=True)
    external_system_name = models.CharField(max_length=50, default='Workday')
    external_candidate_id = models.CharField(max_length=255, db_index=True)
    external_application_id = models.CharField(max_length=255, null=True, blank=True)
    last_sync_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self): return f"{self.candidate.full_name} <-> {self.external_system_name} ({self.external_candidate_id})"

class ATSSyncLog(models.Model):
    SYNC_TYPES = [('PUSH', 'Outgoing Link'), ('PULL', 'Incoming Webhook')]
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=10, choices=SYNC_TYPES)
    payload = models.TextField()
    response = models.TextField(blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    is_success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self): return f"{self.sync_type} - {self.application.candidate.full_name} ({'PASS' if self.is_success else 'FAIL'})"
# 23. GAMIFICATION & ACHIEVEMENTS
class Badge(models.Model):
    RARITY_CHOICES = [('COMMON', 'Common'), ('RARE', 'Rare'), ('EPIC', 'Epic'), ('LEGENDARY', 'Legendary')]
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, default="fas fa-medal")
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='STANDARD')
    hex_color = models.CharField(max_length=20, default="#00d2ff") # Default Neon Blue
    criteria_json = models.TextField(blank=True, help_text="Internal JSON criteria for automated awards")

    @property
    def clash_color(self):
        return "#ff00ff" if self.rarity == 'EPIC' else "#00d2ff"

    def __str__(self): return f"{self.name} ({self.rarity})"
# 13. AUDIT LOG (Ethical AI)
class BiasAuditLog(models.Model):
    """Stores results of retrospective bias audits for Job Postings."""
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='bias_audits')
    audit_date = models.DateTimeField(default=timezone.now)
    
    # Fairness Metrics
    fairness_score = models.FloatField(default=0.0, help_text="Overall rating 0-100")
    disparate_impact_ratio = models.FloatField(default=1.0)
    equal_opportunity_diff = models.FloatField(default=0.0)
    
    # Aggregated Stats (Differential Privacy applied)
    demographics_json = models.JSONField(default=dict, blank=True)
    
    is_certified = models.BooleanField(default=False, help_text="True if process meets meritocratic standards")
    audit_report = models.TextField(blank=True)
    
    # Bias Alerts
    has_risk = models.BooleanField(default=False)
    risk_details = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-audit_date']

    def __str__(self):
        return f"Audit for {self.job.title} - {self.audit_date.date()}"
# 14. SYSTEM DESIGN ASSESSMENT (Architecture Tool)
class SystemDesignAssessment(models.Model):
    """Stores candidate-built system architecture diagrams and AI evaluations."""
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='system_design')
    diagram_json = models.JSONField(default=dict, help_text="Stores Drawflow node and connection data")
    
    # AI Evaluation results
    ai_score = models.FloatField(default=0.0)
    ai_analysis = models.TextField(blank=True, help_text="AI breakdown of architectural strengths and weaknesses")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Design Assessment"
        verbose_name_plural = "System Design Assessments"

    def __str__(self):
        return f"System Design: {self.application.candidate.full_name} ({self.ai_score}%)"

# ==============================================================================
# PHASE 9: SMART SCHEDULER (ZERO-COST CALENDAR ENGINE)
# ==============================================================================
class RecruiterAvailability(models.Model):
    """
    Stores interview timeslots designated by a Recruiter.
    Timezone field ensures correct UTC conversion for international deployments.
    """
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='smart_scheduler_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    # Timezone support for international scheduling
    timezone_name = models.CharField(
        max_length=50,
        default='Asia/Kolkata',
        help_text='IANA timezone e.g. Asia/Kolkata, UTC, America/New_York'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name_plural = "Recruiter Availabilities"
        unique_together = ('recruiter', 'date', 'start_time', 'end_time')

    def __str__(self):
        status = '[BOOKED]' if self.is_booked else '[OPEN]'
        return f"{self.recruiter.username} - {self.date} {self.start_time} to {self.end_time} {status} [{self.timezone_name}]"

    @property
    def slot_label(self):
        """Human-readable display string for the template."""
        return f"{self.start_time.strftime('%H:%M')} – {self.end_time.strftime('%H:%M')} ({self.timezone_name})"


# ─── PLATFORM SETTINGS (Admin-Controlled Global Config) ────────────────────
class PlatformSetting(models.Model):
    """
    Key-value store for admin-configurable platform-wide settings.
    """
    key = models.CharField(max_length=100, unique=True, help_text="Setting identifier e.g. passing_score_r1")
    value = models.TextField(help_text="Setting value (stored as string, cast on read)")
    label = models.CharField(max_length=200, blank=True, help_text="Human-readable label shown in admin UI")
    group = models.CharField(max_length=50, default='general', help_text="Setting group for UI grouping")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['group', 'key']

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, label='', group='general'):
        obj, _ = cls.objects.get_or_create(key=key, defaults={'label': label, 'group': group})
        obj.value = str(value)
        obj.label = label or obj.label
        obj.group = group or obj.group
        obj.save()
        return obj


# ─── INTEGRATION TRIGGERS (Rule Engine) ────────────────────────────────────
class TriggerRule(models.Model):
    """
    Automated rules for external actions based on candidate performance.
    Example: If Score > 90, Send WhatsApp to Admin.
    """
    CONDITION_CHOICES = [
        ('SCORE_ABOVE', 'AI Score Above'),
        ('STAGE_REACHED', 'Application Stage Reached'),
        ('VIOLATION_COUNT', 'Proctoring Violations > X'),
    ]
    ACTION_CHOICES = [
        ('SEND_WHATSAPP', 'Send WhatsApp Notification'),
        ('SEND_EMAIL', 'Send Custom Email'),
        ('TRIGGER_WEBHOOK', 'Fire External Webhook'),
    ]
    
    name = models.CharField(max_length=100)
    condition_type = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    threshold = models.FloatField(null=True, blank=True, help_text="Numeric threshold (e.g. 90.0)")
    target_stage = models.CharField(max_length=50, blank=True, help_text="Target stage for STAGE_REACHED")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    webhook_url = models.URLField(blank=True, null=True, help_text="Required for TRIGGER_WEBHOOK")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rule: {self.name} ({self.get_action_display()})"


# ─── ENCRYPTED API KEYS (Vault) ───────────────────────────────────────────
class EncryptedAPIKey(models.Model):
    """
    Secure storage for third-party API credentials (Twilio, SendGrid, etc).
    Stored encrypted at the database level.
    """
    service_name = models.CharField(max_length=100, unique=True, help_text="e.g. TWILIO_AUTH_TOKEN")
    encrypted_value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    last_rotated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Vault Key: {self.service_name}"

