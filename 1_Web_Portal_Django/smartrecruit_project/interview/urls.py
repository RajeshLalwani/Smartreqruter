from django.urls import path
from . import views

app_name = 'interview'

urlpatterns = [
    path('', views.interview_view, name='interview_page'),
    path('api/chat/', views.chat_api_view, name='chat_api'),
]
