#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from social.models import Post, Like
from django.db.models import Count

def fix_like_counts():
    """Fix all like counts to match actual Like records"""
    print("Fixing like counts...")
    
    # Get all posts with their actual like counts
    posts = Post.objects.annotate(
        actual_likes=Count('likes')
    ).all()
    
    updated_count = 0
    for post in posts:
        if post.likes_count != post.actual_likes:
            print(f"Post {post.id}: {post.likes_count} -> {post.actual_likes}")
            post.likes_count = post.actual_likes
            post.save(update_fields=['likes_count'])
            updated_count += 1
    
    print(f"Updated {updated_count} posts")
    print("Like counts fixed!")

if __name__ == '__main__':
    fix_like_counts()
