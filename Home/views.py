from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'Home/index.html'
    
class AboutView(TemplateView):
    template_name = 'Home/about.html'
    
class ContactView(TemplateView):
    template_name = 'Home/contact.html'
    
# services
class ServicesView(TemplateView):
    template_name = 'Home/services.html'
    
class AfricanWildLifeToursView(TemplateView):
    template_name = 'Services/african_wildlife_tours.html'
    
class TravelPartnershipsView(TemplateView):
    template_name = 'Services/travel_partnerships.html'
    
class HolidayTailorMadeToursView(TemplateView):
    template_name = 'Services/holiday_tailor_made_tours.html'
    
class AirportTransfersView(TemplateView):
    template_name = 'Services/airport_transfers.html'

# tours
class TourView(TemplateView):
    template_name = 'Home/tours.html'
    
class AfricaTourView(TemplateView):
    template_name = 'Tours/africa_tours.html'
    
class EastAfricaTourView(TemplateView):
    template_name = 'Tours/east_africa_tours.html'
    
class InternationalAfricaTourView(TemplateView):
    template_name = 'Tours/international_africa_tours.html'
    
class BookingView(TemplateView):
    template_name = 'Home/booking.html'
    
class CruisesView(TemplateView):
    template_name = 'Home/cruises.html'
    
class AirLineView(TemplateView):
    template_name = 'Home/airline.html'
    
class BlogsView(TemplateView):
    template_name = 'Blogs/blogs.html'
    
class GalleryView(TemplateView):
    template_name = 'Home/gallery.html'
    
class AirBNBView(TemplateView):
    template_name = 'Home/airbnb.html'