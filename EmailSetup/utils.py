# EmailSetup/utils.py
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.template.loader import render_to_string
import logging
from decouple import config

logger = logging.getLogger(__name__)

# Configure API key
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = config('BREVO_API_KEY')

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
            reply_to={'email': 'bookings@daysafarisadventures.co.ke', 'name': 'Day Safaris Support'}
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

def send_booking_confirmation(booking):
    """Send booking confirmation using template"""
    try:
        print(f"Preparing to send booking confirmation email to {booking.email} for booking ID {booking.id}...")
        html_content = render_to_string('Emails/booking_confirmation.html', {'booking': booking})
        return send_transactional_email(
            booking.email, 
            booking.name, 
            f"Booking Confirmation - #{booking.id}", 
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