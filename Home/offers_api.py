"""JSON API for the homepage 'Special Offers' posters (create / read / update).

Same authentication as the hotels API: `Authorization: Bearer dsa_<prefix>_<secret>`.
Every write supports `?dry_run=1`, which validates exactly like a real call but saves nothing.
There is deliberately no delete endpoint: to take an offer down, PATCH it with {"is_active": false} (or set an
earlier end_date). Full usage guide: docs/OFFERS_API.md
"""
import json
import logging
from datetime import date

from django import forms
from django.db import transaction
from django.utils import timezone

from Hotels.api import api_view, check_photo, error, read_payload, reply, truthy, MIN_PHOTO_WIDTH, MAX_PHOTO_BYTES

from .models import Offer

logger = logging.getLogger('hotels.api')

FIELDS = ['title', 'start_date', 'end_date', 'whatsapp_message', 'is_active', 'order']


class OfferApiForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = FIELDS

    def clean(self):
        data = super().clean()
        start, end = data.get('start_date'), data.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'end_date cannot be before start_date.')
        return data


def status_of(offer):
    today = date.today()
    if offer.end_date and offer.end_date < today:
        return 'expired'
    if offer.start_date and offer.start_date > today:
        return 'upcoming'
    return 'active'


def serialise(offer, request):
    return {
        'id': offer.pk, 'title': offer.title, 'status': status_of(offer) if offer.is_active else 'hidden',
        'is_active': offer.is_active, 'start_date': offer.start_date.isoformat() if offer.start_date else None,
        'end_date': offer.end_date.isoformat() if offer.end_date else None, 'order': offer.order,
        'whatsapp_message': offer.whatsapp_message, 'whatsapp_url': offer.whatsapp_url,
        'image_url': request.build_absolute_uri(offer.image.url) if offer.image else None,
        'page': request.build_absolute_uri('/en/') + '#offers',
    }


def validate(data, instance=None):
    known = set(FIELDS)
    unknown = sorted(set(data) - known)
    payload = {f: data[f] for f in FIELDS if f in data}
    if instance is None:
        payload.setdefault('is_active', True)
        payload.setdefault('order', 0)
    else:                                         # PATCH: only change what was sent
        current = {f: getattr(instance, f) for f in FIELDS}
        current.update(payload)
        payload = current
    form = OfferApiForm(payload, instance=instance)
    if not form.is_valid():
        return form, {k: [str(e) for e in v] for k, v in form.errors.items()}, unknown
    return form, None, unknown


def _poster(files):
    """The poster is the single file in the `image` field. Returns (upload, ext, error)."""
    upload = files.get('image')
    if not upload:
        return None, None, None
    ext, why = check_photo(upload)
    return (None, None, why) if why else (upload, ext, None)


@api_view('GET', public=True)
def offers_schema(request, key):
    return reply({
        'ok': True, 'version': 1, 'auth': 'Authorization: Bearer <api key>',
        'required_fields': ['title', 'image (file)'],
        'fields': {
            'title': 'text, max 160', 'start_date': 'YYYY-MM-DD, optional (shows as Upcoming until then)',
            'end_date': 'YYYY-MM-DD, optional (offer disappears after this day)',
            'whatsapp_message': 'optional pre-filled WhatsApp text, max 250 (default: "I am interested in: <title>")',
            'is_active': 'true/false (default true)', 'order': 'integer, lower shows first (default 0)',
        },
        'poster': {'how': 'multipart/form-data: field "data" (JSON) + the poster file in field "image"',
                   'rules': f'JPEG/PNG/WebP, >= {MIN_PHOTO_WIDTH}px wide, <= {MAX_PHOTO_BYTES // 1048576} MB'},
        'options': {'dry_run': '?dry_run=1 validates and returns what would happen, saving nothing'},
        'hide': 'PATCH offers/<id>/ with {"is_active": false}. There is no delete endpoint.',
    })


@api_view('GET', 'POST')
def offers_collection(request, key):
    if request.method == 'GET':
        qs = Offer.objects.all()
        if request.GET.get('active') in ('1', 'true', 'yes'):
            qs = qs.filter(is_active=True)
        try:
            limit = min(max(int(request.GET.get('limit', 100)), 1), 500)
        except ValueError:
            limit = 100
        items = [serialise(o, request) for o in qs[:limit]]
        if request.GET.get('status'):
            items = [i for i in items if i['status'] == request.GET['status']]
        return reply({'ok': True, 'count': len(items), 'offers': items})

    dry_run = truthy(request, 'dry_run')
    if (request.content_type or '').startswith('multipart/'):
        try:
            data, _ = read_payload(request)
        except ValueError as exc:
            return error(str(exc), 400)
    else:
        return error('Send multipart/form-data: a JSON "data" field and the poster file in "image".', 400)
    form, errors, unknown = validate(data)
    upload, ext, why = _poster(request.FILES)
    if why:
        errors = {**(errors or {}), 'image': [why]}
    elif not upload and not errors:
        errors = {'image': ['The poster file is required (multipart field "image").']}
    if errors:
        return error('Validation failed.', 400, errors=errors)
    cleaned = form.cleaned_data
    duplicate = Offer.objects.filter(title__iexact=cleaned['title'], end_date=cleaned.get('end_date')).first()
    if duplicate:
        return reply({'ok': False, 'error': 'An offer with this title and end date already exists.',
                      'existing': serialise(duplicate, request)}, 409)
    if dry_run:
        return reply({'ok': True, 'dry_run': True, 'status': 'would_create', 'title': cleaned['title'],
                      'ignored_fields': unknown})
    with transaction.atomic():
        offer = form.save(commit=False)
        upload.name = f'offer-{timezone.now():%Y%m%d%H%M%S}.{ext}'
        offer.image = upload
        offer.save()
    logger.info('API created offer %s (%s) via key %s', offer.title, offer.pk, key.name)
    return reply({'ok': True, 'status': 'created', 'offer': serialise(offer, request), 'ignored_fields': unknown}, 201)


@api_view('GET', 'PATCH')
def offer_detail(request, key, pk):
    offer = Offer.objects.filter(pk=pk).first()
    if not offer:
        return error('Offer not found.', 404)
    if request.method == 'GET':
        return reply({'ok': True, 'offer': serialise(offer, request)})
    try:
        data, _ = read_payload(request)               # PATCH takes JSON only; replace the poster with POST .../image/
    except ValueError as exc:
        return error(str(exc), 400)
    upload = ext = None
    form, errors, unknown = validate(data, instance=offer)
    if errors:
        return error('Validation failed.', 400, errors=errors)
    changed = sorted(form.changed_data)
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_update', 'changes': changed, 'ignored_fields': unknown})
    offer = form.save(commit=False)
    offer.save()
    logger.info('API updated offer %s fields %s via key %s', offer.pk, changed, key.name)
    return reply({'ok': True, 'status': 'updated', 'changed': changed, 'offer': serialise(offer, request),
                  'ignored_fields': unknown})


@api_view('POST')
def offer_image(request, key, pk):
    """Replace the poster of an existing offer: multipart/form-data with the file in `image`."""
    offer = Offer.objects.filter(pk=pk).first()
    if not offer:
        return error('Offer not found.', 404)
    upload, ext, why = _poster(request.FILES)
    if why or not upload:
        return error('Validation failed.', 400, errors={'image': [why or 'Send the poster in the multipart field "image".']})
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_replace_image'})
    upload.name = f'offer-{timezone.now():%Y%m%d%H%M%S}.{ext}'
    offer.image = upload
    offer.save()
    logger.info('API replaced poster of offer %s via key %s', offer.pk, key.name)
    return reply({'ok': True, 'status': 'image_replaced', 'offer': serialise(offer, request)})
