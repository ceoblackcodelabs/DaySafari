# views.py
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from Places.models import PackagePurchase
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