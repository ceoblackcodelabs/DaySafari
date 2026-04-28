from django.shortcuts import render
from django.views.generic import TemplateView
# Create your views here.

class BankTransferView(TemplateView):
    template_name = 'Bank/index.html'