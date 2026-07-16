import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.template.loader import render_to_string
import logging
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMultiAlternatives
from decouple import config
from .models import CompanyProfile

# Remove this line - it's causing the error
# company = get_object_or_404(CompanyProfile, pk=1)

logger = logging.getLogger(__name__)

# Configure API key
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = config('BREVO_API_KEY')

# Add this function to get company profile lazily
def get_company():
    """Get company profile with lazy loading to avoid import-time database queries"""
    try:
        return get_object_or_404(CompanyProfile, pk=1)
    except Exception as e:
        logger.warning(f"Could not load CompanyProfile: {e}")
        # Return a mock/default company for testing/migration
        return None

def send_transactional_email(to_email, to_name, subject, html_content):
    """Send transactional email using Brevo API"""
    try:
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{'email': to_email, 'name': to_name}],
            sender={'email': 'daysafarisadventures103@gmail.com', 'name': 'Day Safaris Adventures'},
            subject=subject,
            html_content=html_content,
            reply_to={'email': 'sales@daysafarisadventures.co.ke', 'name': 'Day Safaris Support'}
        )

        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email sent successfully! Message ID: {api_response.message_id}")
        return True

    except ApiException as e:
        print(f"Exception when sending email: {e}")
        return False


def send_welcome_email(name="", email=""):
    """Send welcome email using template"""
    try:
        print(f"Preparing to send welcome email to {email}...")
        html_content = render_to_string('Emails/welcome.html', {'name': name})
        return send_transactional_email(email, name, f"Welcome to Day Safaris Adventures, {name}! 🦁", html_content)
    except Exception as e:
        print(f"Error: {e}")
        return False

# confirmation sent to client
def send_booking_confirmation(booking):
    """Send booking confirmation using template"""
    try:
        company = get_company()  # Get company here
        if not company:
            print("Warning: Company profile not found, using default values")

        print(f"Preparing to send booking confirmation email to {booking.email} for booking ID {booking.id}...")
        payment_link = f"{company.mpesa_payment_link if company else 'https://daysafarisadventures.co.ke'}/payment/from-bookings/{booking.id}/"
        context = {
            'payment_link': payment_link,
            'booking': booking,
            'company_phone': company.company_phone if company else '+254759379600',
            'company_whatsapp': company.company_whatsapp if company else '+254140936286',
            'company_email': company.booking_confirmation_email if company else 'info@daysafarisadventures.com',
            'current_year': 2026
        }
        html_content = render_to_string('Emails/booking_confirmation.html', context)

        return send_transactional_email(
            booking.email,
            booking.name,
            f"Booking Confirmation - #{booking.id}",
            html_content
        )
    except Exception as e:
        print(f"Error: {e}")
        return False

# booking confirmation sent to Days
def send_booking_verification(booking):
    """Send booking confirmation using template"""
    try:
        company = get_company()  # Get company here
        if not company:
            print("Warning: Company profile not found, using default values")

        print(f"Preparing to send booking Verification email to {company.booking_confirmation_email if company else 'info@daysafarisadventures.com'} for booking ID {booking.id}...")
        mpesa_payment_link = f"{company.mpesa_payment_link if company else 'https://daysafarisadventures.co.ke'}/payment/from-bookings/{booking.id}/"
        context = {
            'payment_link': mpesa_payment_link,
            'booking': booking,
            'company_phone': company.company_phone if company else '+254759379600',
            'company_whatsapp': company.company_whatsapp if company else '+254140936286',
            'company_email': company.booking_confirmation_email if company else 'info@daysafarisadventures.com',
            'current_year': 2026,

            # more
            'booking': booking,
            'total_price': booking.persons * booking.destination.price,
            'deposit_amount': (booking.persons * booking.destination.price) * int(0.3),
            'balance_amount': (booking.persons * booking.destination.price) * int(0.3),
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'grand_total': booking.persons * booking.destination.price,
        }
        html_content = render_to_string('Emails/bookings_verification.html', context)

        return send_transactional_email(
            company.booking_confirmation_email if company else 'info@daysafarisadventures.com',
            booking.name,
            f"Booking Verification - #{booking.id}",
            html_content
        )
    except Exception as e:
        print(f"Error: {e}")
        return False

def send_contact_response(contact):
    """Send contact response using template"""
    try:
        print(f"Preparing to send contact response email to {contact.email}...")
        html_content = render_to_string('Emails/contact_response.html', {'contact': contact})
        return send_transactional_email(
            contact.email,
            contact.name,
            "We've received your message - Day Safaris Adventures",
            html_content
        )
    except Exception as e:
        print(f"Error: {e}")
        return False

def reply_contact_via_email_at_admin(contact):
    '''from admin reply to client'''
    try:
        print(f"Preparing to send contact response email to {contact.email}...")
        html_content = render_to_string('Emails/contact_response_admin.html', {'contact': contact})
        return send_transactional_email(
            contact.email,
            contact.name,
            f"Response to: {contact.subject} - Day Safaris Adventures",
            html_content
        )
    except Exception as e:
        print(f"Error: {e}")
        return False

def send_test_email(email):
    """Send test email using template"""
    try:
        html_content = render_to_string('Emails/test_email.html', {'email': email})
        return send_transactional_email(email, "Test User", "Test Email - Day Safaris Adventures", html_content)
    except Exception as e:
        print(f"Error: {e}")
        return False

def send_booking_reminder(booking):
    """Send booking reminder using template"""
    try:
        print(f"Preparing to send booking reminder email to {booking.email} for booking ID {booking.id}...")
        from datetime import date
        days_left = (booking.date - date.today()).days if booking.date else 0
        html_content = render_to_string('Emails/booking_reminder.html', {
            'booking': booking,
            'days_left': days_left
        })
        return send_transactional_email(
            booking.email,
            booking.name,
            f"Reminder: Your Safari Adventure is Coming Soon!",
            html_content
        )
    except Exception as e:
        print(f"Error: {e}")
        return False

def send_package_payment_email(package_purchase):
    """Send payment notification email for package purchase"""
    try:
        print(f"Preparing to send payment email to {package_purchase.email} for package {package_purchase.package.name}...")

        # Calculate amounts
        package = package_purchase.package
        package_price = package.price
        total_amount = package_price * package_purchase.number_of_persons

        # Generate payment link (adjust URL as needed)
        # payment_link = f"https://daysafarisadventures.co.ke/payment/{package_purchase.id}/"
        payment_link = f"http://127.0.0.1:8000/payment/{package_purchase.id}/"

        context = {
            'purchase': package_purchase,
            'package': package,
            'package_price': package_price,
            'total_amount': total_amount,
            'persons': package_purchase.number_of_persons,
            'payment_link': payment_link,
            'company_phone': '+254 734 962 965',
            'company_whatsapp': '+254 783 457 058',
            'company_email': 'info@daysafarisadventures.com',
            'current_year': '2025'
        }

        html_content = render_to_string('Emails/package_payment_email.html', context)

        return send_transactional_email(
            package_purchase.email,
            package_purchase.full_name,
            f"Complete Your Payment - {package.name} 🦁",
            html_content
        )
    except Exception as e:
        print(f"Error sending package payment email: {e}")
        return False

def send_new_user_alert_to_admin(user):
    """Send alert email to admin when a new user registers"""
    try:
        company = get_company()  # Get company here
        if not company:
            print("Warning: Company profile not found, using default values")

        print(f"Preparing to send new user alert to admin...")

        # Get admin email from company profile or settings
        admin_email = company.booking_confirmation_email if company else 'info@daysafarisadventures.com'

        context = {
            'user': user,
            'user_full_name': user.get_full_name() or user.username,
            'user_username': user.username,
            'user_email': user.email,
            'user_date_joined': user.date_joined,
            'user_is_active': user.is_active,
            'admin_panel_link': 'https://daysafarisadventures.co.ke/admin/auth/user/',
            'company_phone': company.company_phone if company else '+254759379600',
            'company_whatsapp': company.company_whatsapp if company else '+254140936286',
            'company_email': company.booking_confirmation_email if company else 'info@daysafarisadventures.com',
            'current_year': timezone.now().year
        }

        html_content = render_to_string('Emails/new_user_alert.html', context)

        return send_transactional_email(
            admin_email,
            "Admin - Day Safaris Adventures",
            f"🔔 New User Registration Alert - {user.username}",
            html_content
        )
    except Exception as e:
        print(f"Error sending new user alert email: {e}")
        return False