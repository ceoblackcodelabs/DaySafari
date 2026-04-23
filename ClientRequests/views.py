from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, FormView
from Places.models import AwesomePackages, Destinations
from .models import (
    Bookings, Contact
)
from .forms import (
    BookingsForm, ContactForm
)

# Create your views here.
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
    
# contact views
class ContactView(FormView):
    template_name = 'Requests/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')
    
    def form_valid(self, form):
        # Save the contact message with commit=False
        contact = form.save(commit=False)
        
        # Check if user is logged in and associate with the contact
        if self.request.user.is_authenticated:
            contact.client = self.request.user
            
            # Auto-fill name and email from user profile if fields are empty
            if not contact.name and self.request.user.get_full_name():
                contact.name = self.request.user.get_full_name()
            elif not contact.name:
                contact.name = self.request.user.username
                
            if not contact.email and self.request.user.email:
                contact.email = self.request.user.email
        else:
            contact.user = None
        
        # Save to database
        contact.save()
        
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
        
        # Pre-populate form if user is logged in
        if self.request.user.is_authenticated and not self.request.POST:
            initial_data = {
                'name': self.request.user.get_full_name() or self.request.user.username,
                'email': self.request.user.email,
            }
            context['form'] = self.form_class(initial=initial_data)
        
        context['title'] = 'Contact Us - Day Safaris Adventures'
        context['user'] = self.request.user
        
        return context