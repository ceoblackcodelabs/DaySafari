from django.contrib import messages
from django.db.models import F, Count, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView

from ClientRequests.antispam import AntiSpamViewMixin
from EmailSetup.utils import handle_new_lead, send_booking_confirmation

from .forms import HotelEnquiryForm
from .models import Hotel

SORTS = {
    'featured': ('-is_featured', 'country', 'name'),
    'price_low': (F('price_per_night').asc(nulls_last=True), 'name'),       # hotels without a rate go last
    'price_high': (F('price_per_night').desc(nulls_last=True), 'name'),
    'rating': ('-star_rating', 'name'),
    'name': ('name',),
}


def _initial_for(user):
    if not user.is_authenticated:
        return {}
    return {'name': f'{user.first_name} {user.last_name}'.strip() or user.username, 'email': user.email}


# ---------------------------------------------------------------- hotels
class HotelListView(ListView):
    """Hotel cards (same look as package cards) with gallery-style pill filters."""
    template_name = 'Hotels/hotels.html'
    context_object_name = 'hotels'
    paginate_by = 12

    def published(self):
        return Hotel.objects.filter(is_published=True)

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(queryset, page_size)       # a wrong ?page= shows the nearest real page
        page = paginator.get_page(self.request.GET.get('page'))
        return paginator, page, page.object_list, page.has_other_pages()

    def get_queryset(self):
        params = self.request.GET
        qs = self.published().prefetch_related('images')
        if params.get('country'):
            qs = qs.filter(country__iexact=params['country'])
        if params.get('type') in dict(Hotel.TYPE_CHOICES):
            qs = qs.filter(property_type=params['type'])
        if params.get('q'):
            term = params['q'].strip()[:80]
            qs = qs.filter(Q(name__icontains=term) | Q(location__icontains=term) | Q(location_en__icontains=term)
                           | Q(summary__icontains=term) | Q(summary_en__icontains=term))
        return qs.order_by(*SORTS.get(params.get('sort'), SORTS['featured']))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base = self.published()
        types = dict(Hotel.TYPE_CHOICES)
        context['countries'] = list(base.values('country').annotate(n=Count('id')).order_by('country'))
        context['types'] = [{'key': t['property_type'], 'label': types[t['property_type']], 'n': t['n']}
                            for t in base.values('property_type').annotate(n=Count('id')).order_by('property_type')]
        context['total_all'] = base.count()
        params = self.request.GET
        context['sel_country'] = params.get('country', '')
        context['sel_type'] = params.get('type', '')
        context['sel_sort'] = params.get('sort', 'featured')
        context['query'] = params.get('q', '')
        context['sorts'] = [('featured', _('Featured')), ('rating', _('Star rating')), ('name', _('Name A-Z'))]
        keep = params.copy()
        keep.pop('page', None)
        context['keep_params'] = keep.urlencode()
        return context


class HotelDetailView(AntiSpamViewMixin, DetailView):
    antispam_scope = 'hotel'
    template_name = 'Hotels/hotel_detail.html'
    context_object_name = 'hotel'

    def get_queryset(self):
        return Hotel.objects.filter(is_published=True).prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hotel = self.object
        images = list(hotel.images.all())
        context['images'] = images
        context['main_image'] = hotel.main_image
        context['similar_hotels'] = (Hotel.objects.filter(is_published=True, country=hotel.country)
                                     .exclude(pk=hotel.pk).prefetch_related('images')[:3])
        if len(context['similar_hotels']) < 3:
            context['similar_hotels'] = list(context['similar_hotels']) + list(
                Hotel.objects.filter(is_published=True).exclude(pk=hotel.pk).exclude(country=hotel.country)
                .prefetch_related('images')[:3 - len(context['similar_hotels'])])
        if 'form' not in context:
            context['form'] = HotelEnquiryForm(initial=_initial_for(self.request.user), hotel=hotel)
        return context

    def post(self, request, *args, **kwargs):
        self.object = hotel = self.get_object()
        form = HotelEnquiryForm(request.POST, hotel=hotel)
        if not form.is_valid():
            if form.spam_detected:
                return self.form_invalid(form)  # AntiSpamViewMixin: strike + 400
            return self.render_to_response(self.get_context_data(form=form))

        booking = form.save(commit=False)
        booking.booking_type = 'hotel'
        booking.hotel = hotel
        if request.user.is_authenticated:
            booking.client = request.user
        booking.save()
        handle_new_lead(booking, send_booking_confirmation)
        messages.success(request, _('Thank you %(name)s! Your enquiry for %(hotel)s was received. '
                                    'We will confirm availability and rates within 24 hours.')
                         % {'name': booking.name, 'hotel': hotel.name})
        return redirect(hotel.get_absolute_url())
