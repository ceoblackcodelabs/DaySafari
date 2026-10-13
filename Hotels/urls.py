from django.urls import path

from .views import AirBNBDetailView, AirBNBView, HotelDetailView, HotelListView

urlpatterns = [
    path('hotels/', HotelListView.as_view(), name='hotels'),
    path('hotels/<slug:slug>/', HotelDetailView.as_view(), name='hotel_detail'),
    # airbnb stays (unchanged URLs and names)
    path('airbnb/', AirBNBView.as_view(), name='airbnb'),
    path('airbnb/<int:pk>/', AirBNBDetailView.as_view(), name='bnb_detail'),
]
