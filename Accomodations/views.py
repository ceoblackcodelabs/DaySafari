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

# Create your views here.
#  AirBNB
class AirBNBView(ListView):
    model = AirBNB
    context_object_name = 'bnbs'
    template_name = 'BNB/bnbs.html'
    
class AirBNBDetailView(DetailView):
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
        
        if form.is_valid():
            # Save the booking
            booking = form.save(commit=False)
            booking.airbnb = self.object
            
            # Calculate number of nights and total amount
            nights = (booking.check_out - booking.check_in).days
            if self.object.price_per_night:
                total_amount = self.object.price_per_night * nights
                booking.amount_paid = total_amount
            else:
                booking.amount_paid = Decimal('0.00')
            
            if request.user.is_authenticated:
                booking.user = request.user
            
            booking.save()
            
            # Send payment email to customer (you can integrate with your email system)
            messages.success(request, f'Successfully booked {self.object.title or self.object.location}! A confirmation has been sent to your email.')
            
            # Redirect to payment page or booking confirmation
            return redirect(reverse('bnb_detail', kwargs={'pk': booking.airbnb.id}))
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
        
        # Render the page with form errors
        return self.render_to_response(self.get_context_data(booking_form=form))
    

