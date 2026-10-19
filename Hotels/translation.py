"""Which model fields are translated per language (django-modeltranslation)."""
from modeltranslation.translator import TranslationOptions, register

from .models import Hotel, HotelImage


@register(Hotel)
class HotelTranslationOptions(TranslationOptions):
    fields = ('location', 'summary', 'description', 'amenities', 'child_policy',)


@register(HotelImage)
class HotelImageTranslationOptions(TranslationOptions):
    fields = ('caption',)
