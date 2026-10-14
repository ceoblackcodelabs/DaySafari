# context_processors.py

from .models import Ad
from datetime import date

def ads_context(request):
    """Add active ads to template context"""
    # The discount popup is only for the Packages page
    match = getattr(request, 'resolver_match', None)
    if not match or match.url_name != 'packages':
        return {'popup_ads': [], 'has_popup_ads': False}

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


def _site_stats():
    """Real numbers from the database for the 'Why Day Safaris' cards."""
    from .models import Trekking
    from Hotels.models import Hotel
    from Places.models import AwesomePackages, Destinations
    return {
        'packages': AwesomePackages.objects.count(),
        'hotels': Hotel.objects.filter(is_published=True).count(),
        'treks': Trekking.objects.count(),
        'destinations': Destinations.objects.count(),
    }


def _badges():
    from .models import TrustBadge
    out = {'award': [], 'partner': []}
    for b in TrustBadge.objects.filter(is_active=True):
        try:
            out[b.kind].append({'name': b.name, 'url': b.url, 'img': b.image.url})
        except Exception:
            continue
    return out


def mega_menu(request):
    """Pictures for the header's big hover menus (tours, trekking, cruises, packages). Cached for 10 minutes."""
    from django.core.cache import cache
    data = cache.get('mega_menu_v4')
    if data is None:
        from .models import Trekking
        from .templatetags.image_tags import thumb
        from Places.models import AwesomePackages

        def pic(obj):
            try:
                return thumb(obj.image, 480) if obj and obj.image else ''
            except Exception:
                return ''

        first_pkg = {}
        for p in AwesomePackages.objects.order_by('id'):
            first_pkg.setdefault(p.category, p)
        first_trek = {}
        for t in Trekking.objects.order_by('id'):
            first_trek.setdefault(t.category, t)
        from django.db.models import Count
        counts = {c.replace(' ', '_'): n for c, n in
                  AwesomePackages.objects.values_list('category').annotate(n=Count('id'))}
        data = {
            'pkg_count': counts,
            'stats': _site_stats(),
            'badges': _badges(),
            'lead_tours': list(AwesomePackages.objects.order_by('name').values_list('name', flat=True)[:80]),
            'lead_images': [pic(p) for p in list(first_pkg.values())[:3]] +
                           [pic(p) for p in AwesomePackages.objects.exclude(id__in=[x.id for x in first_pkg.values()]).order_by('id')[:3]],
            'pkg_img': {c.replace(' ', '_'): pic(p) for c, p in first_pkg.items()},
            'trek_img': {c.replace(' ', '_'): pic(t) for c, t in first_trek.items()},
            'cruises': [{'name': p.name, 'slug': p.slug, 'days': p.days, 'img': pic(p)}
                        for p in AwesomePackages.objects.filter(category='Cruises').order_by('id')[:5] if p.slug],
        }
        cache.set('mega_menu_v4', data, 600)
    return {'mega': data}


# Pages where the "What's your next adventure?" popup must not appear
LEAD_POPUP_SKIP = {'booking_create', 'request_booking_detail', 'contact', 'login', 'register', 'logout',
                   'profile', 'account_settings'}


def lead_popup(request):
    match = getattr(request, 'resolver_match', None)
    name = match.url_name if match else ''
    app = (match.app_names if match else [])
    show = bool(name) and name not in LEAD_POPUP_SKIP and 'admin' not in app \
        and not request.path.startswith(('/Mpesa', '/i18n')) and '/admin/' not in request.path \
        and 'payment' not in (name or '')
    return {'show_lead_popup': show}
