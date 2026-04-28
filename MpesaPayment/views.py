from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.
class MpesaPaymentView(TemplateView):
    template_name = 'Mpesa/index.html'