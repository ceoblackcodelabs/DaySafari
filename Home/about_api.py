"""JSON API to add pictures to the rotating 'Who we are' image on the home page (create / list; no delete).

POST /api/v1/about-images/  multipart: `data` = {"caption": "...", "order": 0} + file in `image`. ?dry_run=1 validates only.
GET  /api/v1/about-images/  lists the pictures.
"""
from django.db import transaction
from django.utils import timezone

from Hotels.api import api_view, check_photo, error, read_payload, reply, truthy

from .models import AboutImage


def serialise(a, request):
    return {'id': a.pk, 'caption': a.caption, 'order': a.order, 'is_active': a.is_active, 'image_url': request.build_absolute_uri(a.image.url)}


@api_view('GET', 'POST')
def about_images(request, key):
    if request.method == 'GET':
        items = [serialise(a, request) for a in AboutImage.objects.all()[:100]]
        return reply({'ok': True, 'count': len(items), 'images': items})
    if not (request.content_type or '').startswith('multipart/'):
        return error('Send multipart/form-data: JSON "data" plus the picture in "image".', 400)
    try:
        data, _ = read_payload(request)
    except ValueError as exc:
        return error(str(exc), 400)
    upload = request.FILES.get('image')
    errors = {}
    caption = ' '.join(str(data.get('caption') or '').split())[:150]
    try:
        order = min(max(int(data.get('order', 0)), 0), 9999)
    except (TypeError, ValueError):
        order = 0
        errors['order'] = ['Must be a whole number.']
    ext = None
    if not upload:
        errors['image'] = ['The picture is required (multipart field "image").']
    else:
        ext, why = check_photo(upload)
        if why:
            errors['image'] = [why]
    if errors:
        return error('Validation failed.', 400, errors=errors)
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_create', 'caption': caption})
    with transaction.atomic():
        upload.name = f'about-{timezone.now():%Y%m%d%H%M%S%f}.{ext}'
        a = AboutImage.objects.create(image=upload, caption=caption, order=order)
    return reply({'ok': True, 'status': 'created', 'image': serialise(a, request)}, 201)
