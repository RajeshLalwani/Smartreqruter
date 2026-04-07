import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CodingSyncConsumer(AsyncWebsocketConsumer):
    """
    Real-time synchronization consumer for Monaco Editor using Yjs CRDT.
    Handles binary CRDT updates and JSON-based presence/cursor tracking.
    """
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.user = self.scope["user"]
        self.group_name = f'coding_{self.session_id}'

        if self.user.is_authenticated:
            # Join session group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            
            # Broadcast join event
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'presence_update',
                    'data': {
                        'type': 'user_joined',
                        'user': self.user.username,
                        'id': self.user.id
                    }
                }
            )
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            # Broadcast leave event
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'presence_update',
                    'data': {
                        'type': 'user_left',
                        'user': self.user.username,
                        'id': self.user.id
                    }
                }
            )
            # Leave session group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receives data from the client.
        bytes_data: Binary Yjs update.
        text_data: JSON presence/cursor/save data.
        """
        if bytes_data:
            # Relay binary Yjs sync messages to all users in group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'coding_message',
                    'message': bytes_data,
                    'sender_channel_name': self.channel_name
                }
            )
        elif text_data:
            try:
                data = json.loads(text_data)
                # Relay presence/cursor data
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'presence_update',
                        'data': data,
                        'sender_channel_name': self.channel_name
                    }
                )
            except json.JSONDecodeError:
                pass

    async def coding_message(self, event):
        """
        Sends binary Yjs data back to clients, skipping the sender.
        """
        message = event['message']
        sender = event.get('sender_channel_name')
        
        if self.channel_name != sender:
            await self.send(bytes_data=message)

    async def presence_update(self, event):
        """
        Sends presence/cursor JSON data back to clients, skipping the sender.
        """
        data = event['data']
        sender = event.get('sender_channel_name')
        
        if self.channel_name != sender:
            await self.send(text_data=json.dumps(data))
