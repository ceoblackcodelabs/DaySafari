from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView, CreateView, FormView
from .models import (Services, GalleryCategory, Gallery, Contact,
                     Bookings, Testimonials, Blogs
                     )
from Places.models import Destinations, DestinationsCategory, AwesomePackages
from colorama import Fore, Style
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import BookingsForm, ContactForm
from django.contrib import messages


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
        
        # Add empty booking form to context for GET request
        context['booking_form'] = BookingsForm()
        
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests - process booking form submission
        """
        # Create form instance with POST data
        form = BookingsForm(request.POST)
        
        if form.is_valid():
            # Save the booking
            booking = form.save()
            
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

    
class BookingCreateView(CreateView):
    model = Bookings
    form_class = BookingsForm
    template_name = 'bookings/booking_form.html'  # Update to your template path
    success_url = reverse_lazy('home')  # Create a success URL or use redirect
    
    def form_valid(self, form):
        # You can add additional logic here before saving
        response = super().form_valid(form)
        
        # Add success message
        messages.success(self.request, 
            f"Thank you {form.cleaned_data['name']}! Your booking request has been submitted successfully. "
            f"We will contact you within 24 hours to confirm your {form.cleaned_data['destination']} safari."
        )
        
        # Optional: Send email notification (you'll need to set up email backend)
        # self.send_booking_confirmation_email(form.cleaned_data)
        
        return response
    
    def form_invalid(self, form):
        # Add error message
        messages.error(self.request, 
            "There was an error with your booking. Please check the form and try again."
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data needed for the template
        context['title'] = 'Book Your Safari Adventure'
        context['destinations'] = Destinations.objects.all()[:5]  # Featured destinations
        context['packages'] = AwesomePackages.objects.all()[:3]  # Featured packages
        return context
    
    def send_booking_confirmation_email(self, booking_data):
        """Optional: Send confirmation email to user"""
        pass
    
class BookingDetailView(DetailView):
    model = Bookings
    context_object_name = 'booking'
    template_name = 'bookings/booking_detail.html' 
    
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
    
# contact  
class ContactView(FormView):
    template_name = 'Home/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')
    
    def form_valid(self, form):
        # Save the contact message
        contact = form.save()
        
        # Add success message
        messages.success(self.request, 
            f"Thank you {contact.name}! Your message has been sent successfully. "
            "We will get back to you within 24 hours."
        )
        
        # Optional: Send email notification
        # self.send_notification_email(contact)
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Contact Us - Day Safaris Adventures'
        return context