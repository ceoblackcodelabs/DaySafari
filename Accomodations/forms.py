from django import forms
from .models import Accomodations, AirBNB, AirBNBBooking
from datetime import date

class AccomodationsForm(forms.ModelForm):
    class Meta:
        model = Accomodations
        fields = ['name', 'location', 'specification', 'description', 'price_per_night', 'max_guests']

class BNBbookingsForm(forms.ModelForm):
    class Meta:
        model = AirBNBBooking
        fields = ['guest_name', 'guest_email', 'guests', 'check_in', 'check_out']
        widgets = {
            'guest_name': forms.TextInput(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Your Full Name',
                'required': 'required'
            }),
            'guest_email': forms.EmailInput(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Your Email',
                'required': 'required'
            }),
            'guests': forms.NumberInput(attrs={
                'class': 'form-control bg-white border-0',
                'placeholder': 'Number of Guests',
                'min': 1,
                'required': 'required'
            }),
            'check_in': forms.DateInput(attrs={
                'class': 'form-control bg-white border-0',
                'type': 'date',
                'required': 'required',
                'min': date.today().isoformat()
            }),
            'check_out': forms.DateInput(attrs={
                'class': 'form-control bg-white border-0',
                'type': 'date',
                'required': 'required',
                'min': date.today().isoformat()
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['guest_name'].label = False
        self.fields['guest_email'].label = False
        self.fields['guests'].label = False
        self.fields['check_in'].label = False
        self.fields['check_out'].label = False
    
    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        
        if check_in and check_out and check_out <= check_in:
            self.add_error('check_out', 'Check-out date must be after check-in date')
        
        return cleaned_data