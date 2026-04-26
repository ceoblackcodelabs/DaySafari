from django import forms
from .models import Invoice
from decimal import Decimal

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer_name', 'invoice_title', 'invoice_description', 'amount', 'amount_paid', 'date']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter customer name'
            }),
            'invoice_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Safari Package - Masai Mara'
            }),
            'invoice_description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter invoice description or services provided',
                'rows': 3,
                'style': """
                    height: 100px;
                """
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        amount_paid = cleaned_data.get('amount_paid')
        
        if amount and amount_paid and amount_paid > amount:
            self.add_error('amount_paid', 'Amount paid cannot exceed total amount')
        
        return cleaned_data