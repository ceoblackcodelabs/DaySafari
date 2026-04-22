from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import (
    AccomodationsImage, Accomodations, AirBNB, AirBNBImage
)

# Create your views here.
#  AirBNB
class AirBNBView(ListView):
    model = AirBNB
    context_object_name = 'bnbs'
    template_name = 'BNB/bnbs.html'
    
class AirBNBDetailView(DetailView):
    model = AirBNB
    context_object_name = 'bnb'
    template_name = "BNB/bnbs_detail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_images'] = self.object.images.all().order_by('order')
        context['featured_image'] = context['all_images'].filter(is_featured=True).first() or context['all_images'].first()
        return context