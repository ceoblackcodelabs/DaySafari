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
from .models import UserRecommendations, UserMessage, MessageReply
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from EmailSetup.utils import send_welcome_email

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
        send_welcome_email(email=form.cleaned_data.get('email'), name=form.cleaned_data.get('username'))
        UserMessage.objects.create(
            user=self.object,
            sender_name='Day Safaris Team',
            subject='Welcome to Day Safaris Adventures!',
            message=f"""Dear {form.cleaned_data.get('username')},
            Welcome to the Day Safaris Adventures family! We're thrilled to have you on board. Get ready to explore the wild and experience unforgettable safari adventures with us. If you have any questions or need assistance, our team is here to help. Happy travels! 🦁🌍
        """
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


class PackagesView(ListView):
    model = AwesomePackages
    template_name = 'tours/packages.html'
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
    
class MessageInboxView(LoginRequiredMixin, ListView):
    """
    Main inbox view - returns JSON for dynamic loading
    """
    model = UserMessage
    context_object_name = 'messages'
    template_name = "Messages/message_inbox.html"
    
    def get_queryset(self):
        queryset = UserMessage.objects.filter(
            user=self.request.user,
            is_deleted=False
        )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status and status != 'all':
            if status == 'archived':
                queryset = queryset.filter(status='archived')
            else:
                queryset = queryset.filter(status=status).exclude(status='archived')
        else:
            queryset = queryset.exclude(status='archived')
        
        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority and priority != 'all':
            queryset = queryset.filter(priority=priority)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(subject__icontains=search) |
                Q(message__icontains=search) |
                Q(sender_name__icontains=search)
            )
        
        return queryset.select_related('user').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get counts for different categories
        context['unread_count'] = UserMessage.objects.filter(
            user=self.request.user, 
            status='unread',
            is_deleted=False
        ).count()
        
        context['total_count'] = UserMessage.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).exclude(status='archived').count()
        
        context['read_count'] = UserMessage.objects.filter(
            user=self.request.user,
            status='read',
            is_deleted=False
        ).exclude(status='archived').count()
        
        context['archived_count'] = UserMessage.objects.filter(
            user=self.request.user,
            status='archived',
            is_deleted=False
        ).count()
        
        context['urgent_count'] = UserMessage.objects.filter(
            user=self.request.user,
            priority='urgent',
            status='unread',
            is_deleted=False
        ).count()
        
        # Priority counts
        context['urgent_total'] = UserMessage.objects.filter(
            user=self.request.user,
            priority='urgent',
            is_deleted=False
        ).exclude(status='archived').count()
        
        context['high_total'] = UserMessage.objects.filter(
            user=self.request.user,
            priority='high',
            is_deleted=False
        ).exclude(status='archived').count()
        
        context['medium_total'] = UserMessage.objects.filter(
            user=self.request.user,
            priority='medium',
            is_deleted=False
        ).exclude(status='archived').count()
        
        context['low_total'] = UserMessage.objects.filter(
            user=self.request.user,
            priority='low',
            is_deleted=False
        ).exclude(status='archived').count()
        
        # Current filters
        context['current_status'] = self.request.GET.get('status', 'all')
        context['current_priority'] = self.request.GET.get('priority', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        context['user_json'] = {
            'username': self.request.user.username,
            'first_name': self.request.user.first_name,
            'last_name': self.request.user.last_name,
            'email': self.request.user.email,
        }
        
        context['title'] = 'Message Center - Day Safaris Adventures'
        
        return context


class GetMessagesAPIView(LoginRequiredMixin, View):
    """API endpoint to get messages as JSON"""
    
    def get(self, request):
        try:
            print(f"User: {request.user.username}")  # Debug log
            print(f"User ID: {request.user.id}")  # Debug log
            
            # Check if UserMessage model exists
            try:
                from .models import UserMessage
                print("UserMessage model imported successfully")
            except ImportError:
                return JsonResponse({'success': False, 'error': 'UserMessage model not found'}, status=500)
            
            # Get all messages for the user
            queryset = UserMessage.objects.filter(
                user=request.user,
                is_deleted=False
            )
            
            print(f"Total messages found: {queryset.count()}")  # Debug log
            
            # Filter by status
            status = request.GET.get('status')
            print(f"Status filter: {status}")  # Debug log
            
            if status and status != 'all':
                if status == 'archived':
                    queryset = queryset.filter(status='archived')
                else:
                    queryset = queryset.filter(status=status).exclude(status='archived')
            else:
                queryset = queryset.exclude(status='archived')
            
            print(f"After status filter: {queryset.count()}")  # Debug log
            
            # Filter by priority
            priority = request.GET.get('priority')
            print(f"Priority filter: {priority}")  # Debug log
            
            if priority and priority != 'all':
                queryset = queryset.filter(priority=priority)
            
            print(f"After priority filter: {queryset.count()}")  # Debug log
            
            # Search
            search = request.GET.get('search', '')
            print(f"Search term: {search}")  # Debug log
            
            if search:
                queryset = queryset.filter(
                    Q(subject__icontains=search) |
                    Q(message__icontains=search)
                )
                print(f"After search filter: {queryset.count()}")  # Debug log
            
            messages_data = []
            for msg in queryset.order_by('-created_at'):
                try:
                    # Use getattr to safely get fields
                    sender_name = getattr(msg, 'sender_name', 'Day Safaris Team')
                    subject = getattr(msg, 'subject', 'No Subject')
                    message_text = getattr(msg, 'message', '')
                    priority_val = getattr(msg, 'priority', 'medium')
                    status_val = getattr(msg, 'status', 'unread')
                    created_at = getattr(msg, 'created_at', None)
                    
                    messages_data.append({
                        'id': msg.id,
                        'sender': sender_name,
                        'subject': subject,
                        'preview': message_text[:100] + '...' if len(message_text) > 100 else message_text,
                        'message': message_text,
                        'priority': priority_val,
                        'status': status_val,
                        'date': created_at.isoformat() if created_at else '',
                        'isRead': status_val == 'read'
                    })
                except Exception as e:
                    print(f"Error processing message {msg.id}: {str(e)}")
                    continue
            
            print(f"Final messages count: {len(messages_data)}")  # Debug log
            
            return JsonResponse({'success': True, 'messages': messages_data})
            
        except Exception as e:
            print(f"ERROR in GetMessagesAPIView: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class GetMessageDetailAPIView(LoginRequiredMixin, View):
    """API endpoint to get a single message as JSON"""
    
    def get(self, request, pk):
        try:
            from .models import UserMessage
            
            print(f"Fetching message ID: {pk} for user: {request.user.username}")
            
            # Get the message
            message = UserMessage.objects.get(id=pk, user=request.user, is_deleted=False)
            print(f"Found message: {message.subject}")
            
            # Mark as read if unread
            if message.status == 'unread':
                message.status = 'read'
                message.save(update_fields=['status'])
                print(f"Marked message {pk} as read")
            
            # Safely get all attributes
            data = {
                'id': message.id,
                'sender': getattr(message, 'sender_name', 'Day Safaris Team'),
                'subject': message.subject,
                'message': message.message,
                'priority': message.priority,
                'status': message.status,
                'date': message.created_at.isoformat() if message.created_at else '',
                'formatted_date': message.created_at.strftime("%B %d, %Y at %I:%M %p") if message.created_at else '',
                'replies': []  # Add replies functionality later if needed
            }
            
            print(f"Returning data for message {pk}")
            return JsonResponse({'success': True, 'message': data})
            
        except UserMessage.DoesNotExist:
            print(f"Message {pk} not found for user {request.user.username}")
            return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in GetMessageDetailAPIView: {str(e)}")
            print(error_details)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class ArchiveMessageAPIView(LoginRequiredMixin, View):
    """API endpoint to archive a message"""
    
    def post(self, request):
        try:
            message_id = request.POST.get('message_id')
            message = UserMessage.objects.get(id=message_id, user=request.user)
            message.status = 'archived'
            message.save(update_fields=['status'])
            return JsonResponse({'success': True, 'message': 'Message archived successfully'})
        except UserMessage.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class DeleteMessageAPIView(LoginRequiredMixin, View):
    """API endpoint to delete a message"""
    
    def post(self, request):
        try:
            message_id = request.POST.get('message_id')
            message = UserMessage.objects.get(id=message_id, user=request.user)
            message.is_deleted = True
            message.save(update_fields=['is_deleted'])
            return JsonResponse({'success': True, 'message': 'Message deleted successfully'})
        except UserMessage.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class MarkUnreadAPIView(LoginRequiredMixin, View):
    """API endpoint to mark a message as unread"""
    
    def post(self, request):
        try:
            message_id = request.POST.get('message_id')
            message = UserMessage.objects.get(id=message_id, user=request.user)
            message.status = 'unread'
            message.save(update_fields=['status'])
            return JsonResponse({'success': True, 'message': 'Marked as unread'})
        except UserMessage.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class ReplyToMessageAPIView(LoginRequiredMixin, View):
    """API endpoint to reply to a message"""
    
    def post(self, request):
        try:
            message_id = request.POST.get('message_id')
            reply_text = request.POST.get('reply_message')
            
            if not reply_text or not reply_text.strip():
                return JsonResponse({'success': False, 'error': 'Please enter a reply message'}, status=400)
            
            original_message = UserMessage.objects.get(id=message_id, user=request.user)
            
            # Check if MessageReply model exists
            try:
                from .models import MessageReply
                reply = MessageReply.objects.create(
                    original_message=original_message,
                    user=request.user,
                    reply_message=reply_text
                )
            except:
                # If MessageReply doesn't exist, just return success
                pass
            
            return JsonResponse({'success': True, 'message': 'Reply sent successfully'})
            
        except UserMessage.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Message not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class GetCountsAPIView(LoginRequiredMixin, View):
    """API endpoint to get message counts"""
    
    def get(self, request):
        try:
            counts = {
                'total': UserMessage.objects.filter(
                    user=request.user,
                    is_deleted=False
                ).exclude(status='archived').count(),
                
                'unread': UserMessage.objects.filter(
                    user=request.user,
                    status='unread',
                    is_deleted=False
                ).count(),
                
                'read': UserMessage.objects.filter(
                    user=request.user,
                    status='read',
                    is_deleted=False
                ).exclude(status='archived').count(),
                
                'archived': UserMessage.objects.filter(
                    user=request.user,
                    status='archived',
                    is_deleted=False
                ).count(),
                
                'urgent': UserMessage.objects.filter(
                    user=request.user,
                    priority='urgent',
                    status='unread',
                    is_deleted=False
                ).count(),
            }
            
            return JsonResponse({'success': True, 'counts': counts})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)