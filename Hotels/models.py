from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Hotel(models.Model):
    """A hotel / lodge / camp / villa shown on the public Hotels pages."""

    TYPE_CHOICES = [
        ('hotel', 'Hotel'),
        ('lodge', 'Safari Lodge'),
        ('camp', 'Tented Camp'),
        ('resort', 'Beach Resort'),
        ('villa', 'Villa'),
        ('apartment', 'Apartment / Suite'),
        ('cabin', 'Eco Cabin'),
    ]
    ROOMS_CHOICES = [
        ('Studio', 'Studio'), ('1b', '1 Bedroom'), ('2b', '2 Bedroom'),
        ('3b', '3 Bedroom'), ('4b', '4 Bedroom'),
    ]
    MEAL_CHOICES = [
        ('', 'Not specified'), ('RO', 'Room only'), ('BB', 'Bed & Breakfast'),
        ('HB', 'Half board'), ('FB', 'Full board'), ('AI', 'All inclusive'),
    ]
    STAR_CHOICES = [(i, f'{i} Star') for i in range(1, 6)]

    # ---- public information ----
    name = models.CharField(max_length=120, db_index=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    country = models.CharField(max_length=60, db_index=True, help_text='e.g. Kenya, Tanzania, Uganda')
    location = models.CharField(max_length=100, help_text='Area or town, e.g. Diani Beach')
    property_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='hotel', db_index=True)
    star_rating = models.PositiveSmallIntegerField(choices=STAR_CHOICES, default=4)
    rooms = models.CharField(max_length=20, choices=ROOMS_CHOICES, blank=True)
    summary = models.CharField(max_length=220, blank=True, help_text='One line shown on the hotel card')
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                          help_text='Starting price per night in USD')
    max_guests = models.PositiveSmallIntegerField(default=2)
    meal_plan = models.CharField(max_length=2, choices=MEAL_CHOICES, blank=True)
    amenities = models.TextField(blank=True, help_text='One amenity per line, e.g. Swimming pool')
    child_policy = models.TextField(blank=True)
    is_published = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, help_text='Featured hotels are listed first')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---- internal (never shown to visitors) ----
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    contract_validity = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-is_featured', 'country', 'name']
        indexes = [models.Index(fields=['is_published', 'country'])]

    def __str__(self):
        return f'{self.name} ({self.location}, {self.country})'

    def save(self, *args, **kwargs):
        if not self.slug:
            name_slug = slugify(self.name)
            name_words = set(name_slug.split('-'))
            # add the place to the address, but skip words the name already contains
            # ("Eka Hotel Eldoret" + "Eldoret" -> eka-hotel-eldoret)
            extra = [w for w in slugify(self.location.split('(')[0]).split('-') if w and w not in name_words]
            base = '-'.join([name_slug] + extra) or 'hotel'
            slug, n = base, 2
            while Hotel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f'{base}-{n}', n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('hotel_detail', kwargs={'slug': self.slug})

    @property
    def main_image(self):
        images = list(self.images.all())          # uses prefetch_related when available
        for image in images:
            if image.is_featured:
                return image
        return images[0] if images else None

    @property
    def stars(self):
        return range(self.star_rating)

    @property
    def empty_stars(self):
        return range(5 - self.star_rating)

    @property
    def amenity_list(self):
        return [line.strip() for line in self.amenities.splitlines() if line.strip()]

    @property
    def card_summary(self):
        return self.summary or (self.description[:150].rsplit(' ', 1)[0] + '…' if len(self.description) > 150 else self.description)


class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='hotels/')
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False, help_text='Used as the main photo')
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return f'Photo for {self.hotel.name}'


# ---- Airbnb-style stays (moved here from the removed Accomodations app; same tables, data untouched) ----
class AirBNB(models.Model):
    location = models.CharField(max_length=100)
    specification = models.CharField(max_length=50, choices=(
        ('1b', '1 Bedroom'), ('2b', '2 Bedroom'), ('3b', '3 Bedroom'), ('4b', '4 Bedroom'), ('Studio', 'Studio'),
    ))
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_guests = models.IntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Accomodations_airbnb'        # keep the existing table and its rows

    def __str__(self):
        return f'{self.location} - {self.get_specification_display()}'

    @property
    def main_image(self):
        return self.images.first()

    @property
    def all_images(self):
        return self.images.all()


class AirBNBImage(models.Model):
    airbnb = models.ForeignKey(AirBNB, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='AirBNB/', default='AirBNB/default.jpg')
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Accomodations_airbnbimage'
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return f'Image for {self.airbnb.location}'


class ApiKey(models.Model):
    """Access token for the hotels API. Only a SHA-256 hash is stored; the token itself is shown once."""
    name = models.CharField(max_length=80, help_text='Who/what uses this key, e.g. "Claude assistant"')
    prefix = models.CharField(max_length=12, unique=True, editable=False)
    key_hash = models.CharField(max_length=64, editable=False)
    is_active = models.BooleanField(default=True, help_text='Untick to revoke the key immediately')
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = 'API key'

    def __str__(self):
        return f'{self.name} ({self.prefix}…) {"active" if self.is_active else "REVOKED"}'

    @staticmethod
    def hash_token(token):
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def create_key(cls, name):
        """Create a key and return (instance, token). The token cannot be recovered later."""
        import secrets
        prefix = secrets.token_hex(4)
        token = f'dsa_{prefix}_{secrets.token_urlsafe(32)}'
        return cls.objects.create(name=name, prefix=prefix, key_hash=cls.hash_token(token)), token

    @classmethod
    def authenticate(cls, token):
        """Return the active ApiKey for this token, or None. Constant-time hash comparison."""
        import hmac
        parts = (token or '').split('_', 2)
        if len(parts) != 3 or parts[0] != 'dsa':
            return None
        key = cls.objects.filter(prefix=parts[1], is_active=True).first()
        if key and hmac.compare_digest(key.key_hash, cls.hash_token(token)):
            return key
        return None
