from django.core.management.base import BaseCommand
from EmailSetup.utils import send_test_email

class Command(BaseCommand):
    help = 'Test Brevo API email sending'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email address')

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f"Sending test email to {email}...")
        result = send_test_email(email)
        
        if result:
            self.stdout.write(self.style.SUCCESS(f'✅ Test email sent successfully to {email}'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Failed to send email to {email}'))