from django.contrib import admin
from django.utils.html import format_html

from .models import AirBNB, AirBNBImage, Hotel, HotelImage


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 3
    fields = ['image', 'caption', 'is_featured', 'order']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['thumb', 'name', 'country', 'location', 'property_type', 'star_rating', 'price_per_night',
                    'max_guests', 'is_featured', 'is_published']
    list_display_links = ['thumb', 'name']
    list_editable = ['is_featured', 'is_published']
    list_filter = ['country', 'property_type', 'star_rating', 'is_published', 'is_featured']
    search_fields = ['name', 'location', 'country', 'summary']
    prepopulated_fields = {'slug': ('name', 'location')}
    inlines = [HotelImageInline]
    fieldsets = (
        ('Public listing', {'fields': ('name', 'slug', 'country', 'location', 'property_type', 'star_rating',
                                       'summary', 'description', 'is_published', 'is_featured')}),
        ('Rooms & rates', {'fields': ('rooms', 'price_per_night', 'max_guests', 'meal_plan', 'amenities',
                                      'child_policy')}),
        ('Internal only (never shown to visitors)', {'classes': ('collapse',),
                                                     'fields': ('contact_person', 'email', 'phone_number',
                                                                'contract_validity', 'remarks')}),
    )

    def thumb(self, obj):
        image = obj.main_image
        if image and image.image:
            return format_html('<img src="{}" width="60" height="45" style="object-fit:cover;border-radius:4px">',
                               image.image.url)
        return '-'
    thumb.short_description = 'Photo'


class AirBNBImageInline(admin.TabularInline):
    model = AirBNBImage
    extra = 2
    fields = ['image', 'caption', 'is_featured', 'order']


@admin.register(AirBNB)
class AirBNBAdmin(admin.ModelAdmin):
    list_display = ['title', 'location', 'specification', 'price_per_night', 'max_guests', 'created_at']
    search_fields = ['title', 'location']
    inlines = [AirBNBImageInline]
