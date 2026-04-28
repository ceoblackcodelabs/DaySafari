from django.urls import path
from .views import PaymentDashboardView, PaymentSuccessView

urlpatterns = [
    path('payment/<int:purchase_id>/', PaymentDashboardView.as_view(), name='payment_dashboard'),
    path('payment/<int:purchase_id>/success/', PaymentSuccessView.as_view(), name='payment_success'),
]