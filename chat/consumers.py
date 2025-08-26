import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Conversation, Message, MessageRead, ConversationMember
# Serializer import removed - using manual serialization


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user is participant in the conversation
        is_participant = await self.is_conversation_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send user online status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'username': self.user.username,
                'status': 'online'
            }
        )
    
    async def disconnect(self, close_code):
        # Send user offline status
        if hasattr(self, 'room_group_name') and hasattr(self, 'user'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'status': 'offline'
                }
            )
        
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing(text_data_json)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': f'Error processing message: {str(e)}'
            }))
    
    async def handle_message(self, data):
        content = data.get('content', '').strip()
        if not content:
            return
        
        # Verify mutual follow status
        is_mutual = await self.check_mutual_follow()
        if not is_mutual:
            await self.send(text_data=json.dumps({
                'error': 'You can only chat with mutual followers'
            }))
            return
        
        # Create message in database
        message = await self.create_message(content)
        if not message:
            await self.send(text_data=json.dumps({
                'error': 'Failed to create message'
            }))
            return
        
        # Serialize message
        message_data = await self.serialize_message(message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )
    
    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        
        # Send typing indicator to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing
            }
        )
    
    async def handle_read_receipt(self, data):
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_read(message_id)
            
            # Send read receipt to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'message_id': message_id,
                    'user_id': self.user.id,
                    'username': self.user.username
                }
            )
    
    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))
    
    async def typing_indicator(self, event):
        # Don't send typing indicator to the sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def user_status(self, event):
        # Don't send status to the user themselves
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': event['user_id'],
                'username': event['username'],
                'status': event['status']
            }))
    
    async def read_receipt(self, event):
        # Don't send read receipt to the sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'read_receipt',
                'message_id': event['message_id'],
                'user_id': event['user_id'],
                'username': event['username']
            }))
    
    @database_sync_to_async
    def is_conversation_participant(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def check_mutual_follow(self):
        try:
            from social.models import Follow
            conversation = Conversation.objects.get(id=self.conversation_id)
            other_participant = conversation.participants.exclude(id=self.user.id).first()
            
            if not other_participant:
                return False
            
            # Check mutual follow
            return (
                Follow.objects.filter(follower=self.user, following=other_participant).exists() and
                Follow.objects.filter(follower=other_participant, following=self.user).exists()
            )
        except:
            return False
    
    @database_sync_to_async
    def create_message(self, content):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content,
                message_type='text'
            )
            
            # Update conversation metadata
            conversation.last_message = content
            conversation.last_message_at = message.created_at
            conversation.last_message_by = self.user
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # Mark as read for sender
            MessageRead.objects.get_or_create(message=message, user=self.user)
            
            return message
        except Exception as e:
            print(f"Error creating message: {e}")
            return None
    
    @database_sync_to_async
    def serialize_message(self, message):
        try:
            # Simple serialization for WebSocket
            return {
                'id': str(message.id),
                'content': message.content,
                'message_type': message.message_type,
                'sender': {
                    'id': message.sender.id,
                    'username': message.sender.username,
                    'profile_image_url': message.sender.profile.profile_image_url if hasattr(message.sender, 'profile') else None
                },
                'created_at': message.created_at.isoformat(),
                'is_read': False
            }
        except Exception as e:
            print(f"Error serializing message: {e}")
            return None
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            MessageRead.objects.get_or_create(message=message, user=self.user)
            
            # Update conversation membership
            try:
                membership = ConversationMember.objects.get(
                    conversation=message.conversation,
                    user=self.user
                )
                membership.last_seen_message = message
                membership.last_seen_at = timezone.now()
                membership.save()
            except ConversationMember.DoesNotExist:
                pass
                
        except Message.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error marking message as read: {e}")
