from django.contrib import admin
from .models import (
    Services, GalleryCategory, Brochure,
    Gallery, Testimonials, BlogComments, Blogs,
    Trekking, ItineraryTreking, TrekkingBooking
)

admin.site.site_header = "DAY SAFARIS ADVENTURES"
admin.site.site_title = "Day Safari Admin"

@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)
    list_filter = ('icon',)

@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)

@admin.register(Testimonials)
class TestimonialsAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'starRating')
    search_fields = ('name', 'location')
    list_filter = ('starRating', 'location')
    list_editable = ('starRating',)

# @admin.register(BlogComments)
# class BlogCommentsAdmin(admin.ModelAdmin):
#     list_display = ('name', 'email', 'created_date')
#     search_fields = ('name', 'email', 'comment')
#     list_filter = ('created_date',)

@admin.register(Blogs)
class BlogsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_date')
    search_fields = ('title', 'author')
    list_filter = ('published_date',)

@admin.register(Brochure)
class BrochureAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'created_at']  # Only fields that exist
    list_filter = ['created_at']  # Filter by creation date
    search_fields = ['title', 'description']  # Searchable fields
    readonly_fields = ['created_at']  # Make created_at read-only (it auto-sets)
    ordering = ['-created_at']  # Show newest first

    # Organize the form layout
    fieldsets = (
        ('Brochure Information', {
            'fields': ('title', 'description', 'pdf_file', 'image')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)  # Collapsible section
        }),
    )

    # Optional: Add preview for uploaded files
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user if hasattr(request, 'user') else None
        super().save_model(request, obj, form, change)


class ItineraryTrekingInline(admin.TabularInline):
    model = ItineraryTreking
    extra = 1
    ordering = ['day_number']
    fields = ['day_number', 'title', 'description', 'activities', 'accommodation', 'meals', 'image']

@admin.register(Trekking)
class TrekkingAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'starRating', 'days', 'price', 'persons', 'category']
    list_filter = ['category', 'starRating', 'location']
    search_fields = ['name', 'location', 'description']
    list_editable = ['price', 'days', 'persons']
    list_per_page = 20
    inlines = [ItineraryTrekingInline]  # This will work now
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'category', 'description')
        }),
        ('Pricing & Details', {
            'fields': ('days', 'price', 'persons', 'starRating')
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ItineraryTreking)
class ItineraryTrekingAdmin(admin.ModelAdmin):
    list_display = ['package', 'day_number', 'title', 'accommodation', 'meals']
    list_filter = ['meals', 'package__category', 'package__name']
    search_fields = ['title', 'description', 'activities', 'package__name']
    ordering = ['package__name', 'day_number']
    list_editable = ['day_number', 'title']


@admin.register(TrekkingBooking)
class TrekkingBookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'full_name', 'package', 'travel_date', 'number_of_persons', 'booking_status']
    list_filter = ['booking_status', 'package', 'travel_date']
    search_fields = ['booking_reference', 'full_name', 'email', 'phone_number']
    readonly_fields = ['booking_reference', 'booking_date', 'updated_at']
    list_editable = ['booking_status']

    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking_reference',)
        }),
        ('Package Details', {
            'fields': ('package', 'travel_date', 'number_of_persons', 'total_price')
        }),
        ('Customer Information', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'booking_status')
        }),
        ('Timestamps', {
            'fields': ('booking_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )