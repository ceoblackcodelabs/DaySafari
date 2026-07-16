from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class DestinationsCategory(models.Model):
    ORIENTATION_CHOICES = [
        ('landscape', 'Landscape'),
        ('portrait', 'Portrait')
    ]

    location = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    image = models.ImageField(upload_to='destinations_category/', blank=True, null=True)
    image_orientation = models.CharField(max_length=50, choices=ORIENTATION_CHOICES, default='landscape')

    class Meta:
        verbose_name = 'Destination Category'
        verbose_name_plural = 'Destination Categories'
        ordering = ['category']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return self.category


class Destinations(models.Model):
    category = models.ForeignKey(DestinationsCategory, on_delete=models.CASCADE, related_name='destinations')
    name = models.CharField(max_length=100, db_index=True)
    description = CKEditor5Field('Description', config_name='default')
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Destination'
        verbose_name_plural = 'Destinations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category', 'name']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.name


class MustVisit(models.Model):
    SIZE_CHOICES = [
        ('landscape', 'Landscape'),
        ('portrait', 'Portrait')
    ]

    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='must_visit_images/')
    size = models.CharField(max_length=50, choices=SIZE_CHOICES, default='landscape')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class IncluisiveExcluisive(models.Model):
    package = models.ForeignKey('AwesomePackages', on_delete=models.CASCADE, related_name='inclusions')
    name = models.CharField(max_length=100)
    is_inclusive = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Inclusion/Exclusion'
        verbose_name_plural = 'Inclusions/Exclusions'
        ordering = ['-is_inclusive', 'name']

    def __str__(self):
        return f"{'✓' if self.is_inclusive else '✗'} {self.name}"


class AwesomePackages(models.Model):
    CATEGORY_CHOICES = [
        ("East Africa Tours", "EA-T"),
        ("South Africa", "S-A"),
        ("West Africa", "W-A"),
        ("Africa Tours", "A-T"),
        ("International Tours", "I-T"),
        ("Cruises", "cruises"),
    ]

    STAR_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars')
    ]

    name = models.CharField(max_length=100, db_index=True)
    location = models.CharField(max_length=100, db_index=True)
    star_rating = models.IntegerField(choices=STAR_CHOICES, default=5)
    days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    persons = models.IntegerField()
    description = CKEditor5Field('Description', config_name='default')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="East Africa Tours", db_index=True)
    image = models.ImageField(default='awesome_packages/default.jpg', upload_to='awesome_packages/')
    slug = models.SlugField(max_length=160, unique=True, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['price']),
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'price']),
        ]

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
        return reverse('package_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name

    @property
    def starRating(self):
        """Backward compatibility for templates using starRating"""
        return self.star_rating


class PackagePurchase(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    package = models.ForeignKey(AwesomePackages, on_delete=models.CASCADE, related_name='purchases')
    full_name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(db_index=True)
    phone_number = models.CharField(max_length=20)
    number_of_persons = models.IntegerField()
    travel_date = models.DateField(db_index=True)
    special_requests = models.TextField(blank=True)
    purchase_date = models.DateTimeField(auto_now_add=True)
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', db_index=True)

    class Meta:
        verbose_name = 'Package Purchase'
        verbose_name_plural = 'Package Purchases'
        ordering = ['-purchase_date']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['travel_date']),
            models.Index(fields=['purchase_date']),
        ]

    def save(self, *args, **kwargs):
        if self.package and not self.amount_spent:
            self.amount_spent = self.package.price * self.number_of_persons
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.package.name}"


class Itinerary(models.Model):
    MEAL_CHOICES = [
        ('Breakfast', 'Breakfast Only'),
        ('Half Board', 'Breakfast & Dinner'),
        ('Full Board', 'Breakfast, Lunch & Dinner'),
        ('All Inclusive', 'All Meals & Drinks'),
    ]

    package = models.ForeignKey(AwesomePackages, on_delete=models.CASCADE, related_name='itineraries')
    day_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    activities = models.TextField(help_text="List activities for this day, separated by commas", blank=True)
    accommodation = models.CharField(max_length=200, blank=True)
    meals = models.CharField(max_length=100, choices=MEAL_CHOICES, default='Full Board')
    image = models.ImageField(upload_to='itinerary_images/', blank=True, null=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ['package', 'day_number']
        indexes = [
            models.Index(fields=['package', 'day_number']),
        ]

    def __str__(self):
        return f"Day {self.day_number}: {self.title} - {self.package.name}"


# Cache clearing signals
@receiver([post_save, post_delete], sender=AwesomePackages)
@receiver([post_save, post_delete], sender=Destinations)
@receiver([post_save, post_delete], sender=DestinationsCategory)
def clear_related_cache(sender, **kwargs):
    """Clear relevant caches when package or destination data changes"""
    cache.delete_pattern('home_context_data_*')
    cache.delete_pattern('package_*')
    cache.delete_pattern('destination_*')