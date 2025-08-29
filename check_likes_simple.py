from django.db import connection

def check_likes():
    with connection.cursor() as cursor:
        # Check Post table
        cursor.execute("SELECT id, likes_count FROM social_post")
        posts = cursor.fetchall()
        print("\n=== Post Table ===")
        for post_id, likes_count in posts:
            print(f"Post {post_id}: {likes_count} likes")
        
        # Check Like table
        cursor.execute("""
            SELECT post_id, COUNT(*) as like_count 
            FROM social_like 
            GROUP BY post_id
        """)
        like_counts = cursor.fetchall()
        print("\n=== Like Table Counts ===")
        for post_id, count in like_counts:
            print(f"Post {post_id}: {count} actual likes")

if __name__ == "__main__":
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bim_social.settings')
    django.setup()
    check_likes()
