import io
import json
import shutil
import tempfile
from unittest import mock

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from . import api
from .models import ApiKey, Hotel, HotelImage

LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


def png(width=800, height=600, name='photo.png', fmt='PNG'):
    buffer = io.BytesIO()
    Image.new('RGB', (width, height), (180, 90, 40)).save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


GOOD = {
    'name': 'Sarova Mara Game Camp', 'country': 'kenya', 'location': 'Masai Mara', 'property_type': 'Safari Lodge',
    'star_rating': 4, 'price_per_night': '$1,200', 'max_guests': 6, 'meal_plan': 'Full board',
    'summary': 'Tented luxury on the plains.', 'description': '<b>Great</b> camp.<script>alert(1)</script>',
    'amenities': ['Swimming pool', 'Free Wi-Fi', ' '], 'child_policy': 'Children over 5 welcome.',
}


@override_settings(CACHES=LOCMEM, ALLOWED_HOSTS=['*'])
class HotelsApiTests(TestCase):

    def setUp(self):
        cache.clear()
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, True)
        self.settings_override = override_settings(MEDIA_ROOT=self.media)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.key, self.token = ApiKey.create_key('tests')
        self.auth = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    # ---- helpers
    def post(self, data, query='', **extra):
        return self.client.post(f'/api/v1/hotels/{query}', json.dumps(data), content_type='application/json',
                                **{**self.auth, **extra})

    def make(self, **overrides):
        r = self.post({**GOOD, **overrides})
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()['hotel']

    # ---- public schema
    def test_schema_is_public_and_describes_the_api(self):
        r = self.client.get('/api/v1/hotels/schema/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['required_fields'], ['name', 'country', 'location'])
        self.assertIn('lodge', r.json()['fields']['property_type'])

    # ---- authentication
    def test_requests_without_a_valid_key_are_rejected(self):
        self.assertEqual(self.client.get('/api/v1/hotels/').status_code, 401)
        self.assertEqual(self.client.post('/api/v1/hotels/', '{}', content_type='application/json').status_code, 401)
        for bad in ('Bearer nope', 'Bearer dsa_xxxxxxxx_wrong', f'Bearer {self.token}x', 'Basic abc', ''):
            r = self.client.get('/api/v1/hotels/', HTTP_AUTHORIZATION=bad)
            self.assertEqual(r.status_code, 401, bad)
        self.assertEqual(Hotel.objects.count(), 0)

    def test_revoked_key_stops_working_immediately(self):
        self.assertEqual(self.client.get('/api/v1/hotels/', **self.auth).status_code, 200)
        call_command('create_api_key', '--revoke', self.key.prefix)
        self.assertEqual(self.client.get('/api/v1/hotels/', **self.auth).status_code, 401)

    def test_token_is_stored_only_as_a_hash(self):
        self.key.refresh_from_db()
        self.assertNotIn(self.token, self.key.key_hash)
        self.assertNotIn(self.token.split('_', 2)[2], self.key.key_hash)
        self.assertEqual(len(self.key.key_hash), 64)

    def test_repeated_bad_tokens_get_blocked(self):
        codes = [self.client.get('/api/v1/hotels/', HTTP_AUTHORIZATION='Bearer dsa_aaaaaaaa_bad',
                                 REMOTE_ADDR='9.9.9.9').status_code for _ in range(12)]
        self.assertEqual(codes[:10], [401] * 10)
        self.assertEqual(codes[10:], [429, 429])
        # even the right key is refused from that address while it is blocked, but works elsewhere
        self.assertEqual(self.client.get('/api/v1/hotels/', REMOTE_ADDR='9.9.9.9', **self.auth).status_code, 429)
        self.assertEqual(self.client.get('/api/v1/hotels/', REMOTE_ADDR='8.8.8.8', **self.auth).status_code, 200)

    def test_per_key_rate_limit(self):
        with mock.patch.object(api, 'RATE_LIMITS', [(3, 60)]):
            codes = [self.client.get('/api/v1/hotels/', **self.auth).status_code for _ in range(5)]
        self.assertEqual(codes, [200, 200, 200, 429, 429])

    def test_works_without_a_csrf_token_but_only_with_the_key(self):
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        r = strict.post('/api/v1/hotels/', json.dumps(GOOD), content_type='application/json', **self.auth)
        self.assertEqual(r.status_code, 201)

    def test_key_usage_is_recorded_and_delete_is_not_possible(self):
        self.client.get('/api/v1/hotels/', **self.auth)
        self.key.refresh_from_db()
        self.assertIsNotNone(self.key.last_used_at)
        hotel = self.make()
        self.assertEqual(self.client.delete(f"/api/v1/hotels/{hotel['slug']}/", **self.auth).status_code, 405)
        self.assertEqual(Hotel.objects.count(), 1)

    # ---- create
    def test_create_hotel_normalises_and_cleans_input(self):
        hotel = self.make()
        obj = Hotel.objects.get(pk=hotel['id'])
        self.assertEqual((obj.country, obj.property_type, obj.meal_plan), ('Kenya', 'lodge', 'FB'))
        self.assertEqual(str(obj.price_per_night), '1200.00')
        self.assertEqual(obj.amenity_list, ['Swimming pool', 'Free Wi-Fi'])
        self.assertNotIn('<', obj.description)                      # HTML/script stripped
        self.assertTrue(obj.is_published and not obj.is_featured)   # defaults
        self.assertEqual(obj.slug, 'sarova-mara-game-camp-masai')
        self.assertTrue(hotel['url'].endswith('/hotels/sarova-mara-game-camp-masai/'))

    def test_created_hotel_appears_on_the_public_site(self):
        self.make()
        self.assertContains(self.client.get(reverse('hotels')), 'Sarova Mara Game Camp')
        page = self.client.get(Hotel.objects.get().get_absolute_url())
        self.assertContains(page, 'Free Wi-Fi')

    def test_can_create_an_unpublished_draft(self):
        self.make(name='Draft Lodge', is_published=False)
        self.assertNotContains(self.client.get(reverse('hotels')), 'Draft Lodge')

    def test_validation_errors_are_reported_per_field(self):
        r = self.post({'name': '', 'country': 'Kenya', 'star_rating': 9, 'price_per_night': -5,
                       'property_type': 'castle', 'max_guests': 500, 'location': 'X', 'rooms': 'mansion'})
        self.assertEqual(r.status_code, 400)
        errors = r.json()['errors']
        for field in ('name', 'star_rating', 'price_per_night', 'property_type', 'max_guests', 'rooms'):
            self.assertIn(field, errors, field)
        self.assertEqual(Hotel.objects.count(), 0)

    def test_minimal_hotel_needs_only_name_country_location(self):
        r = self.post({'name': 'Tiny Lodge', 'country': 'Kenya', 'location': 'Nakuru'})
        self.assertEqual(r.status_code, 201, r.content)
        hotel = Hotel.objects.get()
        self.assertEqual((hotel.property_type, hotel.star_rating, hotel.max_guests, hotel.is_published), ('hotel', 4, 2, True))

    def test_missing_required_fields(self):
        r = self.post({'summary': 'only a summary'})
        self.assertEqual(sorted(r.json()['errors']), ['country', 'location', 'name'])

    def test_bad_json_and_wrong_shapes(self):
        self.assertEqual(self.client.post('/api/v1/hotels/', '{not json', content_type='application/json', **self.auth).status_code, 400)
        self.assertEqual(self.client.post('/api/v1/hotels/', '[1,2]', content_type='application/json', **self.auth).status_code, 400)
        self.assertEqual(self.post({'hotels': 'x'}).status_code, 400)

    def test_unknown_fields_are_reported_not_fatal(self):
        r = self.post({**GOOD, 'color': 'blue', 'slug': 'hacked', 'id': 5})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()['ignored_fields'], ['color', 'id', 'slug'])
        self.assertNotEqual(Hotel.objects.get().slug, 'hacked')

    def test_duplicates_are_refused_case_insensitively(self):
        self.make()
        r = self.post({**GOOD, 'name': 'SAROVA MARA GAME CAMP', 'location': 'masai mara', 'country': 'KENYA'})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['existing']['slug'], 'sarova-mara-game-camp-masai')
        self.assertEqual(Hotel.objects.count(), 1)

    def test_same_name_in_another_place_is_allowed(self):
        self.make()
        self.make(location='Naivasha')
        self.assertEqual(Hotel.objects.count(), 2)
        self.assertEqual(len({h.slug for h in Hotel.objects.all()}), 2)

    # ---- dry run + bulk
    def test_dry_run_validates_but_saves_nothing(self):
        r = self.post(GOOD, '?dry_run=1')
        self.assertEqual((r.status_code, r.json()['status'], r.json()['dry_run']), (200, 'would_create', True))
        self.assertEqual(Hotel.objects.count(), 0)
        bad = self.post({'name': 'x'}, '?dry_run=1')
        self.assertEqual(bad.status_code, 400)

    def test_bulk_create_reports_each_hotel(self):
        self.make(name='Existing Lodge')
        r = self.post({'hotels': [
            {**GOOD, 'name': 'Alpha Lodge'}, {**GOOD, 'name': 'Existing Lodge'}, {'name': 'Broken'},
            {**GOOD, 'name': 'Beta Camp', 'location': 'Amboseli'},
        ]})
        body = r.json()
        self.assertEqual(body['summary'], {'created': 2, 'would_create': 0, 'duplicate': 1, 'invalid': 1})
        self.assertEqual([x['status'] for x in body['results']], ['created', 'duplicate', 'invalid', 'created'])
        self.assertEqual(Hotel.objects.count(), 3)

    def test_bulk_dry_run_and_limit(self):
        r = self.post({'hotels': [{**GOOD, 'name': 'A'}, {**GOOD, 'name': 'B'}]}, '?dry_run=1')
        self.assertEqual(r.json()['summary']['would_create'], 2)
        self.assertEqual(Hotel.objects.count(), 0)
        too_many = self.post({'hotels': [{**GOOD, 'name': f'H{i}'} for i in range(api.MAX_BULK + 1)]})
        self.assertEqual(too_many.status_code, 400)

    # ---- read + update
    def test_list_filter_and_detail_include_internal_data_only_with_a_key(self):
        self.make(contact_person='Mr Internal', email='sales@camp.example')
        listing = self.client.get('/api/v1/hotels/?country=kenya', **self.auth).json()
        self.assertEqual(listing['count'], 1)
        detail = self.client.get('/api/v1/hotels/sarova-mara-game-camp-masai/', **self.auth).json()['hotel']
        self.assertEqual(detail['internal']['contact_person'], 'Mr Internal')
        self.assertEqual(self.client.get('/api/v1/hotels/nope/', **self.auth).status_code, 404)
        self.assertNotContains(self.client.get(Hotel.objects.get().get_absolute_url()), 'Mr Internal')

    def test_patch_changes_only_the_fields_sent(self):
        hotel = self.make(is_featured=True)
        r = self.client.patch(f"/api/v1/hotels/{hotel['slug']}/", json.dumps({'price_per_night': 950, 'star_rating': 5}),
                              content_type='application/json', **self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(sorted(r.json()['changed']), ['price_per_night', 'star_rating'])
        obj = Hotel.objects.get()
        self.assertEqual((str(obj.price_per_night), obj.star_rating), ('950.00', 5))
        self.assertTrue(obj.is_published and obj.is_featured)        # untouched booleans stay as they were
        self.assertEqual(obj.amenity_list, ['Swimming pool', 'Free Wi-Fi'])
        self.assertEqual(obj.country, 'Kenya')

    def test_patch_validation_and_dry_run(self):
        hotel = self.make()
        url = f"/api/v1/hotels/{hotel['slug']}/"
        bad = self.client.patch(url, json.dumps({'star_rating': 12}), content_type='application/json', **self.auth)
        self.assertEqual(bad.status_code, 400)
        dry = self.client.patch(url + '?dry_run=1', json.dumps({'price_per_night': 1}), content_type='application/json', **self.auth)
        self.assertEqual(dry.json()['status'], 'would_update')
        self.assertEqual(str(Hotel.objects.get().price_per_night), '1200.00')

    # ---- photos
    def test_photo_upload_attaches_photos_and_features_the_first(self):
        hotel = self.make()
        r = self.client.post(f"/api/v1/hotels/{hotel['slug']}/photos/",
                             {'photos': [png(name='a.png'), png(900, 600, 'b.png')], 'captions': json.dumps(['Pool', 'Room'])},
                             **self.auth)
        self.assertEqual(r.status_code, 201, r.content)
        images = list(HotelImage.objects.order_by('order'))
        self.assertEqual([i.caption for i in images], ['Pool', 'Room'])
        self.assertEqual([i.is_featured for i in images], [True, False])
        self.assertTrue(images[0].image.name.startswith('hotels/sarova-mara-game-camp-masai-1'))

    def test_create_with_photos_in_one_multipart_request(self):
        r = self.client.post('/api/v1/hotels/', {'data': json.dumps(GOOD), 'photos': [png(), png(name='2.png')]}, **self.auth)
        self.assertEqual((r.status_code, r.json()['photos_added']), (201, 2))
        self.assertEqual(Hotel.objects.get().images.count(), 2)

    def test_invalid_photos_are_rejected_and_nothing_is_created(self):
        fake = SimpleUploadedFile('x.png', b'not an image', content_type='image/png')
        r = self.client.post('/api/v1/hotels/', {'data': json.dumps(GOOD), 'photos': [png(), fake, png(300, 200, 'small.png')]}, **self.auth)
        self.assertEqual(r.status_code, 400)
        problems = ' '.join(r.json()['errors']['photos'])
        self.assertIn('not a valid image', problems)
        self.assertIn('too small', problems)
        self.assertEqual(Hotel.objects.count(), 0)                    # whole hotel rolled back
        self.assertEqual(HotelImage.objects.count(), 0)

    def test_photo_limits_and_dry_run(self):
        hotel = self.make()
        url = f"/api/v1/hotels/{hotel['slug']}/photos/"
        too_many = self.client.post(url, {'photos': [png(name=f'{i}.png') for i in range(api.MAX_PHOTOS_PER_HOTEL + 1)]}, **self.auth)
        self.assertEqual(too_many.status_code, 400)
        dry = self.client.post(url + '?dry_run=1', {'photos': [png()]}, **self.auth)
        self.assertEqual(dry.status_code, 200)
        self.assertEqual(HotelImage.objects.count(), 0)
        self.assertEqual(self.client.post(url, {}, **self.auth).status_code, 400)

    def test_gif_and_oversized_files_are_refused(self):
        hotel = self.make()
        buffer = io.BytesIO(); Image.new('RGB', (800, 600)).save(buffer, 'GIF')
        gif = SimpleUploadedFile('a.gif', buffer.getvalue(), content_type='image/gif')
        r = self.client.post(f"/api/v1/hotels/{hotel['slug']}/photos/", {'photos': [gif]}, **self.auth)
        self.assertEqual(r.status_code, 400)
        with mock.patch.object(api, 'MAX_PHOTO_BYTES', 100):
            r = self.client.post(f"/api/v1/hotels/{hotel['slug']}/photos/", {'photos': [png()]}, **self.auth)
        self.assertEqual(r.status_code, 400)

    # ---- key management command
    def test_create_api_key_command_prints_token_once_and_it_works(self):
        out = io.StringIO()
        call_command('create_api_key', '--name', 'Another user', stdout=out)
        token = [l.strip() for l in out.getvalue().splitlines() if l.strip().startswith('dsa_')][0]
        self.assertEqual(self.client.get('/api/v1/hotels/', HTTP_AUTHORIZATION=f'Bearer {token}').status_code, 200)
        listing = io.StringIO()
        call_command('create_api_key', '--list', stdout=listing)
        self.assertIn('Another user', listing.getvalue())
        self.assertNotIn(token, listing.getvalue())


@override_settings(CACHES=LOCMEM, ALLOWED_HOSTS=['*'])
class SeedHotelsTests(TestCase):
    """The researched hotels file must always be loadable, idempotent and safe to show publicly."""

    def seed(self, *args):
        out = io.StringIO()
        call_command('seed_hotels', *args, stdout=out)
        return out.getvalue()

    def test_seed_file_is_valid_and_loads(self):
        output = self.seed()
        self.assertIn('0 invalid', output)
        self.assertGreaterEqual(Hotel.objects.count(), 16)
        self.assertEqual(Hotel.objects.filter(is_published=True).count(), Hotel.objects.count())

    def test_dry_run_saves_nothing_and_second_run_is_a_noop(self):
        self.assertIn('DRY RUN', self.seed('--dry-run'))
        self.assertEqual(Hotel.objects.count(), 0)
        self.seed()
        count = Hotel.objects.count()
        self.assertIn('0 created', self.seed())
        self.assertEqual(Hotel.objects.count(), count)

    def test_update_refreshes_text_but_keeps_photos_and_switches(self):
        self.seed()
        hotel = Hotel.objects.get(name='Medina Palms')
        hotel.summary, hotel.is_featured = 'edited by hand', True
        hotel.save()
        HotelImage.objects.create(hotel=hotel, image='hotels/x.jpg')
        self.seed('--update')
        hotel.refresh_from_db()
        self.assertNotEqual(hotel.summary, 'edited by hand')       # text refreshed from the seed file
        self.assertTrue(hotel.is_featured)                         # switches untouched
        self.assertEqual(hotel.images.count(), 1)                  # photos untouched

    def test_addresses_are_unique_clean_and_free_of_repeated_words(self):
        self.seed()
        slugs = list(Hotel.objects.values_list('slug', flat=True))
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertIn('eka-hotel-eldoret', slugs)
        for slug in slugs:
            words = slug.split('-')
            self.assertNotIn('--', slug)
            self.assertLessEqual(len(slug), 80, slug)

    def test_every_seeded_hotel_page_renders_without_leaking_research_notes(self):
        self.seed()
        for hotel in Hotel.objects.all():
            response = self.client.get(hotel.get_absolute_url())
            self.assertEqual(response.status_code, 200, hotel.slug)
            html = response.content.decode()
            self.assertNotIn('SOURCES:', html)                     # internal notes stay internal
            self.assertNotRegex(html, r'\{%|%\}|\{\{')
            self.assertIn(hotel.name.replace('&', '&amp;'), html)

    def test_only_reliable_prices_are_published(self):
        self.seed()
        priced = dict(Hotel.objects.exclude(price_per_night=None).values_list('name', 'price_per_night'))
        self.assertEqual(list(priced), ['Medina Palms'])           # the one official published rate
