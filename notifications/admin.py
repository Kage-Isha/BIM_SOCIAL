from django.contrib import admin
from .models import Notification, NotificationSettings


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'title_preview', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'title', 'message']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['recipient', 'sender', 'related_post', 'related_comment', 'related_conversation']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def title_preview(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_preview.short_description = 'Title'
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f"{queryset.count()} notifications marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False, read_at=None)
        self.message_user(request, f"{queryset.count()} notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'digest_frequency', 'email_notifications_enabled', 'push_notifications_enabled', 'updated_at']
    list_filter = ['digest_frequency', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def email_notifications_enabled(self, obj):
        return any([
            obj.email_on_follow, obj.email_on_like, obj.email_on_comment,
            obj.email_on_mention, obj.email_on_message
        ])
    email_notifications_enabled.boolean = True
    email_notifications_enabled.short_description = 'Email Notifications'
    
    def push_notifications_enabled(self, obj):
        return any([
            obj.push_on_follow, obj.push_on_like, obj.push_on_comment,
            obj.push_on_mention, obj.push_on_message
        ])
    push_notifications_enabled.boolean = True
    push_notifications_enabled.short_description = 'Push Notifications'
