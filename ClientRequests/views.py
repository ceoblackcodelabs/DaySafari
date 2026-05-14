from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, FormView
from EmailSetup.utils import send_contact_response, send_booking_confirmation, send_booking_verification
from Places.models import AwesomePackages, Destinations
from django.utils import timezone
from time import sleep
from .models import (
    Bookings, Contact
)
from Home.models import Brochure
from .forms import (
    BookingsForm, ContactForm
)

from OurClients.models import UserMessage
import threading

def send_emails_async(booking):
    """Send emails in background thread"""
    send_booking_confirmation(booking)
    sleep(10)
    send_booking_verification(booking)

# Create your views here.
class BookingCreateView(CreateView):
    model = Bookings
    form_class = BookingsForm
    template_name = 'Requests/booking.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        # Set the client if user is logged in
        if self.request.user.is_authenticated:
            form.instance.client = self.request.user

        response = super().form_valid(form)

        # Add success message
        messages.success(self.request,
            f"Thank you {form.cleaned_data['name']}! Your booking request has been submitted successfully. "
            f"We will contact you within 24 hours to confirm your safari."
        )

        # Send emails in background thread (non-blocking)
        thread = threading.Thread(target=send_emails_async, args=(self.object,))
        thread.daemon = True
        thread.start()

        return response

    def form_invalid(self, form):
        # Add error message
        messages.error(self.request,
            "There was an error with your booking. Please check the form and try again."
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Book Your Safari Adventure'
        context['destinations'] = Destinations.objects.all()[:5]
        context['packages'] = AwesomePackages.objects.all()[:3]

        # Pre-fill form for logged-in users
        if self.request.user.is_authenticated:
            initial = {
                'name': f"{self.request.user.first_name} {self.request.user.last_name}".strip() or self.request.user.username,
                'email': self.request.user.email,
            }
            context['form'] = BookingsForm(initial=initial)

        return context

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

        send_contact_response(contact)  # Send email response to user

        # Store the contact message in UserMessage
        UserMessage.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            subject=f"Contact Message from {contact.name}",
            priority='medium',
            email_sent=True,
            email_sent_at=timezone.now(),
            message=f"""Dear {contact.name},

        Thank you for reaching out to Day Safaris Adventures!

        Your message:
        "{contact.message}"

        We have received your message and will respond within 24 hours.

        In the meantime, you can reach us at:
        📞 Call: +254759379600
        💬 WhatsApp: +254 783 457 058
        📧 Email: info@daysafarisadventures.co.ke

        Warm regards,
        The Day Safaris Team 🦁"""
        )

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

        context['brochures'] = Brochure.objects.all()[:3]
        context['title'] = 'Contact Us - Day Safaris Adventures'
        context['user'] = self.request.user

        return context