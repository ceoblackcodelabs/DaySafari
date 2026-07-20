# forms.py
from django import forms
from Accomodations.models import AccomodationsImage
from .models import ItineraryBuilder, ItineraryActivity
from Places.models import Destinations

class ItineraryActivityForm(forms.ModelForm):
    class Meta:
        model = ItineraryActivity
        fields = ['day_number', 'title', 'description', 'location', 'duration']
        widgets = {
            'day_number': forms.NumberInput(attrs={
                'class': 'form-control day-number',
                'min': 1,
                'readonly': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Morning Game Drive'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the activity in detail...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Maasai Mara National Reserve'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 3 hours, Full day'
            }),
        }

class ItineraryBuilderForm(forms.ModelForm):
    """Custom form for ItineraryBuilder with image limit validation"""

    hotel_images = forms.ModelMultipleChoiceField(
        queryset=AccomodationsImage.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False,
        label='Hotel Images (Max 5)'
    )

    destination_images = forms.ModelMultipleChoiceField(
        queryset=Destinations.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False,
        label='Destination Images (Max 5)'
    )

    class Meta:
        model = ItineraryBuilder
        fields = [
            'title', 'client_name', 'days_spent', 'price',
            'description', 'hotel_images', 'destination_images'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter itinerary title'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
            'days_spent': forms.NumberInput(attrs={'class': 'form-control days-spent-input', 'min': 1, 'placeholder': 'Number of days'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Total price'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe the itinerary'}),
        }

    def clean_hotel_images(self):
        images = self.cleaned_data.get('hotel_images')
        if images and len(images) > 5:
            raise forms.ValidationError('You can select a maximum of 5 hotel images.')
        return images

    def clean_destination_images(self):
        images = self.cleaned_data.get('destination_images')
        if images and len(images) > 5:
            raise forms.ValidationError('You can select a maximum of 5 destination images.')
        return images

    def clean_days_spent(self):
        days = self.cleaned_data.get('days_spent')
        if days and days < 1:
            raise forms.ValidationError('Days spent must be at least 1.')
        return days

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError('Price cannot be negative.')
        return price