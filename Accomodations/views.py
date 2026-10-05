from django.shortcuts import render
from django.views.generic import ListView, DetailView

from EmailSetup.utils import send_package_payment_email
from .models import (
    AccomodationsImage, Accomodations, AirBNB, AirBNBImage
)
from django.views.generic import TemplateView
from .forms import AccomodationsForm, BNBbookingsForm
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from decimal import Decimal
import threading
from ClientRequests.antispam import AntiSpamViewMixin
from EmailSetup.utils import send_booking_confirmation, notify_staff_of_lead

# Create your views here.
#  AirBNB
class AirBNBView(ListView):
    model = AirBNB
    context_object_name = 'bnbs'
    template_name = 'BNB/bnbs.html'
    
class AirBNBDetailView(AntiSpamViewMixin, DetailView):
    antispam_scope = 'airbnb'
    model = AirBNB
    context_object_name = 'bnb'
    template_name = "BNB/bnbs_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_images'] = self.object.images.all().order_by('order')
        context['featured_image'] = context['all_images'].filter(is_featured=True).first() or context['all_images'].first()
        
        # Initialize form with user data if logged in
        initial_data = {}
        if self.request.user.is_authenticated:
            initial_data = {
                'guest_name': f"{self.request.user.first_name} {self.request.user.last_name}".strip() or self.request.user.username,
                'guest_email': self.request.user.email,
            }
        
        # If form was submitted with errors, use the submitted form
        if 'booking_form' not in context:
            context['booking_form'] = BNBbookingsForm(initial=initial_data)
        
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = BNBbookingsForm(request.POST)

        if not form.is_valid():
            if form.spam_detected:
                return self.form_invalid(form)  # AntiSpamViewMixin: strike + 400
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return self.render_to_response(self.get_context_data(booking_form=form))

        booking = form.save(commit=False)
        booking.booking_type = 'airbnb'
        booking.airbnb = self.object
        if request.user.is_authenticated:
            booking.client = request.user
        booking.save()

        notify_staff_of_lead(booking)
        threading.Thread(target=send_booking_confirmation, args=(booking,), daemon=True).start()
        messages.success(request, f'Thank you {booking.name}! Your request for '
                                  f'{self.object.title or self.object.location} was received. '
                                  'We will contact you shortly to confirm availability.')
        return redirect(reverse('bnb_detail', kwargs={'pk': self.object.id}))
