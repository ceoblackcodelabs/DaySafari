from django.contrib import admin
from .models import (
    Contact, Bookings, BotAttempt, BlockedIP, set_ip_blocked
)

# contact
@admin.register(Bookings)
class BookingsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'created_at', 'booking_type', 'name', 'email', 'phone', 'item_name', 'persons',
                    'date', 'children', 'status')
    list_editable = ('status',)
    search_fields = ('name', 'email', 'phone', 'message')
    list_filter = ('status', 'booking_type', 'date', 'destination')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    list_per_page = 50

    def children(self, obj):
        return obj.children_summary or '-'


# contact
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('client', 'name', 'email', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('status', 'created_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(status='Read')
        self.message_user(request, f"{queryset.count()} messages marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(status='New')
        self.message_user(request, f"{queryset.count()} messages marked as unread.")
    mark_as_unread.short_description = "Mark selected messages as unread"

from .models import QuickLead


@admin.register(QuickLead)
class QuickLeadAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'name', 'phone', 'tour', 'short_message', 'language', 'status', 'chat')
    list_editable = ('status',)
    list_filter = ('status', 'language', 'created_at')
    search_fields = ('name', 'phone', 'tour', 'message')
    readonly_fields = ('created_at', 'ip', 'page_url', 'language')
    date_hierarchy = 'created_at'
    actions = ['export_csv']

    def short_message(self, obj):
        return (obj.message[:60] + '...') if len(obj.message) > 60 else obj.message

    def chat(self, obj):
        from django.utils.html import format_html
        digits = ''.join(c for c in obj.phone if c.isdigit())
        return format_html('<a href="https://wa.me/{}" target="_blank" rel="noopener">WhatsApp</a>', digits) if digits else ''

    def export_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        resp = HttpResponse(content_type='text/csv')
        resp['Content-Disposition'] = 'attachment; filename="whatsapp-leads.csv"'
        w = csv.writer(resp)
        w.writerow(['Date', 'Name', 'Phone', 'Tour', 'Message', 'Language', 'Status', 'Page'])
        for q in queryset:
            w.writerow([q.created_at.strftime('%Y-%m-%d %H:%M'), q.name, q.phone, q.tour, q.message, q.language, q.status, q.page_url])
        return resp
    export_csv.short_description = 'Download selected leads as CSV'



@admin.register(BotAttempt)
class BotAttemptAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'ip', 'form', 'reasons', 'name', 'short_message', 'hits', 'blacklist')
    list_editable = ('blacklist',)
    list_filter = ('blacklist', 'form', 'created_at')
    search_fields = ('ip', 'name', 'email', 'phone', 'message', 'reasons')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'user_agent', 'path', 'hits')
    list_per_page = 50
    actions = ['blacklist_ips', 'unblock_ips']

    @admin.display(description='Message')
    def short_message(self, obj):
        return (obj.message or '')[:70]

    @admin.action(description='Blacklist the IP address of the selected entries')
    def blacklist_ips(self, request, queryset):
        ips = {i for i in queryset.values_list('ip', flat=True) if i}
        for ip in ips:
            set_ip_blocked(ip, True, 'Blacklisted from the bot trap')
        self.message_user(request, f'{len(ips)} IP address(es) blacklisted.')

    @admin.action(description='Unblock the IP address of the selected entries')
    def unblock_ips(self, request, queryset):
        ips = {i for i in queryset.values_list('ip', flat=True) if i}
        for ip in ips:
            set_ip_blocked(ip, False)
        self.message_user(request, f'{len(ips)} IP address(es) unblocked.')


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = ('ip', 'is_active', 'reason', 'auto', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('ip', 'reason')
    list_filter = ('is_active', 'auto')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        set_ip_blocked(obj.ip, obj.is_active, obj.reason)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        from django.core.cache import cache
        cache.delete('antispam:blocked-ips')
