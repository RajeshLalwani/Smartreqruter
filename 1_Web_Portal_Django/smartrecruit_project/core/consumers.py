import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RecruitmentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            # Group for this specific user
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # Handle messages from WebSocket (e.g. heartbeat)
        data = json.loads(text_data)
        event_type = data.get('type')
        
        if event_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'message': 'Neural Link Active'
            }))

    # Custom event handlers for broadcasting
    async def recruitment_event(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['data']))


from channels.db import database_sync_to_async

class RecruiterChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.interview_id = self.scope['url_route']['kwargs']['interview_id']
        self.room_group_name = f'chat_interview_{self.interview_id}'
        self.user = self.scope["user"]

        # Only allow recruiters
        if self.user.is_authenticated and self.user.role in ['RECRUITER']:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

            # Announce presence
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': f'{self.user.username} joined the discussion.',
                    'username': 'System',
                    'msg_type': 'presence'
                }
            )
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Announce leave
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': f'{self.user.username} left the discussion.',
                    'username': 'System',
                    'msg_type': 'presence'
                }
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        msg_type = data.get('msg_type', 'chat')
        timestamp = data.get('timestamp', '00:00')

        if msg_type in ['chat', 'vote_up', 'vote_down', 'flag']:
            await self.save_message(self.interview_id, self.user.id, message, msg_type, timestamp)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.user.username,
                'msg_type': msg_type,
                'timestamp': timestamp,
                'user_id': self.user.id
            }
        )

    @database_sync_to_async
    def save_message(self, interview_id, user_id, message, msg_type, timestamp):
        try:
            from jobs.models import InterviewDiscussion, Interview
            from django.contrib.auth import get_user_model
            User = get_user_model()
            interview = Interview.objects.get(id=interview_id)
            user = User.objects.get(id=user_id)
            InterviewDiscussion.objects.create(
                interview=interview,
                user=user,
                message=message,
                msg_type=msg_type,
                video_timestamp=timestamp
            )
        except Exception as e:
            print(f"Error saving chat: {e}")

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        msg_type = event.get('msg_type', 'chat')
        timestamp = event.get('timestamp', '00:00')
        user_id = event.get('user_id')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'msg_type': msg_type,
            'timestamp': timestamp,
            'user_id': user_id
        }))
