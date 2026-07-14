from django.urls import path
from .views import (
    TourView, AfricaTourView, EastAfricaTourView,SouthAfricaTourView,
    WestAfricaTourView,
    InternationalAfricaTourView, DestinationDetailView, PackagesDetailView
)


urlpatterns = [
    path('destination/<int:pk>/', DestinationDetailView.as_view(), name='destination_detail'),

    # packages
    path('packages/<slug:slug>/', PackagesDetailView.as_view(), name='package_detail'),

    # tours
    path('tours/', TourView.as_view(), name='tours'),
    path('east-africa-tours/', EastAfricaTourView.as_view(), name='east_africa_tours'),
    path('south-africa-tours/', SouthAfricaTourView.as_view(), name='south_africa_tours'),
    path('west-africa-tours/', WestAfricaTourView.as_view(), name='west_africa_tours'),
    path('international-africa-tours/', InternationalAfricaTourView.as_view(), name='international_tours'),
]
