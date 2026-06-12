from django.urls import path
from .views import (
    RegisterView, CustomLoginView, CustomLogoutView, ProfileView,
    EditProfileView, AccountSettingsView, BookingDetailView,
    CancelBookingView, PackagesView, PackageDetailView,
    BookPackageView, OffersView
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
]