from django.views.generic import CreateView, FormView, TemplateView, ListView, DetailView, UpdateView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext as _
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Q, Sum
from datetime import datetime, timedelta
from django.utils import timezone
from Home.models import Destinations
from Places.models import AwesomePackages
from ClientRequests.models import Bookings
from .models import UserRecommendations, SavedDestination
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from EmailSetup.utils import send_welcome_email, send_new_user_alert_to_admin
from ClientRequests.antispam import AntiSpamViewMixin
from ClientRequests.spamfilter import can_email_customer
import threading
from time import sleep


def send_registration_emails_async(email, name, user):
    """Send registration emails in background thread"""
    def send():
        try:
            # Send welcome email to user
            if can_email_customer(email):   # never mail arbitrary addresses repeatedly
                send_welcome_email(email=email, name=name)
            sleep(10)
            # Send alert email to admin
            send_new_user_alert_to_admin(user)
            print(f"Registration emails sent for: {name}")
        except Exception as e:
            print(f"Error sending registration emails: {e}")

    thread = threading.Thread(target=send)
    thread.daemon = True
    thread.start()


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        """Handle successful login"""
        messages.success(self.request, _("Welcome back, %(name)s! 🦁") % {'name': form.get_user().username})
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle failed login"""
        messages.error(self.request, _("Invalid username or password. Please try again."))
        return super().form_invalid(form)

    def get_success_url(self):
        """Go back to the page that asked for the login; guides land on their own profile; everyone else on the home page."""
        target = self.get_redirect_url()
        if target:
            return target
        guide = getattr(self.request.user, 'guide_profile', None)
        if guide and guide.is_active:
            return guide.get_absolute_url()
        return str(self.success_url)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        # Clear session completely
        request.session.flush()

        # Clear the session ID cookie
        if request.COOKIES.get('sessionid'):
            response = HttpResponseRedirect(self.next_page)
            response.delete_cookie('sessionid')
            response.delete_cookie('csrftoken')

            # Add cache control headers to prevent back button from loading cached pages
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

            messages.info(request, _("You have been successfully logged out. Come back soon! 🦁"))
            return response

        response = super().dispatch(request, *args, **kwargs)

        # Add cache control headers to prevent back button from working
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response


class RegisterView(AntiSpamViewMixin, CreateView):
    antispam_scope = 'register'
    template_name = 'registration/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        """Handle valid registration form"""
        response = super().form_valid(form)

        messages.success(self.request,
            _("Account created successfully! Welcome %(name)s! 🎉 Please log in to continue.")
            % {'name': form.cleaned_data.get('username')}
        )
        # Send emails in background thread (non-blocking)
        send_registration_emails_async(
            email=form.cleaned_data.get('email'),
            name=form.cleaned_data.get('username'),
            user=self.object
        )
        return response

    def form_invalid(self, form):
        """Handle invalid registration form"""
        if form.spam_detected:
            return super().form_invalid(form)  # AntiSpamViewMixin: strike + 400
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Register - Day Safaris Adventures'
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get current date
        today = timezone.now().date()

        # Get all user bookings
        all_bookings = Bookings.objects.filter(email=user.email).select_related('destination')

        # Separate current and past bookings
        current_bookings = all_bookings.filter(
            date__gte=today
        ).order_by('date')

        past_bookings = all_bookings.filter(
            date__lt=today
        ).order_by('-date')

        # Calculate stats
        total_bookings = all_bookings.count()
        upcoming_bookings = current_bookings.count()
        completed_bookings = past_bookings.count()

        # Calculate loyalty points (example: 100 points per completed booking)
        loyalty_points = completed_bookings * 100

        # Get user's destinations from past bookings for recommendations
        user_destinations = past_bookings.values_list('destination__category__category', flat=True).distinct()
        user_locations = past_bookings.values_list('destination__name', flat=True).distinct()

        # Get recommended packages based on user's booking history
        recommended_packages = AwesomePackages.objects.all()

        if user_destinations:
            # Prioritize packages matching user's interests
            recommended_packages = recommended_packages.filter(
                Q(category__icontains='safari') |
                Q(location__in=user_locations[:3])
            ).exclude(
                # Exclude already booked packages? (you might not have direct relation)
                id__in=[]
            ).only('id', 'name', 'image', 'price', 'days', 'category', 'star_rating', 'location', 'slug').order_by('-star_rating')[:6]  # FIXED: starRating -> star_rating
        else:
            # Default recommendations for new users
            recommended_packages = recommended_packages.only(
                'id', 'name', 'image', 'price', 'days', 'category', 'star_rating', 'location', 'slug'
            ).order_by('-star_rating')[:6]  # FIXED: starRating -> star_rating

        # Get user's recommendations from the new model if exists
        if hasattr(user, 'recommendations'):
            user_recs = user.recommendations.select_related('package').order_by('-score')[:6]
            if user_recs:
                recommended_packages = [rec.package for rec in user_recs]

        # Get recent notifications (you can create a simple system using session or a new model)
        notifications = []

        # Saved / favorite destinations
        saved_destinations = SavedDestination.objects.filter(user=user).select_related('destination')[:6]
        saved_destinations_count = SavedDestination.objects.filter(user=user).count()

        context.update({
            'user': user,
            'title': 'My Profile - Day Safaris Adventures',
            'current_bookings': current_bookings,
            'past_bookings': past_bookings,
            'recommended_packages': recommended_packages,
            'total_bookings': total_bookings,
            'upcoming_bookings': upcoming_bookings,
            'completed_bookings': completed_bookings,
            'loyalty_points': loyalty_points,
            'notifications': notifications,
            'saved_destinations': saved_destinations,
            'saved_destinations_count': saved_destinations_count,
            'today': today,
        })

        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'registration/edit_profile.html'
    fields = ['first_name', 'last_name', 'email']
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, _("Your profile has been updated successfully!"))
        return super().form_valid(form)


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/account_settings.html'

    def post(self, request, *args, **kwargs):
        user = request.user
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, _("New passwords do not match."))
            return redirect('account_settings')

        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, _("Your password has been updated successfully!"))
            return redirect('profile')
        else:
            messages.error(request, _("Current password is incorrect."))
            return redirect('account_settings')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Account Settings - Day Safaris Adventures'
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Bookings
    template_name = 'registration/booking_detail.html'
    context_object_name = 'booking'

    def get_queryset(self):
        return Bookings.objects.filter(email=self.request.user.email)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Booking #{self.object.id} - Day Safaris Adventures'
        return context


class CancelBookingView(LoginRequiredMixin, View):
    def post(self, request, booking_id):
        booking = get_object_or_404(Bookings, id=booking_id, email=request.user.email)

        # Check if booking can be cancelled (at least 7 days before travel date)
        days_until_travel = (booking.date - timezone.now().date()).days

        if days_until_travel >= 7:
            booking.delete()  # Or add a status field to Bookings model
            messages.success(request, _("Booking #%(id)s has been cancelled successfully.") % {'id': booking.id})
        else:
            messages.error(request, _("This booking cannot be cancelled as it's too close to the travel date."))

        return redirect('profile')


class PackageDetailView(DetailView):
    model = AwesomePackages
    template_name = 'registration/package_detail.html'
    context_object_name = 'package'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.name} - Day Safaris Adventures'

        # Check if user has booked this package (check via destination relation)
        if self.request.user.is_authenticated:
            context['has_booked'] = Bookings.objects.filter(
                email=self.request.user.email,
                destination__name__icontains=self.object.location
            ).exists()

        return context


class BookPackageView(LoginRequiredMixin, CreateView):
    model = Bookings
    template_name = 'registration/book_package.html'
    fields = ['name', 'email', 'phone', 'persons', 'date', 'message']

    def dispatch(self, request, *args, **kwargs):
        self.package = get_object_or_404(AwesomePackages, id=kwargs['package_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Find or create destination based on package location
        destination, created = Destinations.objects.get_or_create(
            name=self.package.location,
            defaults={
                'category_id': 1,  # Set a default category
                'description': self.package.description[:200]
            }
        )

        form.instance.destination = destination
        form.instance.email = self.request.user.email

        # Auto-fill name if not provided
        if not form.instance.name:
            form.instance.name = self.request.user.get_full_name() or self.request.user.username

        response = super().form_valid(form)

        # Create recommendation for future
        UserRecommendations.objects.update_or_create(
            user=self.request.user,
            package=self.package,
            defaults={'score': 1.0}
        )

        messages.success(self.request, _("Booking confirmed for %(package)s! Your safari adventure awaits!") % {'package': self.package.name})
        return response

    def get_initial(self):
        initial = super().get_initial()
        initial['name'] = self.request.user.get_full_name() or self.request.user.username
        initial['email'] = self.request.user.email
        initial['persons'] = 2
        initial['date'] = timezone.now().date() + timedelta(days=30)
        return initial

    def get_success_url(self):
        return reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['package'] = self.package
        context['title'] = f'Book {self.package.name} - Day Safaris Adventures'
        return context


class OffersView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/offers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Special Offers - Day Safaris Adventures'

        # Show offers based on user's booking history
        user_bookings = Bookings.objects.filter(email=self.request.user.email)
        booking_count = user_bookings.count()

        offers = []

        # Standard offers
        offers.append({
            'title': 'Early Bird Discount',
            'description': 'Book 30 days in advance and get 15% off on any safari package',
            'code': 'EARLYBIRD15',
            'valid_until': timezone.now().date() + timedelta(days=30),
            'icon': 'fa-clock'
        })

        # Loyalty offers
        if booking_count >= 3:
            offers.append({
                'title': 'Loyalty Reward',
                'description': f'As a valued customer with {booking_count} bookings, get 20% off your next adventure!',
                'code': f'LOYALTY{booking_count}0',
                'valid_until': timezone.now().date() + timedelta(days=60),
                'icon': 'fa-gem'
            })

        # Group booking offer
        offers.append({
            'title': 'Group Safari Deal',
            'description': 'Book for 4+ people and get 20% off on select packages',
            'code': 'GROUP20',
            'valid_until': timezone.now().date() + timedelta(days=45),
            'icon': 'fa-users'
        })

        # Referral offer
        offers.append({
            'title': 'Refer a Friend',
            'description': 'Refer a friend and both get $50 credit on your next booking',
            'code': 'REFER50',
            'valid_until': timezone.now().date() + timedelta(days=90),
            'icon': 'fa-user-friends'
        })

        context['offers'] = offers
        return context


class FavoritesView(LoginRequiredMixin, ListView):
    model = SavedDestination
    template_name = 'registration/favorites.html'
    context_object_name = 'saved_destinations'
    login_url = reverse_lazy('login')

    def get_queryset(self):
        return SavedDestination.objects.filter(
            user=self.request.user
        ).select_related('destination', 'destination__category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Saved Destinations - Day Safaris Adventures'
        return context


class ToggleFavoriteView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')

    def post(self, request, destination_id):
        destination = get_object_or_404(Destinations, id=destination_id)
        favorite, created = SavedDestination.objects.get_or_create(
            user=request.user, destination=destination
        )

        if not created:
            favorite.delete()
            messages.info(request, _("Removed %(name)s from your saved destinations.") % {'name': destination.name})
        else:
            messages.success(request, _("Added %(name)s to your saved destinations!") % {'name': destination.name})

        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')

        # Security: never redirect to an attacker-supplied off-site URL.
        # Only follow `next`/Referer if it points back to our own host.
        if not next_url or not url_has_allowed_host_and_scheme(
            url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            next_url = reverse_lazy('profile')

        return HttpResponseRedirect(next_url)


class PackagesView(ListView):
    """Packages list with filters (search, category, place, price, length) and sorting. Bad input never crashes it."""
    model = AwesomePackages
    template_name = 'Packages/packages.html'
    context_object_name = 'packages'
    paginate_by = 9
    CATEGORY_ORDER = ['East Africa Tours', 'South Africa', 'West Africa', 'Africa Tours', 'International Tours', 'Cruises']
    SORTS = {'price_asc': ('price', 'id'), 'price_desc': ('-price', 'id'), 'rating': ('-star_rating', 'id'),
             'days_asc': ('days', 'id'), 'days_desc': ('-days', 'id'), 'newest': ('-created_at', 'id')}

    # ---- reading the filters safely
    @staticmethod
    def _number(raw, kind=int, low=0, high=10**7):
        try:
            value = kind(str(raw).strip())
        except (TypeError, ValueError, ArithmeticError):
            return None
        if value != value or value < low or value > high:      # NaN or out of range
            return None
        return value

    def filters(self):
        from decimal import Decimal
        get = self.request.GET
        min_price = self._number(get.get('min_price'), Decimal)
        max_price = self._number(get.get('max_price'), Decimal)
        if min_price is not None and max_price is not None and min_price > max_price:
            min_price, max_price = max_price, min_price          # forgiving: swap a reversed range
        category = get.get('category', '').strip()
        return {
            'search': ' '.join(get.get('search', '').split())[:100],
            'category': category if category in self.CATEGORY_ORDER else '',
            'location': get.get('location', '').strip()[:100],
            'min_price': min_price, 'max_price': max_price,
            'days': self._number(get.get('days'), int, low=1, high=365),
            'sort': get.get('sort') if get.get('sort') in self.SORTS else '',
        }

    def paginate_queryset(self, queryset, page_size):
        # a wrong or too-high ?page= shows the nearest real page instead of an error
        paginator = self.get_paginator(queryset, page_size)
        page = paginator.get_page(self.request.GET.get('page'))
        return paginator, page, page.object_list, page.has_other_pages()

    def get_queryset(self):
        f = self.filters()
        qs = AwesomePackages.objects.all()
        if f['category']:
            qs = qs.filter(category=f['category'])
        if f['location']:
            qs = qs.filter(location__icontains=f['location'])
        if f['min_price'] is not None:
            qs = qs.filter(price__gte=f['min_price'])
        if f['max_price'] is not None:
            qs = qs.filter(price__lte=f['max_price'])
        if f['days'] is not None:
            qs = qs.filter(days__lte=f['days'])
        for term in [t for t in f['search'].split() if len(t) > 1][:6]:      # every word must match somewhere
            qs = qs.filter(Q(name__icontains=term) | Q(location__icontains=term) |
                           Q(description__icontains=term) | Q(category__icontains=term))
        # a second key keeps pagination stable when many packages share the same value
        qs = qs.order_by(*self.SORTS.get(f['sort'], ('-star_rating', '-created_at', 'id')))
        return qs.only('id', 'name', 'image', 'price', 'days', 'category', 'star_rating', 'location', 'slug',
                       'description', 'persons')

    # ---- helpers for the template
    def _url(self, **changes):
        """The packages URL with the current filters, changing/removing the given ones (None removes). Resets paging."""
        from urllib.parse import urlencode
        params = {k: v for k, v in self.request.GET.items() if k != 'page' and v}
        for key, value in changes.items():
            if value in (None, ''):
                params.pop(key, None)
            else:
                params[key] = value
        base = str(reverse_lazy('packages'))
        return f'{base}?{urlencode(params)}' if params else base

    def get_context_data(self, **kwargs):
        from urllib.parse import urlencode
        context = super().get_context_data(**kwargs)
        f = self.filters()
        counts = dict(AwesomePackages.objects.order_by().values_list('category').annotate(n=Count('id')))
        context['title'] = 'Our Safari Packages - Day Safaris Adventures'
        context['categories'] = [{'value': c, 'n': counts[c], 'url': self._url(category=c), 'active': f['category'] == c}
                                 for c in self.CATEGORY_ORDER if c in counts]
        context['all_url'] = self._url(category=None)
        context['total_all'] = sum(counts.values())
        context['locations'] = sorted({l for l in AwesomePackages.objects.order_by().values_list('location', flat=True) if l})
        context['current_filters'] = {k: ('' if v is None else v) for k, v in f.items()}

        # chips for the filters that are switched on; each one removes itself
        chips = []
        if f['search']:
            chips.append((_('Search') + ': ' + f['search'], self._url(search=None)))
        if f['category']:
            chips.append((_(f['category']), self._url(category=None)))
        if f['location']:
            chips.append((f['location'], self._url(location=None)))
        if f['min_price'] is not None or f['max_price'] is not None:
            lo = f"${f['min_price']:.0f}" if f['min_price'] is not None else ''
            hi = f"${f['max_price']:.0f}" if f['max_price'] is not None else ''
            label = f'{lo} - {hi}' if lo and hi else (f'{_("From")} {lo}' if lo else f'{_("Up to")} {hi}')
            chips.append((label, self._url(min_price=None, max_price=None)))
        if f['days'] is not None:
            chips.append((_('Up to %(n)s days') % {'n': f['days']}, self._url(days=None)))
        context['chips'] = chips
        context['clear_url'] = str(reverse_lazy('packages')) + (f"?{urlencode({'sort': f['sort']})}" if f['sort'] else '')

        context['price_presets'] = []
        context['days_presets'] = [(_('Up to %(n)s days') % {'n': n}, self._url(days=n), f['days'] == n) for n in (3, 5, 7, 10, 14)]
        labels = [('', _('Recommended')), ('rating', _('Rating: High to Low')),
                  ('days_asc', _('Duration: Short to Long')), ('days_desc', _('Duration: Long to Short')),
                  ('newest', _('Newest first'))]
        context['sort_options'] = [(key, label, self._url(sort=key), f['sort'] == key) for key, label in labels]
        # the same query without "page", used by the pagination links
        context['base_qs'] = urlencode({k: v for k, v in self.request.GET.items() if k != 'page' and v})
        return context
