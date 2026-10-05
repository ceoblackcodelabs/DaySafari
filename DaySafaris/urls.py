"""
URL configuration for DaySafaris project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import re
import django
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve as serve_static_file
from django.views.decorators.cache import cache_control
from django.contrib.staticfiles.views import serve as serve_staticfiles

from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView
from Home.sitemaps import sitemaps
from DaySafaris.media import serve_media_with_range

ROBOTS_TXT = """User-agent: *
Allow: /
Disallow: /*/admin/
Disallow: /*/Mpesa/
Disallow: /*/Stripe/
Disallow: /*/Crypto/
Disallow: /*/Bank/
Disallow: /*/payment/
Disallow: /ckeditor5/
Disallow: /i18n/

Sitemap: https://daysafarisadventures.co.ke/sitemap.xml
"""

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),
    path('robots.txt', lambda request: HttpResponse(ROBOTS_TXT, content_type='text/plain')),
    path('sitemap.xml', cache_page(3600)(sitemap), {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switcher endpoint
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('OurClients.urls')),
    path('', include('Home.urls')),
    path('', include('Places.urls')),
    path('', include('ClientRequests.urls')),
    path('', include("Accomodations.urls")),
    path('', include('ChatBot.urls')),
    # path('', include('FinanceManagement.urls')),
    path('', include('Payments.urls')),
    path('Mpesa/', include('MpesaPayment.urls')),
    path('Stripe/', include('StripePayment.urls')),
    path('Crypto/', include('CryptoTransfer.urls')),
    path('Bank/', include('BankTransfer.urls')),
)

# NOTE: django.conf.urls.static.static() is NOT used for MEDIA_URL. It has
# `elif not settings.DEBUG or urlsplit(prefix).netloc: return []` hard-coded
# inside it, so it silently registers NO url pattern at all whenever
# DEBUG=False -- no error, the /media/ route just quietly doesn't exist. That
# is the #1 cause of "images work on localhost but 404 in production".
#
# Instead we wire django.views.static.serve directly, gated by an explicit,
# toggleable settings flag (SERVE_MEDIA_VIA_DJANGO, defined in settings.py),
# so uploads work the same way in both DEBUG=True and DEBUG=False.
if getattr(settings, "SERVE_MEDIA_VIA_DJANGO", True):
    _media_url_path = settings.MEDIA_URL.lstrip("/")
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(_media_url_path),
            # Uploads rarely change: let browsers/CDNs cache them for 30 days
            # (django.views.static.serve already answers If-Modified-Since with 304).
            cache_control(public=True, max_age=60 * 60 * 24 * 365)(serve_media_with_range),
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]

# STATIC_URL fallback used to be DEBUG-only (`if settings.DEBUG: urlpatterns +=
# static(...)`), which is exactly why videos/images "work with DEBUG=True,
# break with DEBUG=False": WhiteNoiseMiddleware only serves what it indexed
# in memory at process start (WHITENOISE_AUTOREFRESH=False), built from
# STATIC_ROOT + finders. If a file was added to Home/static after the last
# `collectstatic`/app restart, or the manifest is stale, WhiteNoise's __call__
# falls through to get_response() -- and with DEBUG=False there used to be NO
# matching urlconf entry at all, so Django's own exception/404 handling took
# over instead of ever serving the file.
#
# Wiring this unconditionally (same pattern as the MEDIA_URL fix above) means
# WhiteNoise still serves the fast path when its index is warm, and this is
# only ever reached as a fallback -- but that fallback now exists in BOTH
# DEBUG=True and DEBUG=False. It uses staticfiles' own `serve()` view with
# insecure=True, which resolves through the STATICFILES_FINDERS (i.e. looks
# directly in Home/static, not just the collected/hashed STATIC_ROOT copy),
# so newly added video files work even before the next `collectstatic` run.
urlpatterns += [
    re_path(
        r"^%s(?P<path>.*)$" % re.escape(settings.STATIC_URL.lstrip("/")),
        serve_staticfiles,
        kwargs={"insecure": True},
    ),
]

handler404 = "DaySafaris.views.custom_404"
handler500 = "DaySafaris.views.custom_500"