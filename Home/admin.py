from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import (
    Services, GalleryCategory, Gallery, Testimonials,
    BlogComments, Blogs, Brochure, ItineraryTreking,
    Trekking, TrekkingBooking, Ad
)


@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'icon', 'description_preview']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_per_page = 20

    def description_preview(self, obj):
        """Show truncated description in admin list"""
        if obj.description:
            return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
        return 'No description'
    description_preview.short_description = 'Description'


@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 20


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'image_preview']
    list_filter = ['category']
    search_fields = ['name', 'category__name']
    ordering = ['category', 'name']
    list_per_page = 20
    autocomplete_fields = ['category']

    def image_preview(self, obj):
        """Display image thumbnail in admin list"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Image Preview'
    image_preview.allow_tags = True


@admin.register(Testimonials)
class TestimonialsAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'location', 'star_rating', 'star_rating_display', 'feedback_preview', 'created_at']  # Added 'star_rating'
    list_filter = ['star_rating', 'created_at']
    search_fields = ['name', 'location', 'feedback']
    ordering = ['-created_at']
    list_per_page = 20
    list_editable = ['star_rating']  # Now 'star_rating' is in list_display
    readonly_fields = ['created_at']

    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'location', 'star_rating')
        }),
        ('Content', {
            'fields': ('feedback',)
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def star_rating_display(self, obj):
        """Display star rating as stars"""
        if obj.star_rating:
            stars = '⭐' * obj.star_rating
            return format_html(f'<span style="font-size: 14px;">{stars}</span>')
        return 'No Rating'
    star_rating_display.short_description = 'Rating'
    star_rating_display.admin_order_field = 'star_rating'

    def feedback_preview(self, obj):
        """Show truncated feedback in admin list"""
        if obj.feedback:
            return obj.feedback[:100] + '...' if len(obj.feedback) > 100 else obj.feedback
        return 'No feedback'
    feedback_preview.short_description = 'Feedback'


@admin.register(BlogComments)
class BlogCommentsAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'comment_preview', 'blog', 'created_date']
    list_filter = ['created_date', 'blog']
    search_fields = ['name', 'email', 'comment']
    ordering = ['-created_date']
    list_per_page = 20
    autocomplete_fields = ['blog']

    def comment_preview(self, obj):
        """Show truncated comment in admin list"""
        if obj.comment:
            return obj.comment[:100] + '...' if len(obj.comment) > 100 else obj.comment
        return 'No comment'
    comment_preview.short_description = 'Comment'


@admin.register(Blogs)
class BlogsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'published_date', 'image_preview', 'likes']
    list_filter = ['published_date', 'author']
    search_fields = ['title', 'content', 'author', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-published_date']
    list_per_page = 20
    readonly_fields = ['published_date']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author')
        }),
        ('Content', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description', 'schema_markup'),
            'classes': ('collapse',)
        }),
        ('Media & Engagement', {
            'fields': ('image', 'likes')
        }),
        ('Comments', {
            'fields': ('comments',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('published_date',),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        """Display image thumbnail in admin list"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Image Preview'
    image_preview.allow_tags = True


@admin.register(Brochure)
class BrochureAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'description_preview', 'created_at', 'pdf_link', 'image_preview']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    list_per_page = 20
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description')
        }),
        ('Files', {
            'fields': ('pdf_file', 'image')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def description_preview(self, obj):
        """Show truncated description in admin list"""
        if obj.description:
            return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
        return 'No description'
    description_preview.short_description = 'Description'

    def image_preview(self, obj):
        """Display image thumbnail in admin list"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Image Preview'
    image_preview.allow_tags = True

    def pdf_link(self, obj):
        """Display PDF download link in admin list"""
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank">📄 View PDF</a>',
                obj.pdf_file.url
            )
        return 'No PDF'
    pdf_link.short_description = 'PDF File'
    pdf_link.allow_tags = True


class ItineraryTrekingInline(admin.TabularInline):
    """Inline admin for Trekking Itinerary"""
    model = ItineraryTreking
    extra = 1
    fields = ['day_number', 'title', 'description', 'activities', 'accommodation', 'meals', 'image']
    ordering = ['day_number']


@admin.register(ItineraryTreking)
class ItineraryTrekingAdmin(admin.ModelAdmin):
    list_display = ['id', 'package', 'day_number', 'title']
    list_filter = ['package']
    search_fields = ['title', 'description', 'package__name']
    ordering = ['package', 'day_number']
    list_per_page = 20


@admin.register(Trekking)
class TrekkingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category', 'location', 'star_rating_display',
        'days', 'price', 'price_formatted', 'persons', 'created_at'  # Added 'price'
    ]
    inlines = [ItineraryTrekingInline]
    list_filter = ['category', 'star_rating', 'location']
    search_fields = ['name', 'location', 'description']
    list_editable = ['category', 'price', 'days']  # Now 'price' is in list_display
    ordering = ['-created_at']
    list_per_page = 20
    readonly_fields = ['created_at']

    fieldsets = (
        ('Package Information', {
            'fields': ('name', 'category', 'location')
        }),
        ('Pricing & Details', {
            'fields': ('price', 'days', 'persons', 'star_rating')
        }),
        ('Content', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('Media', {
            'fields': ('image',),
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def star_rating_display(self, obj):
        """Display star rating as stars"""
        if obj.star_rating:
            stars = '⭐' * obj.star_rating
            return format_html(f'<span style="font-size: 14px;">{stars}</span>')
        return 'No Rating'
    star_rating_display.short_description = 'Rating'
    star_rating_display.admin_order_field = 'star_rating'

    def price_formatted(self, obj):
        """Display formatted price"""
        return f"${obj.price:,.2f}"
    price_formatted.short_description = 'Price'
    price_formatted.admin_order_field = 'price'


@admin.register(TrekkingBooking)
class TrekkingBookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_reference', 'full_name', 'package', 'number_of_persons',
        'total_price_formatted', 'travel_date', 'booking_status', 'booking_status_badge',  # Added 'booking_status'
        'booking_date'
    ]
    list_filter = ['booking_status', 'package', 'travel_date', 'booking_date']
    search_fields = ['booking_reference', 'full_name', 'email', 'phone_number']
    readonly_fields = ['booking_reference', 'booking_date', 'updated_at']
    list_per_page = 20
    date_hierarchy = 'travel_date'
    list_editable = ['booking_status']  # Now 'booking_status' is in list_display
    autocomplete_fields = ['package']

    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking_reference',)
        }),
        ('Customer Information', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Package Details', {
            'fields': ('package', 'number_of_persons', 'travel_date')
        }),
        ('Pricing', {
            'fields': ('total_price',)
        }),
        ('Additional Information', {
            'fields': ('special_requests',)
        }),
        ('Status', {
            'fields': ('booking_status',)
        }),
        ('Timestamps', {
            'fields': ('booking_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_price_formatted(self, obj):
        """Display formatted total price"""
        return f"${obj.total_price:,.2f}"
    total_price_formatted.short_description = 'Total Price'
    total_price_formatted.admin_order_field = 'total_price'

    def booking_status_badge(self, obj):
        """Display booking status as colored badge"""
        colors = {
            'pending': '#ffc107',    # Yellow
            'confirmed': '#28a745',  # Green
            'cancelled': '#dc3545',  # Red
            'completed': '#17a2b8',  # Teal
        }
        color = colors.get(obj.booking_status, '#6c757d')
        status_labels = {
            'pending': 'Pending',
            'confirmed': 'Confirmed',
            'cancelled': 'Cancelled',
            'completed': 'Completed',
        }
        label = status_labels.get(obj.booking_status, obj.booking_status)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, label
        )
    booking_status_badge.short_description = 'Status'
    booking_status_badge.allow_tags = True

    actions = ['mark_as_confirmed', 'mark_as_cancelled', 'mark_as_completed']

    def mark_as_confirmed(self, request, queryset):
        """Bulk action to mark as confirmed"""
        updated = queryset.update(booking_status='confirmed')
        self.message_user(request, f"✅ {updated} booking(s) marked as confirmed.", messages.SUCCESS)
    mark_as_confirmed.short_description = "Mark as Confirmed"

    def mark_as_cancelled(self, request, queryset):
        """Bulk action to mark as cancelled"""
        updated = queryset.update(booking_status='cancelled')
        self.message_user(request, f"❌ {updated} booking(s) marked as cancelled.", messages.WARNING)
    mark_as_cancelled.short_description = "Mark as Cancelled"

    def mark_as_completed(self, request, queryset):
        """Bulk action to mark as completed"""
        updated = queryset.update(booking_status='completed')
        self.message_user(request, f"✅ {updated} booking(s) marked as completed.", messages.SUCCESS)
    mark_as_completed.short_description = "Mark as Completed"


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'get_package_name', 'discount_percentage',
        'is_active', 'start_date', 'end_date', 'image_preview'
    ]
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'discount_percentage']
    ordering = ['-created_at']
    list_per_page = 20

    fieldsets = (
        ('Ad Information', {
            'fields': ('title', 'description')
        }),
        ('Associated Package', {
            'fields': ('package', 'trekking_package'),
            'description': 'Select either a regular package or a trekking package (not both)'
        }),
        ('Media', {
            'fields': ('image',),
        }),
        ('Discount & CTA', {
            'fields': ('discount_percentage', 'show_book_now', 'button_text', 'button_color')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Display Settings', {
            'fields': ('show_on_pages',),
            'help_text': 'Leave blank to show on all pages'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_package_name(self, obj):
        """Get the name of the associated package"""
        if obj.package:
            return obj.package.name
        elif obj.trekking_package:
            return obj.trekking_package.name
        return 'No Package'
    get_package_name.short_description = 'Package'

    def image_preview(self, obj):
        """Display image thumbnail in admin list"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Image Preview'
    image_preview.allow_tags = True


# Admin site headers
admin.site.site_header = "Day Safaris Adventures Admin"
admin.site.site_title = "Day Safaris Admin Portal"
admin.site.index_title = "Welcome to Day Safaris Adventures Dashboard"