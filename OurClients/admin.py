# admin.py

from django.contrib import admin
from .models import UserRecommendations, SavedDestination


@admin.register(SavedDestination)
class SavedDestinationAdmin(admin.ModelAdmin):
    list_display = ['user', 'destination', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'destination__name']


@admin.register(UserRecommendations)
class UserRecommendationsAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'package__name']
