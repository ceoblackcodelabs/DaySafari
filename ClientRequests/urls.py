from django.urls import path
from .views import (
    BookingCreateView, BookingDetailView, ContactView, lead_capture
)

urlpatterns = [
    # bookings
    path('booking/', BookingCreateView.as_view(), name='booking_create'),
    path('booking/<int:pk>/', BookingDetailView.as_view(), name='request_booking_detail'),
    
    path('contact/', ContactView.as_view(), name='contact'),
    path('lead/', lead_capture, name='lead_capture'),
]
