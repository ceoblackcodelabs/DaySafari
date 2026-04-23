from django.urls import path
from .views import (
    RegisterView, CustomLoginView, CustomLogoutView, ProfileView,
    EditProfileView, AccountSettingsView, BookingDetailView,
    CancelBookingView, PackagesView, PackageDetailView,
    BookPackageView, OffersView, MessageInboxView, GetMessagesAPIView,
    GetMessageDetailAPIView, ArchiveMessageAPIView, DeleteMessageAPIView,
    MarkUnreadAPIView, ReplyToMessageAPIView, GetCountsAPIView,
)

urlpatterns = [
    # Authentication URLs
    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', CustomLogoutView.as_view(), name='logout'),
    
    # Profile URLs
    path('accounts/profile/', ProfileView.as_view(), name='profile'),
    path('accounts/profile/edit/', EditProfileView.as_view(), name='edit_profile'),
    path('accounts/profile/settings/', AccountSettingsView.as_view(), name='account_settings'),
    path('accounts/profile/offers/', OffersView.as_view(), name='offers'),
    
    # Booking URLs
    path('booking/<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('booking/<int:booking_id>/cancel/', CancelBookingView.as_view(), name='cancel_booking'),
    
    # Package URLs
    path('packages/', PackagesView.as_view(), name='packages'),
    path('package/<int:pk>/', PackageDetailView.as_view(), name='package_detail'),
    path('package/<int:package_id>/book/', BookPackageView.as_view(), name='book_package'),
    
    # Message System URLs
    path('messages/', MessageInboxView.as_view(), name='message_inbox'),
    
    # API endpoints for dynamic functionality
    path('api/messages/counts/', GetCountsAPIView.as_view(), name='api_message_counts'),
    path('api/messages/archive/', ArchiveMessageAPIView.as_view(), name='api_archive_message'),
    path('api/messages/delete/', DeleteMessageAPIView.as_view(), name='api_delete_message'),
    path('api/messages/unread/', MarkUnreadAPIView.as_view(), name='api_mark_unread'),
    path('api/messages/reply/', ReplyToMessageAPIView.as_view(), name='api_reply_message'),
    path('api/messages/', GetMessagesAPIView.as_view(), name='api_messages'),
    path('api/messages/<int:pk>/', GetMessageDetailAPIView.as_view(), name='api_message_detail'),
]