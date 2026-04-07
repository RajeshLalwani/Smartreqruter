from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    JobViewSet, CandidateViewSet, ApplicationViewSet, 
    QuestionBankViewSet, AssessmentViewSet, DashboardAPIView
)

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='api-jobs')
router.register(r'candidates', CandidateViewSet, basename='api-candidates')
router.register(r'applications', ApplicationViewSet, basename='api-applications')
router.register(r'questions', QuestionBankViewSet, basename='api-questions')
router.register(r'assessments', AssessmentViewSet, basename='api-assessments')
router.register(r'dashboard', DashboardAPIView, basename='api-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
