"""Load the researched hotels from Hotels/seed/hotels_seed.json.

    python manage.py seed_hotels --dry-run     # validate and show what would happen
    python manage.py seed_hotels               # create the hotels that are not on the site yet
    python manage.py seed_hotels --update      # also refresh text fields of hotels that already exist

Safe to run repeatedly: existing hotels (same name + location + country) are skipped unless --update is given, and
--update never touches photos, publish/featured switches or the internal notes of hotels you have edited by hand.
The `remarks` field holds the research sources and caveats for each hotel (internal, never shown to visitors).
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from Hotels.api import HotelApiForm, find_duplicate, validate

SEED_FILE = Path(__file__).resolve().parents[2] / 'seed' / 'hotels_seed.json'
UPDATABLE = ['summary', 'description', 'price_per_night', 'max_guests', 'meal_plan', 'amenities', 'child_policy',
             'property_type', 'star_rating', 'rooms']


class Command(BaseCommand):
    help = 'Seed the researched hotels (idempotent)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--update', action='store_true', help='Refresh text fields of existing hotels')
        parser.add_argument('--file', default=str(SEED_FILE))

    def handle(self, *args, **opts):
        try:
            hotels = json.loads(Path(opts['file']).read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            raise CommandError(f'Cannot read seed file: {exc}')
        created = updated = skipped = invalid = 0
        for data in hotels:
            form, errors, _ = validate(data)
            if errors:
                invalid += 1
                self.stderr.write(self.style.ERROR(f"INVALID  {data.get('name')}: {errors}"))
                continue
            existing = find_duplicate(form.cleaned_data)
            if existing and not opts['update']:
                skipped += 1
                self.stdout.write(f'exists   {existing.name}')
                continue
            if existing:
                if opts['dry_run']:
                    self.stdout.write(f'would update  {existing.name}')
                    continue
                for field in UPDATABLE:
                    setattr(existing, field, form.cleaned_data[field])
                existing.save()
                updated += 1
                self.stdout.write(self.style.WARNING(f'updated  {existing.name}'))
                continue
            if opts['dry_run']:
                created += 1
                self.stdout.write(f"would create  {form.cleaned_data['name']}")
                continue
            hotel = form.save()
            created += 1
            self.stdout.write(self.style.SUCCESS(f'created  {hotel.name}  ->  /hotels/{hotel.slug}/'))
        label = 'DRY RUN: nothing was saved. ' if opts['dry_run'] else ''
        self.stdout.write(f'{label}{created} created, {updated} updated, {skipped} already present, {invalid} invalid.')
        if invalid:
            raise CommandError('Some hotels in the seed file failed validation.')
