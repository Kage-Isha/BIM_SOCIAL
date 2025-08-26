from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Post, Like, Comment, Follow


@receiver(post_save, sender=Like)
def update_post_likes_count_on_create(sender, instance, created, **kwargs):
    """Update post likes count when like is created"""
    if created:
        post = instance.post
        post.likes_count = post.likes.count()
        post.save(update_fields=['likes_count'])


@receiver(post_delete, sender=Like)
def update_post_likes_count_on_delete(sender, instance, **kwargs):
    """Update post likes count when like is deleted"""
    post = instance.post
    post.likes_count = max(0, post.likes.count())
    post.save(update_fields=['likes_count'])


@receiver(post_save, sender=Comment)
def update_post_comments_count_on_create(sender, instance, created, **kwargs):
    """Update post comments count when comment is created"""
    if created:
        post = instance.post
        post.comments_count = post.comments.count()
        post.save(update_fields=['comments_count'])
        
        # Update parent comment replies count if it's a reply
        if instance.parent:
            parent = instance.parent
            parent.replies_count = parent.replies.count()
            parent.save(update_fields=['replies_count'])


@receiver(post_delete, sender=Comment)
def update_post_comments_count_on_delete(sender, instance, **kwargs):
    """Update post comments count when comment is deleted"""
    post = instance.post
    post.comments_count = max(0, post.comments.count())
    post.save(update_fields=['comments_count'])
    
    # Update parent comment replies count if it was a reply
    if instance.parent:
        parent = instance.parent
        parent.replies_count = max(0, parent.replies.count())
        parent.save(update_fields=['replies_count'])


@receiver(post_save, sender=Follow)
def update_follow_counts_on_create(sender, instance, created, **kwargs):
    """Update follower/following counts when follow is created"""
    if created:
        # Update follower's following count
        follower_profile = instance.follower.profile
        follower_profile.following_count = instance.follower.following.count()
        follower_profile.save(update_fields=['following_count'])
        
        # Update following's followers count
        following_profile = instance.following.profile
        following_profile.followers_count = instance.following.followers.count()
        following_profile.save(update_fields=['followers_count'])


@receiver(post_delete, sender=Follow)
def update_follow_counts_on_delete(sender, instance, **kwargs):
    """Update follower/following counts when follow is deleted"""
    # Update follower's following count
    follower_profile = instance.follower.profile
    follower_profile.following_count = max(0, instance.follower.following.count())
    follower_profile.save(update_fields=['following_count'])
    
    # Update following's followers count
    following_profile = instance.following.profile
    following_profile.followers_count = max(0, instance.following.followers.count())
    following_profile.save(update_fields=['followers_count'])


@receiver(post_save, sender=Post)
def update_user_posts_count_on_create(sender, instance, created, **kwargs):
    """Update user posts count when post is created"""
    if created:
        profile = instance.user.profile
        profile.posts_count = instance.user.posts.count()
        profile.save(update_fields=['posts_count'])


@receiver(post_delete, sender=Post)
def update_user_posts_count_on_delete(sender, instance, **kwargs):
    """Update user posts count when post is deleted"""
    profile = instance.user.profile
    profile.posts_count = max(0, instance.user.posts.count())
    profile.save(update_fields=['posts_count'])
