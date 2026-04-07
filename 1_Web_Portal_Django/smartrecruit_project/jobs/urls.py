from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import views_hrms, views_botanist
from . import ats_sync_views, views_recruiter
from .views_analytics_export import (
    export_analytics_csv_view,
    export_analytics_pdf_view,
    analytics_api,
    export_candidates_csv
)
from .analytics_view import recruiter_analytics
from .views_candidate import (
    candidate_profile_view,
    candidate_applications_view,
    candidate_skills_api,
    candidate_statistics_api,
    take_mock_test
)
from . import views_questions, views_proctoring
from .views_ai_features import (
    skill_gap_analysis,
    predictive_score_api,
    candidate_rankings,
    analytics_trend_api,
    skill_gap_api,
    resume_intelligence_view,
    blind_hiring_view,
    sentiment_analysis_view,
    talent_intelligence_view,
    proctoring_heatmap_api,
)
from .views_coding_arena import (
    coding_arena,
    coding_challenge_solve,
    execute_code,
    get_ai_hint,
    coding_leaderboard,
)
from .views_interview_prep import (
    interview_prep_tips,
    regenerate_prep_tips_api,
)
from .views_new_features import (
    hiring_funnel_dashboard,
    cover_letter_scorer,
    resume_ats_checker,
    job_recommendations,
    upskilling_roadmap,
    candidate_analytics,
    jd_enhancer_api,
    score_trend_api,
)
from .views_next_gen import *
from . import views_elite, views_ultimate, views_automation, views_vector, views_agentic, views_experience, views_compliance, views_sourcing, views_assessment_lab, views_negotiation, views_culture, views_velocity, views_oracle, views_hunter, views_mapping, views_crew

from .views_advanced import (
    diversity_dashboard,
    time_to_hire_predictor,
    smart_question_generator,
    ai_email_drafter,
    talent_pool,
    department_analytics,
    reference_check,
    ai_resume_builder,
    psychometric_test,
    video_pitch_analyser,
    analyse_pitch_api,
    competitive_standing,
    salary_calibrator,
    application_tracker,
    job_market_intelligence,
    onboarding_plan,
    proctoring_dashboard,
    submit_feedback,
    feedback_analytics,
    faq_bot_api,
)

from .rag_search_views import api_rag_search

urlpatterns = [
    # --- REDIRECTS FOR USER FRIENDLINESS ---
    path('list/', RedirectView.as_view(url='/jobs/', permanent=True)),
    
    path('', views.job_list, name='job_list'),
    path('<int:job_id>/', views.job_detail, name='job_detail'),
    path('<int:job_id>/apply/', views.apply_job, name='apply_job'),
    
    # Dashboard Links
    path('post-job/', views.post_job, name='post_job'),
    path('generate-jd/', views.generate_jd_ai, name='generate_jd_ai'),
    path('job/<int:job_id>/toggle-status/', views.toggle_job_status, name='toggle_job_status'),
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('application/<int:application_id>/', views.application_details, name='application_details'),
    
    # 🔐 COMPLIANCE & GDPR
    path('profile/export/', views_compliance.candidate_gdpr_export, name='candidate_gdpr_export'),
    
    # NEW: AI Interview (Round 3)
    path('interview/ai/<int:application_id>/', views.ai_interview, name='ai_interview'),
    
    # NEW: HR Interview (Round 4)
    path('interview/hr/<int:application_id>/', views.ai_hr_interview, name='ai_hr_interview'),
    path('hr-decision/<int:application_id>/', views.hr_decision_view, name='hr_decision'),

    
    # NEW: ATS Bi-directional Synchronization
    path('api/v1/ats-sync/', ats_sync_views.ats_webhook_listener, name='ats_webhook_listener'),
    path('ats-monitor/', ats_sync_views.ats_sync_monitor, name='ats_sync_monitor'),
    
    # NEW: Botanist Voice AI Interview (Pre-screening)
    path('interview/botanist/<int:application_id>/', views.botanist_interview_view, name='botanist_interview'),
    path('api/botanist/chat/', views_botanist.botanist_chat_view, name='botanist_chat'),
    path('api/botanist/finalize/', views_botanist.finalize_behavioral_round, name='botanist_finalize_round'),
    path('interview-complete/<int:interview_id>/', views.interview_complete_view, name='interview_complete_report'),
    
    # NEW: Collaborative Live Session (Synchronized IDE)
    path('interview/live/<int:application_id>/', views.live_interview_session, name='live_interview_session'),
    path('api/save-live-code/<int:application_id>/', views.save_live_code, name='save_live_code'),
    path('api/save-system-design/<int:application_id>/', views.save_system_design, name='save_system_design'),
    
    # NEW: View Offer
    path('offer/<int:application_id>/', views.view_offer, name='view_offer'),
    path('offer/<int:application_id>/accept/', views.accept_offer, name='accept_offer'),
    
    # NEW: Interviews Link
    path('interviews/', views.interview_list, name='interview_list'),
    path('calendar/', views.interview_calendar, name='interview_calendar'),
    path('calendar/api/', views.calendar_api, name='calendar_api'),
    
    # Scheduler (Recruiter & Candidate)
    path('availability/', views.manage_availability, name='manage_availability'),
    path('schedule/<int:application_id>/', views.schedule_interview_view, name='schedule_interview_view'),
    path('api/recruiter-slots/<int:recruiter_id>/', views.api_recruiter_slots, name='api_recruiter_slots'),
    path('api/book-slot/', views.api_book_slot, name='api_book_slot'),
    
    # Kanban Board
    path('kanban/', views.kanban_view, name='kanban_board'),
    path('kanban/update/<int:application_id>/<str:new_status>/', views.kanban_update_api, name='kanban_update_api'),
    
    # Email Settings
    path('email/settings/', views.email_settings, name='email_settings'),
    
    # Notification APIs
    path('api/notifications/get/', views.get_notifications_api, name='get_notifications_api'),
    path('api/notifications/read/<int:notification_id>/', views.mark_notification_read_api, name='mark_notification_read_api'),
    path('api/notifications/read/all/', views.mark_all_notifications_read_api, name='mark_all_notifications_read_api'),
    path('api/notifications/delete/<int:notification_id>/', views.delete_notification_api, name='delete_notification_api'),
    
    # FER Sentiment API
    path('api/sentiment-stream/<int:application_id>/', views.process_sentiment_stream, name='process_sentiment_stream'),
    
    # Export PDF

    path('export/pdf/<int:application_id>/', views.export_candidate_pdf, name='export_candidate_pdf'),
    path('export/hr-report/<int:application_id>/', views.export_hr_report, name='export_hr_report'),
    path('export/csv/<int:application_id>/', views.export_candidate_csv, name='export_candidate_csv'),
    
    # NEW: Take Assessment (Round 1 & 2)
    path('assessment/<int:application_id>/<str:test_type>/', views.take_assessment, name='take_assessment'),
    path('assessment/<int:application_id>/regenerate/', views.regenerate_ai_assessment, name='regenerate_ai_assessment'),
    path('assessment/<int:application_id>/terminate/', views.terminate_ai_session, name='terminate_ai_session'),

    # ⚡ Thunder Analysis — AI Resume Preview AJAX Endpoint
    path('api/thunder-analyse/<int:job_id>/', views.api_thunder_analyse, name='api_thunder_analyse'),

    # ⚡ Proctoring Backend — Violation Logger & Vision Heartbeat
    path('api/proctor/log/<int:application_id>/', views.log_violation, name='log_violation'),
    path('api/proctor/heartbeat/<int:application_id>/', views.vision_heartbeat, name='vision_heartbeat'),


    
    # Analytics Dashboard
    path('analytics/', views.recruiter_analytics, name='recruiter_analytics'),
    path('onboarding/<int:application_id>/', views.onboarding_plan, name='onboarding_plan'),
    
    # Analytics Export
    path('analytics/export/csv/', export_analytics_csv_view, name='export_analytics_csv'),
    path('analytics/export/pdf/', export_analytics_pdf_view, name='export_analytics_pdf'),
    path('analytics/api/', analytics_api, name='analytics_api'),
    path('api/system-load/', views_recruiter.system_load_api, name='system_load_api'),
    path('api/ethics-audit/<int:job_id>/', views_recruiter.ethics_audit_api, name='ethics_audit_api'),
    
    # Candidate Profile
    path('profile/', candidate_profile_view, name='candidate_profile'),
    path('my-applications/', candidate_applications_view, name='candidate_applications'),
    path('profile/skills-api/', candidate_skills_api, name='candidate_skills_api'),
    path('profile/statistics-api/', candidate_statistics_api, name='candidate_statistics_api'),
    path('mock-test/', take_mock_test, name='take_mock_test'),
    
    # Question Bank
    path('questions/', views_questions.question_list, name='question_list'),
    path('questions/add/', views_questions.add_question, name='add_question'),
    path('questions/edit/<int:question_id>/', views_questions.edit_question, name='edit_question'),
    path('questions/delete/<int:question_id>/', views_questions.delete_question, name='delete_question'),
    path('questions/preview/<int:job_id>/<str:test_type>/', views_questions.preview_assessment, name='preview_assessment'),
    path('api/generate-questions/', views_questions.generate_questions_api, name='generate_questions_api'),
    
    # Proctoring API
    path('proctor/log/<int:application_id>/', views_proctoring.log_violation, name='log_violation'),
    path('api/proctor/violation/', views_proctoring.log_proctoring_violation_api, name='log_proctoring_violation_api'),
    path('proctor/heartbeat/<int:application_id>/', views_proctoring.vision_heartbeat, name='vision_heartbeat'),
    
    # Bulk Actions
    path('bulk-action/', views.bulk_action, name='bulk_action'),
    path('status/update/<int:application_id>/<str:new_status>/', views.update_status, name='update_status'),
    
    # AI JD Generator
    path('api/generate-jd/', views.generate_jd_api, name='generate_jd_api'),
    
    # Export Candidates
    path('candidates/export/', export_candidates_csv, name='export_candidates_csv'),
    path('api/scorecard/save/<int:application_id>/', views.scorecard_save_api, name='scorecard_save_api'),

    # Agentic AI & Deep Vision
    path('api/agent-insights/', views.agent_insights_api, name='agent_insights_api'),
    path('api/elite-alerts/', views.elite_alerts_api, name='elite_alerts_api'),
    path('api/candidate-navigator/', views.candidate_navigator_api, name='candidate_navigator_api'),
    path('api/invite-draft/<int:application_id>/', views.draft_personalized_invite, name='draft_personalized_invite'),
    path('api/deep-vision-audit/', views.run_deep_vision_audit, name='run_deep_vision_audit'),

    # RAG 'Talk to Resume' Search
    path('api/rag-search/', api_rag_search, name='api_rag_search'),

    # ── AI Features (Data Science & Automation) ──────────────
    path('application/<int:application_id>/skill-gap/', skill_gap_analysis, name='skill_gap_analysis'),
    path('application/<int:application_id>/predictive-score/', predictive_score_api, name='predictive_score_api'),
    path('application/<int:application_id>/skill-gap-api/', skill_gap_api, name='skill_gap_api'),
    path('job/<int:job_id>/rankings/', candidate_rankings, name='candidate_rankings'),
    path('api/analytics/trend/', analytics_trend_api, name='analytics_trend_api'),
    path('application/<int:application_id>/proctoring-heatmap/', proctoring_heatmap_api, name='proctoring_heatmap_api'),

    # ── Resume Intelligence, Blind Hiring, Sentiment ───────────
    path('application/<int:application_id>/resume-intelligence/', resume_intelligence_view, name='resume_intelligence'),
    path('job/<int:job_id>/blind-hiring/', blind_hiring_view, name='blind_hiring'),
    path('application/<int:application_id>/sentiment/', sentiment_analysis_view, name='sentiment_analysis'),

    # ── Talent Intelligence (Salary + Culture + Offer) ────────
    path('application/<int:application_id>/talent-intelligence/', talent_intelligence_view, name='talent_intelligence'),

    # ── Coding Practice Arena ─────────────────────────────
    path('arena/',                                    coding_arena,                name='coding_arena'),
    path('arena/challenge/<slug:slug>/',               coding_challenge_solve,      name='coding_challenge_solve'),
    path('arena/execute/',                            execute_code,                name='execute_code'),
    path('arena/hint/',                               get_ai_hint,                 name='get_ai_hint'),
    path('arena/leaderboard/',                        coding_leaderboard,          name='coding_leaderboard'),

    # ── AI Interview Prep ──────────────────────────────
    path('prepare/',                                  interview_prep_tips,         name='interview_prep'),
    path('prepare/<int:application_id>/',             interview_prep_tips,         name='interview_prep_for_job'),
    path('prepare/regenerate/',                       regenerate_prep_tips_api,    name='regenerate_prep_tips'),

    # ── Feature A: Hiring Funnel Analytics (Recruiter) ───────────
    path('funnel/',                                   hiring_funnel_dashboard,     name='hiring_funnel'),

    # ── Feature B: Cover Letter Scorer ────────────────────
    path('cover-letter/',                             cover_letter_scorer,         name='cover_letter_scorer'),

    # ── Feature E: JD Enhancer API ──────────────────────
    path('api/enhance-jd/',                           jd_enhancer_api,             name='jd_enhancer_api'),

    # ── Feature F: Score Trend API ──────────────────────
    path('application/<int:application_id>/score-trend/', score_trend_api,         name='score_trend_api'),

    # ── Feature G: Resume ATS Checker (Candidate) ──────────
    path('ats-checker/',                              resume_ats_checker,          name='resume_ats_checker'),

    # ── Feature H: Job Recommendations (Candidate) ────────
    path('recommendations/',                          job_recommendations,         name='job_recommendations'),

    # ── Feature I: Upskilling Roadmap ──────────────────
    path('application/<int:application_id>/roadmap/', upskilling_roadmap,          name='upskilling_roadmap'),

    # ── Feature J: Candidate Analytics ─────────────────
    path('my-analytics/',                             candidate_analytics,         name='candidate_analytics'),

    # ── ADVANCED FEATURES (1–18) ──────────────────────────────
    # 1. D&I Dashboard
    path('diversity/',                                diversity_dashboard,         name='diversity_dashboard'),
    # 2. Time-to-Hire Predictor
    path('time-to-hire/',                             time_to_hire_predictor,      name='time_to_hire'),
    # 3. Smart Question Generator
    path('question-gen/',                             smart_question_generator,    name='smart_question_gen'),
    # 4. AI Email Drafter
    path('email-drafter/',                            ai_email_drafter,            name='ai_email_drafter'),
    # 5. Talent Pool
    path('talent-pool/',                              talent_pool,                 name='talent_pool'),
    # 6. Department Analytics
    path('dept-analytics/',                           department_analytics,        name='department_analytics'),
    # 7. Reference Check
    path('application/<int:application_id>/ref-check/', reference_check,          name='reference_check'),
    # 8. AI Resume Builder
    path('resume-builder/',                           ai_resume_builder,           name='ai_resume_builder'),
    # 9. Psychometric Test
    path('psychometric/',                             psychometric_test,           name='psychometric_test'),
    # 10. Video Pitch Analyser
    path('video-pitch/',                              video_pitch_analyser,        name='video_pitch'),
    path('api/analyse-pitch/',                        analyse_pitch_api,           name='analyse_pitch_api'),
    # 11. Competitive Standing
    path('application/<int:application_id>/standing/', competitive_standing,       name='competitive_standing'),
    # 12. Salary Calibrator
    path('salary-calibrator/',                        salary_calibrator,           name='salary_calibrator'),
    # 13. Application Tracker (Kanban)
    path('tracker/',                                  application_tracker,         name='application_tracker'),
    # 14. Market Intelligence
    path('market-intel/',                             job_market_intelligence,     name='job_market_intelligence'),
    # 15. Onboarding Plan
    path('application/<int:application_id>/onboarding/', onboarding_plan,         name='onboarding_plan'),
    # 16. Enhanced Proctoring Dashboard
    path('proctoring/',                               proctoring_dashboard,        name='proctoring_dashboard'),
    # 17. Anonymous Feedback
    path('application/<int:application_id>/feedback/', submit_feedback,            name='submit_feedback'),
    path('feedback-analytics/',                       feedback_analytics,          name='feedback_analytics'),
    # 18. FAQ Bot API
    path('api/faq-bot/',                              faq_bot_api,                 name='faq_bot_api'),

    # ── NEXT-GEN AI FEATURES (19–28) ──────────────────────────
    # 19. Ghosting Risk Index
    path('ghosting-risk/',                            ghosting_risk_index,         name='ghosting_risk'),
    # 20. Inclusive JD Scrubber
    path('jd-scrubber/',                             inclusive_jd_scrubber,       name='jd_scrubber'),
    # 21. Collaborative Panel Scoresheets
    path('panel-scoring/<int:application_id>/',      panel_scoresheet,            name='panel_scoresheet'),
    # 22. Internal Mobility Engine
    path('internal-mobility/',                       internal_mobility_engine,    name='internal_mobility'),
    # 23. Offer Acceptance Predictor
    path('offer-predictor/<int:application_id>/',    offer_acceptance_predictor,  name='offer_predictor'),
    # 24. Interactive 3D Skill Graph
    path('skill-universe/',                          skill_universe_3d,           name='skill_universe'),
    # 25. AI Voice Screening Bot
    path('voice-screening/<int:application_id>/',    voice_screening_bot,         name='voice_screening'),
    # 26. Personal Branding Assistant
    path('branding-assistant/',                      personal_branding_assistant, name='branding_assistant'),
    # 27. Peer Competitive standing (Deep)
    path('peer-standing/<int:application_id>/',      peer_competitive_standing,   name='peer_standing'),
    # 28. Candidate Success Predictor
    path('next-gen/success-predictor/<int:application_id>/', candidate_success_predictor, name='success_predictor'),
    
    # 29. Dynamic AI Interview Processor (Epic 1)
    path('api/interview/process-answer/', process_interview_answer_api, name='process_interview_answer_api'),

    # ══════════════════════════════════════════════════════════════════════════
    # ELITE ENTERPRISE AI FEATURES (Specialized)
    # ══════════════════════════════════════════════════════════════════════════
    path('elite/interview-copilot/<int:application_id>/', views_elite.interview_copilot, name='interview_copilot'),
    path('elite/reference-check-bot/<int:application_id>/', views_elite.reference_check_bot, name='reference_check_bot'),
    path('elite/blind-hiring-redactor/<int:application_id>/', views_elite.blind_hiring_redactor, name='blind_hiring_redactor'),
    path('elite/talent-density-map/', views_elite.talent_density_map, name='talent_density_map'),
    path('elite/career-trajectory-explorer/', views_elite.career_trajectory_explorer, name='career_trajectory_explorer'),
    path('elite/infra-health/', views_elite.infra_health_monitor, name='infra_health_monitor'),
    path('elite/ethics-dashboard/', views_elite.ethics_diversity_dashboard, name='ethics_dashboard'),
    path('api/v1/audit/run/<int:job_id>/', views_elite.run_bias_audit_api, name='run_bias_audit_api'),
    path('api/save-system-design/<int:application_id>/', views_elite.save_system_design, name='save_system_design'),
    path('elite/architecture/preview/<int:application_id>/', views_elite.architecture_preview, name='architecture_preview'),

    # ══════════════════════════════════════════════════════════════════════════
    # ULTIMATE INTELLIGENCE AI FEATURES (Agentic/DL/Data Sci)
    # ══════════════════════════════════════════════════════════════════════════
    path('ultimate/negotiation/<int:application_id>/', views_ultimate.negotiation_sparring, name='negotiation_sparring'),
    path('ultimate/churn-sentinel/', views_ultimate.talent_churn_sentinel, name='churn_sentinel'),
    path('ultimate/success-blueprint/<int:application_id>/', views_ultimate.success_blueprint, name='success_blueprint'),
    path('ultimate/relocation-ai/', views_ultimate.relocation_lifestyle_ai, name='relocation_ai'),
    path('ultimate/culture-simulator/<int:application_id>/', views_ultimate.culture_fit_simulator, name='culture_simulator'),

    # ══════════════════════════════════════════════════════════════════════════
    # AUTOMATION HUB (n8n/Zapier Connectors)
    # ══════════════════════════════════════════════════════════════════════════
    path('automation/hub/', views_automation.automation_hub, name='automation_hub'),
    path('automation/delete/<int:webhook_id>/', views_automation.delete_webhook, name='delete_webhook'),
    path('api/automation/incoming-lead/', views_automation.receive_sourced_candidate, name='receive_sourced_candidate'),

    # ══════════════════════════════════════════════════════════════════════════
    # KNOWLEDGE PILLAR (Vector Search)
    # ══════════════════════════════════════════════════════════════════════════
    path('hunter/semantic/', views_vector.semantic_hunter, name='semantic_hunter'),
    path('hunter/rebuild/', views_vector.rebuild_vector_index, name='rebuild_index'),
    path('hunter/galaxy/', views_vector.talent_galaxy, name='talent_galaxy'),
    path('api/hunter/galaxy/', views_vector.talent_galaxy_api, name='talent_galaxy_api'),

    # ══════════════════════════════════════════════════════════════════════════
    # AUTONOMOUS PILLAR (Agentic Workforce)
    # ══════════════════════════════════════════════════════════════════════════
    path('agentic/boardroom/<int:application_id>/', views_agentic.agentic_boardroom, name='agentic_boardroom'),
    
    # ══════════════════════════════════════════════════════════════════════════
    # EPIC 5: THE VIRTUAL HIRING COMMITTEE (CrewAI)
    # ══════════════════════════════════════════════════════════════════════════
    path('api/crewai/evaluate/<int:application_id>/', views_crew.execute_virtual_committee_api, name='execute_virtual_committee_api'),

    # ══════════════════════════════════════════════════════════════════════════
    # EXPERIENCE PILLAR (Hyper-Personalization)
    # ══════════════════════════════════════════════════════════════════════════
    path('experience/offer/<int:application_id>/', views_experience.candidate_offer_portal, name='candidate_offer_portal'),

    # ══════════════════════════════════════════════════════════════════════════
    # COMPLIANCE PILLAR (Ethical AI & XAI)
    # ══════════════════════════════════════════════════════════════════════════
    path('compliance/xai/<int:application_id>/', views_compliance.xai_audit_report, name='xai_audit_report'),

    # ══════════════════════════════════════════════════════════════════════════
    # FRONTIER PILLAR (Agentic Sourcing)
    # ══════════════════════════════════════════════════════════════════════════
    path('sourcing/terminal/', views_sourcing.talent_scout_dashboard, name='sourcing_dashboard'),
    path('sourcing/delete/<int:index>/', views_sourcing.delete_scouted_lead, name='delete_scouted_lead'),

    # Generative Assessment Lab
    path('frontier/lab/<int:application_id>/', views_assessment_lab.generative_lab_challenge, name='generative_lab_challenge'),
    path('frontier/lab/submit/<int:application_id>/', views_assessment_lab.submit_lab_solution, name='submit_lab_solution'),

    # Negotiation Sparring (Recruitment Singularity)
    path('singularity/negotiate/<int:application_id>/', views_negotiation.negotiation_war_room, name='negotiation_war_room'),
    path('singularity/negotiate/msg/<int:application_id>/', views_negotiation.process_negotiation_msg, name='process_negotiation_msg'),

    # Culture Fit Simulation (Virtual Office)
    path('singularity/culture-fit/<int:application_id>/', views_culture.culture_fit_simulator, name='culture_fit_simulator'),
    path('singularity/culture-fit/submit/<int:application_id>/', views_culture.submit_sim_response, name='submit_sim_response'),

    # ── PHASE 8: AUTONOMOUS SOURCING (Recruitment Singularity) ──────
    path('singular/oracle/', views_oracle.oracle_intelligence_dashboard, name='oracle_dashboard'),
    path('singular/oracle/refresh/', views_oracle.refresh_talent_pool, name='refresh_talent_pool'),
    path('singular/oracle/matrix/<int:job_id>/', views_oracle.recruiter_decision_matrix, name='decision_matrix'),
    path('singular/hunter/', views_hunter.hunter_outreach_terminal, name='hunter_terminal'),
    path('singular/hunter/engage/', views_hunter.initiate_autonomous_engagement, name='initiate_autonomous_engagement'),
    # singularity features
    path('singularity/negotiate/practice/<int:application_id>/', views_negotiation.negotiation_sparring_practice, name='negotiation_sparring_practice'),
    path('singularity/negotiate/sparring-api/<int:application_id>/', views_negotiation.process_sparring_msg, name='process_sparring_msg'),
    path('singularity/office-sim/<int:application_id>/', views_culture.virtual_office_sim, name='virtual_office_sim'),
    path('singularity/roi-oracle/', views_oracle.roi_oracle_view, name='roi_oracle'),
    path('singularity/deep-vision/<int:application_id>/', views_proctoring.interview_deep_vision, name='interview_deep_vision'),

    # Enterprise HRMS Integrations
    path('api/hrms/hired-candidates/', views_hrms.export_hired_candidates_api, name='hrms_export_api'),

    # Phase 9: Smart Scheduler
    path('api/scheduler/slots/<int:recruiter_id>/', views.api_get_recruiter_slots, name='api_get_recruiter_slots'),
    path('api/scheduler/book/', views.api_book_interview_slot, name='api_book_interview_slot'),
    path('api/scheduler/reschedule/', views.api_request_reschedule, name='api_request_reschedule'),

    # ── GLOBAL PLATFORM APIs (chatbot widget + sentiment bubble in base.html) ──
    path('api/faq-bot/', views.faq_bot_api, name='faq_bot_api'),
    path('api/global-sentiment-stream/', views.global_sentiment_stream, name='global_sentiment_stream'),
]

