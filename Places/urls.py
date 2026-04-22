from django.urls import path
from .views import (
    TourView, AfricaTourView, EastAfricaTourView, 
    InternationalAfricaTourView, DestinationDetailView, PackagesDetailView
)


urlpatterns = [
    path('destination/<int:pk>/', DestinationDetailView.as_view(), name='destination_detail'),
    
    # packages
    path('packages/<int:pk>/', PackagesDetailView.as_view(), name='package_detail'),
    
    # tours
    path('tours/', TourView.as_view(), name='tours'),
    path('africa-tours/', AfricaTourView.as_view(), name='africa_tours'),
    path('east-africa-tours/', EastAfricaTourView.as_view(), name='east_africa_tours'),
    path('international-africa-tours/', InternationalAfricaTourView.as_view(), name='international_africa_tours'),
]
