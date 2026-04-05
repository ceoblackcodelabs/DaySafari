from django.urls import path
from .views import HomeView, AboutView, ContactView, ServicesView, TourView, BookingView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('services/', ServicesView.as_view(), name='services'),
    path('tours/', TourView.as_view(), name='tours'),
    path('booking/', BookingView.as_view(), name='booking'),
]