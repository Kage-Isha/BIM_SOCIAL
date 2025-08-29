from django.db import connection
from social.models import Post, Like

def check_likes():
    # Get all posts
    posts = Post.objects.all()
    
    print("\n=== Checking Like Counts ===")
    print(f"Found {len(posts)} posts in total")
    
    for post in posts:
        actual_likes = Like.objects.filter(post=post).count()
        print(f"\nPost ID: {post.id}")
        print(f"Stored likes_count: {post.likes_count}")
        print(f"Actual likes in database: {actual_likes}")
        
        if post.likes_count != actual_likes:
            print("  → MISMATCH DETECTED!")
            # Fix the count
            Post.objects.filter(id=post.id).update(likes_count=actual_likes)
            print(f"  → UPDATED: Set likes_count to {actual_likes}")
    
    # Print all Like objects
    print("\n=== All Like Objects ===")
    likes = Like.objects.all().select_related('user', 'post')
    for like in likes:
        print(f"User '{like.user.username}' likes post {like.post.id} (ID: {like.id})")
    
    print("\n=== Like Count Verification Complete ===")

if __name__ == "__main__":
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
    django.setup()
    check_likes()
