import re
import time
from datetime import date, timedelta
from unittest import mock

from django.core import signing
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from Accomodations.models import AirBNB
from ClientRequests import antispam
from ClientRequests.models import Bookings, Contact
from Home.models import Blogs, Trekking
from Places.models import AwesomePackages, Destinations, DestinationsCategory

LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


def stamp(age=10):
    """A valid, signed form timestamp that is `age` seconds old."""
    return signing.dumps(int(time.time()) - age, salt=antispam.TS_SALT)


@override_settings(CACHES=LOCMEM, ALLOWED_HOSTS=['*'])
class LeadFormTests(TestCase):
    """Every public form must save the lead, notify staff and resist bots."""

    @classmethod
    def setUpTestData(cls):
        cat = DestinationsCategory.objects.create(location='Kenya', category='Parks')
        cls.dest = Destinations.objects.create(category=cat, name='Amboseli', description='d', price=100)
        cls.trek = Trekking.objects.create(name='Mt Kenya', location='Kenya', days=4, price=500, persons=6,
                                           description='d', category='Mt-Kenya')
        cls.bnb = AirBNB.objects.create(location='Nairobi', title='Flat', max_guests=4)
        cls.future = (date.today() + timedelta(days=30)).isoformat()
        cls.later = (date.today() + timedelta(days=33)).isoformat()

    def setUp(self):
        cache.clear()  # rate-limit/ban state must not leak between tests
        self.notify = mock.patch('ClientRequests.views.notify_staff_of_lead').start()
        mock.patch('Home.views.notify_staff_of_lead', self.notify).start()
        mock.patch('Accomodations.views.notify_staff_of_lead', self.notify).start()
        for target in ('ClientRequests.views.send_booking_confirmation', 'ClientRequests.views.send_contact_response',
                       'Home.views.send_booking_confirmation', 'Accomodations.views.send_booking_confirmation'):
            mock.patch(target).start()
        self.addCleanup(mock.patch.stopall)

    def person(self, **extra):
        return {'name': 'Jane Doe', 'email': 'jane@gmail.com', 'phone': '+254 712 345 678',
                'form_ts': stamp(), **extra}

    def post(self, url, ip='10.0.0.1', **data):
        return self.client.post(url, data, REMOTE_ADDR=ip)

    # ---- the five lead paths ------------------------------------------------
    def test_contact_form_saves_and_notifies(self):
        r = self.post(reverse('contact'), **self.person(subject='Quote', message='Five adults in October'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Contact.objects.count(), 1)
        self.notify.assert_called_once()

    def test_booking_page_saves_safari_lead(self):
        r = self.post(reverse('booking_create'), **self.person(destination=self.dest.pk, persons=2, date=self.future))
        self.assertEqual(r.status_code, 302)
        booking = Bookings.objects.get()
        self.assertEqual((booking.booking_type, booking.status, booking.destination), ('safari', 'new', self.dest))
        self.notify.assert_called_once()

    def test_home_page_booking_form_saves_lead(self):
        r = self.post(reverse('home'), **self.person(destination=self.dest.pk, persons=1, date=self.future))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Bookings.objects.count(), 1)
        self.notify.assert_called_once()

    def test_trekking_form_saves_lead(self):
        r = self.post(reverse('kili_detail', args=[self.trek.pk]), **self.person(persons=2, date=self.future))
        self.assertEqual(r.status_code, 302)
        booking = Bookings.objects.get()
        self.assertEqual((booking.booking_type, booking.trekking_package), ('trekking', self.trek))
        self.assertEqual(booking.item_name, str(self.trek))
        self.notify.assert_called_once()

    def test_airbnb_form_saves_lead(self):
        r = self.post(reverse('bnb_detail', args=[self.bnb.pk]),
                      **self.person(persons=2, date=self.future, check_out=self.later))
        self.assertEqual(r.status_code, 302)
        booking = Bookings.objects.get()
        self.assertEqual((booking.booking_type, booking.airbnb, str(booking.check_out)), ('airbnb', self.bnb, self.later))
        self.notify.assert_called_once()

    def test_airbnb_checkout_must_follow_checkin(self):
        r = self.post(reverse('bnb_detail', args=[self.bnb.pk]),
                      **self.person(persons=2, date=self.later, check_out=self.future))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Bookings.objects.count(), 0)

    # ---- bot protection -----------------------------------------------------
    def test_scanner_payload_is_rejected(self):
        r = self.post(reverse('booking_create'), name="xsjyBldb' OR 1=1--", email='email@example.com',
                      phone="555-666-0606'\"", destination=self.dest.pk, persons=1, date=self.future,
                      form_ts=stamp())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Bookings.objects.count(), 0)

    def test_honeypot_blocks_bot_and_bans_ip(self):
        url = reverse('contact')
        r = self.post(url, ip='6.6.6.6', **self.person(subject='x', message='y', website='http://spam'))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Contact.objects.count(), 0)
        again = self.post(url, ip='6.6.6.6', **self.person(subject='x', message='y'))
        self.assertEqual(again.status_code, 429)           # banned
        other = self.post(url, ip='6.6.6.7', **self.person(subject='x', message='y'))
        self.assertEqual(other.status_code, 302)           # other visitors unaffected

    def test_instant_submission_is_a_bot(self):
        r = self.post(reverse('contact'), **self.person(subject='x', message='y', form_ts=stamp(age=0)))
        self.assertEqual(r.status_code, 400)

    def test_missing_or_forged_timestamp_is_rejected(self):
        for ts in ('', 'forged'):
            r = self.post(reverse('contact'), ip=f'7.7.7.{len(ts)}', **self.person(subject='x', message='y', form_ts=ts))
            self.assertEqual(r.status_code, 400)
        self.assertEqual(Contact.objects.count(), 0)

    def test_link_spam_and_html_rejected(self):
        for msg in ('see http://a.example http://b.example', '<a href="x">buy</a>'):
            r = self.post(reverse('contact'), ip='8.8.8.8', **self.person(subject='x', message=msg))
            self.assertEqual(r.status_code, 200)
        self.assertEqual(Contact.objects.count(), 0)

    def test_throwaway_email_rejected(self):
        r = self.post(reverse('contact'), **self.person(email='x@notboxletters.com', subject='x', message='y'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Contact.objects.count(), 0)

    def test_rate_limit_blocks_flooding_ip(self):
        codes = [self.post(reverse('contact'), ip='9.9.9.9', **self.person(subject='s', message='m')).status_code
                 for _ in range(6)]
        self.assertEqual(codes[:3], [302, 302, 302])
        self.assertTrue(all(c == 429 for c in codes[3:]), codes)

    def test_real_names_with_apostrophes_and_hyphens_are_accepted(self):
        r = self.post(reverse('contact'), **self.person(name="Mary O'Brien-Smith", subject='Hi', message='Hello'))
        self.assertEqual(r.status_code, 302)


@override_settings(CACHES=LOCMEM, ALLOWED_HOSTS=['*'])
class SiteHealthTests(TestCase):
    """Smoke tests: every public page renders, with no broken template output."""

    @classmethod
    def setUpTestData(cls):
        cat = DestinationsCategory.objects.create(location='Kenya', category='Parks')
        cls.dest = Destinations.objects.create(category=cat, name='Amboseli', description='d', price=100)
        cls.package = AwesomePackages.objects.create(name='Big Five', location='Kenya', days=5, price=900,
                                                     persons=4, description='<p>Great trip</p>')
        cls.trek = Trekking.objects.create(name='Mt Kenya', location='Kenya', days=4, price=500, persons=6,
                                           description='d', category='Mt-Kenya')
        cls.bnb = AirBNB.objects.create(location='Nairobi', title='Flat')
        cls.blog = Blogs.objects.create(title='Tips', author='Mr Days', content='<p>Body</p>')

    def setUp(self):
        cache.clear()

    def urls(self):
        static = ['home', 'about', 'services', 'packages', 'faq', 'gallary', 'blog', 'brochures', 'contact',
                  'booking_create', 'airbnb', 'cruises', 'airline', 'east_africa_tours', 'south_africa_tours',
                  'west_africa_tours', 'international_tours', 'african_wildlife_tours',
                  'holiday_tailor_made_tours', 'airport_transfers', 'travel_partnerships', 'trekking_kenya',
                  'trekking_kilimanjaro', 'trekking_meru', 'trekking_longonot', 'trekking_suswa',
                  'legal_notice', 'privacy_policy', 'terms_and_conditions', 'cookie_policy', 'sitemap_page']
        urls = [reverse(n) for n in static]
        urls += [self.package.get_absolute_url(), reverse('destination_detail', args=[self.dest.pk]),
                 reverse('kili_detail', args=[self.trek.pk]), reverse('bnb_detail', args=[self.bnb.pk]),
                 reverse('blog_detail', args=[self.blog.slug])]
        return urls

    def test_every_public_page_renders_cleanly(self):
        for url in self.urls():
            with self.subTest(url=url):
                r = self.client.get(url)
                self.assertEqual(r.status_code, 200)
                html = r.content.decode()
                self.assertNotRegex(html, r'\{%|%\}|\{\{', 'unrendered template code leaked into the page')
                self.assertNotIn('%7B%', html)
                self.assertEqual(len(re.findall(r'<meta name="description"', html)), 1)
                self.assertIn('hreflang="x-default"', html)

    def test_pages_have_unique_meta_descriptions(self):
        seen = {}
        for url in self.urls():
            html = self.client.get(url).content.decode()
            desc = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
            seen.setdefault(desc, []).append(url)
        self.assertEqual({d: u for d, u in seen.items() if len(u) > 1}, {})

    def test_sitemap_and_robots(self):
        r = self.client.get('/sitemap.xml')
        self.assertEqual(r.status_code, 200)
        self.assertIn(self.package.slug, r.content.decode())
        robots = self.client.get('/robots.txt')
        self.assertContains(robots, 'Sitemap: https://daysafarisadventures.co.ke/sitemap.xml')

    def test_unknown_page_uses_custom_404(self):
        self.assertEqual(self.client.get('/en/no-such-page/').status_code, 404)

    def test_chatbot_test_endpoints_require_staff(self):
        for name in ('testchatbot', 'test_github_api'):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302)           # redirected to login, nothing leaked

    def test_chatbot_api_is_rate_limited(self):
        with mock.patch('ChatBot.views.get_ai_response', return_value='hi'), \
                mock.patch('ChatBot.views.load_prompt_template', return_value=''):
            codes = [self.client.post(reverse('chatbot_api'), '{"message": "hello"}',
                                      content_type='application/json', REMOTE_ADDR='4.4.4.4').status_code
                     for _ in range(10)]
        self.assertEqual(codes[:8], [200] * 8)
        self.assertEqual(codes[8], 429)
