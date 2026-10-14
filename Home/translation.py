"""Which model fields are translated per language (django-modeltranslation)."""
from modeltranslation.translator import TranslationOptions, register

from .models import Services, GalleryCategory, AboutImage, HeroSlide, Testimonials, Blogs, BlogCategory, Brochure, ItineraryTreking, Trekking, Ad


@register(Services)
class ServicesTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)


@register(GalleryCategory)
class GalleryCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(AboutImage)
class AboutImageTranslationOptions(TranslationOptions):
    fields = ('caption',)


@register(HeroSlide)
class HeroSlideTranslationOptions(TranslationOptions):
    fields = ('eyebrow_text', 'title', 'subtitle', 'button_text',)


@register(Testimonials)
class TestimonialsTranslationOptions(TranslationOptions):
    fields = ('location', 'feedback',)


@register(Blogs)
class BlogsTranslationOptions(TranslationOptions):
    fields = ('title', 'seo_title', 'seo_description', 'content',)


@register(Brochure)
class BrochureTranslationOptions(TranslationOptions):
    fields = ('title', 'description',)


@register(ItineraryTreking)
class ItineraryTrekingTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'activities', 'accommodation', 'meals',)


@register(Trekking)
class TrekkingTranslationOptions(TranslationOptions):
    fields = ('name', 'location', 'description',)


@register(Ad)
class AdTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'button_text',)


@register(BlogCategory)
class BlogCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)
