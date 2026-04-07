from django.contrib import admin
from .models import JobPosting, Candidate, Application, Interview, EmailTemplate, Question, ProctoringLog, Assessment, Offer

class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_at')
    list_filter = ('status', 'job_type')
    search_fields = ('title', 'required_skills')

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'experience_years')
    search_fields = ('full_name', 'email')

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'status', 'ai_score')
    list_filter = ('status',)

admin.site.register(JobPosting, JobPostingAdmin)
admin.site.register(Candidate, CandidateAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Interview)
admin.site.register(EmailTemplate)
admin.site.register(Question)
admin.site.register(ProctoringLog)
admin.site.register(Assessment)
admin.site.register(Offer)
