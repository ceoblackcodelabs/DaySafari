"""JSON API to add / list guest testimonials (no edit, no delete).

POST /api/v1/testimonials/  JSON {"name": "...", "feedback": "...", "location": "", "star_rating": 5}. ?dry_run=1 validates only.
                            An identical name + feedback is never added twice (returns status "exists").
GET  /api/v1/testimonials/  lists the latest testimonials.
"""
from django.db import transaction

from Hotels.api import api_view, error, read_payload, reply, truthy

from .models import Testimonials


def serialise(t):
    return {'id': t.pk, 'name': t.name, 'location': t.location, 'feedback': t.feedback, 'star_rating': t.star_rating}


@api_view('GET', 'POST')
def testimonials(request, key):
    if request.method == 'GET':
        items = [serialise(t) for t in Testimonials.objects.all()[:100]]
        return reply({'ok': True, 'count': len(items), 'testimonials': items})
    try:
        data, _ = read_payload(request)
    except ValueError as exc:
        return error(str(exc), 400)
    errors = {}
    name = ' '.join(str(data.get('name') or '').split())[:100]
    feedback = str(data.get('feedback') or '').strip()[:2000]
    location = ' '.join(str(data.get('location') or '').split())[:100]
    try:
        stars = int(data.get('star_rating', 5))
        if not 1 <= stars <= 5:
            raise ValueError
    except (TypeError, ValueError):
        stars = 5
        errors['star_rating'] = ['Must be a whole number from 1 to 5.']
    if not name:
        errors['name'] = ['The guest name is required.']
    if len(feedback) < 10:
        errors['feedback'] = ['The review text is required (at least 10 characters).']
    if errors:
        return error('Validation failed.', 400, errors=errors)
    existing = Testimonials.objects.filter(name__iexact=name, feedback=feedback).first()
    if existing:
        return reply({'ok': True, 'status': 'exists', 'testimonial': serialise(existing)})
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_create', 'name': name})
    with transaction.atomic():
        t = Testimonials.objects.create(name=name, location=location, feedback=feedback, star_rating=stars)
    return reply({'ok': True, 'status': 'created', 'testimonial': serialise(t)}, 201)
