# admin.py

from django.contrib import admin
from .models import SavedDestination


@admin.register(SavedDestination)
class SavedDestinationAdmin(admin.ModelAdmin):
    list_display = ['user', 'destination', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'destination__name']
