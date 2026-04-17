from django.core.management.base import BaseCommand
from Home.models import Services


class Command(BaseCommand):
    help = "Seed database with default services"

    def handle(self, *args, **kwargs):
        services_data = [
            {
                "name": "African Wildlife Safaris",
                "description": "Experience the magic of the African wilderness with our expert guides. Track the Big Five in Masai Mara, witness the Great Wildebeest Migration, and capture breathtaking moments of lions, elephants, rhinos, leopards, and buffalos in their natural habitat.",
                "icon": "fa fa-globe"
            },
            {
                "name": "Travel Partnership Programs",
                "description": "Join our exclusive travel partnership network and unlock special rates for group bookings, corporate retreats, and family vacations. We work with hotels, airlines, and local guides to provide seamless travel experiences across East Africa.",
                "icon": "fa fa-handshake"
            },
            {
                "name": "Airport Transfers & Shuttles",
                "description": "Enjoy hassle-free airport transfers from Jomo Kenyatta International Airport, Moi International Airport, Kilimanjaro International Airport, and Entebbe Airport. Our professional drivers and comfortable vehicles ensure you start and end your journey stress-free.",
                "icon": "fa fa-plane"
            },
            {
                "name": "Custom Tailor-Made Tours",
                "description": "Design your dream African adventure with our personalized tour planning service. Whether it's a romantic honeymoon safari, a family vacation, or a solo expedition, we craft itineraries that match your preferences, budget, and travel style perfectly.",
                "icon": "fa fa-globe"
            }
        ]

        created_count = 0

        for service in services_data:
            obj, created = Services.objects.get_or_create(
                name=service["name"],
                defaults={
                    "description": service["description"],
                    "icon": service["icon"]
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Added: {obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Already exists: {obj.name}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. {created_count} new services added."))