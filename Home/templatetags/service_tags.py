from django import template
from django.urls import reverse

register = template.Library()

# keyword in the service name -> url name; anything else (e.g. visa processing) goes to the contact form
_PAGES = (('wildlife', 'african_wildlife_tours'), ('hotel', 'hotels'), ('airport', 'airport_transfers'),
          ('partner', 'travel_partnerships'), ('tailor', 'holiday_tailor_made_tours'))


@register.filter
def service_url(service):
    name = (getattr(service, 'name_en', None) or getattr(service, 'name', '') or '').lower()
    for key, url_name in _PAGES:
        if key in name:
            return reverse(url_name)
    return reverse('contact')
