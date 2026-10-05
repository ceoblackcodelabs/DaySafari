"""Fill in star ratings and inclusions/exclusions for every AwesomePackages row.

Safe to re-run: packages that already have inclusions keep them, and ratings
are only set where missing (0). Use --force to rebuild inclusions/ratings.

    python manage.py seed_package_details [--force]
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from Places.models import AwesomePackages, IncluisiveExcluisive

COMMON_EXCLUDED = [
    'International flights to and from your home country',
    'Visa fees and entry permits (unless stated)',
    'Travel, medical and cancellation insurance',
    'Tips and gratuities for guides and staff',
    'Personal expenses (laundry, souvenirs, phone calls)',
    'Anything not listed under "What\'s Included"',
]

SAFARI = {
    'included': [
        'Airport pick-up and drop-off',
        'Accommodation in lodges/tented camps as per itinerary',
        'Meals as stated in the daily itinerary',
        'Park, conservancy and entry fees',
        'Professional English-speaking driver-guide',
        'Game drives in a 4x4 safari vehicle with pop-up roof',
        'Bottled drinking water during game drives',
        'Government taxes and service charges',
    ],
    'excluded': COMMON_EXCLUDED + ['Optional activities (e.g. hot air balloon safari)'],
}
PRIMATE = {
    'included': ['Gorilla / chimpanzee trekking permits', 'Park entry fees and ranger guides'],
    'excluded': ['Porter fees for trekking (optional)'],
}
SELF_DRIVE = {
    'included': ['Rental car for the whole trip with unlimited mileage', 'Pre-booked guesthouses and lodges',
                 'Printed route notes and maps', '24/7 emergency support line'],
    'excluded': ['Fuel and road tolls', 'Car rental excess/damage deposit', 'Meals not listed in the itinerary'],
}
CULTURE = {
    'included': [
        'Airport transfers',
        'Hotel accommodation with daily breakfast',
        'Private air-conditioned transport with driver',
        'Licensed local English-speaking guide',
        'Entrance fees to sites and museums in the itinerary',
        'Bottled water in the vehicle',
        'Government taxes and service charges',
    ],
    'excluded': COMMON_EXCLUDED + ['Lunches and dinners unless stated'],
}
INTERNATIONAL = {
    'included': [
        'Airport transfers',
        'Hotel accommodation with daily breakfast',
        'Guided sightseeing tours as per itinerary',
        'Entrance tickets to listed attractions',
        'Private/shared air-conditioned transport',
        'Local tour manager / English-speaking guide',
        'Taxes and service charges',
    ],
    'excluded': COMMON_EXCLUDED + ['Lunches and dinners unless stated', 'Optional tours and excursions'],
}
CRUISE = {
    'included': [
        'Cabin accommodation for the full cruise',
        'Main dining room meals and buffet',
        'Onboard entertainment and activities',
        'Port charges and government taxes',
        'Airport/port transfers on arrival and departure',
        'Day-by-day cruise itinerary with port calls',
    ],
    'excluded': COMMON_EXCLUDED + ['Shore excursions (bookable as optional extras)',
                                    'Drinks packages and specialty restaurants',
                                    'Onboard gratuities / service charges'],
}


def profile(pkg):
    name = pkg.name.lower()
    if pkg.category == 'Cruises':
        return CRUISE, []
    if pkg.category == 'International Tours':
        return INTERNATIONAL, []
    if pkg.category in ('West Africa', 'Africa Tours') and not any(k in name for k in ('delta', 'wildlife', 'desert')):
        return CULTURE, []
    extra = []
    if any(k in name for k in ('gorilla', 'primate', 'chimp')):
        extra.append(PRIMATE)
    if 'self drive' in name or 'self-drive' in name:
        extra.append(SELF_DRIVE)
    return SAFARI, extra


def rating(pkg):
    name = pkg.name.lower()
    if any(k in name for k in ('luxury', 'prima', 'okavango', 'sabi sands')):
        return 5
    if 'self drive' in name:
        return 3
    return 4


class Command(BaseCommand):
    help = 'Seed star ratings and inclusions/exclusions for all packages'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Rebuild even where data already exists')

    @transaction.atomic
    def handle(self, *args, **opts):
        force = opts['force']
        rated = filled = 0
        for pkg in AwesomePackages.objects.all():
            if force or not pkg.star_rating:
                pkg.star_rating = rating(pkg)
                pkg.save(update_fields=['star_rating'])
                rated += 1
            if pkg.inclusions.exists() and not force:
                continue
            base, extras = profile(pkg)
            included = list(base['included'])
            excluded = list(base['excluded'])
            for extra in extras:
                included += extra['included']
                excluded += extra['excluded']
            pkg.inclusions.all().delete()
            IncluisiveExcluisive.objects.bulk_create(
                [IncluisiveExcluisive(package=pkg, name=n, is_inclusive=True) for n in included] +
                [IncluisiveExcluisive(package=pkg, name=n, is_inclusive=False) for n in excluded])
            filled += 1
        self.stdout.write(self.style.SUCCESS(f'Ratings set on {rated} packages; inclusions/exclusions added to {filled}.'))
