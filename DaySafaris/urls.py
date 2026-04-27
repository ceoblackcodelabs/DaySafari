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
from django.conf.urls.static import static  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('OurClients.urls')),
    path('', include('Home.urls')),
    path('', include('Places.urls')),
    path('', include('ClientRequests.urls')),
    path('', include("Accomodations.urls")),
    path('', include('ChatBot.urls')),
    # path('', include('FinanceManagement.urls')),
    path('SudoSu/', include('SuperMode.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)