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
import django
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static

urlpatterns = [
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
    path('SudoSu/', include('SuperMode.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "DaySafaris.views.custom_404"