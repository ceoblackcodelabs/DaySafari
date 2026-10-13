from datetime import date

from django import forms

from ClientRequests.antispam import AntiSpamFormMixin
from ClientRequests.models import Bookings


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
        self.initial['date'] = None            # don't pre-fill today's date
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


class HotelEnquiryForm(AntiSpamFormMixin, forms.ModelForm):
    """Hotel enquiry; saved as a Bookings lead (booking_type='hotel')."""

    class Meta:
        model = Bookings
        fields = ['name', 'email', 'phone', 'persons', 'date', 'check_out', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email', 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone / WhatsApp', 'required': 'required'}),
            'persons': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Guests', 'min': 1, 'required': 'required'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': 'required',
                                           'min': date.today().isoformat()}),
            'check_out': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': 'required',
                                                'min': date.today().isoformat()}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                             'placeholder': 'Room preferences, special requests…'}),
        }

    def __init__(self, *args, **kwargs):
        self.hotel = kwargs.pop('hotel', None)
        super().__init__(*args, **kwargs)
        self.initial['date'] = None            # don't pre-fill today's date
        self.fields['check_out'].required = True
        self.fields['date'].label = 'Check-in'
        self.fields['check_out'].label = 'Check-out'
        self.fields['persons'].label = 'Guests'
        if self.hotel:
            self.fields['persons'].widget.attrs['max'] = self.hotel.max_guests

    def clean_persons(self):
        persons = self.cleaned_data.get('persons')
        if persons is None or persons < 1:
            raise forms.ValidationError('Guests must be at least 1.')
        if self.hotel and persons > self.hotel.max_guests:
            raise forms.ValidationError(f'This hotel sleeps up to {self.hotel.max_guests} guests. '
                                        'For larger groups please contact us.')
        return persons

    def clean(self):
        cleaned = super().clean()
        check_in, check_out = cleaned.get('date'), cleaned.get('check_out')
        if check_in and check_in < date.today():
            self.add_error('date', 'Check-in cannot be in the past.')
        if check_in and check_out and check_out <= check_in:
            self.add_error('check_out', 'Check-out must be after check-in.')
        return cleaned
