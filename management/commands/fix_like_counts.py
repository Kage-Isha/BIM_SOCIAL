from django.core.management.base import BaseCommand
from social.models import Post, Like
from django.db.models import Count

class Command(BaseCommand):
    help = 'Fixes any inconsistencies between Post.likes_count and actual Like objects'

    def handle(self, *args, **options):
        # Get all posts with their actual like counts
        posts = Post.objects.annotate(actual_likes=Count('likes'))
        
        fixed = 0
        for post in posts:
            if post.likes_count != post.actual_likes:
                self.stdout.write(self.style.WARNING(
                    f'Post {post.id}: Count was {post.likes_count}, actual likes: {post.actual_likes}'
                ))
                # Update the count
                Post.objects.filter(id=post.id).update(likes_count=post.actual_likes)
                fixed += 1
        
        if fixed > 0:
            self.stdout.write(self.style.SUCCESS(f'Fixed like counts for {fixed} posts'))
        else:
            self.stdout.write(self.style.SUCCESS('All like counts are correct!'))
