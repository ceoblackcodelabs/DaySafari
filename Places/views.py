from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView
from .models import (
    Destinations, AwesomePackages, DestinationsCategory, IncluisiveExcluisive
)
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from EmailSetup.utils import send_package_payment_email
from .forms import PackagePurchaseForm
from datetime import date
from django.db.models import Prefetch


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
class TourView(TemplateView):
    template_name = 'Home/tours.html'


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

        # Organize destinations by category for filtering
        destinations_by_category = {}
        for category in categories:
            category_destinations = Destinations.objects.filter(
                category=category
            ).select_related('category').only(
                'id', 'name', 'image', 'price', 'category__id', 'category__category'
            )
            destinations_by_category[category.id] = category_destinations

        context['destinations_by_category'] = destinations_by_category

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

        # Organize destinations by category for filtering
        destinations_by_category = {}
        for category in categories:
            category_destinations = Destinations.objects.filter(
                category=category
            ).select_related('category').only(
                'id', 'name', 'image', 'price', 'category__id', 'category__category'
            )
            destinations_by_category[category.id] = category_destinations

        context['destinations_by_category'] = destinations_by_category

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

        # Organize destinations by category for filtering
        destinations_by_category = {}
        for category in categories:
            category_destinations = Destinations.objects.filter(
                category=category
            ).select_related('category').only(
                'id', 'name', 'image', 'price', 'category__id', 'category__category'
            )
            destinations_by_category[category.id] = category_destinations

        context['destinations_by_category'] = destinations_by_category

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

        # Organize destinations by category for filtering
        destinations_by_category = {}
        for category in categories:
            category_destinations = Destinations.objects.filter(
                category=category
            ).select_related('category').only(
                'id', 'name', 'image', 'price', 'category__id', 'category__category'
            )
            destinations_by_category[category.id] = category_destinations

        context['destinations_by_category'] = destinations_by_category

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

        # Organize destinations by category for filtering
        destinations_by_category = {}
        for category in categories:
            category_destinations = Destinations.objects.filter(
                category=category
            ).select_related('category').only(
                'id', 'name', 'image', 'price', 'category__id', 'category__category'
            )
            destinations_by_category[category.id] = category_destinations

        context['destinations_by_category'] = destinations_by_category

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

        # Get similar packages
        similar_packages = AwesomePackages.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id).only(
            'id', 'name', 'image', 'price', 'days', 'category', 'star_rating'
        )[:3]
        context['similar_packages'] = similar_packages

        # Initialize form with user data if logged in
        initial_data = {}
        if self.request.user.is_authenticated:
            initial_data = {
                'full_name': f"{self.request.user.first_name} {self.request.user.last_name}".strip() or self.request.user.username,
                'email': self.request.user.email,
            }

        # Check if form was submitted with errors
        if 'form' not in context:
            context['form'] = PackagePurchaseForm(initial=initial_data, package=self.object)

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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PackagePurchaseForm(request.POST, package=self.object)

        if form.is_valid():
            # Save the purchase
            purchase = form.save(commit=False)
            purchase.package = self.object
            purchase.amount_spent = self.object.price * form.cleaned_data['number_of_persons']

            if request.user.is_authenticated:
                purchase.user = request.user

            purchase.save()

            # Send payment email to customer
            email_sent = send_package_payment_email(purchase)

            if email_sent:
                messages.success(request, f'Successfully booked {self.object.name}! A payment link has been sent to your email.')
            else:
                messages.warning(request, f'Booking saved! However, we could not send the email. Please contact us to complete payment.')

            # Redirect to payment page or home
            return redirect(reverse('payment_dashboard', kwargs={'purchase_id': purchase.id}))
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        # Render the page with form errors
        return self.render_to_response(self.get_context_data(form=form))