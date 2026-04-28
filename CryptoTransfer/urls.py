from django.urls import path
from .views import CryptoPaymentView

urlpatterns = [
    path('', CryptoPaymentView.as_view(), name='crypto_payment'),
]