from datetime import date

from django import forms

from ClientRequests.antispam import AntiSpamFormMixin
from ClientRequests.models import Bookings


class TrekkingBookingForm(AntiSpamFormMixin, forms.ModelForm):
    """Trekking enquiry; saved as a Bookings lead (booking_type='trekking')."""

    class Meta:
        model = Bookings
        fields = ['name', 'email', 'phone', 'persons', 'date', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'persons': forms.NumberInput(attrs={'class': 'form-control', 'min': 1,
                                                'placeholder': 'Number of persons'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date',
                                           'min': date.today().isoformat()}),
            'message': forms.Textarea(attrs={'class': 'form-control',
                                             'placeholder': 'Any special requests?', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.package = kwargs.pop('package', None)
        super().__init__(*args, **kwargs)
        self.fields['persons'].min_value = 1
        if self.package:
            self.fields['persons'].widget.attrs['max'] = self.package.persons
            self.fields['persons'].help_text = f"Maximum {self.package.persons} persons"

    def clean_persons(self):
        persons = self.cleaned_data.get('persons')
        if persons is None or persons < 1:
            raise forms.ValidationError("Number of persons must be at least 1.")
        if self.package and persons > self.package.persons:
            raise forms.ValidationError(f"Maximum {self.package.persons} persons allowed for this package.")
        return persons

    def clean_date(self):
        travel_date = self.cleaned_data.get('date')
        if travel_date and travel_date < date.today():
            raise forms.ValidationError("Travel date cannot be in the past.")
        return travel_date
