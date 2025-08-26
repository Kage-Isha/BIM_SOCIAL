#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from social.models import Post

print("Fixing post counts...")

for post in Post.objects.all():
    actual_likes = post.likes.count()
    actual_comments = post.comments.count()
    
    if post.likes_count != actual_likes or post.comments_count != actual_comments:
        print(f"Post {post.id}:")
        print(f"  Likes: {post.likes_count} -> {actual_likes}")
        print(f"  Comments: {post.comments_count} -> {actual_comments}")
        
        post.likes_count = actual_likes
        post.comments_count = actual_comments
        post.save()

print("Done! All post counts corrected.")
