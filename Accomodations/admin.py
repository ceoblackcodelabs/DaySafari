from django.contrib import admin
from .models import (
    Accomodations, AccomodationsImage, AirBNBImage, AirBNB
)

# Register your models here.
class AccomodationsImageInline(admin.TabularInline):
    model = AccomodationsImage
    extra = 3
    fields = ['image', 'caption', 'is_featured', 'order']


@admin.register(Accomodations)
class AccomodationsAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'specification', 'price_per_night', 'max_guests', 'created_at']
    list_filter = ['specification', 'location']
    search_fields = ['name', 'location']
    inlines = [AccomodationsImageInline]


@admin.register(AccomodationsImage)
class AccomodationsImageAdmin(admin.ModelAdmin):
    list_display = ['accomodation', 'caption', 'is_featured', 'order', 'uploaded_at']
    list_filter = ['is_featured']
    search_fields = ['caption']
    
# Airbnb    
class AirBNBImageInline(admin.TabularInline):
    model = AirBNBImage
    extra = 3
    fields = ['image', 'caption', 'is_featured', 'order']

@admin.register(AirBNB)
class AirBNBAdmin(admin.ModelAdmin):
    list_display = ['location', 'specification', 'created_at']
    list_filter = ['specification']
    search_fields = ['location']
    inlines = [AirBNBImageInline]

@admin.register(AirBNBImage)
class AirBNBImageAdmin(admin.ModelAdmin):
    list_display = ['airbnb', 'is_featured', 'order', 'uploaded_at']
    list_filter = ['is_featured', 'airbnb']