from django.contrib import admin
from .models import EmailLog, CompanyProfile

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'subject', 'status', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['recipient', 'subject']

@admin.register(CompanyProfile)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'booking_confirmation_email'
    ]