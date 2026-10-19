from . import content

_NAV = {
    'destinations': [d for d in content.DESTINATIONS.values() if d['menu']],
    'cruises': content.CRUISE_MENU,
}


def nav(request):
    return {'nav': _NAV, 'reviews_url': content.GOOGLE_REVIEWS_URL}
