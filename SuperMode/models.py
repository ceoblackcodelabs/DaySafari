# models.py
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from Accomodations.models import AccomodationsImage
from Places.models import Destinations

class ItineraryActivity(models.Model):
    """Model for individual activities within an itinerary"""
    itinerary = models.ForeignKey(
        "ItineraryBuilder",
        on_delete=models.CASCADE,
        related_name='activities'
    )
    day_number = models.IntegerField(help_text="Day number for this activity")
    title = models.CharField(max_length=200, help_text="Activity title (e.g., 'Departure', 'Game Drive')")
    description = models.TextField(blank=True, help_text="Detailed description of the activity")
    location = models.CharField(max_length=200, blank=True, help_text="Location of the activity")
    duration = models.CharField(max_length=100, blank=True, help_text="Duration (e.g., '2 hours', 'Full day')")
    order = models.IntegerField(default=0, help_text="Order within the day")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_number', 'order']
        unique_together = ['itinerary', 'day_number', 'title']
        indexes = [
            models.Index(fields=['itinerary', 'day_number']),
        ]

    def __str__(self):
        return f"Day {self.day_number}: {self.title} - {self.itinerary.title}"

    def clean(self):
        if self.day_number < 1:
            raise ValidationError({'day_number': 'Day number must be at least 1.'})
        if self.day_number > self.itinerary.days_spent:
            raise ValidationError({
                'day_number': f'Day number cannot exceed the total days ({self.itinerary.days_spent}).'
            })

class ItineraryBuilder(models.Model):
    title = models.CharField(max_length=50, default="")
    client_name = models.CharField(max_length=50, default='')
    days_spent = models.IntegerField(default=10)
    price = models.IntegerField(default=10)
    description = models.TextField(default='')
    hotel_images = models.ManyToManyField(
        AccomodationsImage,
        blank=True,
        related_name='itineraries'
    )
    destination_images = models.ManyToManyField(
        Destinations,
        blank=True,
        related_name='itineraries'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        help_text="Auto-generated from title and client name"
    )
    share_link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Generated link to share the itinerary"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['client_name']),
            models.Index(fields=['title']),
            models.Index(fields=['slug']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.client_name}"

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = self._generate_unique_slug()

        # Generate share link if not provided and slug exists
        if not self.share_link and self.slug:
            self.share_link = self._generate_share_link()

        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        """Generate a unique slug from title and client name"""
        base_slug = slugify(f"{self.title}-{self.client_name}")
        if not base_slug:
            base_slug = "itinerary"

        slug = base_slug
        counter = 1
        while ItineraryBuilder.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def _generate_share_link(self):
        """Generate the share link - replace with your actual domain"""
        # In production, use your actual domain
        base_url = "https://daysafarisadventures.com/share/"
        return f"{base_url}{self.slug}"

    def clean(self):
        """Validate that image counts don't exceed 5"""
        super().clean()
        if self.pk:  # Only check if the instance already exists
            if self.hotel_images.count() > 5:
                raise ValidationError({
                    'hotel_images': 'You can select a maximum of 5 hotel images.'
                })
            if self.destination_images.count() > 5:
                raise ValidationError({
                    'destination_images': 'You can select a maximum of 5 destination images.'
                })

    def get_absolute_url(self):
        """Get the absolute URL for the itinerary detail view"""
        from django.urls import reverse
        return reverse('itinerary_detail', kwargs={'slug': self.slug})

    @property
    def shareable_link(self):
        """Property to get the share link"""
        return self.share_link or self._generate_share_link()