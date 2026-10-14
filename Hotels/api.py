"""JSON API for managing hotels (create / read / update / photo upload).

Authentication: `Authorization: Bearer dsa_<prefix>_<secret>` (create keys with
`python manage.py create_api_key --name "..."`). Every write supports `?dry_run=1`, which validates exactly like a
real call but saves nothing. There is deliberately no delete endpoint: removal stays in the admin.
Full usage guide: docs/HOTELS_API.md
"""
import json
import logging
import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone, translation
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt

from ClientRequests.antispam import get_client_ip, hit_rate_limit

from .models import ApiKey, Hotel, HotelImage

logger = logging.getLogger('hotels.api')

MAX_JSON_BYTES = 1_000_000
MAX_BULK = 25
MAX_PHOTOS_PER_HOTEL = 12
MAX_PHOTO_BYTES = 8 * 1024 * 1024
MIN_PHOTO_WIDTH = 640
MAX_PHOTO_PIXELS = 50_000_000
ALLOWED_FORMATS = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}
RATE_LIMITS = [(60, 60), (600, 3600)]          # per API key: 60/minute, 600/hour
AUTH_FAIL_LIMIT, AUTH_FAIL_WINDOW = 10, 600    # per IP: 10 bad tokens in 10 minutes -> blocked

PUBLIC_FIELDS = ['name', 'country', 'location', 'property_type', 'star_rating', 'rooms', 'summary', 'description',
                 'price_per_night', 'max_guests', 'meal_plan', 'amenities', 'child_policy', 'is_published',
                 'is_featured']
INTERNAL_FIELDS = ['contact_person', 'email', 'phone_number', 'contract_validity', 'remarks']
TEXT_FIELDS = ['name', 'country', 'location', 'summary', 'description', 'amenities', 'child_policy',
               'contact_person', 'phone_number', 'remarks']


# ----------------------------------------------------------------------------- plumbing
def reply(data, status=200):
    response = JsonResponse(data, status=status, json_dumps_params={'indent': 2})
    response['Cache-Control'] = 'no-store'
    return response


def error(message, status, **extra):
    return reply({'ok': False, 'error': message, **extra}, status)


def api_view(*methods, public=False):
    """Token auth + throttling + method check for an API endpoint."""
    def decorator(view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            if request.method not in methods:
                response = error(f'Method {request.method} not allowed here.', 405)
                response['Allow'] = ', '.join(methods)
                return response
            if public:
                return view(request, None, *args, **kwargs)

            ip = get_client_ip(request)
            fail_key = f'hotelsapi:fail:{ip}'
            if (cache.get(fail_key) or 0) >= AUTH_FAIL_LIMIT:
                return error('Too many failed attempts. Try again later.', 429)
            header = request.META.get('HTTP_AUTHORIZATION', '')
            token = header[7:].strip() if header.lower().startswith('bearer ') else ''
            key = ApiKey.authenticate(token)
            if key is None:
                cache.set(fail_key, (cache.get(fail_key) or 0) + 1, AUTH_FAIL_WINDOW)
                return error('Missing, invalid or revoked API key.', 401)
            wait = hit_rate_limit(f'key-{key.prefix}', 'hotels-api', RATE_LIMITS)
            if wait:
                response = error('Rate limit exceeded.', 429)
                response['Retry-After'] = str(wait)
                return response
            now = timezone.now()
            if not key.last_used_at or (now - key.last_used_at).total_seconds() > 60:
                ApiKey.objects.filter(pk=key.pk).update(last_used_at=now)
            request.api_key = key
            return view(request, key, *args, **kwargs)
        wrapper.__name__ = view.__name__

        def english(request, *args, **kwargs):
            # The API always reads and writes the English text (modeltranslation uses the active language).
            with translation.override('en'):
                return wrapper(request, *args, **kwargs)
        english.__name__ = view.__name__
        english.csrf_exempt = True
        return english
    return decorator


def read_payload(request):
    """Return (data_dict, files) from a JSON body or a multipart request with a JSON `data` field."""
    content_type = request.content_type or ''
    if content_type.startswith('multipart/'):
        raw, files = request.POST.get('data', ''), request.FILES.getlist('photos')
    else:
        if len(request.body) > MAX_JSON_BYTES:
            raise ValueError('Request body too large (max 1 MB).')
        raw, files = request.body.decode('utf-8', 'replace'), []
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno}).')
    if not isinstance(data, dict):
        raise ValueError('The JSON body must be an object.')
    return data, files


def truthy(request, name):
    return request.GET.get(name, '').lower() in ('1', 'true', 'yes')


# ----------------------------------------------------------------------------- validation
def _choice(value, choices):
    """Accept either the stored key or the human label, case-insensitively."""
    if value in (None, ''):
        return value
    text = str(value).strip().lower()
    for key, label in choices:
        if text in (str(key).lower(), str(label).lower()):
            return key
    return value


def normalise(data):
    clean = {k: v for k, v in data.items() if k in PUBLIC_FIELDS + INTERNAL_FIELDS}
    if isinstance(clean.get('amenities'), (list, tuple)):
        clean['amenities'] = '\n'.join(str(a).strip() for a in clean['amenities'] if str(a).strip())
    clean['property_type'] = _choice(clean.get('property_type'), Hotel.TYPE_CHOICES) if 'property_type' in clean else None
    for field, choices in (('rooms', Hotel.ROOMS_CHOICES), ('meal_plan', Hotel.MEAL_CHOICES)):
        if field in clean:
            clean[field] = _choice(clean[field], choices)
    if not clean.get('property_type'):
        clean.pop('property_type', None)
    for field in TEXT_FIELDS:
        if isinstance(clean.get(field), str):
            clean[field] = strip_tags(clean[field]).strip()
    if isinstance(clean.get('country'), str):
        clean['country'] = clean['country'].title()
    if isinstance(clean.get('price_per_night'), str):
        clean['price_per_night'] = clean['price_per_night'].replace('$', '').replace(',', '').strip()
    return clean


class HotelApiForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = PUBLIC_FIELDS + INTERNAL_FIELDS

    def clean_price_per_night(self):
        price = self.cleaned_data.get('price_per_night')
        if price is not None and not Decimal('0') < price < Decimal('100000'):
            raise forms.ValidationError('Price must be between 0 and 100,000 (USD per night).')
        return price

    def clean_amenities(self):
        lines = [l for l in (self.cleaned_data.get('amenities') or '').splitlines() if l.strip()]
        if len(lines) > 40 or any(len(l) > 80 for l in lines):
            raise forms.ValidationError('At most 40 amenities of up to 80 characters each.')
        return '\n'.join(lines)

    def clean_description(self):
        text = self.cleaned_data.get('description') or ''
        if len(text) > 8000:
            raise forms.ValidationError('Description is too long (max 8000 characters).')
        return text

    def clean_max_guests(self):
        guests = self.cleaned_data.get('max_guests')
        if guests is not None and not 1 <= guests <= 60:
            raise forms.ValidationError('Max guests must be between 1 and 60.')
        return guests


def current_values(hotel):
    values = {f: getattr(hotel, f) for f in PUBLIC_FIELDS + INTERNAL_FIELDS}
    values['contract_validity'] = hotel.contract_validity.isoformat() if hotel.contract_validity else ''
    return values


def validate(data, instance=None):
    """Return (form, errors). For updates, missing fields keep their current value."""
    payload = normalise(data)
    if instance is None:
        payload.setdefault('is_published', True)
        payload.setdefault('is_featured', False)
        for field in ('property_type', 'star_rating', 'max_guests'):       # model defaults when not supplied
            payload.setdefault(field, Hotel._meta.get_field(field).default)
        form = HotelApiForm(payload)
        for field in ('name', 'country', 'location'):
            if not str(payload.get(field) or '').strip():
                form.add_error(field, 'This field is required.')
    else:
        form = HotelApiForm({**current_values(instance), **payload}, instance=instance)
    errors = {f: [str(e) for e in errs] for f, errs in form.errors.items()}
    unknown = sorted(set(data) - set(PUBLIC_FIELDS) - set(INTERNAL_FIELDS) - {'photos'})
    if unknown:
        errors['_unknown_fields'] = [f'Ignored/unknown fields: {", ".join(unknown)}']
    return form, {k: v for k, v in errors.items() if k != '_unknown_fields'}, unknown


def find_duplicate(cleaned):
    return Hotel.objects.filter(name__iexact=cleaned['name'], location__iexact=cleaned['location'],
                                country__iexact=cleaned['country']).first()


# ----------------------------------------------------------------------------- photos
def check_photo(upload):
    """Validate an uploaded file is a real, reasonably sized JPEG/PNG/WebP image. Returns (extension, None) or (None, why)."""
    from PIL import Image
    if upload.size > MAX_PHOTO_BYTES:
        return None, f'{upload.name}: larger than {MAX_PHOTO_BYTES // 1048576} MB.'
    try:
        with Image.open(upload) as img:
            fmt, (width, height) = img.format, img.size
            img.verify()
    except Exception:
        return None, f'{upload.name}: not a valid image.'
    finally:
        upload.seek(0)
    if fmt not in ALLOWED_FORMATS:
        return None, f'{upload.name}: format {fmt} not allowed (use JPEG, PNG or WebP).'
    if width < MIN_PHOTO_WIDTH:
        return None, f'{upload.name}: too small ({width}px wide; minimum {MIN_PHOTO_WIDTH}px).'
    if width * height > MAX_PHOTO_PIXELS:
        return None, f'{upload.name}: too many pixels.'
    return ALLOWED_FORMATS[fmt], None


def attach_photos(hotel, files, captions=None, dry_run=False):
    """Validate and (unless dry_run) save photos. Raises ValueError listing every problem."""
    existing = hotel.images.count() if hotel.pk else 0
    problems, checked = [], []
    if existing + len(files) > MAX_PHOTOS_PER_HOTEL:
        problems.append(f'A hotel can have at most {MAX_PHOTOS_PER_HOTEL} photos '
                        f'({existing} already, {len(files)} sent).')
    for upload in files:
        ext, why = check_photo(upload)
        (problems.append(why) if why else checked.append((upload, ext)))
    if problems:
        raise ValueError(problems)
    if dry_run:
        return len(checked)
    captions = captions or []
    for i, (upload, ext) in enumerate(checked):
        number = existing + i + 1
        upload.name = f'{hotel.slug}-{number}.{ext}'
        HotelImage.objects.create(hotel=hotel, image=upload, order=number,
                                  caption=(captions[i] if i < len(captions) else f'{hotel.name} - photo {number}')[:200],
                                  is_featured=(existing == 0 and i == 0))
    return len(checked)


# ----------------------------------------------------------------------------- serialisation
def serialise(hotel, request, detail=False):
    data = {
        'id': hotel.pk, 'slug': hotel.slug, 'name': hotel.name, 'country': hotel.country, 'location': hotel.location,
        'property_type': hotel.property_type, 'star_rating': hotel.star_rating, 'is_published': hotel.is_published,
        'is_featured': hotel.is_featured, 'price_per_night': str(hotel.price_per_night) if hotel.price_per_night is not None else None,
        'max_guests': hotel.max_guests, 'photos': hotel.images.count(),
        'url': request.build_absolute_uri(hotel.get_absolute_url()),
    }
    if detail:
        data.update({f: getattr(hotel, f) for f in ('rooms', 'summary', 'description', 'meal_plan', 'amenities', 'child_policy')})
        data['amenities'] = hotel.amenity_list
        data['internal'] = {f: (str(getattr(hotel, f)) if getattr(hotel, f) else '') for f in INTERNAL_FIELDS}
        data['photo_urls'] = [request.build_absolute_uri(i.image.url) for i in hotel.images.all()]
    return data


# ----------------------------------------------------------------------------- endpoints
@api_view('GET', public=True)
def schema(request, key):
    """Self-describing list of fields and allowed values (public, contains no data)."""
    return reply({
        'ok': True, 'version': 1, 'auth': 'Authorization: Bearer <api key>',
        'required_fields': ['name', 'country', 'location'],
        'fields': {
            'name': 'text, max 120', 'country': 'text, e.g. Kenya', 'location': 'text, town/area, max 100',
            'property_type': [k for k, _ in Hotel.TYPE_CHOICES] + ['(labels accepted too)'],
            'star_rating': '1-5 (default 4)', 'rooms': [k for k, _ in Hotel.ROOMS_CHOICES if k],
            'summary': 'one line, max 220', 'description': 'text, max 8000',
            'price_per_night': 'USD number, starting rate', 'max_guests': 'integer 1-60 (default 2)',
            'meal_plan': [k for k, _ in Hotel.MEAL_CHOICES if k], 'amenities': 'list of strings (or newline text), max 40',
            'child_policy': 'text', 'is_published': 'true/false (default true)', 'is_featured': 'true/false (default false)',
            'internal (never shown publicly)': INTERNAL_FIELDS,
        },
        'photos': {'how': 'multipart/form-data: field "data" (JSON) + one or more "photos" files',
                   'rules': f'JPEG/PNG/WebP, >= {MIN_PHOTO_WIDTH}px wide, <= {MAX_PHOTO_BYTES // 1048576} MB each, '
                            f'max {MAX_PHOTOS_PER_HOTEL} per hotel'},
        'options': {'dry_run': '?dry_run=1 validates and returns what would happen, saving nothing'},
        'bulk': {'body': '{"hotels": [ {...}, {...} ]}', 'max': MAX_BULK},
    })


@api_view('GET', 'POST')
def hotels_collection(request, key):
    if request.method == 'GET':
        qs = Hotel.objects.all().prefetch_related('images')
        for param, field in (('country', 'country__iexact'), ('property_type', 'property_type'), ('q', 'name__icontains')):
            if request.GET.get(param):
                qs = qs.filter(**{field: request.GET[param]})
        try:
            limit = min(max(int(request.GET.get('limit', 100)), 1), 500)
        except ValueError:
            limit = 100
        return reply({'ok': True, 'count': qs.count(), 'hotels': [serialise(h, request) for h in qs[:limit]]})

    dry_run = truthy(request, 'dry_run')
    try:
        data, files = read_payload(request)
    except ValueError as exc:
        return error(str(exc), 400)

    if 'hotels' in data:                                    # ---- bulk
        items = data['hotels']
        if not isinstance(items, list) or not items:
            return error('"hotels" must be a non-empty list.', 400)
        if len(items) > MAX_BULK:
            return error(f'At most {MAX_BULK} hotels per request.', 400)
        results = [create_one(request, item if isinstance(item, dict) else {}, [], dry_run) for item in items]
        summary = {s: sum(1 for r in results if r['status'] == s) for s in ('created', 'would_create', 'duplicate', 'invalid')}
        logger.info('API %s bulk by key %s: %s', 'dry-run' if dry_run else 'write', key.name, summary)
        return reply({'ok': True, 'dry_run': dry_run, 'summary': summary, 'results': results})

    result = create_one(request, data, files, dry_run)
    status = {'created': 201, 'would_create': 200, 'duplicate': 409, 'invalid': 400}[result['status']]
    return reply({'ok': status < 400, 'dry_run': dry_run, **result}, status)


def create_one(request, data, files, dry_run):
    form, errors, unknown = validate(data)
    if errors:
        return {'status': 'invalid', 'name': str(data.get('name', '')), 'errors': errors}
    cleaned = form.cleaned_data
    duplicate = find_duplicate(cleaned)
    if duplicate:
        return {'status': 'duplicate', 'name': cleaned['name'], 'error': 'A hotel with this name, location and country already exists.',
                'existing': serialise(duplicate, request)}
    try:
        with transaction.atomic():
            hotel = form.save(commit=False)
            if dry_run:
                photos = attach_photos(Hotel(), files, dry_run=True) if files else 0
                return {'status': 'would_create', 'name': cleaned['name'], 'photos_valid': photos,
                        'ignored_fields': unknown}
            hotel.save()
            photos = attach_photos(hotel, files) if files else 0
    except ValueError as exc:
        return {'status': 'invalid', 'name': cleaned['name'], 'errors': {'photos': exc.args[0]}}
    logger.info('API created hotel %s (%s) via key %s', hotel.slug, hotel.pk, request.api_key.name)
    return {'status': 'created', 'hotel': serialise(hotel, request, detail=True), 'photos_added': photos,
            'ignored_fields': unknown}


@api_view('GET', 'PATCH')
def hotel_detail(request, key, slug):
    hotel = Hotel.objects.filter(slug=slug).prefetch_related('images').first()
    if not hotel:
        return error('Hotel not found.', 404)
    if request.method == 'GET':
        return reply({'ok': True, 'hotel': serialise(hotel, request, detail=True)})
    try:
        data, _ = read_payload(request)
    except ValueError as exc:
        return error(str(exc), 400)
    form, errors, unknown = validate(data, instance=hotel)
    if errors:
        return error('Validation failed.', 400, errors=errors)
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_update',
                      'changes': sorted(k for k in form.changed_data), 'ignored_fields': unknown})
    changed = sorted(form.changed_data)
    hotel = form.save()
    logger.info('API updated hotel %s fields %s via key %s', hotel.slug, changed, key.name)
    return reply({'ok': True, 'status': 'updated', 'changed': changed, 'hotel': serialise(hotel, request, detail=True),
                  'ignored_fields': unknown})


@api_view('POST')
def hotel_photos(request, key, slug):
    hotel = Hotel.objects.filter(slug=slug).first()
    if not hotel:
        return error('Hotel not found.', 404)
    files = request.FILES.getlist('photos')
    if not files:
        return error('Send multipart/form-data with one or more files in the "photos" field.', 400)
    captions = []
    if request.POST.get('captions'):
        try:
            captions = [str(c) for c in json.loads(request.POST['captions'])]
        except (ValueError, TypeError):
            return error('"captions" must be a JSON list of strings.', 400)
    dry_run = truthy(request, 'dry_run')
    try:
        with transaction.atomic():
            added = attach_photos(hotel, files, captions, dry_run)
    except ValueError as exc:
        return error('Photo validation failed.', 400, errors=exc.args[0])
    if not dry_run:
        logger.info('API added %s photo(s) to hotel %s via key %s', added, hotel.slug, key.name)
    return reply({'ok': True, 'dry_run': dry_run, 'photos_added' if not dry_run else 'photos_valid': added,
                  'hotel': serialise(hotel, request)}, 200 if dry_run else 201)
