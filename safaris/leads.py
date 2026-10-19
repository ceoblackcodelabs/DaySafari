"""Validation and saving of the landing-page enquiry form (saved as a ClientRequests booking lead)."""
import logging
import re
from datetime import date

from django.core.cache import cache

from . import content

log = logging.getLogger(__name__)
UTM_KEYS = ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term')


def _text(value, limit=160):
    return value.strip()[:limit] if isinstance(value, str) else ''


def add_months(d, n):
    m = d.month - 1 + n
    return date(d.year + m // 12, m % 12 + 1, 1)


def next_months(count=24):
    today = date.today().replace(day=1)
    out = []
    for i in range(count):
        d = add_months(today, i)
        out.append({'value': f'{d:%Y-%m}', 'label': f'{d:%b %Y}'})
    return out


def validate(raw):
    """Returns cleaned fields or raises ValueError with a visitor-friendly message."""
    page = content.PAGE_BY_SLUG.get(_text(raw.get('page_slug'), 70))
    if not page:
        raise ValueError('Please refresh the page and try again.')
    sid = _text(raw.get('submission_id'), 60)
    if not re.fullmatch(r'[a-f0-9-]{36}', sid, re.I):
        raise ValueError('Please refresh the form and try again.')
    name = _text(raw.get('full_name'), 100)
    if len(name) < 2:
        raise ValueError('Please enter your name.')
    contact = _text(raw.get('contact'), 120)
    email = contact.lower() if re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', contact) else ''
    digits = re.sub(r'\D', '', contact)
    phone = ''
    if not email and re.fullmatch(r'[+()\d\s.-]+', contact) and 7 <= len(digits) <= 15:
        if contact.startswith('+'):
            phone = '+' + digits
        elif re.fullmatch(r'0[17]\d{8}', digits):
            phone = '+254' + digits[1:]
        elif re.fullmatch(r'254[17]\d{8}', digits):
            phone = '+' + digits
    if not email and not phone:
        raise ValueError('Enter a valid email or a WhatsApp number with country code.')

    candidate = _text(raw.get('destination_key'), 30)
    key = page['destination'] or (candidate if candidate in content.DESTINATIONS else None)
    dest = content.DESTINATIONS.get(key)
    trip_id = _text(raw.get('trip_id'), 70)
    offer = content.OFFER_BY_ID.get(trip_id)
    if trip_id and (not offer or (key and offer['destination'] != key and key not in offer['also'] and offer['destination'] not in content._ALSO_TRIPS.get(key, []))):
        raise ValueError('Please select an option that matches this section.')

    try:
        travellers = int(raw.get('travellers'))
    except (TypeError, ValueError):
        travellers = 0
    if not 1 <= travellers <= 50:
        raise ValueError('Enter between 1 and 50 travellers.')

    month = _text(raw.get('travel_month'), 40)
    if month != 'Still deciding':
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', month):
            raise ValueError('Choose a travel month or Still deciding.')
        today = date.today().replace(day=1)
        if month < f'{today:%Y-%m}' or month > f'{add_months(today, 24):%Y-%m}':
            raise ValueError('Please choose a travel month within the next two years.')

    answers = {}
    supplied = raw.get('answers') if isinstance(raw.get('answers'), dict) else {}
    for q in (dest['questions'] if dest else []):
        answer = _text(supplied.get(q['key']))
        if answer and answer not in q['options']:
            raise ValueError(f"Please choose a valid answer for {q['label'].lower()}")
        if answer:
            answers[q['key']] = answer
    incoming = raw.get('utm') if isinstance(raw.get('utm'), dict) else {}
    utm = {k: _text(incoming.get(k)) for k in UTM_KEYS if _text(incoming.get(k))}
    return {
        'id': sid, 'full_name': name, 'email': email, 'phone': phone,
        'kind': dest['group'] if dest else 'safari', 'destination': dest['label'] if dest else 'Help me choose',
        'destination_key': key or 'undecided', 'item': offer['name'] if offer else '', 'trip_id': offer['id'] if offer else '',
        'travel_month': month, 'travellers': travellers, 'answers': answers, 'notes': _text(raw.get('notes'), 1200),
        'page_slug': page['slug'] or 'home', 'page_title': page['title'], 'utm': utm,
    }


def save(data, request):
    """Idempotent save into ClientRequests.Bookings + the usual staff/customer emails.
    Returns (booking_or_None, error_message, http_status)."""
    from ClientRequests.models import Bookings
    from EmailSetup.utils import handle_new_lead, send_booking_confirmation

    marker = f"safaris:lead:{data['id']}"
    done = cache.get(marker)
    if done:
        return Bookings.objects.filter(pk=done).first(), None, 200

    lines = [f"Enquiry from the {data['page_title']} page ({data['page_slug']}).",
             f"Interested in: {data['destination']}" + (f" - {data['item']}" if data['item'] else ''),
             f"Travel month: {data['travel_month']}", f"Travellers: {data['travellers']}"]
    lines += [f'{k.replace("_", " ").capitalize()}: {v}' for k, v in data['answers'].items()]
    if data['notes']:
        lines.append(f"Notes: {data['notes']}")
    if data['utm']:
        lines.append('Campaign: ' + ', '.join(f'{k}={v}' for k, v in data['utm'].items()))
    if not data['email']:
        lines.append('Preferred contact: WhatsApp')
    month = data['travel_month']
    when = date.today() if month == 'Still deciding' else date(int(month[:4]), int(month[5:]), 1)
    booking = Bookings(
        booking_type='hotel' if data['kind'] == 'hotel' else 'safari', name=data['full_name'],
        email=data['email'] or 'email@example.com', phone=data['phone'], persons=data['travellers'], date=when,
        message='\n'.join(lines), client=request.user if request.user.is_authenticated else None)
    booking.save()
    cache.set(marker, booking.pk, 86400)
    try:
        handle_new_lead(booking, send_booking_confirmation if data['email'] else None)
    except Exception:
        log.exception('Lead notification failed')
    return booking, None, 201
