from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Prefetch, Q, Count
from django.db.models.functions import Random
from django.utils.html import strip_tags
from django.core.cache import cache
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from .models import (
    Brochure, Services, GalleryCategory, Gallery,
    Testimonials, Blogs, Trekking, ItineraryTreking,
    Ad
)
from Places.models import Destinations, DestinationsCategory, AwesomePackages, IncluisiveExcluisive
from ClientRequests.forms import BookingsForm
from .forms import TrekkingBookingForm
from EmailSetup.utils import send_booking_confirmation
from colorama import Fore, Style

import logging

logger = logging.getLogger(__name__)


class HomeView(ListView):
    """Homepage with optimized queries and caching"""
    model = Services
    context_object_name = 'services'
    template_name = 'Home/index.html'
    paginate_by = None

    def get_queryset(self):
        """Return only necessary fields for services"""
        return Services.objects.only('id', 'name', 'icon', 'description')[:6]

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data(**kwargs)

        initial_data = {}
        if request.user.is_authenticated:
            user = request.user
            initial_data.update({
                'name': user.get_full_name() or user.username,
                'email': user.email,
            })
            if hasattr(user, 'phone') and user.phone:
                initial_data['phone'] = user.phone

        context['booking_form'] = BookingsForm(initial=initial_data)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = BookingsForm(request.POST)

        if form.is_valid():
            booking = form.save(commit=False)

            if request.user.is_authenticated:
                booking.client = request.user
                if not booking.name:
                    booking.name = request.user.get_full_name() or request.user.username
                if not booking.email:
                    booking.email = request.user.email
            else:
                booking.client = None

            booking.save()

            try:
                send_booking_confirmation(booking)
            except Exception as e:
                logger.error(f"Email sending failed: {e}")

            messages.success(
                request,
                f"Thank you {booking.name}! Your booking request has been submitted successfully. "
                "We will contact you within 24 hours."
            )
            return redirect('home')

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

        self.object_list = self.get_queryset()
        context = self.get_context_data(**kwargs)
        context['booking_form'] = form
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Try to get cached data
        cache_key = f'home_context_data_{self.request.user.is_authenticated}'
        cached_data = cache.get(cache_key)

        if cached_data:
            context.update(cached_data)
            return context

        # Services already in object_list
        services = self.object_list
        context['services1'] = services[:3]
        context['services2'] = services[3:]

        # Categories
        categories = DestinationsCategory.objects.only(
            'id', 'location', 'category', 'image', 'image_orientation'
        ).all()
        context['categories'] = categories

        # Destinations - optimized with prefetch
        destinations_query = Destinations.objects.select_related('category').only(
            'id', 'name', 'image', 'price', 'category__id',
            'category__image_orientation'
        )

        # Get all destinations for "All" tab
        all_destinations = destinations_query[:8]
        context['tab_destinations'] = {
            'all': self._organize_destinations(all_destinations)
        }

        # Add category-specific destinations
        for category in categories:
            cat_destinations = destinations_query.filter(category=category)[:8]
            context['tab_destinations'][category.id] = self._organize_destinations(cat_destinations)

        # Packages with only necessary fields - FIXED: use star_rating not starRating
        context['awesome_packages'] = AwesomePackages.objects.only(
            'id', 'name', 'image', 'price', 'days', 'star_rating'
        ).all()[:4]

        # Testimonials
        context['testimonials'] = Testimonials.objects.only(
            'id', 'name', 'image', 'feedback', 'location'
        ).order_by('-id')[:6]

        # Blogs
        context['blogs'] = Blogs.objects.only(
            'id', 'title', 'image', 'published_date', 'author', 'slug'
        ).order_by('-published_date')[:3]

        # Cache data for 15 minutes (only for non-authenticated users)
        if not self.request.user.is_authenticated:
            cache_data = {
                k: v for k, v in context.items()
                if k in ['services1', 'services2', 'categories',
                       'tab_destinations', 'awesome_packages',
                       'testimonials', 'blogs']
            }
            cache.set(cache_key, cache_data, 900)

        return context

    def _organize_destinations(self, destinations):
        """Organize destinations with proper orientation"""
        if not destinations:
            return self._empty_destination_layout()

        portrait = []
        landscape = []

        for dest in destinations:
            if hasattr(dest, 'category') and dest.category.image_orientation == 'portrait':
                portrait.append(dest)
            else:
                landscape.append(dest)

        layout = self._empty_destination_layout()

        if portrait:
            layout['portrait'] = portrait[0]

        landscape_positions = ['landscape_1', 'landscape_2', 'landscape_3',
                              'landscape_4', 'landscape_5', 'landscape_6', 'landscape_7']

        available_landscapes = landscape.copy()
        if portrait and portrait[0] in available_landscapes:
            available_landscapes.remove(portrait[0])

        for i, pos in enumerate(landscape_positions[:7]):
            if i < len(available_landscapes):
                layout[pos] = available_landscapes[i]

        return layout

    def _empty_destination_layout(self):
        """Return empty destination layout"""
        return {f'landscape_{i}': None for i in range(1, 8)} | {'portrait': None}


class FAQView(TemplateView):
    template_name = 'Home/faq.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['testimonials'] = Testimonials.objects.only(
            'id', 'name', 'image', 'feedback'
        ).order_by('-id')[:6]
        return context


class AboutView(ListView):
    model = Services
    context_object_name = 'services'
    template_name = 'Home/about.html'

    def get_queryset(self):
        return Services.objects.only('id', 'name', 'icon', 'description')[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        services = self.object_list
        context['services1'] = services[:3]
        context['services2'] = services[3:]
        return context


class ServicesView(ListView):
    model = Services
    template_name = 'Home/services.html'

    def get_queryset(self):
        return Services.objects.only('id', 'name', 'icon', 'description')[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        services = self.object_list
        context['services1'] = services[:3]
        context['services2'] = services[3:]
        context['testimonials'] = Testimonials.objects.only(
            'id', 'name', 'feedback'
        ).order_by('-id')[:6]
        return context


class CruisesView(ListView):
    model = Services
    template_name = 'Home/cruises.html'

    def get_queryset(self):
        return Services.objects.only('id', 'name', 'icon', 'description')[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        services = self.object_list
        context['services1'] = services[:3]
        context['services2'] = services[3:]

        # Optimized cruise query - FIXED: use 'inclusions' instead of 'incluisiveexcluisive_set'
        cruise_qs = AwesomePackages.objects.filter(
            category="Cruises"
        ).prefetch_related(
            Prefetch(
                'inclusions',  # Changed from 'incluisiveexcluisive_set' to 'inclusions'
                queryset=IncluisiveExcluisive.objects.only('id', 'name', 'is_inclusive', 'package')
            )
        ).only('id', 'name', 'image', 'price', 'days', 'category').order_by('?')[:3]

        context["cruise_carousels"] = cruise_qs
        context['awesome_packages'] = AwesomePackages.objects.filter(
            category="Cruises"
        ).only('id', 'name', 'image', 'price', 'days')

        return context


class BlogsView(ListView):
    model = Blogs
    context_object_name = "blogs"
    template_name = 'Blogs/blogs.html'
    paginate_by = 10

    def get_queryset(self):
        return Blogs.objects.only(
            'id', 'title', 'image', 'content', 'published_date',
            'author', 'slug'
        ).order_by('-published_date')


class BlogDetailView(DetailView):
    model = Blogs
    context_object_name = 'blog'
    template_name = 'Blogs/blog_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blog = self.object

        # Recent posts (exclude current)
        context['recent_posts'] = Blogs.objects.exclude(
            id=blog.id
        ).only('id', 'title', 'image', 'published_date', 'slug')[:5]

        # Calculate reading time
        if blog.content:
            word_count = len(strip_tags(blog.content).split())
            context['reading_time'] = max(1, round(word_count / 200))
        else:
            context['reading_time'] = 1

        return context


class GalleryView(ListView):
    model = Gallery
    template_name = 'Home/gallery.html'
    context_object_name = 'galleries'

    def get_queryset(self):
        return Gallery.objects.select_related('category').only(
            'id', 'name', 'image', 'category__id', 'category__name'
        )[:16]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Categories
        categories = GalleryCategory.objects.only('id', 'name').all()
        context['categories'] = categories

        # All galleries
        all_galleries = self.object_list
        context['all_galleries'] = all_galleries

        # Group galleries by category in Python (single query)
        galleries_by_category = {
            category.id: [g for g in all_galleries if g.category_id == category.id]
            for category in categories
        }
        context['galleries_by_category'] = galleries_by_category

        return context


class BrochureView(ListView):
    model = Brochure
    context_object_name = 'brochures'
    template_name = 'Home/brochures.html'

    def get_queryset(self):
        return Brochure.objects.only('id', 'title', 'pdf_file', 'image', 'description')


# Trekking Views
class TrekkingListView(ListView):
    """Generic list view for all trekking packages"""
    model = Trekking
    template_name = 'Trekking/trekking_list.html'
    context_object_name = 'packages'
    paginate_by = 12

    def get_queryset(self):
        return Trekking.objects.only(
            'id', 'name', 'image', 'price', 'days', 'category', 'location'
        ).all()

class KenyaTrekking(TemplateView):
    model = Trekking
    template_name = "Trekking/kenya.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["packages"] = Trekking.objects.filter(
            category="Kenya"
        ).only('id', 'name', 'image', 'price', 'duration', 'category')[:12]
        return context


class TanzaniaTrekking(TemplateView):
    template_name = "Trekking/tanzania.html"


class KilimanjaroTrekking(ListView):
    model = Trekking
    template_name = "Trekking/kilimanjaro.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["packages"] = Trekking.objects.filter(
            category="Kilimanjaro"
        ).only('id', 'name', 'image', 'price', 'duration', 'category')[:12]
        return context


class SuswaTrekking(TemplateView):
    model = Trekking
    template_name = "Trekking/suswa.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["packages"] = Trekking.objects.filter(
            category="Suswa"
        ).only('id', 'name', 'image', 'price', 'duration', 'category')[:12]
        return context


class LongonotTrekking(TemplateView):
    model = Trekking
    template_name = "Trekking/longonot.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["packages"] = Trekking.objects.filter(
            category="Longonot"
        ).only('id', 'name', 'image', 'price', 'duration', 'category')[:12]
        return context


class MeruTrekking(TemplateView):
    model = Trekking
    template_name = "Trekking/meru.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["packages"] = Trekking.objects.filter(
            category="Meru"
        ).only('id', 'name', 'image', 'price', 'duration', 'category')[:12]
        return context


class TrekkingCategoryView(TrekkingListView):
    """View for specific trekking category"""
    template_name = 'Trekking/trekking_category.html'

    def get_queryset(self):
        category = self.kwargs.get('category')
        return super().get_queryset().filter(category=category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.kwargs.get('category')
        return context


class TrekkingDetailView(DetailView):
    model = Trekking
    context_object_name = "package"
    template_name = "Trekking/trekking_detail.html"

    def get_queryset(self):
        return Trekking.objects.only(
            'id', 'name', 'image', 'price', 'days', 'category',
            'location', 'description', 'persons'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        package = self.object

        # Itineraries
        context["itineraries"] = ItineraryTreking.objects.filter(
            package=package
        ).only('id', 'day_number', 'title', 'description', 'image').order_by('day_number')

        # Similar packages
        context['similar_packages'] = Trekking.objects.exclude(
            id=package.id
        ).filter(
            category=package.category
        ).only('id', 'name', 'image', 'price', 'days')[:3]

        # Form initialization
        initial_data = {}
        if self.request.user.is_authenticated:
            user = self.request.user
            initial_data = {
                'full_name': user.get_full_name() or user.username,
                'email': user.email,
            }
            if hasattr(user, 'phone'):
                initial_data['phone_number'] = user.phone

        context['form'] = TrekkingBookingForm(initial=initial_data, package=package)
        return context


# Simple Template Views
class AfricanWildLifeToursView(TemplateView):
    template_name = 'Services/african_wildlife_tours.html'


class TravelPartnershipsView(TemplateView):
    template_name = 'Services/travel_partnerships.html'


class HolidayTailorMadeToursView(TemplateView):
    template_name = 'Services/holiday_tailor_made_tours.html'


class AirportTransfersView(TemplateView):
    template_name = 'Services/airport_transfers.html'


class AirLineView(TemplateView):
    template_name = 'Home/airline.html'