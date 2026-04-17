from django.contrib import admin
from .models import (
    Services, MustVisit, AwesomePackages, GalleryCategory, 
    Gallery, Bookings, Testimonials, BlogComments, Blogs,
    DestinationsCategory, Destinations
)

@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)
    list_filter = ('icon',)

@admin.register(MustVisit)
class MustVisitAdmin(admin.ModelAdmin):
    list_display = ('name', 'size')
    search_fields = ('name',)
    list_filter = ('size',)

@admin.register(AwesomePackages)
class AwesomePackagesAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'starRating', 'days', 'price', 'persons')
    search_fields = ('name', 'location')
    list_filter = ('starRating', 'location')
    list_editable = ('price', 'days')
    ordering = ('-starRating', 'price')

@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    search_fields = ('name',)
    list_filter = ('category',)

@admin.register(Bookings)
class BookingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'destination', 'persons', 'categories')
    search_fields = ('name', 'email', 'destination')
    list_filter = ('categories', 'destination')
    readonly_fields = ('name', 'email', 'phone', 'destination', 'persons', 'categories', 'message')

@admin.register(Testimonials)
class TestimonialsAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'starRating')
    search_fields = ('name', 'location')
    list_filter = ('starRating', 'location')
    list_editable = ('starRating',)
    
@admin.register(BlogComments)
class BlogCommentsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'blog')
    search_fields = ('name', 'email', 'blog__title')
    list_filter = ('blog',)
    
@admin.register(Blogs)
class BlogsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_date')
    search_fields = ('title', 'author')
    list_filter = ('published_date',)

# Register DestinationsCategory model
@admin.register(DestinationsCategory)
class DestinationsCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'location', 'image_orientation', 'image')
    search_fields = ('category', 'location')
    list_filter = ('image_orientation',)
    ordering = ('category',)
    list_per_page = 20
    
    # Add fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'location')
        }),
        ('Media', {
            'fields': ('image', 'image_orientation'),
            'description': 'Upload an image for this category. Choose orientation based on the image shape.'
        }),
    )

# Register Destinations model
@admin.register(Destinations)
class DestinationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'display_image')
    search_fields = ('name', 'description', 'category__category')
    list_filter = ('category',)
    ordering = ('category', 'name')
    list_per_page = 20
    autocomplete_fields = ['category']  # Useful if you have many categories
    
    # Add fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name')
        }),
        ('Content', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('Media', {
            'fields': ('image',),
            'description': 'Upload a destination image'
        }),
    )
    
    def display_image(self, obj):
        """Display a thumbnail of the image in admin list view"""
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    display_image.short_description = 'Image Preview'
    
    # Override save method if needed
    def save_model(self, request, obj, form, change):
        """Add custom save behavior if needed"""
        super().save_model(request, obj, form, change)
    
    # Add actions for bulk operations
    actions = ['make_landscape', 'make_portrait']
    
    def make_landscape(self, request, queryset):
        """Bulk action to set category orientation to landscape"""
        updated = queryset.update(category__image_orientation='landscape')
        self.message_user(request, f'{updated} destinations set to landscape orientation.')
    make_landscape.short_description = "Set selected destinations' categories to landscape"
    
    def make_portrait(self, request, queryset):
        """Bulk action to set category orientation to portrait"""
        updated = queryset.update(category__image_orientation='portrait')
        self.message_user(request, f'{updated} destinations set to portrait orientation.')
    make_portrait.short_description = "Set selected destinations' categories to portrait"