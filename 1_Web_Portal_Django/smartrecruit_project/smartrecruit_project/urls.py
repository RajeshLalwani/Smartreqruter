from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
# --- THIS IMPORT WAS MISSING OR INCORRECT ---
from core import views as core_views 
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from jobs.api_views import CandidateDashboardAPI, JobPostingListAPI, InterviewStateAPI

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth & Dashboard
    path('', core_views.landing, name='home'),
    path('login/', core_views.login_view, name='login'),
    path('register/', core_views.register_view, name='register'),
    path('logout/', core_views.logout_view, name='logout'),
    path('accounts/', include('allauth.urls')),
    path('forgot-password/', core_views.forgot_password_view, name='forgot_password'),
    path(
        'reset-password-confirm/<str:uidb64>/<str:token>/',
        core_views.reset_password_confirm_view,
        name='reset_password_confirm'
    ),
    path('dashboard/', core_views.dashboard, name='dashboard'),
    path('verify/', core_views.verify_credential, name='verify_credential'),
    path('api/analyze-vocal-confidence/', core_views.analyze_vocal_confidence, name='analyze_vocal_confidence'),
    
    # Admin Dashboard URLs (Superuser)
    path('portal-admin/dashboard/', core_views.admin_dashboard, name='admin_dashboard'),
    path('portal-admin/users/', core_views.admin_users, name='admin_users'),
    path('portal-admin/users/add/', core_views.admin_add_user, name='admin_add_user'),
    path('portal-admin/users/export/', core_views.admin_export_users, name='admin_export_users'),
    path('portal-admin/users/<int:user_id>/toggle-status/', core_views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('portal-admin/users/<int:user_id>/delete/', core_views.admin_delete_user, name='admin_delete_user'),
    path('portal-admin/jobs/', core_views.admin_jobs, name='admin_jobs'),
    path('portal-admin/jobs/<int:job_id>/toggle/', core_views.admin_toggle_job_status, name='admin_toggle_job_status'),
    path('portal-admin/jobs/<int:job_id>/approve/', core_views.admin_approve_job, name='admin_approve_job'),
    path('portal-admin/interviews/', core_views.admin_interviews, name='admin_interviews'),
    path('portal-admin/applications/', core_views.admin_applications, name='admin_applications'),
    path('portal-admin/system-log/', core_views.admin_system_log, name='admin_system_log'),
    path('portal-admin/analytics/', core_views.admin_analytics, name='admin_analytics'),
    path('portal-admin/settings/', core_views.admin_platform_settings, name='admin_platform_settings'),
    path('portal-admin/broadcast/', core_views.admin_broadcast, name='admin_broadcast'),
    path('portal-admin/recruiters/', core_views.admin_recruiter_performance, name='admin_recruiter_performance'),
    path('portal-admin/ai-hub/', core_views.admin_ai_hub, name='admin_ai_hub'),
    path('portal-admin/compliance/', core_views.admin_compliance_vault, name='admin_compliance_vault'),
    path('portal-admin/integrations/', core_views.admin_integration_center, name='admin_integration_center'),
    path('portal-admin/api-vault/', core_views.admin_api_keys, name='admin_api_keys'),
    path('portal-admin/questions/', core_views.admin_question_bank, name='admin_question_bank'),
    path('portal-admin/questions/moderate/<int:q_id>/', core_views.admin_question_moderate, name='admin_question_moderate'),
    path('portal-admin/questions/gen-api/', core_views.admin_question_gen_api, name='admin_question_gen_api'),
    path('portal-admin/questions/bulk-save/', core_views.admin_question_bulk_save, name='admin_question_bulk_save'),
    path('portal-admin/export-data/', core_views.admin_export_data, name='admin_export_data'),
    path('portal-admin/activity-feed-api/', core_views.admin_activity_feed_api, name='admin_activity_feed_api'),
    
    # Advanced Proctoring Configuration (Module 5)
    path('portal-admin/proctoring/config/', core_views.admin_proctoring_config, name='admin_proctoring_config'),
    path('portal-admin/proctoring/review/', core_views.admin_proctoring_review, name='admin_proctoring_review'),
    path('portal-admin/proctoring/review/<int:interview_id>/', core_views.admin_proctoring_detail, name='admin_proctoring_detail'),


    # System Health War Room
    path('system-health/', core_views.system_health_dashboard, name='system_health'),
    path('system-health/api/', core_views.system_health_api, name='system_health_api'),

    
    # Settings URL
    path('settings/', core_views.settings_view, name='settings'),
    path('i18n/', include('django.conf.urls.i18n')),

    # Jobs App URLs
    path('jobs/', include('jobs.urls')),

    # Interview App URLs
    path('interview/', include('interview.urls')),
    
    path('api/v1/jobs/', JobPostingListAPI.as_view(), name='api_job_list'),
    path('api/v1/dashboard/', CandidateDashboardAPI.as_view(), name='api_dashboard'),
    path('api/v1/interview/<int:interview_id>/', InterviewStateAPI.as_view(), name='api_interview_state'),
    
    # JWT Auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # PWA Support
    path('offline/', core_views.offline_view, name='offline'),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw.js'),

    # Proctoring Replay & Reports
    path('api/proctor/session/<int:interview_id>/frames/', core_views.get_session_frames, name='api_proctor_frames'),
    path('api/proctor/session/<int:interview_id>/report/', core_views.download_proctoring_report, name='api_proctor_report'),
    # Neural Assistant (Phase 10)
    path('core/voice-assistant-api/', core_views.voice_assistant_api, name='voice_assistant_api'),
]

# Serving media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
