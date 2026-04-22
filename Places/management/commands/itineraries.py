# management/commands/seed_itineraries.py
from django.core.management.base import BaseCommand
from Places.models import AwesomePackages, Itinerary

class Command(BaseCommand):
    help = 'Seed itineraries for existing packages'

    def handle(self, *args, **options):
        packages = AwesomePackages.objects.all()
        
        for package in packages:
            # Check if itineraries already exist
            if Itinerary.objects.filter(package=package).exists():
                self.stdout.write(f"Itineraries already exist for {package.name}")
                continue
            
            # Create itineraries based on package name
            if "Masai Mara" in package.name:
                Itinerary.objects.create(
                    package=package,
                    day_number=1,
                    title="Arrival in Nairobi",
                    description="Arrive at Jomo Kenyatta International Airport. Meet your guide and transfer to your hotel. Evening briefing about your safari.",
                    accommodation="Nairobi Serena Hotel",
                    meals="Half Board"
                )
                Itinerary.objects.create(
                    package=package,
                    day_number=2,
                    title="Drive to Masai Mara",
                    description="Depart Nairobi and drive through the Great Rift Valley. Arrive at Masai Mara in time for lunch. Afternoon game drive.",
                    accommodation="Mara Serena Safari Lodge",
                    meals="Full Board"
                )
                # Add more days...
                
            elif "Zanzibar" in package.name:
                Itinerary.objects.create(
                    package=package,
                    day_number=1,
                    title="Arrival in Zanzibar",
                    description="Arrive at Abeid Amani Karume International Airport. Transfer to your beachfront resort.",
                    accommodation="Zanzibar Beach Resort",
                    meals="Half Board"
                )
                # Add more days...
            
            self.stdout.write(self.style.SUCCESS(f"Itineraries created for {package.name}"))