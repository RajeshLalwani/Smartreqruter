from django.urls import re_path
from . import consumers
from jobs import consumers as jobs_consumers

websocket_urlpatterns = [
    re_path(r'ws/recruitment/$', consumers.RecruitmentConsumer.as_asgi()),
    re_path(r'ws/interview/(?P<interview_id>\w+)/chat/$', consumers.RecruiterChatConsumer.as_asgi()),
    re_path(r'ws/coding/(?P<session_id>\w+)/$', jobs_consumers.CodingSyncConsumer.as_asgi()),
]
