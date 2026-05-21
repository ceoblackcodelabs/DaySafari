from django.db import models
from PIL import Image
from django.utils import timezone
from Places.models import Destinations

class Services(models.Model):
    # img = models.ImageField(upload_to='services_images/', default="services_images/default.jpg", null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100, default='fa fa-globe')

    def __str__(self):
        return self.name

class GalleryCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Gallery(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(GalleryCategory, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='gallery_images/')

    def __str__(self):
        return self.name

class Testimonials(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    feedback = models.TextField()
    starRating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], default=5)
    image = models.ImageField(upload_to='testimonials/', default='testimonials/default.jpg', blank=True, null=True)

    def __str__(self):
        return self.name

class BlogComments(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    comment = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.name} on {self.created_date}"

class Blogs(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    content = models.TextField()
    likes = models.IntegerField(default=0)
    comments = models.ManyToManyField(BlogComments, blank=True)
    published_date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(default='blog_images/default.jpg', upload_to='blog_images/', blank=True, null=True)

    def __str__(self):
        return self.title

class Brochure(models.Model):  # Note: Should be "Brochure" not "Bronchure"
    title = models.CharField(max_length=200)
    pdf_file = models.FileField(upload_to='brochures/')
    image = models.ImageField(upload_to='brochure_images/', blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Brochure"
        verbose_name_plural = "Brochures"

# Home/models.py

class ItineraryTreking(models.Model):
    package = models.ForeignKey('Trekking', on_delete=models.CASCADE, related_name='itinerary_days')
    day_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    activities = models.TextField(help_text="List activities for this day, separated by commas", blank=True)
    accommodation = models.CharField(max_length=200, blank=True)
    meals = models.CharField(max_length=100, choices=[
        ('Breakfast', 'Breakfast Only'),
        ('Half Board', 'Breakfast & Dinner'),
        ('Full Board', 'Breakfast, Lunch & Dinner'),
        ('All Inclusive', 'All Meals & Drinks'),
    ], default='Full Board')
    image = models.ImageField(upload_to='itinerary_trekking_images/', blank=True, null=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ['package', 'day_number']

    def __str__(self):
        return f"Day {self.day_number}: {self.title} - {self.package.name}"

class Trekking(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    starRating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], default=5)
    days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    persons = models.IntegerField()
    description = models.TextField()
    category = models.CharField(default="East Africa Tours", max_length=50, choices=(
        ("Kilimanjaro", "kilimanjaro"),
        ("Kenya", "kenya"),
        ("Longonot", "longonot"),
        ("Suswa", "suswa")
    ))
    image = models.ImageField(default='awesome_packages/default.jpg', upload_to='awesome_packages/')

    def __str__(self):
        return self.name

class TrekkingBooking(models.Model):
    BOOKING_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    # Booking reference
    booking_reference = models.CharField(max_length=20, unique=True, editable=False)

    # Package details
    package = models.ForeignKey('Trekking', on_delete=models.CASCADE, related_name='bookings')

    # Customer details
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)

    # Booking details
    number_of_persons = models.IntegerField()
    travel_date = models.DateField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    # Optional
    special_requests = models.TextField(blank=True)

    # Status
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')

    # Timestamps
    booking_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date']
        verbose_name = "Trekking Booking"
        verbose_name_plural = "Trekking Bookings"

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            import random
            import string
            from datetime import date
            date_str = date.today().strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            self.booking_reference = f"TREK-{date_str}-{random_str}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_reference} - {self.full_name} - {self.package.name}"