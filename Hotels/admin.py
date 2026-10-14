from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from django.utils.html import format_html

from .models import AirBNB, AirBNBImage, ApiKey, Hotel, HotelImage, HotelBooking


class HotelImageInline(TranslationTabularInline):
    model = HotelImage
    extra = 3
    fields = ['image', 'caption', 'is_featured', 'order']


@admin.register(Hotel)
class HotelAdmin(TranslationAdmin):
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


class AirBNBImageInline(TranslationTabularInline):
    model = AirBNBImage
    extra = 2
    fields = ['image', 'caption', 'is_featured', 'order']


@admin.register(AirBNB)
class AirBNBAdmin(TranslationAdmin):
    list_display = ['title', 'location', 'specification', 'price_per_night', 'max_guests', 'created_at']
    search_fields = ['title', 'location']
    inlines = [AirBNBImageInline]


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    """Keys are created with `python manage.py create_api_key`; here you can see usage and revoke them."""
    list_display = ['name', 'prefix', 'is_active', 'created_at', 'last_used_at']
    list_filter = ['is_active']
    readonly_fields = ['name', 'prefix', 'created_at', 'last_used_at']
    fields = ['name', 'prefix', 'is_active', 'created_at', 'last_used_at']

    def has_add_permission(self, request):
        return False


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    """Every enquiry sent from a hotel page (a request, not a paid booking)."""
    list_display = ('pk', 'created_at', 'name', 'phone', 'hotel', 'date', 'check_out', 'persons', 'kids', 'status', 'chat')
    list_editable = ('status',)
    list_filter = ('status', 'hotel', 'date', 'created_at')
    search_fields = ('name', 'email', 'phone', 'message', 'hotel__name')
    date_hierarchy = 'created_at'
    list_select_related = ('hotel',)
    readonly_fields = ('created_at',)
    list_per_page = 50
    actions = ['mark_contacted', 'mark_confirmed', 'mark_cancelled']
    fields = ('hotel', 'name', 'email', 'phone', 'date', 'check_out', 'persons', 'has_children', 'children_count',
              'children_ages', 'message', 'status', 'client', 'created_at')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(booking_type='hotel')

    def save_model(self, request, obj, form, change):
        obj.booking_type = 'hotel'
        super().save_model(request, obj, form, change)

    @admin.display(description='Children')
    def kids(self, obj):
        return obj.children_summary or '-'

    @admin.display(description='Chat')
    def chat(self, obj):
        digits = ''.join(c for c in (obj.phone or '') if c.isdigit())
        return format_html('<a href="https://wa.me/{}" target="_blank" rel="noopener">WhatsApp</a>', digits) if digits else ''

    def _mark(self, request, queryset, status, label):
        n = queryset.update(status=status)
        self.message_user(request, f'{n} enquiries marked {label}.')

    @admin.action(description='Mark selected as contacted')
    def mark_contacted(self, request, queryset):
        self._mark(request, queryset, 'contacted', 'contacted')

    @admin.action(description='Mark selected as confirmed')
    def mark_confirmed(self, request, queryset):
        self._mark(request, queryset, 'confirmed', 'confirmed')

    @admin.action(description='Mark selected as cancelled')
    def mark_cancelled(self, request, queryset):
        self._mark(request, queryset, 'cancelled', 'cancelled')
