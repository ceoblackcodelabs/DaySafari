from django.urls import path
from .views import PaymentDashboardView, PaymentSuccessView, PayFromBookings

urlpatterns = [
    path('payment/<int:purchase_id>/', PaymentDashboardView.as_view(), name='payment_dashboard'),
    path('payment/<int:purchase_id>/success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/from-bookings/<int:booking_pk>/', PayFromBookings.as_view(), name='payment_from_bookings'),
]