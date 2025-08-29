from django.core.management.base import BaseCommand
from django.db.models import Count
from social.models import Post, Like

class Command(BaseCommand):
    help = 'Syncs the likes_count field with actual Like objects'

    def handle(self, *args, **options):
        # Get all posts with their actual like counts
        posts = Post.objects.annotate(actual_likes=Count('likes'))
        
        fixed = 0
        for post in posts:
            if post.likes_count != post.actual_likes:
                self.stdout.write(
                    f'Post {post.id}: Updating likes_count from {post.likes_count} to {post.actual_likes}'
                )
                # Update the count directly in the database
                Post.objects.filter(id=post.id).update(likes_count=post.actual_likes)
                fixed += 1
        
        if fixed > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed like counts for {fixed} posts'))
        else:
            self.stdout.write(self.style.SUCCESS('All like counts are correct!'))
            
        # Also check for any posts with negative like counts
        negative_likes = Post.objects.filter(likes_count__lt=0)
        if negative_likes.exists():
            self.stdout.write("\nFixing negative like counts...")
            negative_likes.update(likes_count=0)
            self.stdout.write(self.style.SUCCESS(f'Fixed {negative_likes.count()} posts with negative like counts'))
