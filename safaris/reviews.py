"""Live Google reviews via the Places API (optional: needs GOOGLE_MAPS_API_KEY). Review content is never stored."""
import json
import re
import urllib.request
from datetime import datetime, timezone
from urllib.parse import quote, urlparse

from .content import GOOGLE_REVIEWS_URL

LISTING_NAME = 'Days Safari Adventures Limited'
LOCATION = {'latitude': -1.2935604, 'longitude': 36.8222022}
_place_id = None


def _google_url(value):
    try:
        u = urlparse(value)
    except Exception:
        return None
    ok = ('google.com', 'googleusercontent.com', 'gstatic.com', 'maps.app.goo.gl')
    if u.scheme == 'https' and any(u.hostname == h or (u.hostname or '').endswith('.' + h) for h in ok):
        return value
    return None


def _rating(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) and 1 <= v <= 5 else None


def _request(path, key, mask, body=None):
    req = urllib.request.Request(
        f'https://places.googleapis.com/v1/{path}', json.dumps(body).encode() if body else None,
        {'X-Goog-Api-Key': key, 'X-Goog-FieldMask': mask, **({'Content-Type': 'application/json'} if body else {})})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


def _resolve_place_id(key):
    global _place_id
    if _place_id:
        return _place_id
    data = _request('places:searchText', key, 'places.id,places.displayName,places.location', {
        'textQuery': f'{LISTING_NAME}, Nairobi, Kenya', 'languageCode': 'en', 'regionCode': 'KE', 'maxResultCount': 5,
        'locationBias': {'circle': {'center': LOCATION, 'radius': 500}}})
    for p in data.get('places', []):
        loc = p.get('location') or {}
        if (p.get('displayName', {}).get('text', '').strip().lower() == LISTING_NAME.lower()
                and abs(loc.get('latitude', 99) - LOCATION['latitude']) < .003 and abs(loc.get('longitude', 99) - LOCATION['longitude']) < .003):
            _place_id = p['id']
            return _place_id
    raise ValueError('Google listing could not be confirmed')


def fetch(key, place_id=''):
    pid = place_id or _resolve_place_id(key)
    if not re.fullmatch(r'[A-Za-z0-9_-]{10,250}', pid):
        raise ValueError('Invalid place id')
    place = _request(f'places/{quote(pid)}?languageCode=en', key, 'id,displayName,rating,userRatingCount,googleMapsUri,reviews,attributions')
    if not place.get('id') or not place.get('displayName', {}).get('text'):
        raise ValueError('Invalid Google Places response')
    source = _google_url(place.get('googleMapsUri')) or GOOGLE_REVIEWS_URL
    count = place.get('userRatingCount')
    reviews = []
    for i, r in enumerate((place.get('reviews') or [])[:5]):
        text, orig, author = r.get('text') or {}, r.get('originalText') or {}, r.get('authorAttribution') or {}
        reviews.append({
            'id': r.get('name') or str(i), 'rating': _rating(r.get('rating')), 'text': text.get('text') or orig.get('text') or '',
            'author': author.get('displayName') or 'Google Maps reviewer', 'authorUrl': _google_url(author.get('uri')),
            'avatar': _google_url(author.get('photoUri')), 'sourceUrl': _google_url(r.get('googleMapsUri')) or source,
            'date': r.get('relativePublishTimeDescription') or '',
            'translated': bool(text.get('languageCode') and orig.get('languageCode') and text['languageCode'] != orig['languageCode'])})
    return {
        'status': 'live', 'name': place['displayName']['text'], 'rating': _rating(place.get('rating')),
        'count': count if isinstance(count, int) and count >= 0 else None, 'sourceUrl': source, 'reviews': reviews,
        'attributions': [{'name': a['provider'], 'url': _google_url(a.get('providerUri'))} for a in place.get('attributions') or [] if a.get('provider')],
        'fetchedAt': datetime.now(timezone.utc).isoformat()}
