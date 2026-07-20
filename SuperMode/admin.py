# admin.py
from django.contrib import admin
from django import forms
from .models import ItineraryBuilder

class ItineraryBuilderForm(forms.ModelForm):
    class Meta:
        model = ItineraryBuilder
        fields = '__all__'

    def clean_hotel_images(self):
        images = self.cleaned_data.get('hotel_images')
        if images and len(images) > 5:
            raise forms.ValidationError('You can select a maximum of 5 hotel images.')
        return images

    def clean_destination_images(self):
        images = self.cleaned_data.get('destination_images')
        if images and len(images) > 5:
            raise forms.ValidationError('You can select a maximum of 5 destination images.')
        return images

@admin.register(ItineraryBuilder)
class ItineraryBuilderAdmin(admin.ModelAdmin):
    form = ItineraryBuilderForm
    list_display = ['title', 'client_name', 'days_spent', 'price', 'slug', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'client_name', 'slug']
    prepopulated_fields = {'slug': ('title', 'client_name')}
    readonly_fields = ['share_link', 'created_at', 'updated_at']
    filter_horizontal = ['hotel_images', 'destination_images']