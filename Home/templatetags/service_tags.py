from django import template
from django.urls import reverse

register = template.Library()

# keyword in the service name -> (url name, label) of the page that goes deeper on it
_PAGES = (('wildlife', 'african_wildlife_tours', 'Explore wildlife tours'), ('hotel', 'hotels', 'Browse hotels'),
          ('airport', 'airport_transfers', 'See transfer details'), ('partner', 'travel_partnerships', 'See partnerships'),
          ('tailor', 'holiday_tailor_made_tours', 'See tailor-made holidays'))


@register.filter
def service_url(service):
    """Every service card opens that service's own page."""
    return reverse('service_detail', args=[service.pk])


@register.filter
def service_related(service):
    name = (getattr(service, 'name_en', None) or getattr(service, 'name', '') or '').lower()
    for key, url_name, label in _PAGES:
        if key in name:
            return {'url': reverse(url_name), 'label': label}
    return None
