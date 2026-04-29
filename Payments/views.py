# views.py
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from Places.models import PackagePurchase
from ClientRequests.models import Bookings
from decimal import Decimal

class PaymentDashboardView(TemplateView):
    template_name = 'Payments/payment_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase_id = self.kwargs.get('purchase_id')
        
        # Get the purchase
        purchase = get_object_or_404(PackagePurchase, id=purchase_id)
        package = purchase.package
        
        # Calculate totals - Convert everything to Decimal
        subtotal = package.price * Decimal(purchase.number_of_persons)
        tax = subtotal * Decimal('0.16')  # 16% VAT as Decimal
        total = subtotal + tax
        
        context['purchase'] = purchase
        context['package'] = package
        context['subtotal'] = subtotal
        context['tax'] = tax
        context['total'] = total
        context['persons'] = purchase.number_of_persons
        context['payment_methods'] = [
            {'id': 'mpesa', 'name': 'M-Pesa', 'icon': 'fab fa-empire', 'color': '#28a745'},
            {'id': 'stripe', 'name': 'Credit/Debit Card', 'icon': 'fab fa-cc-visa', 'color': '#6772e5'},
            {'id': 'bank', 'name': 'Bank Transfer', 'icon': 'fas fa-university', 'color': '#fd7e14'},
            {'id': 'crypto', 'name': 'Cryptocurrency', 'icon': 'fab fa-bitcoin', 'color': '#f7931a'},
        ]
        
        return context
    
class PaymentSuccessView(TemplateView):
    template_name = 'Payments/payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase_id = self.kwargs.get('purchase_id')
        context['purchase'] = get_object_or_404(PackagePurchase, id=purchase_id)
        return context


class PayFromBookings(TemplateView):
    template_name = 'Payments/pay_from_bookings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking_id = self.kwargs.get('booking_pk')
        bookings = get_object_or_404(Bookings, id=booking_id)
        sub_total = bookings.persons * bookings.destination.price
        tax_amount = (16 * sub_total) / 100
        total_amount = sub_total + tax_amount

        context['booking_purchase'] = bookings
        context.update(
            {
                "sub_total": sub_total,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "payment_methods": [
                    {'id': 'mpesa', 'name': 'M-Pesa', 'icon': 'fab fa-empire', 'color': '#28a745'},
                    {'id': 'stripe', 'name': 'Credit/Debit Card', 'icon': 'fab fa-cc-visa', 'color': '#6772e5'},
                    {'id': 'bank', 'name': 'Bank Transfer', 'icon': 'fas fa-university', 'color': '#fd7e14'},
                    {'id': 'crypto', 'name': 'Cryptocurrency', 'icon': 'fab fa-bitcoin', 'color': '#f7931a'},
                ]
            }
        )
        return context
    
    def post(self, request, *args, **kwargs):
        booking_id = self.kwargs.get('booking_pk')
        booking = get_object_or_404(Bookings, id=booking_id)
        
        # Here you would handle the payment processing logic
        # For demonstration, we'll just mark it as paid and redirect to success
        
        booking.is_paid = True
        booking.save()
        
        messages.success(request, 'Payment successful!')
        return redirect(reverse('payment_success', kwargs={'purchase_id': booking.id}))