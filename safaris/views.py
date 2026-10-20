import json
import logging

from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from ClientRequests.antispam import add_strike, get_client_ip, rate_limited
from ClientRequests.spamfilter import spam_reasons
from . import content, leads, reviews as reviews_api
from django.conf import settings

log = logging.getLogger(__name__)
_NO_STORE = {'Cache-Control': 'no-store'}
_visits = {}


def origin_for(request):
    return (getattr(settings, 'SITE_ORIGIN', '') or f'{request.scheme}://{request.get_host()}').rstrip('/')


def page(request, slug):
    """Landing pages: Kenya, Tanzania, Uganda, Masai Mara, Kilimanjaro, safari+beach, safari ideas and cruise pages."""
    pg = content.PAGE_BY_SLUG.get(slug)
    if not pg or slug in content.SITE_OWNED_SLUGS:
        raise Http404
    origin = origin_for(request)
    dest_key = pg['destination']
    pool = [d for d in content.DESTINATIONS.values() if d['menu']]
    related = ([d for d in pool if d['key'] != dest_key][:3] if dest_key in {d['key'] for d in pool}
               else [d for d in pool if d['key'] in ('kenya', 'tanzania', 'uganda')])
    hero = pg['image']
    schema = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': origin},
        {'@type': 'ListItem', 'position': 2, 'name': pg['eyebrow'].split('•')[0].strip(), 'item': f"{origin}/{pg['slug']}"}]}
    return render(request, 'safaris/page.html', {
        'page': pg, 'catalogue': slug == 'safaris', 'hero_image': hero, 'hero_place': content.CREDITS[hero]['caption'].split(',')[0],
        'destination': content.DESTINATIONS.get(dest_key), 'related': related, 'offers': content.offers_for(pg),
        'catalogue_filters': ['All journeys', 'Kenya', 'Tanzania', 'Uganda', 'Trek & coast'] if slug == 'safaris' else [],
        'whatsapp': content.whatsapp_url(origin, pg), 'schema': json.dumps(schema).replace('<', '\\u003c'),
        'credits': [c for c in content.CREDITS.values() if 'license_url' in c], 'reviews_url': content.GOOGLE_REVIEWS_URL,
    })


def _fail(message, status):
    return JsonResponse({'error': message}, status=status)


@require_POST
@rate_limited('landing-lead', [(4, 300), (15, 86400)])
def enquiry(request):
    """JSON endpoint behind the landing-page enquiry form. Saved as a booking lead (admin: Client Requests > Bookings)."""
    if len(request.body) > 16000:
        return _fail('Your enquiry is too long.', 413)
    try:
        raw = json.loads(request.body)
        if not isinstance(raw, dict):
            raise ValueError
    except ValueError:
        return _fail('Please check the form and try again.', 400)
    if raw.get('website'):  # honeypot
        return _fail('Please refresh the form and try again.', 400)
    try:
        data = leads.validate(raw)
    except ValueError as exc:
        return _fail(str(exc), 400)
    reasons = spam_reasons(name=data['full_name'], email=data['email'], message=data['notes'])
    if reasons:        # bots are told it worked, but nothing is saved or emailed
        add_strike(get_client_ip(request), 'spam landing enquiry: ' + ', '.join(reasons))
        return JsonResponse({'success': True, 'reference': 'DSA'})
    try:
        booking, error, status = leads.save(data, request)
    except Exception:
        log.exception('Enquiry save failed')
        return _fail('We could not save your enquiry. Please contact us on WhatsApp.', 503)
    if error:
        return _fail(error, status)
    return JsonResponse({'success': True, 'reference': f'DSA-{booking.pk:05d}' if booking else 'DSA'})


@require_GET
def reviews(request):
    fallback = {'status': 'unavailable', 'sourceUrl': content.GOOGLE_REVIEWS_URL}
    key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    if not key:
        return JsonResponse(fallback, headers=_NO_STORE)  # not configured: quiet fallback
    import time
    ip, now = request.META.get('REMOTE_ADDR', ''), time.time()
    for k in [k for k, v in _visits.items() if now - v[0] >= 60]:
        del _visits[k]
    start, count = _visits.get(ip, (now, 0))
    if count >= 15:
        return JsonResponse(fallback, status=429, headers=_NO_STORE)
    if len(_visits) < 1000 or ip in _visits:
        _visits[ip] = (start, count + 1)
    try:
        return JsonResponse(reviews_api.fetch(key, getattr(settings, 'GOOGLE_PLACE_ID', '')), headers=_NO_STORE)
    except Exception:
        log.error('Google reviews unavailable')
        return JsonResponse(fallback, status=503, headers=_NO_STORE)
