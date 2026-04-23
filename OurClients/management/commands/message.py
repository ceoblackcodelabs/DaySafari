# OurClients/management/commands/add_test_messages.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from OurClients.models import UserMessage
from datetime import datetime, timedelta
import random
from django.utils import timezone

class Command(BaseCommand):
    help = 'Add 20 test messages for a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='BlackSheep',
            help='Username to add messages for (default: BlackSheep)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing messages before adding new ones'
        )

    def handle(self, *args, **options):
        username = options['username']
        clear_existing = options['clear']
        
        # Get or create user
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f'✓ Found user: {user.username} (ID: {user.id})'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'User "{username}" not found. Creating user...'))
            user = User.objects.create_user(
                username=username,
                email=f'{username}@daysafaris.com',
                password='TestPass123!',
                first_name=username.capitalize(),
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created new user: {user.username}'))
        
        # Clear existing messages if flag is set
        if clear_existing:
            existing_count = UserMessage.objects.filter(user=user).count()
            UserMessage.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING(f'✓ Cleared {existing_count} existing messages'))
        
        # Sample messages data (subject and message pairs)
        messages_data = [
            {
                'subject': "Welcome to Day Safaris Adventures!",
                'message': """Dear Valued Customer,

Thank you for choosing Day Safaris Adventures! We're thrilled to welcome you to our family.

Your journey to unforgettable African adventures starts here. Our team is available 24/7 to assist you with any questions.

Best regards,
Day Safaris Team""",
                'priority': 'medium'
            },
            {
                'subject': "Your Safari Booking Confirmation #SAF-2024-001",
                'message': """Hello,

Your safari booking has been confirmed! Here are your details:

Package: 5 Days Maasai Mara Safari
Date: March 15-20, 2024
Number of guests: 2 adults
Total amount: $2,500

Please arrive at the meeting point by 7:00 AM on the departure date.

Thank you for choosing Day Safaris!""",
                'priority': 'high'
            },
            {
                'subject': "Exclusive 20% Discount on Your Next Safari",
                'message': """Dear Customer,

We're excited to offer you an exclusive Early Bird Discount! 

Book any safari package 30 days in advance and save 20%. Use code: EARLYBIRD20 at checkout.

This offer expires in 15 days. Don't miss out on this amazing opportunity!

Best regards,
Special Offers Team""",
                'priority': 'low'
            },
            {
                'subject': "Important: Travel Advisory Update",
                'message': """Important Travel Advisory:

Due to recent weather conditions, please be aware of the following updates for your safari:

1. Carry warm clothing for evening game drives
2. Roads may be muddy - we're using 4x4 vehicles
3. Some wildlife viewing spots may be affected

Contact our support team if you have any concerns.""",
                'priority': 'urgent'
            },
            {
                'subject': "How was your safari experience? Share your feedback!",
                'message': """Dear Safari Adventurer,

We hope you had an amazing experience with Day Safaris! 

Please take a moment to share your feedback and rate your safari experience. Your reviews help us improve and serve you better.

Click here to leave a review and get 100 loyalty points!

Thank you for being part of our journey.""",
                'priority': 'low'
            },
            {
                'subject': "Your Dream Safari Itinerary is Ready",
                'message': """Hello,

Your personalized safari itinerary is ready! Based on your preferences, we've created an amazing adventure for you.

Day 1: Arrival and welcome dinner
Day 2-4: Game drives in Maasai Mara
Day 5: Visit local Maasai village
Day 6: Departure

View full itinerary in your account.""",
                'priority': 'medium'
            },
            {
                'subject': "Special Early Bird Offer: Save 30%",
                'message': """Early Bird Special Alert! 🦁

Book your next safari today and save 30% on select packages. 

Destinations included:
- Maasai Mara Safari (5 days) - Was $2,500 Now $1,750
- Serengeti Migration (7 days) - Was $3,500 Now $2,450
- Amboseli Elephants (4 days) - Was $2,000 Now $1,400

Use code: EARLYBIRD30

Hurry! Limited spots available.""",
                'priority': 'high'
            },
            {
                'subject': "Payment Confirmation Received",
                'message': """Payment Confirmation ✓

Dear Customer,

We have successfully received your payment of $2,500 for booking #SAF-2024-001.

Your booking status is now CONFIRMED. You will receive your e-tickets within 24 hours.

Thank you for choosing Day Safaris!""",
                'priority': 'medium'
            },
            {
                'subject': "Urgent: Please Update Your Travel Documents",
                'message': """URGENT: Document Update Required

Please update your travel documents before your safari:

1. Passport (valid for 6+ months)
2. Visa requirements
3. Travel insurance
4. Vaccination certificates

Upload your documents in your account dashboard by March 1, 2024.

Failure to provide documents may result in booking cancellation.""",
                'priority': 'urgent'
            },
            {
                'subject': "New Safari Destinations Added for 2024",
                'message': """New Destinations Added! 🌍

We've expanded our horizons! Check out these amazing new destinations:

✨ Zanzibar Beach Holiday
✨ Victoria Falls Adventure  
✨ Mount Kilimanjaro Trek
✨ Gorilla Trekking in Uganda

Book now and get 15% off on your first trip to these destinations!

Explore the new adventures waiting for you!""",
                'priority': 'low'
            },
            {
                'subject': "Refer a Friend and Get $100 Credit",
                'message': """Refer a Friend! 🎁

Share the adventure with your friends and family. For every friend who books a safari, you both get $100 credit towards your next adventure!

Share your unique referral link: https://daysafaris.com/refer/blacksheep

Start referring today!""",
                'priority': 'low'
            },
            {
                'subject': "Your Safari Packing Guide",
                'message': """Safari Packing Guide 🎒

Here's what to pack for your upcoming safari:

✓ Lightweight clothing in neutral colors
✓ Comfortable walking shoes
✓ Sunscreen and hat
✓ Insect repellent
✓ Binoculars
✓ Camera with extra batteries
✓ Prescription medications

Safe travels!""",
                'priority': 'medium'
            },
            {
                'subject': "Flight Booking Confirmation",
                'message': """Flight Confirmation ✈️

Your flights have been booked:

Departure: March 15, 2024 - 09:00 AM - Flight KQ 123
Return: March 20, 2024 - 14:00 PM - Flight KQ 124

Please arrive 3 hours before departure.

E-tickets attached to this message.""",
                'priority': 'high'
            },
            {
                'subject': "Loyalty Points Update: You've earned 500 points!",
                'message': """Loyalty Points Update ⭐

Congratulations! You've earned 500 loyalty points from your recent booking.

Current points: 500
Points to next tier: 500

Redeem your points for discounts on future bookings!""",
                'priority': 'medium'
            },
            {
                'subject': "Last Chance: Flash Sale Ends Tomorrow",
                'message': """⚡ LAST CHANCE! Flash Sale Ends Tomorrow ⚡

Don't miss out on our biggest sale of the year!

- 30% off all safari packages
- Free airport transfer
- Complimentary hotel night

Use code: FLASH30

Sale ends tomorrow at midnight!""",
                'priority': 'high'
            },
            {
                'subject': "Your Safari Photos Are Ready",
                'message': """Your Safari Memories 📸

Your safari photos have been uploaded to your account!

View and download your photos here: https://daysafaris.com/gallery

Share your amazing moments with friends and family!""",
                'priority': 'low'
            },
            {
                'subject': "Weather Update for Your Upcoming Safari",
                'message': """Weather Update ☀️

Good news! The weather forecast for your safari dates looks perfect:

Day temperatures: 25-28°C (77-82°F)
Night temperatures: 15-18°C (59-64°F)
Rain chance: 10%

Perfect weather for game viewing!""",
                'priority': 'medium'
            },
            {
                'subject': "Special Invitation: Members Only Safari",
                'message': """Exclusive Invitation 🎟️

You're invited to our exclusive Members Only Safari!

Date: April 10, 2024
Location: Private Game Reserve
Special rate: $1,500 (Regular $2,500)

Limited to 20 spots. RSVP by March 1st.""",
                'priority': 'high'
            },
            {
                'subject': "Payment Reminder: Due in 7 Days",
                'message': """Payment Reminder 💰

Dear Customer,

This is a reminder that your payment of $1,500 is due in 7 days for your upcoming safari.

Please login to your account to complete the payment.

Thank you for choosing Day Safaris!""",
                'priority': 'urgent'
            },
            {
                'subject': "Meet Your Safari Guide",
                'message': """Meet Your Safari Guide! 🦁

We're pleased to introduce your safari guide, James.

Experience: 15 years
Languages: English, Swahili, French
Specialty: Big Cat photography

James will contact you 2 days before your safari to confirm meeting point.

Get ready for an unforgettable adventure!""",
                'priority': 'medium'
            }
        ]
        
        priorities = ['low', 'medium', 'high', 'urgent']
        statuses = ['unread', 'read']
        
        # Create 20 messages
        messages_created = []
        for i in range(20):
            # Get message data (cycle through if needed)
            msg_data = messages_data[i % len(messages_data)]
            
            # Alternate priorities and statuses
            if i < 10:
                status = 'unread'
                email_sent = False
            else:
                status = 'read'
                email_sent = True
            
            # Create date ranging from 30 days ago to now
            days_ago = random.randint(0, 30)
            created_date = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            sent_date = created_date + timedelta(hours=random.randint(1, 24))
            
            # Create the message (without sender_name)
            msg = UserMessage.objects.create(
                user=user,
                subject=msg_data['subject'],
                message=msg_data['message'],
                priority=msg_data['priority'],
                status=status,
                created_at=created_date,
                sent_at=sent_date,
                email_sent=email_sent,
                email_sent_at=sent_date if email_sent else None,
                is_deleted=False
            )
            
            messages_created.append(msg)
            self.stdout.write(f"  ✓ Created: [{msg.id}] {msg.subject[:50]}... ({msg.priority}, {msg.status})")
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully created {len(messages_created)} messages for user: {user.username}'))
        self.stdout.write(self.style.SUCCESS('='*50))
        
        # Statistics
        unread_count = UserMessage.objects.filter(user=user, status='unread', is_deleted=False).count()
        read_count = UserMessage.objects.filter(user=user, status='read', is_deleted=False).count()
        archived_count = UserMessage.objects.filter(user=user, status='archived', is_deleted=False).count()
        
        self.stdout.write(f'\n📊 Message Statistics:')
        self.stdout.write(f"  Total messages: {len(messages_created)}")
        self.stdout.write(f"  Unread: {unread_count}")
        self.stdout.write(f"  Read: {read_count}")
        self.stdout.write(f"  Archived: {archived_count}")
        
        # Priority breakdown
        self.stdout.write(f'\n📊 Priority Breakdown:')
        for priority in priorities:
            count = UserMessage.objects.filter(user=user, priority=priority, is_deleted=False).count()
            self.stdout.write(f"  {priority.capitalize()}: {count}")
        
        self.stdout.write(self.style.SUCCESS('\n✨ You can now view these messages at: /accounts/messages/'))