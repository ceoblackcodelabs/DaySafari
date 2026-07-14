from django.db import models
from PIL import Image
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
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
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)
    # SEO Fields
    seo_title = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Keep under 60 characters. Leave blank to auto-generate from title."
    )
    seo_description = models.TextField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Keep under 160 characters. Leave blank to auto-generate from content."
    )
    schema_markup = models.TextField(blank=True, help_text="Paste raw JSON-LD schema here")
    author = models.CharField(max_length=100)
    content = RichTextUploadingField()
    likes = models.IntegerField(default=0)
    comments = models.ManyToManyField(BlogComments, blank=True)
    published_date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(default='blog_images/default.jpg', upload_to='blog_images/', blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_base = self.title.lower().replace(' ', '-')
            slug = slug_base
            counter = 1
            while Blogs.objects.filter(slug=slug).exists():
                slug = f"{slug_base}-{counter}"
                counter += 1
            self.slug = slug
        super(Blogs, self).save(*args, **kwargs)

class Brochure(models.Model):
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
        ("Suswa", "suswa"),
        ("Meru", "meru")
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

# models.py

class Ad(models.Model):
    """Popup advertisement model"""
    title = models.CharField(max_length=200)
    package = models.ForeignKey('Places.AwesomePackages', on_delete=models.CASCADE, related_name='ads', null=True, blank=True)
    trekking_package = models.ForeignKey('Home.Trekking', on_delete=models.CASCADE, related_name='ads', null=True, blank=True)

    image = models.ImageField(upload_to='ads/', help_text="Main advertisement image")
    description = models.TextField(blank=True, help_text="Short description for the ad")

    discount_percentage = models.IntegerField(default=0, help_text="Discount percentage (0-100)")
    show_book_now = models.BooleanField(default=True, help_text="Show Book Now button")

    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField(default=True)
    show_on_pages = models.CharField(max_length=200, blank=True, help_text="Comma separated URLs or leave blank for all pages")

    button_text = models.CharField(max_length=50, default="View Package", help_text="Text for the CTA button")
    button_color = models.CharField(max_length=20, default="btn-primary", help_text="Bootstrap button color class")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Advertisement"
        verbose_name_plural = "Advertisements"

    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"

    def get_package_url(self):
        """Get the URL for the associated package"""
        if self.package:
            return self.package.get_absolute_url()
        elif self.trekking_package:
            return f"/trekking/{self.trekking_package.category.lower()}/{self.trekking_package.id}/"
        elif self.cruise_package:
            return f"/cruises/{self.cruise_package.id}/"
        return "#"

    def get_package_name(self):
        """Get the name of the associated package"""
        if self.package:
            return self.package.name
        elif self.trekking_package:
            return self.trekking_package.name
        elif self.cruise_package:
            return self.cruise_package.name
        return self.title

    def get_package_price(self):
        """Get the price of the associated package"""
        if self.package:
            return self.package.price
        elif self.trekking_package:
            return self.trekking_package.price
        elif self.cruise_package:
            return self.cruise_package.price
        return None

    def get_discounted_price(self):
        """Calculate discounted price"""
        original_price = self.get_package_price()
        if original_price and self.discount_percentage > 0:
            discount_amount = (original_price * self.discount_percentage) / 100
            return original_price - discount_amount
        return original_price

    def get_booking_url(self):
        """Get the booking URL for the associated package"""
        if self.package:
            return f'/places/package/{self.package.id}/book/'
        elif self.trekking_package:
            return f'/trekking/{self.trekking_package.category.lower()}/{self.trekking_package.id}/book/'
        elif self.cruise_package:
            return f'/cruises/{self.cruise_package.id}/book/'
        return "#"

    def get_whatsapp_message(self):
        """Generate a WhatsApp message for this ad"""
        package_name = self.get_package_name()
        discount_text = f" with {self.discount_percentage}% discount" if self.discount_percentage > 0 else ""

        message = f"""Hello Day Safaris Adventures,

        I'm interested in booking the following package:
        📦 Package: {package_name}{discount_text}
        🔗 Ad: {self.title}

        Please send me more information about:
        - Availability
        - Total cost
        - Payment options
        - Itinerary details

        Thank you!"""

        return message