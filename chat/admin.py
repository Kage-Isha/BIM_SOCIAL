from django.contrib import admin
from .models import Conversation, Message, MessageRead, ConversationMember


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'participants_list', 'last_message_preview', 'last_message_by', 'last_message_at', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['participants__username', 'last_message']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['participants']
    
    def participants_list(self, obj):
        return ', '.join([user.username for user in obj.participants.all()])
    participants_list.short_description = 'Participants'
    
    def last_message_preview(self, obj):
        return obj.last_message[:50] + '...' if obj.last_message and len(obj.last_message) > 50 else obj.last_message
    last_message_preview.short_description = 'Last Message'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation_preview', 'content_preview', 'message_type', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'created_at']
    search_fields = ['sender__username', 'content', 'conversation__participants__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['conversation', 'sender']
    
    def conversation_preview(self, obj):
        participants = [user.username for user in obj.conversation.participants.all()]
        return f"Conversation: {' & '.join(participants)}"
    conversation_preview.short_description = 'Conversation'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ['user', 'message_preview', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username', 'message__content']
    raw_id_fields = ['message', 'user']
    
    def message_preview(self, obj):
        return obj.message.content[:30] + '...' if len(obj.message.content) > 30 else obj.message.content
    message_preview.short_description = 'Message'


@admin.register(ConversationMember)
class ConversationMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'conversation_preview', 'is_muted', 'is_archived', 'is_pinned', 'unread_count', 'joined_at']
    list_filter = ['is_muted', 'is_archived', 'is_pinned', 'joined_at']
    search_fields = ['user__username', 'conversation__participants__username']
    readonly_fields = ['id', 'unread_count', 'joined_at', 'updated_at']
    raw_id_fields = ['conversation', 'user', 'last_seen_message']
    
    def conversation_preview(self, obj):
        participants = [user.username for user in obj.conversation.participants.all()]
        return f"Conversation: {' & '.join(participants)}"
    conversation_preview.short_description = 'Conversation'
