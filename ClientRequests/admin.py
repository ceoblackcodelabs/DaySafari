from django.contrib import admin
from .models import (
    Contact, Bookings
)

# contact
@admin.register(Bookings)
class BookingsAdmin(admin.ModelAdmin):
    list_display = ('client', 'name', 'email', 'phone', 'destination', 'persons', 'date')
    search_fields = ('client', 'name', 'email', 'destination')
    list_filter = ('date', 'destination')
    readonly_fields = ('name', 'email', 'phone', 'destination', 'persons', 'date', 'message')
    
    
# contact
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['client', 'name', 'email', 'subject', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['client', 'name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']
    list_editable = ['is_read']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('client', 'name', 'email', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} messages marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} messages marked as unread.")
    mark_as_unread.short_description = "Mark selected messages as unread"