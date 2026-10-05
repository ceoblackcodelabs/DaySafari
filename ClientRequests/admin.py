from django.contrib import admin
from .models import (
    Contact, Bookings
)

# contact
@admin.register(Bookings)
class BookingsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'created_at', 'booking_type', 'name', 'email', 'phone', 'item_name', 'persons',
                    'date', 'status')
    list_editable = ('status',)
    search_fields = ('name', 'email', 'phone', 'message')
    list_filter = ('status', 'booking_type', 'date', 'destination')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    list_per_page = 50


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