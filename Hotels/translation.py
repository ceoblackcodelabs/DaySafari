"""Which model fields are translated per language (django-modeltranslation)."""
from modeltranslation.translator import TranslationOptions, register

from .models import Hotel, HotelImage, AirBNB, AirBNBImage


@register(Hotel)
class HotelTranslationOptions(TranslationOptions):
    fields = ('location', 'summary', 'description', 'amenities', 'child_policy',)


@register(HotelImage)
class HotelImageTranslationOptions(TranslationOptions):
    fields = ('caption',)


@register(AirBNB)
class AirBNBTranslationOptions(TranslationOptions):
    fields = ('title', 'location', 'description',)


@register(AirBNBImage)
class AirBNBImageTranslationOptions(TranslationOptions):
    fields = ('caption',)
