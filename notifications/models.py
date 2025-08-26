from django.db import models
from django.contrib.auth.models import User
import uuid


class Notification(models.Model):
    """Notification model for user activities"""
    NOTIFICATION_TYPES = [
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('mention', 'Mention'),
        ('message', 'Message'),
        ('post', 'New Post'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField(max_length=500)
    
    # Related objects (optional)
    related_post = models.ForeignKey('social.Post', on_delete=models.CASCADE, null=True, blank=True)
    related_comment = models.ForeignKey('social.Comment', on_delete=models.CASCADE, null=True, blank=True)
    related_conversation = models.ForeignKey('chat.Conversation', on_delete=models.CASCADE, null=True, blank=True)
    
    # Additional data (JSON field for flexibility)
    extra_data = models.JSONField(default=dict, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type.title()} notification for {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationSettings(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    
    # Email notifications
    email_on_follow = models.BooleanField(default=True)
    email_on_like = models.BooleanField(default=True)
    email_on_comment = models.BooleanField(default=True)
    email_on_mention = models.BooleanField(default=True)
    email_on_message = models.BooleanField(default=True)
    
    # Push notifications
    push_on_follow = models.BooleanField(default=True)
    push_on_like = models.BooleanField(default=True)
    push_on_comment = models.BooleanField(default=True)
    push_on_mention = models.BooleanField(default=True)
    push_on_message = models.BooleanField(default=True)
    
    # In-app notifications
    app_on_follow = models.BooleanField(default=True)
    app_on_like = models.BooleanField(default=True)
    app_on_comment = models.BooleanField(default=True)
    app_on_mention = models.BooleanField(default=True)
    app_on_message = models.BooleanField(default=True)
    
    # General settings
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        default='weekly'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_settings'
    
    def __str__(self):
        return f"Notification settings for {self.user.username}"
