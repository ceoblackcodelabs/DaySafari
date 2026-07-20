from django.contrib import admin
from .models import (
    DestinationsCategory, Destinations, Itinerary,
    MustVisit, AwesomePackages, PackagePurchase,
    IncluisiveExcluisive, DestinationImage
)
from django.utils.html import format_html
from django.contrib import messages


class ItineraryInline(admin.TabularInline):
    model = Itinerary
    extra = 1
    fields = ['day_number', 'title', 'description', 'activities', 'accommodation', 'meals', 'image']
    ordering = ['day_number']


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ['package', 'day_number', 'title']
    list_filter = ['package']
    search_fields = ['package__name', 'title', 'description']
    ordering = ['package', 'day_number']


@admin.register(MustVisit)
class MustVisitAdmin(admin.ModelAdmin):
    list_display = ['name', 'size', 'order', 'image_preview']
    search_fields = ['name']
    list_filter = ['size']
    ordering = ['order', 'name']
    list_editable = ['order', 'size']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image'


@admin.register(IncluisiveExcluisive)
class IncluisiveExcluisiveAdmin(admin.ModelAdmin):
    list_display = ['package', 'name', 'is_inclusive', 'type_badge']
    list_filter = ['is_inclusive', 'package']
    search_fields = ['name', 'package__name']
    list_editable = ['is_inclusive']
    ordering = ['-is_inclusive', 'name']

    def type_badge(self, obj):
        color = '#28a745' if obj.is_inclusive else '#dc3545'
        label = '✓ Included' if obj.is_inclusive else '✗ Excluded'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, label
        )
    type_badge.short_description = 'Type'


@admin.register(AwesomePackages)
class AwesomePackagesAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'location', 'star_rating_display',
        'days', 'price_formatted', 'persons', 'slug', 'created_at'
    ]
    inlines = [ItineraryInline]
    search_fields = ['name', 'category', 'location', 'slug', 'description']
    list_filter = ['category', 'location', 'star_rating']
    list_editable = ['category', 'days']
    ordering = ['-created_at', 'name']
    prepopulated_fields = {'slug': ('name', 'location')}
    readonly_fields = ['created_at']
    list_per_page = 25

    def star_rating_display(self, obj):
        if obj.star_rating:
            stars = '⭐' * obj.star_rating
            return format_html(f'<span style="font-size: 14px;">{stars}</span>')
        return 'No Rating'
    star_rating_display.short_description = 'Rating'
    star_rating_display.admin_order_field = 'star_rating'

    def price_formatted(self, obj):
        return f"${obj.price:,.2f}"
    price_formatted.short_description = 'Price'
    price_formatted.admin_order_field = 'price'

    actions = ['clone_package']

    def clone_package(self, request, queryset):
        cloned_count = 0
        for package in queryset:
            cloned = AwesomePackages(
                name=f"{package.name} (Copy)",
                location=package.location,
                star_rating=package.star_rating,
                days=package.days,
                price=package.price,
                persons=package.persons,
                description=package.description,
                category=package.category,
                image=package.image,
            )
            cloned.save()

            for itinerary in package.itineraries.all():
                Itinerary.objects.create(
                    package=cloned,
                    day_number=itinerary.day_number,
                    title=itinerary.title,
                    description=itinerary.description,
                    activities=itinerary.activities,
                    accommodation=itinerary.accommodation,
                    meals=itinerary.meals,
                    image=itinerary.image,
                )

            for item in package.inclusions.all():
                IncluisiveExcluisive.objects.create(
                    package=cloned,
                    name=item.name,
                    is_inclusive=item.is_inclusive,
                )

            cloned_count += 1

        self.message_user(request, f"Successfully cloned {cloned_count} package(s).")
    clone_package.short_description = "Clone selected packages"


@admin.register(DestinationsCategory)
class DestinationsCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'location', 'image_orientation', 'image_preview']
    search_fields = ['category', 'location']
    list_filter = ['image_orientation']
    ordering = ['category']
    list_editable = ['image_orientation']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" style="object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image Preview'

    actions = ['make_landscape', 'make_portrait']

    def make_landscape(self, request, queryset):
        updated = queryset.update(image_orientation='landscape')
        self.message_user(request, f'{updated} category(ies) set to landscape.')
    make_landscape.short_description = "Set to landscape"

    def make_portrait(self, request, queryset):
        updated = queryset.update(image_orientation='portrait')
        self.message_user(request, f'{updated} category(ies) set to portrait.')
    make_portrait.short_description = "Set to portrait"


class DestinationImageInline(admin.TabularInline):
    model = DestinationImage
    extra = 3
    fields = ['image', 'caption', 'is_featured', 'order']
    ordering = ['order']

@admin.register(Destinations)
class DestinationsAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    inlines = [DestinationImageInline]

@admin.register(DestinationImage)
class DestinationImageAdmin(admin.ModelAdmin):
    list_display = ['destination', 'caption', 'is_featured', 'order', 'created_at']
    list_filter = ['is_featured', 'destination', 'created_at']
    search_fields = ['caption', 'destination__name']


@admin.register(PackagePurchase)
class PackagePurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'full_name', 'package', 'number_of_persons',
        'amount_spent_formatted', 'travel_date', 'status',
        'purchase_date'
    ]
    list_filter = ['status', 'package', 'travel_date', 'purchase_date']
    search_fields = ['full_name', 'email', 'phone_number', 'package__name']
    readonly_fields = ['amount_spent_calculated', 'purchase_date']
    list_per_page = 20
    date_hierarchy = 'travel_date'
    list_editable = ['status']
    autocomplete_fields = ['package', 'user']

    def amount_spent_formatted(self, obj):
        return f"${obj.amount_spent:,.2f}"
    amount_spent_formatted.short_description = 'Amount'
    amount_spent_formatted.admin_order_field = 'amount_spent'

    def amount_spent_calculated(self, obj):
        if obj.package and obj.package.price:
            calculated = obj.package.price * obj.number_of_persons
            return format_html(
                '<strong>${:,.2f}</strong> <span style="color: #6c757d; font-size: 11px;">({} × ${:,.2f})</span>',
                calculated, obj.number_of_persons, obj.package.price
            )
        return "N/A"
    amount_spent_calculated.short_description = 'Calculated Amount'

    actions = ['mark_as_confirmed', 'mark_as_cancelled', 'mark_as_pending']

    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='Confirmed')
        self.message_user(request, f"✅ {updated} booking(s) confirmed.")
    mark_as_confirmed.short_description = "Mark as Confirmed"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='Cancelled')
        self.message_user(request, f"❌ {updated} booking(s) cancelled.")
    mark_as_cancelled.short_description = "Mark as Cancelled"

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='Pending')
        self.message_user(request, f"⏳ {updated} booking(s) pending.")
    mark_as_pending.short_description = "Mark as Pending"

    def save_model(self, request, obj, form, change):
        if not obj.amount_spent and obj.package:
            obj.amount_spent = obj.package.price * obj.number_of_persons
        super().save_model(request, obj, form, change)


# Admin site headers
admin.site.site_header = "Day Safaris Adventures Admin"
admin.site.site_title = "Day Safaris Admin Portal"
admin.site.index_title = "Welcome to Day Safaris Adventures Dashboard"