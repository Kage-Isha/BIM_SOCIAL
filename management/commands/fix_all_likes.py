from django.core.management.base import BaseCommand
from django.db import transaction
from social.models import Post, Like

class Command(BaseCommand):
    help = 'Fixes all like counts and ensures data consistency'

    def handle(self, *args, **options):
        self.stdout.write('Starting to fix like counts...')
        
        with transaction.atomic():
            # Update all post like counts
            for post in Post.objects.all():
                actual_likes = Like.objects.filter(post=post).count()
                if post.likes_count != actual_likes:
                    self.stdout.write(f'Updating post {post.id}: {post.likes_count} -> {actual_likes} likes')
                    post.likes_count = actual_likes
                    post.save(update_fields=['likes_count'])
            
            # Remove any duplicate likes
            duplicates = Like.objects.raw("""
                SELECT MIN(id) as id, user_id, post_id, COUNT(*) as count
                FROM social_like
                GROUP BY user_id, post_id
                HAVING COUNT(*) > 1
            """)
            
            for dup in duplicates:
                # Keep the first like, delete the rest
                likes = Like.objects.filter(
                    user_id=dup.user_id,
                    post_id=dup.post_id
                ).order_by('created_at')
                
                for like in likes[1:]:  # Keep the first one
                    self.stdout.write(f'Removing duplicate like: user={like.user_id}, post={like.post_id}')
                    like.delete()
        
        self.stdout.write(self.style.SUCCESS('Successfully fixed all like counts!'))
