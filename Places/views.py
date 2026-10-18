from django.shortcuts import render
from django.views.generic import RedirectView, ListView, DetailView, TemplateView
from collections import defaultdict
from .models import (
    Destinations, AwesomePackages, DestinationsCategory, IncluisiveExcluisive
)
from django.contrib import messages
from django.utils.translation import gettext as _
from django.shortcuts import redirect
from django.urls import reverse
from datetime import date
from django.db.models import Prefetch


def group_destinations_by_category(categories):
    """Fetch ALL destinations in a single query and bucket them by category
    in Python. Replaces the old pattern of running one Destinations query
    PER category (an N+1 query per page load) used across the tour views
    below."""
    all_destinations = Destinations.objects.select_related('category').only(
        'id', 'name', 'image', 'price', 'category__id', 'category__category'
    )
    grouped = defaultdict(list)
    for destination in all_destinations:
        grouped[destination.category_id].append(destination)
    # Ensure every category key exists (even if empty) so templates that
    # look up a category id that has no destinations yet don't KeyError.
    return {category.id: grouped.get(category.id, []) for category in categories}


# Create your views here.
class DestinationDetailView(DetailView):
    model = Destinations
    context_object_name = 'destination'
    template_name = 'Destinations/destination_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get similar destinations (same category)
        similar_destinations = Destinations.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id).only('id', 'name', 'image', 'price', 'category')[:3]

        context['similar_destinations'] = similar_destinations

        # Has the logged-in user already saved this destination?
        if self.request.user.is_authenticated:
            context['is_saved'] = self.object.saved_by.filter(user=self.request.user).exists()
        else:
            context['is_saved'] = False

        return context


# tours
class TourView(RedirectView):
    """/tours/ has no page of its own; send visitors to the main tours listing."""
    pattern_name = 'east_africa_tours'
    permanent = False


class AfricaTourView(ListView):
    model = AwesomePackages
    context_object_name = "africaPackages"
    template_name = 'Tours/africa_tours.html'

    def get_queryset(self):
        return AwesomePackages.objects.filter(
            category__in=['East Africa Tours', 'South Africa', 'West Africa', 'Africa Tours']
        ).only('id', 'name', 'image', 'price', 'days', 'category', 'star_rating', 'location')[:12]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all destination categories for tabs
        categories = DestinationsCategory.objects.only('id', 'category', 'location', 'image_orientation').all()
        context['categories'] = categories

        # Get all destinations with select_related for optimization
        all_destinations = Destinations.objects.select_related('category').only(
            'id', 'name', 'image', 'price', 'category__id', 'category__category', 'category__image_orientation'
        )[:9]
        context['all_destinations'] = all_destinations

        # Organize destinations by category for filtering (single query,
        # grouped in Python -- see group_destinations_by_category above)
        context['destinations_by_category'] = group_destinations_by_category(categories)

        return context


class EastAfricaTourView(ListView):
    model = AwesomePackages
    context_object_name = "africaPackages"
    template_name = 'Tours/east_africa_tours.html'

    def get_queryset(self):
        return AwesomePackages.objects.filter(
            category='East Africa Tours'
        ).only('id', 'name', 'image', 'price', 'days', 'category', 'star_rating', 'location', 'slug')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all destination categories for tabs
        categories = DestinationsCategory.objects.only('id', 'category', 'location', 'image_orientation').all()
        context['categories'] = categories

        # Get all destinations
        all_destinations = Destinations.objects.select_related('category').only(
            'id', 'name', 'image', 'price', 'category__id', 'category__category', 'category__image_orientation'
        )[:9]
        context['all_destinations'] = all_destinations

        # Organize destinations by category for filtering (single query,
        # grouped in Python -- see group_destinations_by_category above)
        context['destinations_by_category'] = group_destinations_by_category(categories)

        return context


class SouthAfricaTourView(ListView):
    model = AwesomePackages
    context_object_name = "africaPackages"
    template_name = 'Tours/south_africa_tours.html'

    def get_queryset(self):
        return AwesomePackages.objects.filter(
            category='South Africa'
        ).only('id', 'name', 'image', 'price', 'days', 'category', 'star_rating', 'location', 'slug')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all destination categories for tabs
        categories = DestinationsCategory.objects.only('id', 'category', 'location', 'image_orientation').all()
        context['categories'] = categories

        # Get all destinations
        all_destinations = Destinations.objects.select_related('category').only(
            'id', 'name', 'image', 'price', 'category__id', 'category__category', 'category__image_orientation'
        )[:9]
        context['all_destinations'] = all_destinations

        # Organize destinations by category for filtering (single query,
        # grouped in Python -- see group_destinations_by_category above)
        context['destinations_by_category'] = group_destinations_by_category(categories)

        return context


class WestAfricaTourView(ListView):
    model = AwesomePackages
    context_object_name = "africaPackages"
    template_name = 'Tours/west_africa_tours.html'

    def get_queryset(self):
        return AwesomePackages.objects.filter(
            category='West Africa'
        ).only('id', 'name', 'image', 'price', 'days', 'category', 'star_rating', 'location', 'slug')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all destination categories for tabs
        categories = DestinationsCategory.objects.only('id', 'category', 'location', 'image_orientation').all()
        context['categories'] = categories

        # Get all destinations
        all_destinations = Destinations.objects.select_related('category').only(
            'id', 'name', 'image', 'price', 'category__id', 'category__category', 'category__image_orientation'
        )[:9]
        context['all_destinations'] = all_destinations

        # Organize destinations by category for filtering (single query,
        # grouped in Python -- see group_destinations_by_category above)
        context['destinations_by_category'] = group_destinations_by_category(categories)

        return context


class InternationalAfricaTourView(ListView):
    model = AwesomePackages
    context_object_name = "africaPackages"
    template_name = 'Tours/international_tours.html'

    def get_queryset(self):
        return AwesomePackages.objects.filter(
            category='International Tours'
        ).only('id', 'name', 'image', 'price', 'days', 'category', 'star_rating', 'location', 'slug')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all destination categories for tabs
        categories = DestinationsCategory.objects.only('id', 'category', 'location', 'image_orientation').all()
        context['categories'] = categories

        # Get all destinations
        all_destinations = Destinations.objects.select_related('category').only(
            'id', 'name', 'image', 'price', 'category__id', 'category__category', 'category__image_orientation'
        )[:9]
        context['all_destinations'] = all_destinations

        # Organize destinations by category for filtering (single query,
        # grouped in Python -- see group_destinations_by_category above)
        context['destinations_by_category'] = group_destinations_by_category(categories)

        return context


# packages
class PackagesDetailView(DetailView):
    model = AwesomePackages
    context_object_name = 'package'
    template_name = 'Packages/package_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        package = self.object

        # Get itineraries for this package
        context['itineraries'] = self.object.itineraries.all().order_by('day_number')
        context['gallery'] = list(self.object.gallery.all()[:12])

        # Get similar packages
        similar_packages = AwesomePackages.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id).only(
            'id', 'name', 'image', 'price', 'days', 'category', 'star_rating'
        )[:3]
        context['similar_packages'] = similar_packages

        # FIXED: Changed 'status' to 'is_inclusive'
        inclusive = IncluisiveExcluisive.objects.filter(
            package=package,
            is_inclusive=True  # Changed from 'status=True'
        ).only('id', 'name', 'is_inclusive')

        exclusive = IncluisiveExcluisive.objects.filter(
            package=package,
            is_inclusive=False  # Changed from 'status=False'
        ).only('id', 'name', 'is_inclusive')

        context['inclusive'] = inclusive
        context['exclusive'] = exclusive

        return context
