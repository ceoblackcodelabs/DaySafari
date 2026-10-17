"""JSON API to read and improve the packages' text and SEO (title, description, itinerary days).

Same authentication as the hotels API: `Authorization: Bearer dsa_<prefix>_<secret>`. Writes support `?dry_run=1`.
There is no delete endpoint. Prices, images and the web address (slug) are never changed here.
When an English text changes, the other languages of that same field are cleared so the page shows the new English
text until a translation is supplied (modeltranslation falls back to English).
"""
import logging

from django.conf import settings
from django.db import transaction

from Hotels.api import api_view, error, read_payload, reply, truthy

from .models import AwesomePackages, Itinerary

logger = logging.getLogger('hotels.api')

PACKAGE_TEXT = {'name': 100, 'location': 100, 'seo_title': 70, 'seo_description': 170, 'description': 20000}
DAY_TEXT = {'title': 200, 'description': 4000, 'activities': 1000, 'accommodation': 200}
MEALS = [k for k, _ in Itinerary.MEAL_CHOICES]
OTHER_LANGS = [code for code, _ in settings.LANGUAGES if code != 'en']


def _forget_other_languages(obj, fields):
    for f in fields:
        for lang in OTHER_LANGS:
            if hasattr(obj, f'{f}_{lang}'):
                setattr(obj, f'{f}_{lang}', None)


def day_json(i):
    return {'day_number': i.day_number, 'title': i.title, 'description': i.description, 'activities': i.activities,
            'accommodation': i.accommodation, 'meals': i.meals}


def serialise(p, request, full=False):
    data = {'id': p.pk, 'slug': p.slug, 'name': p.name, 'category': p.category, 'location': p.location, 'days': p.days,
            'seo_title': p.seo_title, 'seo_description': p.seo_description, 'description_length': len(p.description or ''),
            'itinerary_days': p.itineraries.count(), 'page': request.build_absolute_uri(f'/en/packages/{p.slug}/')}
    if full:
        data['description'] = p.description
        data['itineraries'] = [day_json(i) for i in p.itineraries.all()]
    return data


def validate(data, package):
    errors, clean = {}, {}
    unknown = sorted(set(data) - set(PACKAGE_TEXT) - {'itineraries'})
    for f, limit in PACKAGE_TEXT.items():
        if f in data:
            value = data[f]
            if not isinstance(value, str) or (f in ('name', 'description') and not value.strip()):
                errors[f] = ['Must be non-empty text.' if f in ('name', 'description') else 'Must be text.']
            elif len(value) > limit:
                errors[f] = [f'Too long ({len(value)} > {limit} characters).']
            else:
                clean[f] = value.strip()
    days = []
    if 'itineraries' in data:
        if not isinstance(data['itineraries'], list):
            errors['itineraries'] = ['Must be a list of day objects.']
        else:
            seen = set()
            for n, item in enumerate(data['itineraries']):
                bad = {}
                if not isinstance(item, dict):
                    errors[f'itineraries[{n}]'] = ['Must be an object.']
                    continue
                num = item.get('day_number')
                if not isinstance(num, int) or isinstance(num, bool) or not 1 <= num <= 60:
                    bad['day_number'] = ['Required integer 1-60.']
                elif num in seen:
                    bad['day_number'] = ['Duplicate day_number.']
                else:
                    seen.add(num)
                for f, limit in DAY_TEXT.items():
                    if f in item and (not isinstance(item[f], str) or len(item[f]) > limit):
                        bad[f] = [f'Must be text up to {limit} characters.']
                if 'meals' in item and item['meals'] not in MEALS:
                    bad['meals'] = [f'One of: {", ".join(MEALS)}.']
                if bad:
                    errors[f'itineraries[{n}]'] = bad
                else:
                    days.append(item)
    return clean, days, errors, unknown


@api_view('GET')
def packages_collection(request, key):
    qs = AwesomePackages.objects.order_by('id')
    if request.GET.get('category'):
        qs = qs.filter(category__iexact=request.GET['category'])
    items = [serialise(p, request) for p in qs]
    return reply({'ok': True, 'count': len(items), 'packages': items})


@api_view('GET', 'PATCH')
def package_detail(request, key, slug):
    package = AwesomePackages.objects.filter(slug=slug).first()
    if not package:
        return error('Package not found.', 404)
    if request.method == 'GET':
        return reply({'ok': True, 'package': serialise(package, request, full=True)})
    try:
        data, _ = read_payload(request)
    except ValueError as exc:
        return error(str(exc), 400)
    clean, days, errors, unknown = validate(data, package)
    if errors:
        return error('Validation failed.', 400, errors=errors)
    changed = [f for f, v in clean.items() if getattr(package, f) != v]
    day_changes = []
    existing = {i.day_number: i for i in package.itineraries.all()}
    for item in days:
        current = existing.get(item['day_number'])
        if current is None:
            day_changes.append((item['day_number'], 'create'))
        elif any(f in item and getattr(current, f) != item[f] for f in list(DAY_TEXT) + ['meals']):
            day_changes.append((item['day_number'], 'update'))
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_update', 'changes': changed,
                      'days': [{'day_number': d, 'action': a} for d, a in day_changes], 'ignored_fields': unknown})
    with transaction.atomic():
        for f in changed:
            setattr(package, f, clean[f])
        if changed:
            _forget_other_languages(package, changed)
            package.save()
        for item in days:
            current = existing.get(item['day_number'])
            if current is None:
                current = Itinerary(package=package, day_number=item['day_number'], title=item.get('title', f'Day {item["day_number"]}'),
                                    description=item.get('description', ''))
            touched = []
            for f in list(DAY_TEXT) + ['meals']:
                if f in item and getattr(current, f) != item[f]:
                    setattr(current, f, item[f]); touched.append(f)
            if touched or current.pk is None:
                _forget_other_languages(current, touched)
                current.save()
    logger.info('API updated package %s fields %s days %s via key %s', package.slug, changed, day_changes, key.name)
    return reply({'ok': True, 'status': 'updated', 'changed': changed,
                  'days': [{'day_number': d, 'action': a} for d, a in day_changes],
                  'package': serialise(package, request), 'ignored_fields': unknown})
