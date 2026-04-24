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


def send_welcome_email(name, email):
    """Send welcome email"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Welcome to Day Safaris</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #420d24; color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .button {{ background: #420d24; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Day Safaris Adventures! 🦁</h1>
                </div>
                <div class="content">
                    <h2>Hello {name}!</h2>
                    <p>Thank you for joining Day Safaris Adventures! We're excited to help you explore East Africa.</p>
                    <div style="background: #f9f9f9; padding: 20px; margin: 20px 0;">
                        <h3>🎁 Special Offer!</h3>
                        <p>Use code: <strong>WELCOME10</strong> for 10% off your first booking</p>
                    </div>
                    <p>Questions? Call us: +254 734 962 965</p>
                    <p>Warm regards,<br>The Day Safaris Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_transactional_email(email, name, f"Welcome to Day Safaris Adventures, {name}! 🦁", html_content)
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def send_booking_confirmation(booking):
    """Send booking confirmation email"""
    try:
        destination_name = booking.destination.name if booking.destination else 'TBD'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Booking Confirmation</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #420d24; color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .details {{ background: #f9f9f9; padding: 20px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Booking Confirmed! ✅</h1>
                </div>
                <div class="content">
                    <h2>Dear {booking.name},</h2>
                    <p>Your safari adventure is confirmed!</p>
                    <div class="details">
                        <h3>Booking Details:</h3>
                        <p><strong>Booking ID:</strong> #{booking.id}</p>
                        <p><strong>Destination:</strong> {destination_name}</p>
                        <p><strong>Travel Date:</strong> {booking.date}</p>
                        <p><strong>Persons:</strong> {booking.persons}</p>
                    </div>
                    <p>Our team will contact you within 24 hours.</p>
                    <p>Questions? Call: +254 734 962 965</p>
                    <p>Best regards,<br>The Day Safaris Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
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
    """Send contact response email"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>We Received Your Message</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #420d24; color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>We've Received Your Message! 📧</h1>
                </div>
                <div class="content">
                    <h2>Dear {contact.name},</h2>
                    <p>Thank you for contacting Day Safaris Adventures!</p>
                    <p>We have received your message and will respond within 24 hours.</p>
                    <div style="background: #f9f9f9; padding: 20px; margin: 20px 0;">
                        <p><strong>Your message:</strong> "{contact.message[:200]}"</p>
                    </div>
                    <p>In the meantime, reach us at: +254 734 962 965</p>
                    <p>Warm regards,<br>The Day Safaris Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_transactional_email(
            contact.email, 
            contact.name, 
            "We've received your message - Day Safaris Adventures", 
            html_content
        )
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def send_test_email(email):
    """Send test email"""
    try:
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Test Email</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .success { color: green; font-size: 24px; }
            </style>
        </head>
        <body>
            <h1 class="success">✅ Test Successful!</h1>
            <p>Your Brevo API configuration is working perfectly.</p>
            <p>🦁 Welcome to Day Safaris Adventures!</p>
            <p>This email was sent using Brevo API.</p>
        </body>
        </html>
        """
        
        return send_transactional_email(email, "Test User", "Test Email - Day Safaris Adventures", html_content)
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def send_booking_reminder(booking):
    """Send booking reminder email"""
    try:
        from datetime import date
        days_left = (booking.date - date.today()).days if booking.date else 0
        destination_name = booking.destination.name if booking.destination else 'TBD'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Booking Reminder</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #420d24; color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Safari Adventure is Coming Soon! 🦁</h1>
                </div>
                <div class="content">
                    <h2>Dear {booking.name},</h2>
                    <p>Your safari to <strong>{destination_name}</strong> is just {days_left} days away!</p>
                    <div style="background: #f9f9f9; padding: 20px; margin: 20px 0;">
                        <h3>Quick Tips:</h3>
                        <ul>
                            <li>Pack neutral-colored clothing</li>
                            <li>Bring sunscreen and insect repellent</li>
                            <li>Don't forget your camera</li>
                            <li>Carry a valid passport</li>
                        </ul>
                    </div>
                    <p>Questions? Call us: +254 734 962 965</p>
                    <p>The Day Safaris Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_transactional_email(
            booking.email, 
            booking.name, 
            f"Reminder: Your {destination_name} Adventure is Coming Soon!", 
            html_content
        )
        
    except Exception as e:
        print(f"Error: {e}")
        return False
