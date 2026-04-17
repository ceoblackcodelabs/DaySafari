from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from .models import (Services, DestinationsCategory, Destinations,
                     
                     )
from colorama import Fore, Style


class HomeView(ListView):
    model = Services
    context_object_name = 'services'
    template_name = 'Home/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Services logic (your existing code)
        services1 = []
        services2 = []
        for i, service in enumerate(Services.objects.all()):
            if i <= 1:
                services1.append(service)
            else:
                services2.append(service)
        if len(services2) == 0: 
            print(f"{Fore.RED}No services found in the database.")
        else:
            print(f"{Fore.GREEN}Successfully retrieved {len(services2)} services from the database.")
        context['services1'] = services1
        context['services2'] = services2
        
        # Get all destination categories for tabs
        categories = DestinationsCategory.objects.all()
        context['categories'] = categories
        
        # Prepare destination data for each tab
        tab_destinations = {}
        
        # For "All Destinations" tab
        all_destinations = Destinations.objects.select_related('category').all()[:8]  # Limit to 8
        tab_destinations['all'] = self.organize_destinations(all_destinations)
        
        # For each category tab
        for category in categories:
            category_destinations = Destinations.objects.filter(
                category=category
            ).select_related('category')[:8]  # Limit to 8 per category
            tab_destinations[category.id] = self.organize_destinations(category_destinations)
        
        context['tab_destinations'] = tab_destinations
        
        return context
    
    def organize_destinations(self, destinations):
        """
        Organize destinations to have 1 portrait and 7 landscape images.
        If no portrait exists, use landscape for all.
        Returns a dictionary with explicit positions.
        """
        destinations_list = list(destinations)
        
        # Separate portrait and landscape
        portrait_destinations = [d for d in destinations_list if d.category.image_orientation == 'portrait']
        landscape_destinations = [d for d in destinations_list if d.category.image_orientation == 'landscape']
        
        # If we have less than 8 total, pad with None
        while len(destinations_list) < 8:
            destinations_list.append(None)
        
        # Organize into positions (7 landscape, 1 portrait)
        organized = {
            'landscape_1': None,   # position 1
            'landscape_2': None,   # position 2
            'landscape_3': None,   # position 3
            'landscape_4': None,   # position 4
            'landscape_5': None,   # position 5
            'landscape_6': None,   # position 6
            'landscape_7': None,   # position 7
            'portrait': None,      # position 8 (large right column)
        }
        
        # Assign portrait if available
        if portrait_destinations:
            organized['portrait'] = portrait_destinations[0]
            # Remove the used portrait from landscape pool if it was counted
            if portrait_destinations[0] in landscape_destinations:
                landscape_destinations.remove(portrait_destinations[0])
        
        # Assign landscape images to positions (max 7)
        landscape_positions = ['landscape_1', 'landscape_2', 'landscape_3', 'landscape_4', 
                               'landscape_5', 'landscape_6', 'landscape_7']
        
        for i, pos in enumerate(landscape_positions):
            if i < len(landscape_destinations):
                organized[pos] = landscape_destinations[i]
            elif i < len(destinations_list) and destinations_list[i] and destinations_list[i] != organized['portrait']:
                # Fallback to any other destination
                organized[pos] = destinations_list[i]
        
        return organized
    
class DestinationDetailView(DetailView):
    model = Destinations
    context_object_name = 'destination'
    template_name = 'Home/destination_detail.html'
    
class AboutView(ListView):
    model = Services
    context_object_name = 'services'
    template_name = 'Home/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        services1 = []
        services2 = []
        for i, service in enumerate(Services.objects.all()):
            if i <= 1:
                services1.append(service)
            else:
                services2.append(service)
        if len(services2) == 0: 
            print(f"{Fore.RED}No services found in the database.")
        else:
            print(f"{Fore.GREEN}Successfully retrieved {len(services2)} services from the database.")
        context['services1'] = services1
        context['services2'] = services2
        return context
    
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