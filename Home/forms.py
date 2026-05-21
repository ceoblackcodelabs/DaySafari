# forms.py

from django import forms
from .models import TrekkingBooking
from datetime import date

class TrekkingBookingForm(forms.ModelForm):
    class Meta:
        model = TrekkingBooking
        fields = [
            'full_name', 'email', 'phone_number',
            'number_of_persons', 'travel_date', 'special_requests'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'number_of_persons': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Number of persons'
            }),
            'travel_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': date.today().isoformat()
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Any special requests?',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        self.package = kwargs.pop('package', None)
        super().__init__(*args, **kwargs)

        if self.package:
            self.fields['number_of_persons'].widget.attrs['max'] = self.package.persons
            self.fields['number_of_persons'].help_text = f"Maximum {self.package.persons} persons"

    def clean_number_of_persons(self):
        persons = self.cleaned_data.get('number_of_persons')
        if self.package and persons > self.package.persons:
            raise forms.ValidationError(f"Maximum {self.package.persons} persons allowed for this package.")
        return persons

    def clean_travel_date(self):
        travel_date = self.cleaned_data.get('travel_date')
        if travel_date and travel_date < date.today():
            raise forms.ValidationError("Travel date cannot be in the past.")
        return travel_date