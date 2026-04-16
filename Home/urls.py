from django.urls import path
from .views import (HomeView, AboutView, ContactView, 
                    ServicesView, TourView, BookingView,
                    AfricaTourView, EastAfricaTourView, InternationalAfricaTourView,
                    CruisesView, AirLineView, BlogsView, GalleryView, AirBNBView,
                    AfricanWildLifeToursView, TravelPartnershipsView, HolidayTailorMadeToursView, AirportTransfersView
                    )

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    
    # services
    path('services/', ServicesView.as_view(), name='services'),
    path('african-wildlife-tours/', AfricanWildLifeToursView.as_view(), name='african_wildlife_tours'),
    path('travel-partnerships/', TravelPartnershipsView.as_view(), name='travel_partnerships'),
    path('holiday-tailor-made-tours/', HolidayTailorMadeToursView.as_view(), name='holiday_tailor_made_tours'),
    path('airport-transfers/', AirportTransfersView.as_view(), name='airport_transfers'),
    
    path('cruises/', CruisesView.as_view(), name='cruises'),
    path('airline/', AirLineView.as_view(), name='airline'),
    path('blog/', BlogsView.as_view(), name='blog'),
    path('packages/', GalleryView.as_view(), name='packages'),
    path('airbnb/', AirBNBView.as_view(), name='airbnb'),

    # tours
    path('tours/', TourView.as_view(), name='tours'),
    path('africa-tours/', AfricaTourView.as_view(), name='africa_tours'),
    path('east-africa-tours/', EastAfricaTourView.as_view(), name='east_africa_tours'),
    path('international-africa-tours/', InternationalAfricaTourView.as_view(), name='international_africa_tours'),
    # bookings
    path('booking/', BookingView.as_view(), name='booking'),
]