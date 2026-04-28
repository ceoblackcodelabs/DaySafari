from django.urls import path
from .views import StripePaymentView

urlpatterns = [
    path('', StripePaymentView.as_view(), name='stripe_payment'),
]