from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from Hotels.models import AirBNB, Hotel
from Home.models import Blogs, Trekking
from Places.models import AwesomePackages, Destinations


class _Base(Sitemap):
    protocol = 'https'
    i18n = True            # one entry per language, with hreflang alternates
    alternates = True
    x_default = True


class StaticPagesSitemap(_Base):
    priority = 0.8
    changefreq = 'weekly'
    names = ['home', 'about', 'services', 'packages', 'east_africa_tours', 'south_africa_tours',
             'west_africa_tours', 'international_tours', 'african_wildlife_tours', 'holiday_tailor_made_tours',
             'airport_transfers', 'travel_partnerships', 'cruises', 'airline', 'gallary', 'blog', 'brochures',
             'faq', 'contact', 'hotels', 'legal_notice', 'privacy_policy', 'terms_and_conditions', 'cookie_policy', 'sitemap_page', 'booking_create', 'airbnb', 'trekking_kenya', 'trekking_kilimanjaro',
             'trekking_meru', 'trekking_longonot', 'trekking_suswa']

    def items(self):
        return self.names

    def location(self, name):
        return reverse(name)


class PackagesSitemap(_Base):
    priority, changefreq = 0.9, 'weekly'

    def items(self):
        return AwesomePackages.objects.exclude(slug__isnull=True).exclude(slug='')

    def location(self, obj):
        return reverse('package_detail', args=[obj.slug])


class DestinationsSitemap(_Base):
    priority, changefreq = 0.8, 'monthly'

    def items(self):
        return Destinations.objects.all()

    def location(self, obj):
        return reverse('destination_detail', args=[obj.pk])


class TrekkingSitemap(_Base):
    priority, changefreq = 0.8, 'monthly'

    def items(self):
        return Trekking.objects.all()

    def location(self, obj):
        return reverse('kili_detail', args=[obj.pk])


class BlogSitemap(_Base):
    priority, changefreq = 0.6, 'weekly'

    def items(self):
        return Blogs.objects.exclude(slug__isnull=True).exclude(slug='')

    def location(self, obj):
        return reverse('blog_detail', args=[obj.slug])


class HotelsSitemap(_Base):
    priority, changefreq = 0.8, 'weekly'

    def items(self):
        return Hotel.objects.filter(is_published=True)

    def location(self, obj):
        return reverse('hotel_detail', args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class StaysSitemap(_Base):
    priority, changefreq = 0.5, 'monthly'

    def items(self):
        return AirBNB.objects.all()

    def location(self, obj):
        return reverse('bnb_detail', args=[obj.pk])


sitemaps = {
    'pages': StaticPagesSitemap, 'packages': PackagesSitemap, 'destinations': DestinationsSitemap,
    'trekking': TrekkingSitemap, 'hotels': HotelsSitemap, 'blog': BlogSitemap, 'stays': StaysSitemap,
}
