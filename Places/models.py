from django.db import models
from django.contrib.auth.models import User
from google.auth import default
from django.urls import reverse
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

# Create your models here.
class DestinationsCategory(models.Model):
    location = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    image = models.ImageField(upload_to='destinations_category/', blank=True, null=True)
    image_orientation = models.CharField(max_length=50, choices=[('landscape', 'Landscape'), ('portrait', 'Portrait')], default='landscape')

    def __str__(self):
        return self.category

class Destinations(models.Model):
    category = models.ForeignKey(DestinationsCategory, on_delete=models.CASCADE )
    name = models.CharField(max_length=100)
    description = CKEditor5Field('Description', config_name='default')
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    def __str__(self):
        return self.name

class MustVisit(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='must_visit_images/')
    size = models.CharField(max_length=50, choices=[('landscape', 'Landscape'), ('portrait', 'Portrait')], default='landscape')

    def __str__(self):
        return self.name

class IncluisiveExcluisive(models.Model):
    package = models.ForeignKey('AwesomePackages', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=True)

class AwesomePackages(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    starRating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], default=5)
    days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    persons = models.IntegerField()
    description = CKEditor5Field('Description', config_name='default')
    category = models.CharField(default="East Africa Tours", max_length=50, choices=(
        ("East Africa Tours", "EA-T"),
        ("South Africa", "S-A"),
        ("West Africa", "W-A"),
        ("Africa Tours", "A-T"),
        ("International Tours", "I-T"),
        ("Cruises",  "cruises"),
    ))
    image = models.ImageField(default='awesome_packages/default.jpg', upload_to='awesome_packages/')
    slug = models.SlugField(max_length=160, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base_slug = slugify(f"{self.name}-{self.location}") or slugify(self.name) or "package"
        slug = base_slug
        counter = 2
        while AwesomePackages.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def get_absolute_url(self):
        """Return the URL to view this package"""
        return reverse('package_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

class PackagePurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    package = models.ForeignKey(AwesomePackages, on_delete=models.CASCADE, related_name='purchases')
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    number_of_persons = models.IntegerField()
    travel_date = models.DateField()
    special_requests = models.TextField(blank=True)
    purchase_date = models.DateTimeField(auto_now_add=True)
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Cancelled', 'Cancelled')], default='Pending')

    def __str__(self):
        return f"{self.full_name} - {self.package.name}"

    def save(self, *args, **kwargs):
        # Auto-calculate amount_spent based on package price and persons
        if self.package and not self.amount_spent:
            self.amount_spent = self.package.price * self.number_of_persons
        super().save(*args, **kwargs)

class Itinerary(models.Model):
    package = models.ForeignKey(AwesomePackages, on_delete=models.CASCADE, related_name='itineraries')
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
    image = models.ImageField(upload_to='itinerary_images/', blank=True, null=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ['package', 'day_number']

    def __str__(self):
        return f"Day {self.day_number}: {self.title} - {self.package.name}"


