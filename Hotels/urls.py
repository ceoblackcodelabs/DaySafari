from django.urls import path

from .views import HotelDetailView, HotelListView

urlpatterns = [
    path('hotels/', HotelListView.as_view(), name='hotels'),
    path('hotels/<slug:slug>/', HotelDetailView.as_view(), name='hotel_detail'),
]
