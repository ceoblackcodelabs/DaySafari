from django.urls import path
from .views import MpesaPaymentView

urlpatterns = [
    path('', MpesaPaymentView.as_view(), name='mpesa_payment'),
]