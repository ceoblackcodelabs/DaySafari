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
