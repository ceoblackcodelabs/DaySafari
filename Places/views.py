from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView
from .models import (
    Destinations, AwesomePackages, DestinationsCategory
)

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
        ).exclude(id=self.object.id)[:3]
        
        context['similar_destinations'] = similar_destinations
        
        return context
    
# tours
class TourView(TemplateView):
    template_name = 'Home/tours.html'
    
class AfricaTourView(ListView):
    model = AwesomePackages
    context_object_name = "africaPackages"
    template_name = 'Tours/africa_tours.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all destination categories for tabs
        categories = DestinationsCategory.objects.all()
        context['categories'] = categories
        
        # Get all destinations
        all_destinations = Destinations.objects.select_related('category')[:9]
        context['all_destinations'] = all_destinations
        
        # Organize destinations by category for filtering
        destinations_by_category = {}
        for category in categories:
            category_destinations = Destinations.objects.filter(
                category=category
            ).select_related('category')
            destinations_by_category[category.id] = category_destinations
        
        context['destinations_by_category'] = destinations_by_category
        
        return context
    
class EastAfricaTourView(ListView):
    model = AwesomePackages
    context_object_name = "africaPackages"
    template_name = 'Tours/east_africa_tours.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all destination categories for tabs
        categories = DestinationsCategory.objects.all()
        context['categories'] = categories
        
        # Get all destinations
        all_destinations = Destinations.objects.select_related('category')[:9]
        context['all_destinations'] = all_destinations
        
        # Organize destinations by category for filtering
        destinations_by_category = {}
        for category in categories:
            category_destinations = Destinations.objects.filter(
                category=category
            ).select_related('category')
            destinations_by_category[category.id] = category_destinations
        
        context['destinations_by_category'] = destinations_by_category
        
        return context
    
class InternationalAfricaTourView(ListView):
    model = AwesomePackages
    context_object_name = "africaPackages"
    template_name = 'Tours/international_africa_tours.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all destination categories for tabs
        categories = DestinationsCategory.objects.all()
        context['categories'] = categories
        
        # Get all destinations
        all_destinations = Destinations.objects.select_related('category')[:9]
        context['all_destinations'] = all_destinations
        
        # Organize destinations by category for filtering
        destinations_by_category = {}
        for category in categories:
            category_destinations = Destinations.objects.filter(
                category=category
            ).select_related('category')
            destinations_by_category[category.id] = category_destinations
        
        context['destinations_by_category'] = destinations_by_category
        
        return context

#  packages
class PackagesDetailView(DetailView):
    model = AwesomePackages
    context_object_name = 'package'
    template_name = 'Packages/package_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get itineraries for this package
        context['itineraries'] = self.object.itineraries.all().order_by('day_number')
        
        # Get similar packages
        similar_packages = AwesomePackages.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id)[:3]
        context['similar_packages'] = similar_packages
        
        return context