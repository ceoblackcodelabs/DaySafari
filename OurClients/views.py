from django.views.generic import CreateView, FormView, TemplateView, ListView, DetailView, UpdateView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.urls import reverse_lazy
from django.contrib import messages
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
import threading
from time import sleep

def send_registration_emails_async(email, name, user):
    """Send registration emails in background thread"""
    def send():
        try:
            # Send welcome email to user
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
        messages.success(self.request, f"Welcome back, {form.get_user().username}! 🦁")
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle failed login"""
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)

    def get_success_url(self):
        return self.success_url


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

            messages.info(request, "You have been successfully logged out. Come back soon! 🦁")
            return response

        response = super().dispatch(request, *args, **kwargs)

        # Add cache control headers to prevent back button from working
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

        return response

class RegisterView(CreateView):
    template_name = 'registration/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        """Handle valid registration form"""
        response = super().form_valid(form)

        messages.success(self.request,
            f"Account created successfully! Welcome {form.cleaned_data.get('username')}! 🎉 "
            "Please log in to continue."
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
            ).order_by('-starRating')[:6]
        else:
            # Default recommendations for new users
            recommended_packages = recommended_packages.order_by('-starRating')[:6]

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
        messages.success(self.request, "Your profile has been updated successfully!")
        return super().form_valid(form)


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/account_settings.html'

    def post(self, request, *args, **kwargs):
        user = request.user
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect('account_settings')

        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, "Your password has been updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Current password is incorrect.")
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
            messages.success(request, f"Booking #{booking.id} has been cancelled successfully.")
        else:
            messages.error(request, "This booking cannot be cancelled as it's too close to the travel date.")

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

        messages.success(self.request, f"Booking confirmed for {self.package.name}! Your safari adventure awaits!")
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
            messages.info(request, f"Removed {destination.name} from your saved destinations.")
        else:
            messages.success(request, f"Added {destination.name} to your saved destinations!")

        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')

        # Security: never redirect to an attacker-supplied off-site URL.
        # Only follow `next`/Referer if it points back to our own host.
        if not next_url or not url_has_allowed_host_and_scheme(
            url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            next_url = reverse_lazy('profile')

        return HttpResponseRedirect(next_url)


class PackagesView(ListView):
    model = AwesomePackages
    template_name = 'Packages/packages.html'
    context_object_name = 'packages'
    paginate_by = 9

    def get_queryset(self):
        queryset = AwesomePackages.objects.all()

        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by location
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)

        # Filter by price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Filter by days
        days = self.request.GET.get('days')
        if days:
            queryset = queryset.filter(days__lte=days)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(location__icontains=search) |
                Q(description__icontains=search)
            )

        # Sort
        sort_by = self.request.GET.get('sort')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-starRating')
        elif sort_by == 'days_asc':
            queryset = queryset.order_by('days')
        else:
            queryset = queryset.order_by('-starRating')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Our Safari Packages - Day Safaris Adventures'
        context['categories'] = AwesomePackages.objects.values_list('category', flat=True).distinct()
        context['locations'] = AwesomePackages.objects.values_list('location', flat=True).distinct()

        # Add filter values to context for form persistence
        context['current_filters'] = {
            'category': self.request.GET.get('category', ''),
            'location': self.request.GET.get('location', ''),
            'min_price': self.request.GET.get('min_price', ''),
            'max_price': self.request.GET.get('max_price', ''),
            'days': self.request.GET.get('days', ''),
            'search': self.request.GET.get('search', ''),
            'sort': self.request.GET.get('sort', ''),
        }

        return context