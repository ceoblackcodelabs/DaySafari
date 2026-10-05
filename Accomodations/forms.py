from django import forms
from .models import Accomodations, AirBNB
from ClientRequests.antispam import AntiSpamFormMixin
from ClientRequests.models import Bookings
from datetime import date

class AccomodationsForm(forms.ModelForm):
    class Meta:
        model = Accomodations
        fields = ['name', 'location', 'specification', 'description', 'price_per_night', 'max_guests']

class BNBbookingsForm(AntiSpamFormMixin, forms.ModelForm):
    """Airbnb enquiry; saved as a Bookings lead (booking_type='airbnb')."""

    class Meta:
        model = Bookings
        fields = ['name', 'email', 'phone', 'persons', 'date', 'check_out']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control bg-white border-0',
                                           'placeholder': 'Your Full Name', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control bg-white border-0',
                                             'placeholder': 'Your Email', 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control bg-white border-0',
                                            'placeholder': 'Phone / WhatsApp', 'required': 'required'}),
            'persons': forms.NumberInput(attrs={'class': 'form-control bg-white border-0',
                                                'placeholder': 'Number of Guests', 'min': 1,
                                                'required': 'required'}),
            'date': forms.DateInput(attrs={'class': 'form-control bg-white border-0', 'type': 'date',
                                           'required': 'required', 'min': date.today().isoformat()}),
            'check_out': forms.DateInput(attrs={'class': 'form-control bg-white border-0', 'type': 'date',
                                                'required': 'required', 'min': date.today().isoformat()}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['check_out'].required = True
        for f in ('name', 'email', 'phone', 'persons', 'date', 'check_out'):
            self.fields[f].label = False

    def clean_persons(self):
        persons = self.cleaned_data.get('persons')
        if persons is None or not 1 <= persons <= 50:
            raise forms.ValidationError('Guests must be between 1 and 50.')
        return persons

    def clean(self):
        cleaned = super().clean()
        check_in, check_out = cleaned.get('date'), cleaned.get('check_out')
        if check_in and check_in < date.today():
            self.add_error('date', 'Check-in cannot be in the past.')
        if check_in and check_out and check_out <= check_in:
            self.add_error('check_out', 'Check-out date must be after check-in date')
        return cleaned
