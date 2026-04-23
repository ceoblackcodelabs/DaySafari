# admin.py

from django.contrib import admin
from .models import UserMessage, MessageReply

@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'subject', 'priority', 'status', 'created_at', 'email_sent']
    list_filter = ['priority', 'status', 'email_sent', 'created_at']
    search_fields = ['user__username', 'user__email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'email_sent_at']
    fieldsets = (
        ('Recipient', {
            'fields': ('user',)
        }),
        ('Message Details', {
            'fields': ('subject', 'message', 'priority')
        }),
        ('Status', {
            'fields': ('status', 'is_deleted')
        }),
        ('Email Backup', {
            'fields': ('email_sent', 'email_sent_at')
        }),
        ('Bulk Info', {
            'fields': ('is_bulk', 'bulk_group'),
            'classes': ('collapse',)
        }),
        ('Attachments', {
            'fields': ('has_attachment', 'attachment_url', 'attachment_name'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at'),
            'classes': ('collapse',)
        })
    )
    actions = ['mark_as_read', 'mark_as_unread', 'archive_messages']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(status='read')
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(status='unread')
        self.message_user(request, f'{updated} messages marked as unread.')
    mark_as_unread.short_description = 'Mark selected messages as unread'
    
    def archive_messages(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} messages archived.')
    archive_messages.short_description = 'Archive selected messages'

@admin.register(MessageReply)
class MessageReplyAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_message', 'user', 'created_at', 'is_read_by_admin']
    list_filter = ['is_read_by_admin', 'created_at']
    search_fields = ['user__username', 'reply_message']