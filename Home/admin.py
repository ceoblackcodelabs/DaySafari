from django.contrib import admin
from .models import (
    Services, MustVisit, AwesomePackages, GalleryCategory, 
    Gallery, Bookings, Testimonials, BlogComments, Blogs
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