from django.urls import path
from .views import (HomeView, AboutView, ServicesView, 
                    CruisesView, AirLineView, BlogsView, GalleryView,
                    AfricanWildLifeToursView, TravelPartnershipsView, HolidayTailorMadeToursView, AirportTransfersView,
                    BlogDetailView
                    )

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    
    # services
    path('services/', ServicesView.as_view(), name='services'),
    path('african-wildlife-tours/', AfricanWildLifeToursView.as_view(), name='african_wildlife_tours'),
    path('travel-partnerships/', TravelPartnershipsView.as_view(), name='travel_partnerships'),
    path('holiday-tailor-made-tours/', HolidayTailorMadeToursView.as_view(), name='holiday_tailor_made_tours'),
    path('airport-transfers/', AirportTransfersView.as_view(), name='airport_transfers'),
    
    path('cruises/', CruisesView.as_view(), name='cruises'),
    path('airline/', AirLineView.as_view(), name='airline'),
    path('gallery/', GalleryView.as_view(), name='gallary'),
    
    # blogs
    path('blog/', BlogsView.as_view(), name='blog'),
    path('blog/<int:pk>/', BlogDetailView.as_view(), name='blog_detail'),
]