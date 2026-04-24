from django.contrib import admin
from .models import EmailLog  # Create this model if needed

class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'subject', 'status', 'sent_at']
    list_filter = ['status', 'sent_at']
    search_fields = ['recipient', 'subject']

# admin.site.register(EmailLog, EmailLogAdmin)