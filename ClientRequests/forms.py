from django import forms
from django.core.exceptions import ValidationError
from .models import Bookings, Contact
from Places.models import Destinations
from datetime import date, datetime, timedelta

# bookings
class BookingsForm(forms.ModelForm):
    class Meta:
        model = Bookings
        fields = ['name', 'email', 'phone', 'destination', 'persons', 'date', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Your Name',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Your Email',
                'required': 'required'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Phone Number',
                'required': 'required'
            }),
            'destination': forms.Select(attrs={
                'class': 'form-select bg-white border-0',
                'required': 'required'
            }),
            'persons': forms.Select(attrs={
                'class': 'form-select bg-white border-0',
                'required': 'required'
            }, choices=[(1, '1 Person'), (2, '2 Persons'), (3, '3 Persons'), (4, '4 Persons'), (5, '5 Persons'), (6, '6+ Persons')]),
            'date': forms.DateInput(attrs={
                'class': 'form-control bg-white border-0',
                'type': 'date',
                'required': 'required',
                'min': date.today().isoformat(),
                'placeholder': 'Select Date'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Special Requests (Dietary, Accessibility, etc.)',
                'rows': 3,
                'style': 'height: 100px'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set up destination choices
        self.fields['destination'].queryset = Destinations.objects.all().order_by('name')
        self.fields['destination'].empty_label = "Select Destination"
        
        # Set min date for date picker (today's date)
        self.fields['date'].widget.attrs['min'] = date.today().isoformat()
        
        # Customize labels (set to False for floating labels)
        self.fields['name'].label = False
        self.fields['email'].label = False
        self.fields['phone'].label = False
        self.fields['destination'].label = False
        self.fields['persons'].label = False
        self.fields['date'].label = False
        self.fields['message'].label = False
    
    def clean_persons(self):
        persons = self.cleaned_data.get('persons')
        if persons and persons < 1:
            raise ValidationError("Number of persons must be at least 1.")
        if persons and persons > 50:
            raise ValidationError("For groups larger than 50 persons, please contact us directly.")
        return persons
    
    def clean_date(self):
        booking_date = self.cleaned_data.get('date')
        if booking_date:
            if booking_date < date.today():
                raise ValidationError("Travel date cannot be in the past. Please select a future date.")
        return booking_date
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and '@' not in email:
            raise ValidationError("Please enter a valid email address.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove common separators
            cleaned_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            if len(cleaned_phone) < 10:
                raise ValidationError("Please enter a valid phone number with at least 10 digits.")
        return phone
    

class SudoBookingsForm(forms.ModelForm):
    class Meta:
        model = Bookings
        fields = ['name', 'email', 'phone', 'destination', 'persons', 'date', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email',
                'required': 'required'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number',
                'required': 'required'
            }),
            'destination': forms.Select(attrs={
                'class': 'form-control',
                'required': 'required'
            }),
            'persons': forms.Select(attrs={
                'class': 'form-control',
                'required': 'required'
            }, choices=[(1, '1 Person'), (2, '2 Persons'), (3, '3 Persons'), (4, '4 Persons'), (5, '5 Persons'), (6, '6+ Persons')]),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': 'required',
                'min': date.today().isoformat(),
                'placeholder': 'Select Date'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Special Requests (Dietary, Accessibility, etc.)',
                'rows': 3,
                'style': 'height: 100px'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set up destination choices
        self.fields['destination'].queryset = Destinations.objects.all().order_by('name')
        self.fields['destination'].empty_label = "Select Destination"
        
        # Set min date for date picker (today's date)
        self.fields['date'].widget.attrs['min'] = date.today().isoformat()
        
        # Customize labels (set to False for floating labels)
        self.fields['name'].label = False
        self.fields['email'].label = False
        self.fields['phone'].label = False
        self.fields['destination'].label = False
        self.fields['persons'].label = False
        self.fields['date'].label = False
        self.fields['message'].label = False
    
    def clean_persons(self):
        persons = self.cleaned_data.get('persons')
        if persons and persons < 1:
            raise ValidationError("Number of persons must be at least 1.")
        if persons and persons > 50:
            raise ValidationError("For groups larger than 50 persons, please contact us directly.")
        return persons
    
    def clean_date(self):
        booking_date = self.cleaned_data.get('date')
        if booking_date:
            if booking_date < date.today():
                raise ValidationError("Travel date cannot be in the past. Please select a future date.")
        return booking_date
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and '@' not in email:
            raise ValidationError("Please enter a valid email address.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove common separators
            cleaned_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            if len(cleaned_phone) < 10:
                raise ValidationError("Please enter a valid phone number with at least 10 digits.")
        return phone

#  contact
class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control border-0',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control border-0',
                'placeholder': 'Your Email'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control border-0',
                'placeholder': 'Subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control border-0',
                'placeholder': 'Leave a message here',
                'style': 'height: 160px'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and '@' not in email:
            raise forms.ValidationError("Please enter a valid email address.")
        return email
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name