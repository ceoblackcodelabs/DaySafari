import re
from datetime import date

from django import forms
from django.utils.translation import gettext_lazy as _

from ClientRequests.antispam import AntiSpamFormMixin
from ClientRequests.models import Bookings

_LINKISH = re.compile(r'https?|www|\.[a-z]{2,}', re.I)


class HotelEnquiryForm(AntiSpamFormMixin, forms.ModelForm):
    """Hotel enquiry; saved as a Bookings lead (booking_type='hotel')."""

    traveling_with_children = forms.ChoiceField(
        required=False, initial='no', label=_('Travelling with children?'),
        choices=[('no', _('No children')), ('yes', _('Yes, with children'))],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = Bookings
        fields = ['name', 'email', 'phone', 'persons', 'date', 'check_out', 'children_count', 'children_ages', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Your full name'), 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Your email'), 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Phone / WhatsApp'), 'required': 'required'}),
            'persons': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Guests'), 'min': 1, 'required': 'required'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': 'required',
                                           'min': date.today().isoformat()}),
            'check_out': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': 'required',
                                                'min': date.today().isoformat()}),
            'children_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10,
                                                       'placeholder': _('How many?')}),
            'children_ages': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 60,
                                                    'placeholder': _('Ages, e.g. 4, 7')}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                             'placeholder': _('Room preferences, special requests…')}),
        }

    def __init__(self, *args, **kwargs):
        self.hotel = kwargs.pop('hotel', None)
        super().__init__(*args, **kwargs)
        self.initial['date'] = None            # don't pre-fill today's date
        self.fields['check_out'].required = True
        self.fields['date'].label = _('Check-in')
        self.fields['check_out'].label = _('Check-out')
        self.fields['persons'].label = _('Guests (including children)')
        self.fields['children_count'].label = _('Number of children')
        self.fields['children_ages'].label = _("Children's ages")
        self.fields['children_count'].required = False
        self.fields['children_ages'].required = False
        if self.hotel:
            self.fields['persons'].widget.attrs['max'] = self.hotel.max_guests

    def clean_persons(self):
        persons = self.cleaned_data.get('persons')
        if persons is None or persons < 1:
            raise forms.ValidationError(_('Guests must be at least 1.'))
        if self.hotel and persons > self.hotel.max_guests:
            raise forms.ValidationError(_('This hotel sleeps up to %(n)s guests. '
                                        'For larger groups please contact us.') % {'n': self.hotel.max_guests})
        return persons

    def clean_children_ages(self):
        ages = (self.cleaned_data.get('children_ages') or '').strip()
        if ages and not re.fullmatch(r"[0-9A-Za-z ,.\-/&]{1,60}", ages):
            raise forms.ValidationError(_('Please enter ages as numbers, e.g. 4, 7.'))
        if _LINKISH.search(ages):
            raise forms.ValidationError(_('Please enter ages as numbers, e.g. 4, 7.'))
        return ages

    def clean(self):
        cleaned = super().clean()
        check_in, check_out = cleaned.get('date'), cleaned.get('check_out')
        if check_in and check_in < date.today():
            self.add_error('date', _('Check-in cannot be in the past.'))
        if check_in and check_out and check_out <= check_in:
            self.add_error('check_out', _('Check-out must be after check-in.'))

        with_kids = cleaned.get('traveling_with_children') == 'yes'
        count, persons = cleaned.get('children_count'), cleaned.get('persons')
        if with_kids:
            if not count or not 1 <= count <= 10:
                self.add_error('children_count', _('Please tell us how many children (1 to 10).'))
            elif persons and count > persons:
                self.add_error('children_count', _('Children cannot be more than the total number of guests.'))
        else:
            cleaned['children_count'] = None
            cleaned['children_ages'] = ''
        self._with_kids = with_kids
        return cleaned

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.has_children = bool(getattr(self, '_with_kids', False))
        if not booking.has_children:
            booking.children_count, booking.children_ages = None, ''
        if commit:
            booking.save()
        return booking
