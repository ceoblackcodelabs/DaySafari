from django import forms
from django.core.exceptions import ValidationError
from .models import AwesomePackages, PackagePurchase
from datetime import date

class PackagePurchaseForm(forms.ModelForm):
    class Meta:
        model = PackagePurchase
        fields = ['full_name', 'email', 'phone_number', 'number_of_persons', 'travel_date', 'special_requests']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Your Full Name',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Your Email',
                'required': 'required'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Phone Number',
                'required': 'required'
            }),
            'number_of_persons': forms.Select(attrs={
                'class': 'form-select bg-white border-0',
                'required': 'required'
            }, choices=[(1, '1 Person'), (2, '2 Persons'), (3, '3 Persons'), (4, '4 Persons'), 
                       (5, '5 Persons'), (6, '6 Persons'), (7, '7 Persons'), (8, '8 Persons'), 
                       (9, '9 Persons'), (10, '10+ Persons')]),
            'travel_date': forms.DateInput(attrs={
                'class': 'form-control bg-white border-0',
                'type': 'date',
                'required': 'required',
                'min': date.today().isoformat(),
                'placeholder': 'Select Date'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Special Requests (Dietary, Accessibility, etc.)',
                'rows': 3,
                'style': 'height: 100px'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.package = kwargs.pop('package', None)
        super().__init__(*args, **kwargs)
        
        # Set min date for date picker (today's date)
        self.fields['travel_date'].widget.attrs['min'] = date.today().isoformat()
        
        # Customize labels (set to False for floating labels)
        self.fields['full_name'].label = False
        self.fields['email'].label = False
        self.fields['phone_number'].label = False
        self.fields['number_of_persons'].label = False
        self.fields['travel_date'].label = False
        self.fields['special_requests'].label = False
    
    def clean_number_of_persons(self):
        persons = self.cleaned_data.get('number_of_persons')
        if persons and persons < 1:
            raise ValidationError("Number of persons must be at least 1.")
        
        # Check max persons for the package
        if self.package and persons > self.package.persons:
            raise ValidationError(f"This package can only accommodate up to {self.package.persons} persons. Please contact us for group bookings.")
        
        return persons
    
    def clean_travel_date(self):
        travel_date = self.cleaned_data.get('travel_date')
        if travel_date and travel_date < date.today():
            raise ValidationError("Travel date cannot be in the past. Please select a future date.")
        return travel_date
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and '@' not in email:
            raise ValidationError("Please enter a valid email address.")
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove common separators
            cleaned_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            if len(cleaned_phone) < 10:
                raise ValidationError("Please enter a valid phone number with at least 10 digits.")
        return phone