from django.db import models
from django.contrib.auth.models import User
import uuid


class Conversation(models.Model):
    """Conversation between two users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Denormalized fields for performance
    last_message = models.TextField(blank=True, null=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='last_messages'
    )
    
    class Meta:
        db_table = 'chat_conversation'
        ordering = ['-updated_at']
    
    def __str__(self):
        usernames = [user.username for user in self.participants.all()[:2]]
        return f"Conversation: {' & '.join(usernames)}"
    
    @property
    def other_participant(self, current_user):
        """Get the other participant in the conversation"""
        return self.participants.exclude(id=current_user.id).first()


class Message(models.Model):
    """Chat message model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(max_length=1000)
    
    # Message status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Message type (for future features like images, files, etc.)
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('file', 'File'),
            ('system', 'System'),
        ],
        default='text'
    )
    
    # Optional file attachment
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_message'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."


class MessageRead(models.Model):
    """Track message read status per user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_message_read'
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['user', '-read_at']),
            models.Index(fields=['message', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} read message {self.message.id}"


class ConversationMember(models.Model):
    """Conversation membership with additional metadata"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_memberships')
    
    # Member settings
    is_muted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    # Last seen message
    last_seen_message = models.ForeignKey(
        Message, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='seen_by_members'
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_conversation_member'
        unique_together = ['conversation', 'user']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['conversation', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.conversation}"
    
    @property
    def unread_count(self):
        """Get unread message count for this member"""
        if not self.last_seen_message:
            return self.conversation.messages.count()
        
        return self.conversation.messages.filter(
            created_at__gt=self.last_seen_message.created_at
        ).exclude(sender=self.user).count()
