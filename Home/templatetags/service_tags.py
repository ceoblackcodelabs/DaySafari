from django import template
from django.urls import reverse

register = template.Library()

# keyword in the service name -> (url name, label) of the page that goes deeper on it
_PAGES = (('wildlife', 'african_wildlife_tours', 'Explore wildlife tours'), ('hotel', 'hotels', 'Browse hotels'),
          ('airport', 'airport_transfers', 'See transfer details'), ('partner', 'travel_partnerships', 'See partnerships'),
          ('tailor', 'holiday_tailor_made_tours', 'See tailor-made holidays'))


def _match(service):
    name = (getattr(service, 'name_en', None) or getattr(service, 'name', '') or '').lower()
    for key, url_name, label in _PAGES:
        if key in name:
            return url_name, label
    return None


@register.filter
def service_url(service):
    """The existing page for that service; a service with no page of its own (e.g. visa) gets a generic one."""
    hit = _match(service)
    return reverse(hit[0]) if hit else reverse('service_detail', args=[service.pk])


@register.filter
def service_related(service):
    hit = _match(service)
    return {'url': reverse(hit[0]), 'label': hit[1]} if hit else None


_IMAGES = (('wildlife', 'img/elephant.webp'), ('hotel', 'img/hotel.webp'), ('airport', 'img/air.webp'),
           ('partner', 'img/partn.webp'), ('tailor', 'img/tailor.webp'), ('visa', 'img/passport.webp'))


@register.filter
def service_image(service):
    """Fallback picture (a static file) for a service that has no photo uploaded in the admin."""
    name = (getattr(service, 'name_en', None) or getattr(service, 'name', '') or '').lower()
    for key, path in _IMAGES:
        if key in name:
            return path
    return 'img/about-img.webp'
