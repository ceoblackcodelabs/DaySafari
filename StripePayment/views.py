from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.
class StripePaymentView(TemplateView):
    template_name = 'Stripe/index.html'