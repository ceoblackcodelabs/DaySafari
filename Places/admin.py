from django.contrib import admin
from .models import (
    DestinationsCategory, Destinations, Itinerary,
    MustVisit, AwesomePackages, PackagePurchase
)
from django.utils.html import format_html

# Register your models here.
class ItineraryInline(admin.TabularInline):
    model = Itinerary
    extra = 1
    fields = ['day_number', 'title', 'description', 'accommodation', 'meals']

@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ['package', 'day_number', 'title']
    list_filter = ['package']
@admin.register(MustVisit)
class MustVisitAdmin(admin.ModelAdmin):
    list_display = ('name', 'size')
    search_fields = ('name',)
    list_filter = ('size',)

@admin.register(AwesomePackages)
class AwesomePackagesAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'location', 'starRating', 'days', 'price', 'persons')
    inlines = [ItineraryInline]
    search_fields = ('name', 'category', 'location')
    list_filter = ('starRating', 'category', 'location')
    list_editable = ('price', 'category', 'days')
    ordering = ('-starRating', 'price')
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

@admin.register(PackagePurchase)
class PackagePurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'package', 'number_of_persons', 'amount_spent_formatted', 'travel_date', 'status', 'status_badge', 'purchase_date']
    list_filter = ['status', 'package', 'travel_date', 'purchase_date']
    search_fields = ['full_name', 'email', 'phone_number', 'package__name']
    readonly_fields = ['amount_spent_calculated']
    list_per_page = 20
    date_hierarchy = 'travel_date'
    list_editable = ['status']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Booking Details', {
            'fields': ('package', 'number_of_persons', 'travel_date', 'special_requests', 'amount_spent_calculated', 'status')
        }),
        ('User Account', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        ('Payment Information', {
            'fields': ('purchase_date',),
            'classes': ('collapse',)
        }),
    )
    
    def amount_spent_formatted(self, obj):
        return f"${obj.amount_spent:,.2f}"
    amount_spent_formatted.short_description = 'Amount Spent'
    amount_spent_formatted.admin_order_field = 'amount_spent'
    
    def amount_spent_calculated(self, obj):
        """Show calculated amount based on package price and persons"""
        if obj.package:
            calculated = obj.package.price * obj.number_of_persons
            return f"${calculated:,.2f}"
        return "N/A"
    amount_spent_calculated.short_description = 'Calculated Amount'
    
    def status_badge(self, obj):
        colors = {
            'Pending': 'orange',
            'Confirmed': 'green',
            'Cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Status'
    
    actions = ['mark_as_confirmed', 'mark_as_cancelled', 'mark_as_pending']
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='Confirmed')
        self.message_user(request, f"{updated} booking(s) marked as confirmed.")
    mark_as_confirmed.short_description = "Mark selected as Confirmed"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='Cancelled')
        self.message_user(request, f"{updated} booking(s) marked as cancelled.")
    mark_as_cancelled.short_description = "Mark selected as Cancelled"
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='Pending')
        self.message_user(request, f"{updated} booking(s) marked as pending.")
    mark_as_pending.short_description = "Mark selected as Pending"

    def resend_payment_email(self, request, queryset):
        sent_count = 0
        for purchase in queryset:
            if send_package_payment_email(purchase):
                sent_count += 1
        self.message_user(request, f"Payment email resent to {sent_count} customer(s).")
    resend_payment_email.short_description = "Resend payment email to selected customers"
    
    def save_model(self, request, obj, form, change):
        # Auto-calculate amount_spent if not set
        if not obj.amount_spent and obj.package:
            obj.amount_spent = obj.package.price * obj.number_of_persons
        super().save_model(request, obj, form, change)

# Register Destinations model
@admin.register(Destinations)
class DestinationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'display_image')
    search_fields = ('name', 'description', 'category__category')
    list_filter = ('category',)
    ordering = ('category', 'name')
    list_per_page = 20
    autocomplete_fields = ['category'] 
    
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