from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView, CreateView, FormView
from .models import (Services, GalleryCategory, Gallery,
                     Testimonials, Blogs
                     )
from OurClients.models import UserMessage
from Places.models import Destinations, DestinationsCategory, AwesomePackages
from colorama import Fore, Style
from django.urls import reverse_lazy
from django.shortcuts import redirect
from ClientRequests.forms import BookingsForm
from django.contrib import messages
from EmailSetup.utils import send_booking_confirmation


class HomeView(ListView):
    model = Services
    context_object_name = 'services'
    template_name = 'Home/index.html'
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests - display the homepage with booking form
        """
        # Call the parent get method to get the context
        self.object_list = self.get_queryset()
        context = self.get_context_data(**kwargs)
        
        # Pre-populate form if user is logged in
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            }
            if getattr(request.user, 'phone', None):
                initial_data['phone'] = getattr(request.user, 'phone', '')
        
        # Add empty booking form to context for GET request
        context['booking_form'] = BookingsForm(initial=initial_data)
        
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests - process booking form submission
        """
        # Create form instance with POST data
        form = BookingsForm(request.POST)
        
        if form.is_valid():
            # Save the booking
            booking = form.save(commit=False)
            
            # Check if user is logged in
            if request.user.is_authenticated:
                booking.client = request.user
                # Auto-fill name and email from user profile if not provided in form
                if not booking.name and request.user.get_full_name():
                    booking.name = request.user.get_full_name()
                elif not booking.name:
                    booking.name = request.user.username
                    
                if not booking.email and request.user.email:
                    booking.email = request.user.email
            else:
                booking.client = None
            
            # Save the booking to database
            
            booking.save()
            
            # Send booking confirmation email
            send_booking_confirmation(booking)

            # backup for email
            UserMessage.objects.create(
                user=request.user if request.user.is_authenticated else None,
                subject=f"Booking Confirmation - #{booking.id} - {booking.name}",
                priority='high',
                email_sent=True,
                message=f"Dear {booking.name},\n\nYour safari booking is confirmed!\n\nBooking ID: #{booking.id}\nDestination: {booking.destination.name if booking.destination else 'TBD'}\nTravel Date: {booking.date}\nPersons: {booking.persons}\n\n📌 Next steps:\n1. Our travel expert will contact you within 24 hours\n2. Pay 30% deposit to confirm your spot\n3. Receive your detailed itinerary\n\n❓ Questions? Call: +254 734 962 965\n\nWe look forward to hosting you in East Africa! 🦁\n\nThe Day Safaris Team"
            )

            # Add success message
            messages.success(
                request, 
                f"Thank you {booking.name}! Your booking request has been submitted successfully. "
                "We will contact you within 24 hours to confirm your safari adventure."
            )
            
            # Redirect to home page to prevent form resubmission
            return redirect('home')
        else:
            # Form is invalid - show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            # Get the normal context data
            self.object_list = self.get_queryset()
            context = self.get_context_data(**kwargs)
            
            # Add the invalid form to context to show errors
            context['booking_form'] = form
            
            return self.render_to_response(context)
    
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
            print(f"{Fore.RED}No services found in the database.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}Successfully retrieved {len(services2)} services from the database.{Style.RESET_ALL}")
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
        
        context['awesome_packages'] = AwesomePackages.objects.all()
        context['testimonials'] = Testimonials.objects.all().order_by('-id')[:6]
        context['blogs'] = Blogs.objects.all().order_by('-published_date')[:3]  # Latest 6 blogs
        
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
    
class CruisesView(TemplateView):
    template_name = 'Home/cruises.html'
    
class AirLineView(TemplateView):
    template_name = 'Home/airline.html'
    
class BlogsView(ListView):
    model = Blogs
    context_object_name = "blogs"
    template_name = 'Blogs/blogs.html'
    
class BlogDetailView(DetailView):
    model = Blogs
    context_object_name = 'blog'
    template_name = 'Blogs/blog_detail.html'

# Gallery
class GalleryView(ListView):
    model = Gallery
    template_name = 'Home/gallery.html'
    context_object_name = 'galleries'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all categories
        categories = GalleryCategory.objects.all()
        context['categories'] = categories
        
        # Get all galleries
        all_galleries = Gallery.objects.select_related('category')[:16]
        context['all_galleries'] = all_galleries
        
        # Group galleries by category
        galleries_by_category = {}
        for category in categories:
            galleries_by_category[category.id] = Gallery.objects.filter(category=category).select_related('category')
        
        context['galleries_by_category'] = galleries_by_category
        
        return context
    
