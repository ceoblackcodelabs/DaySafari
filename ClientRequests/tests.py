import re
import time
from datetime import date, timedelta
from unittest import mock

from django.core import signing
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from Hotels.models import AirBNB, Hotel, HotelImage
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
        self.notify = mock.patch('ClientRequests.views.handle_new_lead').start()
        mock.patch('Home.views.handle_new_lead', self.notify).start()
        mock.patch('Hotels.views.handle_new_lead', self.notify).start()
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
        cls.hotel = Hotel.objects.create(name='Test Lodge', country='Kenya', location='Amboseli', summary='A lodge.',
                                         description='Nice place.', price_per_night=200, max_guests=4)
        cls.blog = Blogs.objects.create(title='Tips', author='Mr Days', content='<p>Body</p>')

    def setUp(self):
        cache.clear()

    def urls(self):
        static = ['home', 'about', 'services', 'packages', 'faq', 'gallary', 'blog', 'brochures', 'contact',
                  'booking_create', 'airbnb', 'cruises', 'airline', 'east_africa_tours', 'south_africa_tours',
                  'west_africa_tours', 'international_tours', 'african_wildlife_tours',
                  'holiday_tailor_made_tours', 'airport_transfers', 'travel_partnerships', 'trekking_kenya',
                  'trekking_kilimanjaro', 'trekking_meru', 'trekking_longonot', 'trekking_suswa', 'hotels',
                  'legal_notice', 'privacy_policy', 'terms_and_conditions', 'cookie_policy', 'sitemap_page']
        urls = [reverse(n) for n in static]
        urls += [self.package.get_absolute_url(), reverse('destination_detail', args=[self.dest.pk]),
                 reverse('kili_detail', args=[self.trek.pk]), reverse('bnb_detail', args=[self.bnb.pk]),
                 self.hotel.get_absolute_url(),
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



@override_settings(CACHES=LOCMEM, ALLOWED_HOSTS=['*'])
class SpamProtectionTests(TestCase):
    """Rotating-IP bots: content/campaign filtering and outbound-email safety."""

    BOT = dict(name='mussymync', email='orrw8102@gmail.com', subject='I promised.',
               message='Photos for my escort application are uploaded. Let me know if they work.')

    def setUp(self):
        cache.clear()

    def test_classifier_flags_known_bot_campaigns(self):
        from ClientRequests.spamfilter import spam_reasons
        samples = [
            self.BOT,
            dict(name='BillyRaw', email='a@b.com', subject='Hello! YOUR_BALANCE_86810.86_USD_GET www',
                 message='TOKENS CREDITED WITHOUT YOUR INVOLVEMENT'),
            dict(name='Ivan', email='i@mail.ru', subject='Ваш билет неизрасходован', message='Новейший тираж'),
            dict(name='Marco', email='m@gmail.com', subject='Quick note about your site',
                 message='Our SEO services can rank your website higher'),
        ]
        for sample in samples:
            with self.subTest(sample['name']):
                self.assertTrue(spam_reasons(count_campaign=False, **sample))

    def test_classifier_keeps_real_enquiries(self):
        from ClientRequests.spamfilter import spam_reasons
        real = [
            dict(name='Patricia', email='patricia.omedo@busara.global', subject='Request for Quote',
                 message='I would like a quote for 6 people traveling to Arusha, Tanzania for two nights.'),
            dict(name='john', email='john@gmail.com', subject='Safari question',
                 message='How much is a 3 day Masai Mara trip for two?'),
            dict(name='Amina Yusuf', email='amina@gmail.com', subject='Group trip',
                 message='We saw https://example.org/trek and want 4 places in December'),
        ]
        for sample in real:
            with self.subTest(sample['name']):
                self.assertEqual(spam_reasons(count_campaign=False, **sample), [])

    def test_repeated_identical_text_is_a_campaign(self):
        from ClientRequests.spamfilter import spam_reasons
        msg = dict(name='Sam Jones', email='sam@gmail.com', subject='Offer', message='Please call me about a special deal')
        self.assertEqual(spam_reasons(**msg), [])
        self.assertEqual(spam_reasons(**{**msg, 'email': 'b@gmail.com'}), [])
        self.assertTrue(spam_reasons(**{**msg, 'email': 'c@gmail.com'}))     # third copy => campaign

    def test_spam_is_quarantined_and_nobody_is_emailed(self):
        from EmailSetup import utils
        contact = Contact.objects.create(name=self.BOT['name'], email=self.BOT['email'],
                                         subject=self.BOT['subject'], message=self.BOT['message'])
        with mock.patch.object(utils, 'notify_staff_of_lead') as notify, \
                mock.patch.object(utils.threading, 'Thread') as thread:
            self.assertFalse(utils.handle_new_lead(contact, customer_email=lambda lead: None))
        contact.refresh_from_db()
        self.assertEqual(contact.status, 'Spam')
        notify.assert_not_called()
        thread.assert_not_called()

    def test_genuine_lead_notifies_staff_and_emails_customer_once(self):
        from EmailSetup import utils
        booking = Bookings.objects.create(name='Jane Doe', email='jane@gmail.com', phone='0712345678',
                                          message='Two adults, December')
        with mock.patch.object(utils, 'notify_staff_of_lead') as notify, \
                mock.patch.object(utils.threading, 'Thread') as thread:
            self.assertTrue(utils.handle_new_lead(booking, customer_email=lambda lead: None))
            self.assertTrue(utils.handle_new_lead(booking, customer_email=lambda lead: None))
        self.assertEqual(notify.call_count, 2)           # staff always hear about real leads
        self.assertEqual(thread.call_count, 1)           # the customer is emailed only once per day

    def test_customer_email_site_wide_cap(self):
        from ClientRequests.spamfilter import can_email_customer, CUSTOMER_EMAILS_PER_HOUR
        results = [can_email_customer(f'user{i}@gmail.com') for i in range(CUSTOMER_EMAILS_PER_HOUR + 5)]
        self.assertEqual(sum(results), CUSTOMER_EMAILS_PER_HOUR)

    def test_contact_form_never_auto_replies_to_submitter(self):
        import inspect
        from ClientRequests import views
        self.assertNotIn('send_contact_response', inspect.getsource(views))

    def test_registration_has_bot_traps_and_works_for_humans(self):
        url = reverse('register')
        data = {'username': 'janedoe77', 'first_name': 'Jane', 'last_name': 'Doe', 'email': 'jane77@gmail.com',
                'password1': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd'}
        bot = self.client.post(url, {**data, 'form_ts': stamp(), 'website': 'x'}, REMOTE_ADDR='5.5.5.5')
        self.assertEqual(bot.status_code, 400)
        seo = self.client.post(url, {**data, 'username': 'seoguy', 'email': 'x@rockstarseo.net', 'form_ts': stamp()},
                               REMOTE_ADDR='5.5.5.6')
        self.assertEqual(seo.status_code, 200)
        from django.contrib.auth.models import User
        self.assertFalse(User.objects.filter(username='seoguy').exists())
        with mock.patch('OurClients.views.send_registration_emails_async'):
            ok = self.client.post(url, {**data, 'form_ts': stamp()}, REMOTE_ADDR='5.5.5.7')
        self.assertEqual(ok.status_code, 302)
        self.assertTrue(User.objects.filter(username='janedoe77').exists())



@override_settings(CACHES=LOCMEM, ALLOWED_HOSTS=['*'])
class HotelsTests(TestCase):
    """The Hotels app: listing + filters, detail page, enquiry leads, header and footer gallery."""

    @classmethod
    def setUpTestData(cls):
        mk = Hotel.objects.create
        cls.lodge = mk(name='Amboseli Lodge', country='Kenya', location='Amboseli', property_type='lodge',
                       star_rating=5, price_per_night=400, max_guests=4, summary='Views of Kilimanjaro.',
                       description='Full description here.', amenities='Swimming pool\nFree Wi-Fi',
                       child_policy='Children welcome.', contact_person='SECRET Manager',
                       email='secret-internal@lodge.example', remarks='INTERNAL CONTRACT NOTE')
        cls.villa = mk(name='Diani Villa', country='Kenya', location='Diani', property_type='villa',
                       star_rating=4, price_per_night=250, max_guests=6, summary='Beachfront.')
        cls.camp = mk(name='Zanzibar Camp', country='Tanzania', location='Zanzibar', property_type='camp',
                      star_rating=3, price_per_night=120, max_guests=2, summary='Tented.')
        cls.hidden = mk(name='Hidden Draft', country='Kenya', location='Nowhere', is_published=False)

    def setUp(self):
        cache.clear()
        self.notify = mock.patch('Hotels.views.handle_new_lead').start()
        self.addCleanup(mock.patch.stopall)

    def names(self, response):
        return [h.name for h in response.context['hotels']]

    # ---- listing -----------------------------------------------------------
    def test_listing_shows_published_hotels_only(self):
        r = self.client.get(reverse('hotels'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(self.names(r)), {'Amboseli Lodge', 'Diani Villa', 'Zanzibar Camp'})
        self.assertNotContains(r, 'Hidden Draft')

    def test_filter_by_country_type_and_search(self):
        url = reverse('hotels')
        self.assertEqual(set(self.names(self.client.get(url, {'country': 'Tanzania'}))), {'Zanzibar Camp'})
        self.assertEqual(set(self.names(self.client.get(url, {'country': 'kenya'}))), {'Amboseli Lodge', 'Diani Villa'})
        self.assertEqual(self.names(self.client.get(url, {'type': 'villa'})), ['Diani Villa'])
        self.assertEqual(self.names(self.client.get(url, {'q': 'zanz'})), ['Zanzibar Camp'])
        self.assertEqual(self.names(self.client.get(url, {'country': 'Kenya', 'type': 'camp'})), [])

    def test_sorting(self):
        url = reverse('hotels')
        self.assertEqual(self.names(self.client.get(url, {'sort': 'price_low'})),
                         ['Zanzibar Camp', 'Diani Villa', 'Amboseli Lodge'])
        self.assertEqual(self.names(self.client.get(url, {'sort': 'price_high'}))[0], 'Amboseli Lodge')

    def test_bad_filter_values_do_not_crash(self):
        r = self.client.get(reverse('hotels'), {'country': "x' OR 1=1--", 'type': '<script>', 'sort': 'zzz', 'page': 'abc'})
        self.assertIn(r.status_code, (200, 404))
        self.assertEqual(self.client.get(reverse('hotels'), {'type': '<script>'}).status_code, 200)

    def test_filter_pills_show_counts(self):
        r = self.client.get(reverse('hotels'))
        self.assertContains(r, 'All Hotels <span>3</span>')
        self.assertContains(r, 'Kenya <span>2</span>')
        self.assertContains(r, 'Tanzania <span>1</span>')

    # ---- detail ------------------------------------------------------------
    def test_detail_page_content_and_no_internal_data_leak(self):
        r = self.client.get(self.lodge.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        for text in ('Amboseli Lodge', 'Swimming pool', 'Free Wi-Fi', 'Children welcome.', 'Check availability'):
            self.assertContains(r, text)
        for secret in ('SECRET Manager', 'secret-internal@lodge.example', 'INTERNAL CONTRACT NOTE'):
            self.assertNotContains(r, secret)
        self.assertContains(r, '"@type":"Hotel"')

    def test_unpublished_hotel_is_404(self):
        self.assertEqual(self.client.get(self.hidden.get_absolute_url()).status_code, 404)

    def test_amenities_section_hidden_when_empty(self):
        self.assertNotContains(self.client.get(self.villa.get_absolute_url()), 'Amenities')

    # ---- enquiry -> lead ---------------------------------------------------
    def enquiry(self, **extra):
        today = date.today()
        data = {'name': 'Jane Doe', 'email': 'jane@gmail.com', 'phone': '+254 712 345 678', 'persons': 2,
                'date': (today + timedelta(days=30)).isoformat(), 'check_out': (today + timedelta(days=33)).isoformat(),
                'message': 'Sea view please', 'form_ts': stamp()}
        ip = extra.pop('ip', '3.3.3.3') if 'ip' in extra else '3.3.3.3'
        return self.client.post(self.lodge.get_absolute_url(), {**data, **extra}, REMOTE_ADDR=ip)

    def test_enquiry_creates_hotel_lead(self):
        r = self.enquiry()
        self.assertEqual(r.status_code, 302)
        booking = Bookings.objects.get()
        self.assertEqual((booking.booking_type, booking.hotel, booking.status), ('hotel', self.lodge, 'new'))
        self.assertEqual(booking.item_name, str(self.lodge))
        self.notify.assert_called_once()

    def test_enquiry_validation(self):
        self.assertEqual(self.enquiry(persons=9).status_code, 200)                      # more than max_guests
        self.assertEqual(self.enquiry(check_out=date.today().isoformat()).status_code, 200)   # checkout before checkin
        self.assertEqual(Bookings.objects.count(), 0)

    def test_enquiry_bot_traps(self):
        self.assertEqual(self.enquiry(website='http://spam').status_code, 400)
        self.assertEqual(Bookings.objects.count(), 0)

    # ---- header + footer ---------------------------------------------------
    def test_header_has_hotels_and_no_gallery_link(self):
        html = self.client.get(reverse('home')).content.decode()
        nav = html[html.index('navbar-nav'):html.index('Book Now')]
        self.assertIn(reverse('hotels'), nav)
        self.assertNotIn(reverse('gallary'), nav)

    def test_footer_gallery_six_photos_last_links_to_gallery(self):
        from Home.models import Gallery, GalleryCategory
        cat = GalleryCategory.objects.create(name='Wildlife')
        for i in range(8):
            Gallery.objects.create(name=f'Photo {i}', category=cat, image='gallery_images/x.jpg')
        html = self.client.get(reverse('hotels')).content.decode()
        self.assertEqual(html.count('data-lightbox="footer-gallery"'), 5)           # first five open the lightbox
        self.assertEqual(html.count('footer-gallery-more"'), 1)                     # the sixth links onward
        self.assertIn('href="%s" class="footer-gallery-more"' % reverse('gallary'), html)


    # ---- gallery strip + children section ------------------------------------
    def test_photo_strip_appears_only_with_several_photos(self):
        url = self.lodge.get_absolute_url()
        self.assertNotContains(self.client.get(url), 'class="hotel-thumbs')
        for i in (1, 2, 3):
            HotelImage.objects.create(hotel=self.lodge, image=f'hotels/test-{i}.jpg', order=i,
                                      is_featured=(i == 1))
        r = self.client.get(url)
        self.assertEqual(r.content.decode().count('class="hotel-thumb'), 4)       # strip + 3 thumbs
        self.assertContains(r, 'id="hotel-main-img"')
        self.assertContains(r, 'data-full="/media/hotels/test-2.jpg"')

    def test_detail_page_has_children_question_and_brown_fact_boxes(self):
        r = self.client.get(self.lodge.get_absolute_url())
        self.assertContains(r, 'Travelling with children?')
        self.assertContains(r, 'name="traveling_with_children"')
        self.assertContains(r, 'id="children-fields"')
        self.assertContains(r, 'class="hotel-fact"', count=2)                       # guests + rating (rooms not set)

    def test_enquiry_without_children(self):
        self.assertEqual(self.enquiry(traveling_with_children='no', children_count='3').status_code, 302)
        booking = Bookings.objects.get()
        self.assertIs(booking.has_children, False)
        self.assertIsNone(booking.children_count)           # stray values are ignored when "no"
        self.assertEqual(booking.children_summary, 'No children')

    def test_enquiry_with_children_is_saved(self):
        r = self.enquiry(persons=4, traveling_with_children='yes', children_count='2', children_ages='4, 7')
        self.assertEqual(r.status_code, 302)
        booking = Bookings.objects.get()
        self.assertEqual((booking.has_children, booking.children_count, booking.children_ages), (True, 2, '4, 7'))
        self.assertEqual(booking.children_summary, 'Yes, 2 children (ages 4, 7)')

    def test_children_validation(self):
        base = dict(persons=3, traveling_with_children='yes')
        self.assertEqual(self.enquiry(**base, ip='7.0.0.1').status_code, 200)                                  # count missing
        self.assertEqual(self.enquiry(**base, children_count='5', ip='7.0.0.2').status_code, 200)              # more kids than guests
        self.assertEqual(self.enquiry(**base, children_count='1', children_ages='x.com', ip='7.0.0.3').status_code, 200)
        self.assertEqual(self.enquiry(**base, children_count='1', children_ages='<b>5</b>', ip='7.0.0.4').status_code, 200)
        self.assertEqual(Bookings.objects.count(), 0)

    def test_old_clients_without_the_children_field_still_work(self):
        r = self.enquiry()                                  # no traveling_with_children posted at all
        self.assertEqual(r.status_code, 302)
        self.assertIs(Bookings.objects.get().has_children, False)

    def test_staff_alert_includes_children(self):
        from EmailSetup import utils
        booking = Bookings.objects.create(name='Jane Doe', email='jane@gmail.com', phone='0712345678',
                                          booking_type='hotel', hotel=self.lodge, has_children=True,
                                          children_count=2, children_ages='3, 6')
        sent = {}
        with mock.patch.object(utils, 'send_transactional_email', lambda to, name, subj, html: sent.update(html=html)), \
                mock.patch.object(utils.threading, 'Thread', lambda target, daemon=None: type('T', (), {'start': lambda self: target()})()):
            utils.notify_staff_of_lead(booking)
        self.assertIn('Yes, 2 children (ages 3, 6)', sent['html'])


    def test_purge_spam_delete_also_clears_quarantined_rows(self):
        from django.core.management import call_command
        import io
        real = Contact.objects.create(name='Patricia', email='p@busara.global', subject='Request for Quote',
                                      message='I would like a quote for 6 people to Arusha for two nights.')
        for i in range(3):
            Contact.objects.create(name='mussymync', email=f'v{i}@gmail.com', subject='I promised.',
                                   message='Photos for my escort application', status='Spam')
        out = io.StringIO()
        call_command('purge_spam', stdout=out)                                    # dry run
        self.assertEqual(Contact.objects.count(), 4)
        call_command('purge_spam', '--delete', stdout=out)
        self.assertEqual(list(Contact.objects.values_list('pk', flat=True)), [real.pk])


@override_settings(CACHES=LOCMEM, ALLOWED_HOSTS=['*'])
class I18nTests(SiteHealthTests):
    """The site must work completely in every language (en, fr, sw, es, de, it)."""
    # reuse the fixtures and URL list of SiteHealthTests but do not re-run its tests
    test_every_public_page_renders_cleanly = None
    test_pages_have_unique_meta_descriptions = None
    LANGS = ['fr', 'sw', 'es', 'de', 'it']

    def test_translation_files_are_complete(self):
        """No untranslated or fuzzy entries (fuzzy entries are ignored by Django and are usually wrong)."""
        from django.conf import settings
        for lang in self.LANGS:
            text = (settings.BASE_DIR / 'locale' / lang / 'LC_MESSAGES' / 'django.po').read_text(encoding='utf-8')
            for block in text.split('\n\n'):
                if 'msgid ""' in block.split('\n')[0:3] or 'msgid_plural' in block:
                    continue
                m = re.search(r'^msgid ((?:".*"\n?)+)msgstr ((?:".*"\n?)+)', block, re.M)
                if not m or m.group(1).strip() == '""' and 'Project-Id-Version' in m.group(2):
                    continue
                self.assertNotIn('#, fuzzy', block, f'{lang}: fuzzy entry {m.group(1)[:60]}')
                self.assertNotEqual(m.group(2).replace('"', '').strip(), '', f'{lang}: untranslated {m.group(1)[:60]}')

    def test_every_public_page_works_in_every_language(self):
        for lang in self.LANGS:
            for url in self.urls():
                path = '/' + lang + url[3:]
                with self.subTest(url=path):
                    r = self.client.get(path)
                    self.assertEqual(r.status_code, 200)
                    html = r.content.decode()
                    self.assertIn(f'<html lang="{lang}"', html)
                    self.assertNotRegex(html, r'\{%|%\}|\{\{', 'unrendered template code leaked into the page')

    def test_navigation_and_forms_are_translated(self):
        expect = {'fr': ('Hôtels', 'Contactez-nous'), 'de': ('Hotels', 'Kontakt'), 'es': ('Hoteles', 'Contacto'),
                  'sw': ('Hoteli', 'Wasiliana'), 'it': ('Hotel', 'Contatti')}
        for lang, words in expect.items():
            html = self.client.get(f'/{lang}/contact/').content.decode()
            for w in words:
                self.assertIn(w, html, f'{lang}: expected {w!r} on the contact page')
            self.assertNotIn('Get In Touch With Us', html)
            self.assertNotIn('Send Us a Message', html)
        # booking form placeholders come from forms.py
        self.assertIn('Choisir une destination', self.client.get('/fr/booking/').content.decode())

    def test_meta_description_is_translated(self):
        fr = self.client.get('/fr/contact/').content.decode()
        en = self.client.get('/en/contact/').content.decode()
        d = lambda h: re.search(r'<meta name="description" content="([^"]*)"', h).group(1)
        self.assertNotEqual(d(fr), d(en))

    def test_form_messages_use_the_active_language(self):
        from django.utils import translation
        from ClientRequests.forms import BookingsForm
        with translation.override('fr'):
            self.assertEqual(str(BookingsForm().fields['destination'].empty_label), 'Choisir une destination')

    def test_database_content_is_translated(self):
        """Packages, itineraries, hotels and blogs read from the <field>_<lang> columns, English is the fallback."""
        from django.utils import translation
        from Home.models import Blogs
        from Places.models import DestinationsCategory
        with translation.override('en'):    # new rows are written to the active language's column
            blog = Blogs.objects.create(title='Safari tips', title_fr='Conseils de safari')
            cat = DestinationsCategory.objects.create(location='Diani', category='Beach')
        with translation.override('fr'):
            self.assertEqual(blog.title, 'Conseils de safari')
            self.assertEqual(cat.category, 'Beach')      # no French yet -> English fallback
        with translation.override('en'):
            self.assertEqual(blog.title, 'Safari tips')

    def test_blog_category_filter(self):
        from Home.models import Blogs, BlogCategory
        from django.utils import translation
        with translation.override('en'):
            cat = BlogCategory.objects.create(name='Tips', name_fr='Conseils')
            Blogs.objects.create(title='Tip one', author='A', content='<p>x</p>', category=cat)
            Blogs.objects.create(title='Other one', author='A', content='<p>y</p>')
        html = self.client.get(f'/fr/blog/?category={cat.slug}').content.decode()
        self.assertIn('Tip one', html)
        self.assertNotIn('Other one', html)
        self.assertIn('Conseils', html)

    def test_home_offers_paginate_by_8_and_hide_expired(self):
        import shutil, tempfile
        from django.test import override_settings
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, True)
        override = override_settings(MEDIA_ROOT=media)     # never write test files into the real media folder
        override.enable()
        self.addCleanup(override.disable)
        from datetime import date, timedelta
        from django.core.files.uploadedfile import SimpleUploadedFile
        from Home.models import Offer
        gif = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,'
               b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
        with __import__('django.utils.translation', fromlist=['x']).override('en'):
            for i in range(10):
                Offer.objects.create(title=f'Deal {i}', image=SimpleUploadedFile(f'o{i}.gif', gif, 'image/gif'))
            Offer.objects.create(title='Old deal', image=SimpleUploadedFile('old.gif', gif, 'image/gif'),
                                 end_date=date.today() - timedelta(days=1))
        h1 = self.client.get('/en/').content.decode()
        h2 = self.client.get('/en/?offers=2').content.decode()
        self.assertEqual(h1.count('class="offer-card"'), 8)
        self.assertEqual(h2.count('class="offer-card"'), 2)
        self.assertNotIn('Old deal', h1 + h2)

    def test_quick_lead_popup_saves_lead(self):
        from unittest import mock
        from ClientRequests.models import QuickLead
        from EmailSetup import utils
        import ClientRequests.antispam as a
        from ClientRequests.antispam import lead_token
        url = '/en/lead/'
        mock.patch.object(a, 'MIN_FILL_SECONDS', 0).start()
        self.addCleanup(mock.patch.stopall)
        with mock.patch.object(utils, 'notify_staff_of_lead') as notify:
            ok = self.client.post(url, {'name': 'Amina Test', 'phone': '+254 712 345 678', 'tour': 'Bali', 'message': 'Hi',
                                        'form_ts': lead_token()})
            self.assertEqual(ok.status_code, 200)
            self.assertEqual(QuickLead.objects.count(), 1)
            notify.assert_called_once()
        self.assertEqual(self.client.post(url, {'name': 'A', 'phone': '+254712345678'}).status_code, 400)
        self.assertEqual(self.client.post(url, {'name': 'Amina', 'phone': 'abc'}).status_code, 400)
        self.client.post(url, {'name': 'Bot Bot', 'phone': '+254712345678', 'website': 'spam.com'})
        self.assertEqual(QuickLead.objects.count(), 1)           # honeypot filled -> nothing saved

    def test_popups_only_where_intended(self):
        home = self.client.get('/en/').content.decode()
        self.assertIn('id="leadOverlay" data-auto="1"', home)          # pops up by itself on normal pages
        self.assertNotIn('id="popupOverlay"', home)               # the discount popup is packages-page only
        contact = self.client.get('/en/contact/').content.decode()
        self.assertIn('id="leadOverlay" data-auto=""', contact)       # still opens from the Get a Quote button...
        self.assertIn('data-open-lead', contact)                       # ...but never by itself on the contact page
        self.assertNotIn('chatbot', home.lower())


class PackagesFilterTests(TestCase):
    """The packages page filters, sorting and paging must work for every input, good or bad."""

    @classmethod
    def setUpTestData(cls):
        from Places.models import AwesomePackages
        from django.utils import translation
        with translation.override('en'):
            rows = [('Masai Mara Safari', 'Masai Mara', 'East Africa Tours', 900, 3, 5),
                    ('Amboseli Elephant Trip', 'Amboseli', 'East Africa Tours', 1500, 5, 4),
                    ('Cape Town Wine Tour', 'Cape Town', 'South Africa', 2400, 7, 5),
                    ('Nile Cruise', 'Luxor', 'Cruises', 3500, 10, 5)]
            for i, (name, loc, cat, price, days, stars) in enumerate(rows):
                AwesomePackages.objects.create(name=name, location=loc, category=cat, price=price, days=days, persons=2,
                                               star_rating=stars, description=f'<p>A trip number {i}</p>')
            for i in range(10):     # enough packages to need a second page
                AwesomePackages.objects.create(name=f'Filler {i}', location='Nairobi', category='East Africa Tours',
                                               price=100 + i, days=1, persons=1, star_rating=3, description='<p>x</p>')

    def names(self, query=''):
        html = self.client.get('/en/packages/' + query).content.decode()
        return re.findall(r'<h2 class="pk-title"><a [^>]*>([^<]*)</a>', html)

    def test_each_filter(self):
        self.assertEqual(self.names('?category=Cruises'), ['Nile Cruise'])
        self.assertEqual(self.names('?location=amboseli'), ['Amboseli Elephant Trip'])
        self.assertEqual(self.names('?min_price=2000&max_price=3000'), ['Cape Town Wine Tour'])
        self.assertEqual(self.names('?days=3&search=mara'), ['Masai Mara Safari'])
        self.assertEqual(self.names('?search=elephant%20amboseli'), ['Amboseli Elephant Trip'])   # words need not be next to each other
        self.assertEqual(self.names('?search=zzzz'), [])

    def test_combined_and_reversed_price_range(self):
        self.assertEqual(self.names('?category=East+Africa+Tours&max_price=1000&days=3&search=masai'), ['Masai Mara Safari'])
        self.assertEqual(self.names('?min_price=3000&max_price=2000'), ['Cape Town Wine Tour'])     # 3000/2000 is swapped, not empty

    def test_sorting(self):
        first = self.names('?category=East+Africa+Tours&sort=price_desc&search=trip')
        self.assertEqual(first, ['Amboseli Elephant Trip', 'Masai Mara Safari'])
        self.assertEqual(self.names('?sort=price_asc&min_price=1000')[:2], ['Amboseli Elephant Trip', 'Cape Town Wine Tour'])
        self.assertEqual(self.names('?sort=days_desc&min_price=1000')[0], 'Nile Cruise')

    def test_bad_input_never_errors(self):
        for query in ['?min_price=abc', '?max_price=1e999', '?days=-5', '?days=x', '?page=abc', '?page=999', '?page=0',
                      '?category=Nope', '?sort=hack', '?search=' + 'a' * 500, "?search='%3Bdrop%20table", '?location=%00']:
            self.assertEqual(self.client.get('/en/packages/' + query).status_code, 200, query)

    def test_paging_keeps_filters_and_never_repeats(self):
        page1 = self.names('?category=East+Africa+Tours&sort=price_asc')
        page2 = self.names('?category=East+Africa+Tours&sort=price_asc&page=2')
        self.assertEqual(len(page1), 9)
        self.assertFalse(set(page1) & set(page2))
        html = self.client.get('/en/packages/?category=East+Africa+Tours&sort=price_asc').content.decode()
        self.assertIn('category=East+Africa+Tours&amp;sort=price_asc&page=2', html)

    def test_filter_button_is_the_strong_one_and_chips_show(self):
        html = self.client.get('/en/packages/?category=Cruises').content.decode()
        self.assertLess(html.index('pk-btn pk-btn-main'), html.index('pk-btn pk-btn-quiet'))
        self.assertIn('class="pk-tag"', html)
        self.assertNotIn('pk-btn-quiet', self.client.get('/en/packages/').content.decode())    # nothing to reset yet


class UiPagesTests(TestCase):
    """The upgraded list/info pages render and keep their key features."""

    def test_faq_is_an_accordion_with_search(self):
        html = self.client.get('/en/faq/').content.decode()
        self.assertEqual(html.count('class="faq-item"'), 6)
        self.assertIn('id="faqSearch"', html)

    def test_cta_band_shows_on_content_pages_only(self):
        self.assertIn('class="cta-strip"', self.client.get('/en/services/').content.decode())
        for url in ('/en/', '/en/packages/', '/en/contact/', '/en/faq/', '/en/privacy-policy/'):
            self.assertNotIn('class="cta-strip"', self.client.get(url).content.decode(), url)

    def test_contact_has_quick_cards_and_trek_pages_use_cards(self):
        self.assertIn('tel:+254759379600', self.client.get('/en/contact/').content.decode())
        for url in ('/en/trekking/Mt-Kenya/', '/en/trekking/Mt-Meru/', '/en/hotels/', '/en/hotels/?page=99'):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_pages_never_ship_the_old_carousel_for_treks(self):
        self.assertNotIn('packages-carousel', self.client.get('/en/trekking/Mt-Kenya/').content.decode())


from django.utils import translation


class PackageGalleryTests(TestCase):
    def test_gallery_shows_thumbnails_only_when_extra_photos_exist(self):
        import tempfile
        from io import BytesIO
        from PIL import Image
        from django.core.files.base import ContentFile
        from django.test import override_settings
        from Places.models import AwesomePackages, PackageImage
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            def jpg(name):
                buf = BytesIO(); Image.new('RGB', (800, 600), 'tan').save(buf, 'JPEG')
                return ContentFile(buf.getvalue(), name)
            with translation.override('en'):
                pkg = AwesomePackages.objects.create(name='Gallery Trip', location='Kenya', days=3, price=100, persons=2,
                                                     description='<p>x</p>', category='East Africa Tours')
            pkg.image.save('main.jpg', jpg('main.jpg'))
            url = f'/en/packages/{pkg.slug}/'
            html = self.client.get(url).content.decode()
            self.assertIn('id="pgMain"', html)
            self.assertNotIn('pg-strip', html)
            for n in range(3):
                g = PackageImage(package=pkg, order=n); g.image.save(f'g{n}.jpg', jpg(f'g{n}.jpg'))
            html = self.client.get(url).content.decode()
            self.assertEqual(html.count('class="pg-th'), 4)       # main photo + 3 extras


class LeadBotTests(TestCase):
    """The WhatsApp popup endpoint: bots are swallowed silently, people still get through."""

    def setUp(self):
        cache.clear()

    def post(self, ts=None, **over):
        from ClientRequests.antispam import lead_token
        import ClientRequests.antispam as a
        data = {'name': 'Grace Wanjiru', 'phone': '0722123456', 'tour': 'Masai Mara', 'message': 'Two adults in March',
                'form_ts': ts if ts is not None else lead_token()}
        data.update(over)
        with mock.patch.object(a, 'MIN_FILL_SECONDS', 0):
            return self.client.post('/en/lead/', data)

    def test_real_lead_is_saved(self):
        from ClientRequests.models import QuickLead
        with mock.patch('EmailSetup.utils.notify_staff_of_lead'):
            r = self.post()
        self.assertTrue(r.json()['success'])
        self.assertEqual(QuickLead.objects.count(), 1)

    def test_bot_spam_is_swallowed_not_saved(self):
        from ClientRequests.models import QuickLead
        with mock.patch('EmailSetup.utils.notify_staff_of_lead') as notify:
            for kw in ({'message': 'Photos for my escort application are uploaded. Preview: https://tinyurl.com/4yf4mchz#2cQlWZ'},
                       {'message': 'Check https://example.com/offer'},
                       {'ts': 'forged-token'}):
                r = self.post(**kw)
                self.assertTrue(r.json()['success'])           # bots are never told
            notify.assert_not_called()
        self.assertEqual(QuickLead.objects.count(), 0)


class ServicePagesTests(TestCase):
    def test_service_cards_open_the_existing_page_or_a_generic_one(self):
        from django.core.cache import cache
        from Home.models import Services
        cache.clear()
        with translation.override('en'):
            hotel = Services.objects.create(name='Hotel Accommodation', description='Comfort and luxury stays.', icon='fa fa-hotel')
            visa = Services.objects.create(name='Visa Processing Services', description='We guide your visa application.', icon='fa fa-passport')
        home = self.client.get('/en/').content.decode()
        self.assertIn('href="/en/hotels/" class="stretched-link"', home)       # has its own page already
        self.assertIn(f'/en/services/{visa.pk}/', home)                         # no page of its own: generic one
        page = self.client.get(f'/en/services/{hotel.pk}/').content.decode()
        self.assertIn('Hotel Accommodation', page)
        self.assertIn('Comfort and luxury stays.', page)
        self.assertIn('/en/hotels/', page)                       # hotels also get a deeper link
        self.assertIn('Visa Processing Services', page)          # sidebar lists the other services
        self.assertEqual(self.client.get('/en/services/999999/').status_code, 404)


class PackagesApiTests(TestCase):
    def setUp(self):
        cache.clear()
        from Hotels.models import ApiKey
        _, token = ApiKey.create_key('tests')
        self.auth = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
        with translation.override('en'):
            self.pkg = AwesomePackages.objects.create(name='Old Name', location='Kenya', days=2, price=100, persons=2,
                                                      description='<p>short</p>', category='East Africa Tours')
            from Places.models import Itinerary
            Itinerary.objects.create(package=self.pkg, day_number=1, title='Arrive', description='old text')
        self.url = f'/api/v1/packages/{self.pkg.slug}/'

    def patch(self, body, query=''):
        import json
        return self.client.patch(self.url + query, json.dumps(body), content_type='application/json', **self.auth)

    def test_needs_a_key(self):
        self.assertEqual(self.client.get('/api/v1/packages/').status_code, 401)
        self.assertEqual(self.client.get('/api/v1/packages/', **self.auth).json()['count'], 1)

    def test_update_text_seo_and_days_keeps_slug_and_forgets_other_languages(self):
        from Places.models import Itinerary
        AwesomePackages.objects.filter(pk=self.pkg.pk).update(description_fr='<p>vieux</p>')
        r = self.patch({'description': '<p>A much better description.</p>', 'seo_title': 'Great Safari | Day Safaris',
                        'seo_description': 'Book it.', 'itineraries': [
                            {'day_number': 1, 'title': 'Arrive in Nairobi', 'meals': 'Half Board'},
                            {'day_number': 2, 'title': 'Depart', 'description': 'Fly home.'}]})
        self.assertEqual(r.status_code, 200, r.content)
        p = AwesomePackages.objects.get(pk=self.pkg.pk)
        self.assertEqual(p.slug, self.pkg.slug)                         # web address untouched
        with translation.override('en'):
            self.assertEqual(p.seo_title, 'Great Safari | Day Safaris')
        self.assertFalse(p.description_fr)                              # stale French text cleared -> English shown
        days = {i.day_number: i for i in Itinerary.objects.filter(package=p)}
        self.assertEqual(sorted(days), [1, 2])
        self.assertEqual(days[1].meals, 'Half Board')
        self.assertEqual(days[1].description, 'old text')               # untouched field kept
        html = self.client.get(f'/en/packages/{p.slug}/').content.decode()
        self.assertIn('<title>Great Safari | Day Safaris', html)
        self.assertIn('content="Book it."', html)

    def test_dry_run_and_validation(self):
        r = self.patch({'seo_title': 'x' * 80}); self.assertEqual(r.status_code, 400)
        r = self.patch({'itineraries': [{'day_number': 1, 'meals': 'Nope'}]}); self.assertEqual(r.status_code, 400)
        r = self.patch({'name': 'New Name'}, '?dry_run=1')
        self.assertEqual(r.json()['changes'], ['name'])
        self.pkg.refresh_from_db(); self.assertEqual(self.pkg.name, 'Old Name')
        r = self.patch({'price': 5}); self.assertEqual(r.json()['ignored_fields'], ['price'])   # prices never change here


class GuidesTests(TestCase):
    UA = {'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36'}

    def setUp(self):
        from django.core.cache import cache
        from django.contrib.auth.models import User
        from Home.models import Guide
        cache.clear()
        self.owner = User.objects.create_user('daniel', 'd@example.com', 'pw12345!')
        self.other = User.objects.create_user('someone', 's@example.com', 'pw12345!')
        with translation.override('en'):
            self.g = Guide.objects.create(name='Daniel Kiprop', role='Senior Safari Guide', short_bio='Big cats expert.',
                                          bio='<p>Twelve years in the Mara.</p>', specializations='Big Cats, Birding',
                                          languages='English, Swahili', years_experience=12, user=self.owner)
            Guide.objects.create(name='Hidden Guide', role='Driver', is_active=False)
        self.url = f'/en/guides/{self.g.slug}/'

    def test_guides_on_about_page_with_their_own_profile_pages(self):
        self.assertEqual(self.g.slug, 'daniel-kiprop')
        about = self.client.get('/en/about/').content.decode()
        self.assertIn('Meet Our Guides', about)
        self.assertIn(self.url, about)
        self.assertNotIn('Hidden Guide', about)
        page = self.client.get(self.url).content.decode()
        for text in ('Daniel Kiprop', 'Senior Safari Guide', 'Big Cats', 'Birding', 'Swahili', 'Twelve years in the Mara.'):
            self.assertIn(text, page)
        self.assertIn('"@type":"Person"', page)
        self.assertNotIn('Subscribe for Safari Updates', page)          # standalone page: no site header/footer
        self.assertIn('Powered by', page)
        self.assertGreaterEqual(page.count('href="/en/"'), 3)            # logo, header link and footer lead back
        self.assertIn('id="leadForm"', page)                             # lead form + QR card for everyone
        self.assertIn('id="qrCard"', page)
        self.assertNotIn('editToggle', page)                             # ...but no editing or analytics for visitors
        self.assertNotIn('/analytics/', page)
        self.assertEqual(self.client.get('/en/guides/hidden-guide/').status_code, 404)
        self.assertIn(self.url, self.client.get('/sitemap.xml').content.decode())

    def test_about_page_without_guides_has_no_guides_section(self):
        from Home.models import Guide
        Guide.objects.all().delete()
        self.assertNotIn('Meet Our Guides', self.client.get('/en/about/').content.decode())

    def test_new_guide_gets_comprehensive_defaults(self):
        from Home.models import Guide
        with translation.override('en'):
            g = Guide.objects.create(name='Fresh Guide')
        self.assertTrue(g.role and g.short_bio and g.bio and g.years_experience and g.motto)
        self.assertGreaterEqual(len(g.specialization_list), 4)
        self.assertGreaterEqual(len(g.language_list), 2)
        self.assertGreaterEqual(len(g.park_list), 4)
        page = self.client.get(f'/en/guides/{g.slug}/').content.decode()
        self.assertIn('Professional Safari Guide', page)
        self.assertIn('Birdwatching', page)

    def post_lead(self, **over):
        import ClientRequests.antispam as a
        from ClientRequests.antispam import lead_token
        from Home.models import GuideEvent
        ev = GuideEvent.objects.filter(name='Travel Expo').first() or GuideEvent.objects.create(name='Travel Expo')
        data = {'name': 'Grace Wanjiru', 'phone': '0722123456', 'category': 'trekking', 'group_size': '4', 'src': 'qr',
                'event': str(ev.pk), 'travel_date': '2027-03-14', 'message': 'Mt Kenya in August', 'form_ts': lead_token()}
        data.update(over)
        with mock.patch.object(a, 'MIN_FILL_SECONDS', 0), mock.patch('Home.guides._notify'):
            return self.client.post(f'{self.url}lead/', data)

    def test_lead_form_saves_with_category_source_and_event_and_swallows_bots(self):
        from Home.models import GuideLead
        r = self.post_lead()
        self.assertTrue(r.json()['ok'])
        self.assertIn('wa.me/', r.json()['whatsapp'])
        lead = GuideLead.objects.get()
        self.assertEqual((lead.category, lead.source, lead.event, lead.group_size, lead.guide_id),
                         ('trekking', 'event', 'Travel Expo', 4, self.g.pk))         # a real event id makes it an event lead
        self.assertEqual(str(lead.travel_date), '2027-03-14')
        self.assertEqual(GuideLead.objects.exclude(event='').count(), 1)
        self.post_lead(event='9999', name='No Event')                                   # unknown event ids are ignored
        self.assertEqual(GuideLead.objects.get(name='No Event').event, '')
        GuideLead.objects.filter(name='No Event').delete()
        self.assertEqual(self.post_lead(name='A').status_code, 400)                      # validation
        self.assertEqual(self.post_lead(phone='abc').status_code, 400)
        for bot in ({'message': 'Visit https://tinyurl.com/abc now'}, {'website': 'x'}, {'form_ts': 'forged'}):
            self.assertTrue(self.post_lead(**bot).json()['ok'])                          # bots are never told
        self.assertEqual(GuideLead.objects.count(), 1)

    def test_owner_gets_edit_and_analytics_others_do_not(self):
        self.client.login(username='daniel', password='pw12345!')
        page = self.client.get(self.url).content.decode()
        self.assertIn('editToggle', page)
        self.assertIn('id="eventPick"', page)                                             # agents pick an admin-created event
        self.assertIn(f'{self.url}analytics/', page)
        r = self.client.post(f'{self.url}edit/', '{"role": "Lead Guide", "years_experience": 15, "bio": "<p>New</p><script>x</script>", "parks": "Mara, Tsavo"}',
                             content_type='application/json')
        self.assertTrue(r.json()['ok'])
        self.g.refresh_from_db()
        self.assertEqual((self.g.role, self.g.years_experience, self.g.parks), ('Lead Guide', 15, 'Mara, Tsavo'))
        self.assertNotIn('script', self.g.bio)
        self.client.logout()
        self.client.login(username='someone', password='pw12345!')
        self.assertEqual(self.client.post(f'{self.url}edit/', '{"role": "Hacked"}', content_type='application/json').status_code, 403)
        self.assertEqual(self.client.get(f'{self.url}analytics/').status_code, 404)
        self.assertNotIn('editToggle', self.client.get(self.url).content.decode())
        self.client.logout()
        self.assertEqual(self.client.get(f'{self.url}analytics/').status_code, 302)      # sent to login

    def test_analytics_counts_leads_views_and_exports(self):
        from Home.models import GuideLead, GuideDayStat
        self.post_lead(); self.post_lead(category='safari', src='profile', event='')
        self.assertEqual(GuideLead.objects.count(), 2)
        self.client.get(self.url, **self.UA); self.client.get(self.url + '?src=qr', **self.UA)
        self.client.get(self.url, HTTP_USER_AGENT='Googlebot/2.1')                       # bots are not counted
        stat = GuideDayStat.objects.get()
        self.assertEqual((stat.views, stat.qr_scans), (2, 1))
        self.client.login(username='daniel', password='pw12345!')
        self.client.get(self.url, **self.UA)                                              # the owner's own visits are not counted
        self.assertEqual(GuideDayStat.objects.get().views, 2)
        page = self.client.get(f'{self.url}analytics/').content.decode()
        self.assertIn('Total leads', page)
        self.assertIn('Trekking', page)
        csv_page = self.client.get(f'{self.url}analytics/?export=csv')
        self.assertIn('Grace Wanjiru', csv_page.content.decode())
        lead = GuideLead.objects.first()
        self.assertTrue(self.client.post(f'{self.url}leads/{lead.pk}/status/', {'status': 'Contacted'}).json()['ok'])
        lead.refresh_from_db(); self.assertEqual(lead.status, 'Contacted')

    def test_share_preview_image_and_meta(self):
        import tempfile
        from io import BytesIO
        from PIL import Image
        from django.core.files.base import ContentFile
        from django.test import override_settings
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            buf = BytesIO(); Image.new('RGB', (900, 1100), (200, 150, 90)).save(buf, 'JPEG')
            self.g.photo.save('face.jpg', ContentFile(buf.getvalue()))
            page = self.client.get(self.url).content.decode()
            self.assertIn(f'property="og:image" content="https://daysafarisadventures.co.ke{self.url}og.jpg"', page)
            self.assertIn('og:image:width" content="1200"', page)
            self.assertIn('twitter:card" content="summary_large_image"', page)
            r = self.client.get(f'{self.url}og.jpg')
            self.assertEqual((r.status_code, r['Content-Type']), (200, 'image/jpeg'))
            data = b''.join(r.streaming_content)
            self.assertEqual(Image.open(BytesIO(data)).size, (1200, 630))
            self.assertLess(len(data), 300_000)                                  # small enough for WhatsApp previews
            self.g.photo.delete(save=True)                                        # no photo: still a branded card
            r = self.client.get(f'{self.url}og.jpg')
            self.assertEqual(Image.open(BytesIO(b''.join(r.streaming_content))).size, (1200, 630))
            self.assertEqual(self.client.get('/en/guides/hidden-guide/og.jpg').status_code, 404)
