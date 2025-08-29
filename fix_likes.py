import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
django.setup()

from django.db import connection
from social.models import Post, Like

def fix_likes():
    with connection.cursor() as cursor:
        # Print current state
        print("=== Current State ===")
        cursor.execute("SELECT id, likes_count FROM social_post")
        posts = cursor.fetchall()
        for post_id, likes_count in posts:
            print(f"Post {post_id}: {likes_count} likes")
        
        # Get actual like counts
        cursor.execute("""
            SELECT post_id, COUNT(*) as like_count 
            FROM social_like 
            GROUP BY post_id
        """)
        actual_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Update counts
        print("\n=== Updating Counts ===")
        for post_id, _ in posts:
            actual_count = actual_counts.get(post_id, 0)
            cursor.execute(
                "UPDATE social_post SET likes_count = %s WHERE id = %s",
                [actual_count, post_id]
            )
            print(f"Updated post {post_id} to {actual_count} likes")
        
        # Verify updates
        print("\n=== Verification ===")
        cursor.execute("SELECT id, likes_count FROM social_post")
        for post_id, likes_count in cursor.fetchall():
            print(f"Post {post_id}: {likes_count} likes")

if __name__ == "__main__":
    fix_likes()
