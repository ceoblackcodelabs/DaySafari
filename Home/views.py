from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'Home/index.html'
    
class AboutView(TemplateView):
    template_name = 'Home/about.html'
    
class ContactView(TemplateView):
    template_name = 'Home/contact.html'
    
class ServicesView(TemplateView):
    template_name = 'Home/services.html'
    
class TourView(TemplateView):
    template_name = 'Home/tours.html'
    
class BookingView(TemplateView):
    template_name = 'Home/booking.html'