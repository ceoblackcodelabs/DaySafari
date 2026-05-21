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