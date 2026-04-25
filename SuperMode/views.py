from django.shortcuts import render
from django.views.generic import TemplateView

class AdminDashboardView(TemplateView):
    template_name = 'Dashboard/index.html'