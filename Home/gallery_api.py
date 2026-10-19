"""JSON API to add pictures to the Gallery (create / list). Same keys as the hotels API; no delete endpoint.

POST /api/v1/gallery/   multipart: `data` = {"name": "...", "category": "<id or name>"} + file in `image`. ?dry_run=1 validates only.
GET  /api/v1/gallery/   lists categories (with counts) and pictures.
"""
import logging

from django.db import transaction
from django.utils import timezone

from Hotels.api import api_view, check_photo, error, read_payload, reply, truthy

from .models import Gallery, GalleryCategory

logger = logging.getLogger('hotels.api')


def find_category(value):
    value = str(value or '').strip()
    if value.isdigit():
        return GalleryCategory.objects.filter(pk=int(value)).first()
    return GalleryCategory.objects.filter(name__iexact=value).first()


def serialise(g, request):
    return {'id': g.pk, 'name': g.name, 'category': g.category.name, 'image_url': request.build_absolute_uri(g.image.url)}


@api_view('GET', 'POST')
def gallery_collection(request, key):
    if request.method == 'GET':
        cats = [{'id': c.pk, 'name': c.name, 'count': c.galleries.count()} for c in GalleryCategory.objects.all()]
        items = [serialise(g, request) for g in Gallery.objects.select_related('category')[:500]]
        return reply({'ok': True, 'categories': cats, 'count': len(items), 'images': items})
    if not (request.content_type or '').startswith('multipart/'):
        return error('Send multipart/form-data: JSON "data" plus the picture in "image".', 400)
    try:
        data, _ = read_payload(request)
    except ValueError as exc:
        return error(str(exc), 400)
    upload = request.FILES.get('image')
    errors = {}
    name = ' '.join(str(data.get('name') or '').split())[:100]
    if not name:
        errors['name'] = ['Required (max 100 characters).']
    category = find_category(data.get('category'))
    if not category:
        errors['category'] = ['Unknown category. Use an id or exact name from GET /api/v1/gallery/.']
    ext = None
    if not upload:
        errors['image'] = ['The picture is required (multipart field "image").']
    else:
        ext, why = check_photo(upload)
        if why:
            errors['image'] = [why]
    if errors:
        return error('Validation failed.', 400, errors=errors)
    if Gallery.objects.filter(category=category, name__iexact=name).exists():
        return error('A picture with this name already exists in that category.', 409)
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_create', 'name': name, 'category': category.name})
    with transaction.atomic():
        upload.name = f'api-{timezone.now():%Y%m%d%H%M%S%f}.{ext}'
        g = Gallery.objects.create(name=name, category=category, image=upload)
    logger.info('API added gallery picture %s (%s) via key %s', g.pk, name, key.name)
    return reply({'ok': True, 'status': 'created', 'image': serialise(g, request)}, 201)


@api_view('POST')
def gallery_image(request, key, pk):
    """Replace the picture of an existing gallery item (multipart field `image`); name and category stay."""
    g = Gallery.objects.select_related('category').filter(pk=pk).first()
    if not g:
        return error('Picture not found.', 404)
    upload = request.FILES.get('image')
    if not upload:
        return error('Send the picture in the multipart field "image".', 400)
    ext, why = check_photo(upload)
    if why:
        return error('Validation failed.', 400, errors={'image': [why]})
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_replace_image'})
    upload.name = f'api-{timezone.now():%Y%m%d%H%M%S%f}.{ext}'
    g.image = upload
    g.save()
    return reply({'ok': True, 'status': 'image_replaced', 'image': serialise(g, request)})
