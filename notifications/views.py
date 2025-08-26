# All API views removed - functionality moved to web_views.py
# This app now only contains Django models and admin configuration
from django.contrib.auth.models import User
from .models import Notification, NotificationSettings
import logging

logger = logging.getLogger(__name__)


# Utility functions for creating notifications
def create_notification(recipient, notification_type, title, message, sender=None, **kwargs):
    """Create a new notification"""
    try:
        # Check if user has this type of notification enabled
        settings = getattr(recipient, 'notification_settings', None)
        if settings:
            app_setting = getattr(settings, f'app_on_{notification_type}', True)
            if not app_setting:
                return None
        
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            **kwargs
        )
        
        return notification
        
    except Exception as e:
        logger.error(f"Create notification error: {str(e)}")
        return None


def create_follow_notification(follower, following):
    """Create notification for new follower"""
    return create_notification(
        recipient=following,
        sender=follower,
        notification_type='follow',
        title='New Follower',
        message=f'{follower.username} started following you'
    )


def create_like_notification(liker, post):
    """Create notification for post like"""
    if liker != post.user:  # Don't notify for self-likes
        return create_notification(
            recipient=post.user,
            sender=liker,
            notification_type='like',
            title='Post Liked',
            message=f'{liker.username} liked your post',
            related_post=post
        )


def create_comment_notification(commenter, comment):
    """Create notification for new comment"""
    if commenter != comment.post.user:  # Don't notify for self-comments
        return create_notification(
            recipient=comment.post.user,
            sender=commenter,
            notification_type='comment',
            title='New Comment',
            message=f'{commenter.username} commented on your post',
            related_post=comment.post,
            related_comment=comment
        )


def create_message_notification(sender, conversation, message):
    """Create notification for new message"""
    # Notify all participants except sender
    for participant in conversation.participants.exclude(id=sender.id):
        create_notification(
            recipient=participant,
            sender=sender,
            notification_type='message',
            title='New Message',
            message=f'{sender.username} sent you a message',
            related_conversation=conversation
        )
