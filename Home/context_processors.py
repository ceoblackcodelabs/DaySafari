# context_processors.py

from .models import Ad
from datetime import date

def ads_context(request):
    """Add active ads to template context"""
    today = date.today()
    active_ads = Ad.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )

    # Optional: Filter by current page URL
    current_path = request.path
    page_specific_ads = []
    general_ads = []

    for ad in active_ads:
        if ad.show_on_pages:
            show_pages = [page.strip() for page in ad.show_on_pages.split(',')]
            if any(page in current_path for page in show_pages):
                page_specific_ads.append(ad)
        else:
            general_ads.append(ad)

    # Prioritize page-specific ads, then general ads
    display_ads = page_specific_ads + general_ads

    return {
        'popup_ads': display_ads,
        'has_popup_ads': len(display_ads) > 0
    }


def footer_gallery(request):
    """Six small gallery photos for the site footer (cached; the last one links to the full gallery)."""
    from django.core.cache import cache
    data = cache.get('footer_gallery_v1')
    if data is None:
        from .models import Gallery
        from .templatetags.image_tags import thumb
        data = []
        for item in Gallery.objects.order_by('-id')[:6]:
            try:
                data.append({'name': item.name, 'url': item.image.url, 'thumb': thumb(item.image, 200)})
            except Exception:
                continue
        cache.set('footer_gallery_v1', data, 600)
    return {'footer_gallery': data}


def chat_i18n(request):
    """Chat widget texts in the visitor's language (read by static/js/chatbot.js)."""
    from django.utils.translation import gettext as _
    return {'chat_i18n': {
        'err_connect': _("I'm having trouble connecting to our support system. Please contact us directly at info@daysafarisadventures.com or call +254759379600 for assistance. 🦁"),
        'err_network': _("Network error. Please check your connection or contact us directly at info@daysafarisadventures.com. We're here to help! 🦁"),
        'wait': _("Please wait for my response before sending another message. 🦁"),
        'greeting': _("Hello! Welcome to Day Safaris Adventures! 🦁 How can I help you plan your East African safari today? I can assist with destinations, packages, bookings, or any questions about our services!"),
        'help': _("I can help you with:\n• Booking safaris\n• Destination information\n• Package prices\n• Payment options\n• Group discounts\n• Travel tips\n\nJust let me know what you need! 😊"),
        'contact': _("You can reach us at:\n📞 Phone: +254759379600\n📧 Email: info@daysafarisadventures.com\n📍 Location: Nairobi, Kenya\n🌐 Website: daysafarisadventures.co.ke\n\nWe're available 24/7!"),
        'hours': _("Our customer support is available:\nMonday - Friday: 8:00 AM - 8:00 PM (EAT)\nSaturday: 9:00 AM - 6:00 PM (EAT)\nSunday: 10:00 AM - 4:00 PM (EAT)\nEmergency support: 24/7 at +254 782 390 295"),
        'packages': _("Our safari packages start from $649 for 3-day adventures to $1,899 for luxury experiences. Popular packages include:\n• Masai Mara Safari (4 days, $849)\n• Zanzibar Beach Holiday (6 days, $1,299)\n• Serengeti Migration (5 days, $1,499)\n• Amboseli Elephant Experience (3 days, $649)\n\nWould you like details on any specific package?"),
        'destinations': _("We offer amazing destinations across East Africa:\n🇰🇪 Kenya: Masai Mara, Amboseli, Tsavo, Diani Beach\n🇹🇿 Tanzania: Serengeti, Zanzibar, Kilimanjaro, Ngorongoro\n🇺🇬 Uganda: Bwindi Gorillas, Queen Elizabeth Park\n🇷🇼 Rwanda: Kigali Cultural Tour, Lake Kivu\n\nWhich destination interests you? 🗺️"),
    }}
