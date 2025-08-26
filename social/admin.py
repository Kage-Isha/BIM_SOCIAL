from django.contrib import admin
from .models import Post, Like, Comment, CommentLike, Follow, Share, SavedPost, Report


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['user', 'caption_preview', 'media_type', 'likes_count', 'comments_count', 'is_public', 'created_at']
    list_filter = ['is_public', 'allow_comments', 'created_at']
    search_fields = ['user__username', 'caption']
    readonly_fields = ['id', 'likes_count', 'comments_count', 'shares_count', 'created_at', 'updated_at']
    raw_id_fields = ['user']
    
    def caption_preview(self, obj):
        return obj.caption[:50] + '...' if obj.caption and len(obj.caption) > 50 else obj.caption
    caption_preview.short_description = 'Caption'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__caption']
    raw_id_fields = ['user', 'post']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content_preview', 'parent', 'likes_count', 'replies_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content', 'post__caption']
    raw_id_fields = ['user', 'post', 'parent']
    readonly_fields = ['id', 'likes_count', 'replies_count', 'created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'comment__content']
    raw_id_fields = ['user', 'comment']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    raw_id_fields = ['follower', 'following']


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'caption_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__caption', 'caption']
    raw_id_fields = ['user', 'post']
    
    def caption_preview(self, obj):
        return obj.caption[:50] + '...' if obj.caption and len(obj.caption) > 50 else obj.caption
    caption_preview.short_description = 'Share Caption'


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__caption']
    raw_id_fields = ['user', 'post']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reported_user', 'reported_post', 'report_type', 'is_resolved', 'created_at']
    list_filter = ['report_type', 'is_resolved', 'created_at']
    search_fields = ['reporter__username', 'reported_user__username', 'description']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['reporter', 'reported_user', 'reported_post']
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f"{queryset.count()} reports marked as resolved.")
    mark_resolved.short_description = "Mark selected reports as resolved"
