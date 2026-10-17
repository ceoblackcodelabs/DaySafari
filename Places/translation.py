"""Which model fields are translated per language (django-modeltranslation)."""
from modeltranslation.translator import TranslationOptions, register

from .models import DestinationImage, DestinationsCategory, Destinations, IncluisiveExcluisive, AwesomePackages, Itinerary


@register(DestinationImage)
class DestinationImageTranslationOptions(TranslationOptions):
    fields = ('caption',)


@register(DestinationsCategory)
class DestinationsCategoryTranslationOptions(TranslationOptions):
    fields = ('location', 'category',)


@register(Destinations)
class DestinationsTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)


@register(IncluisiveExcluisive)
class IncluisiveExcluisiveTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(AwesomePackages)
class AwesomePackagesTranslationOptions(TranslationOptions):
    fields = ('name', 'location', 'description', 'seo_title', 'seo_description',)


@register(Itinerary)
class ItineraryTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'activities', 'accommodation', 'meals',)
