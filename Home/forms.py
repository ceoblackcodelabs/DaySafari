from django import forms
from django.core.exceptions import ValidationError
from .models import Bookings, Destinations
from datetime import date

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
            'date': forms.Select(attrs={
                'class': 'form-select bg-white border-0',
                'required': 'required'
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
        
        # Set up date choices (next 6 months)
        from datetime import datetime, timedelta
        today = datetime.now().date()
        date_choices = []
        for i in range(6):
            next_month = today + timedelta(days=30*i)
            date_choices.append((next_month.strftime('%Y-%m'), next_month.strftime('%B %Y')))
        self.fields['date'].widget.choices = date_choices
        self.fields['date'].empty_label = "Select Date"
        
        # Customize labels
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
        return persons
    
    def clean_date(self):
        booking_date = self.cleaned_data.get('date')
        if booking_date:
            from datetime import datetime
            try:
                # Convert from YYYY-MM format to date
                booking_date_obj = datetime.strptime(booking_date, '%Y-%m').date()
                if booking_date_obj < datetime.now().date():
                    raise ValidationError("Travel date cannot be in the past. Please select a future date.")
            except:
                pass
        return booking_date