from django.urls import path
from .views import (
    BookingCreateView, BookingDetailView, ContactView
)

urlpatterns = [
    # bookings
    path('booking/', BookingCreateView.as_view(), name='booking_create'),
    path('booking/<int:pk>/', BookingDetailView.as_view(), name='book_package'),
    
    path('contact/', ContactView.as_view(), name='contact'),
]
