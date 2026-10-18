from django.db import models
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from Places.models import Destinations
from .validators import validate_image_10mb, validate_document_20mb, validate_video_50mb
import logging
logger = logging.getLogger(__name__)

class Services(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100, default='fa fa-globe')
    image = models.ImageField(upload_to='services/', blank=True, null=True, help_text='Optional picture shown on the service card')

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class GalleryCategory(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Gallery Category'
        verbose_name_plural = 'Gallery Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Gallery(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(GalleryCategory, on_delete=models.CASCADE, related_name='galleries')
    image = models.ImageField(upload_to='gallery_images/', validators=[validate_image_10mb])

    class Meta:
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.name


class AboutImage(models.Model):
    """Images that loop/rotate in the 'About' section on the homepage and
    about page. Add as many as you like; only active ones are shown, in
    'order' then newest-first."""
    image = models.ImageField(upload_to='about_images/', validators=[validate_image_10mb])
    caption = models.CharField(max_length=150, blank=True, help_text="Optional alt text / caption")
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'About Section Image'
        verbose_name_plural = 'About Section Images'
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'order']),
        ]

    def __str__(self):
        return self.caption or f"About image #{self.pk}"


class HeroSlide(models.Model):
    """Slides shown in the homepage hero carousel at the top of the page.
    Add as many as you like; only active ones are shown, in 'order'.
    Each slide is either an Image or a Video - upload the matching file
    for whichever media_type you pick. A video slide should also get a
    fallback_image, which is shown if the browser can't play the video."""

    MEDIA_IMAGE = 'image'
    MEDIA_VIDEO = 'video'
    MEDIA_TYPE_CHOICES = [
        (MEDIA_IMAGE, 'Image'),
        (MEDIA_VIDEO, 'Video'),
    ]

    media_type = models.CharField(
        max_length=10, choices=MEDIA_TYPE_CHOICES, default=MEDIA_IMAGE,
        help_text="Choose Image or Video, then upload the matching file below."
    )
    image = models.ImageField(
        upload_to='hero_slides/images/', blank=True, null=True,
        validators=[validate_image_10mb],
        help_text="Required when Media type = Image."
    )
    video = models.FileField(
        upload_to='hero_slides/videos/', blank=True, null=True,
        validators=[validate_video_50mb],
        help_text="Required when Media type = Video. MP4 recommended, max 50MB."
    )
    fallback_image = models.ImageField(
        upload_to='hero_slides/fallback/', blank=True, null=True,
        validators=[validate_image_10mb],
        help_text="Shown if the video can't load. Recommended for Video slides."
    )

    eyebrow_text = models.CharField(
        max_length=100, blank=True,
        help_text="Small uppercase line above the title, e.g. 'Explore The World'"
    )
    title = models.CharField(
        max_length=200,
        help_text="Main heading, e.g. 'Kenya Safari Tours & East Africa Packages'"
    )
    subtitle = models.CharField(
        max_length=200, blank=True,
        help_text="Line under the title, e.g. \"Adventure Awaits - Let's Go\""
    )

    button_text = models.CharField(max_length=50, blank=True, default='Discover Now')
    button_url = models.CharField(
        max_length=200, blank=True, default='/about/',
        help_text="Where the button links to, e.g. /about/ or /packages/"
    )

    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hero Slide'
        verbose_name_plural = 'Hero Slides'
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'order']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.media_type == self.MEDIA_IMAGE and not self.image:
            raise ValidationError({'image': "Please upload an image, or switch Media type to Video."})
        if self.media_type == self.MEDIA_VIDEO and not self.video:
            raise ValidationError({'video': "Please upload a video, or switch Media type to Image."})


class Testimonials(models.Model):
    STAR_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars')
    ]

    name = models.CharField(max_length=100, db_index=True)
    location = models.CharField(max_length=100)
    feedback = models.TextField()
    star_rating = models.IntegerField(choices=STAR_CHOICES, default=5)
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True, validators=[validate_image_10mb])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['star_rating']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    @property
    def starRating(self):
        """Backward compatibility for templates using starRating"""
        return self.star_rating


class BlogComments(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    comment = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    blog = models.ForeignKey('Blogs', on_delete=models.CASCADE, related_name='blog_comments', null=True)

    class Meta:
        verbose_name = 'Blog Comment'
        verbose_name_plural = 'Blog Comments'
        ordering = ['-created_date']

    def __str__(self):
        return f"Comment by {self.name} on {self.created_date}"


class BlogCategory(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers show first")

    class Meta:
        verbose_name = 'Blog category'
        verbose_name_plural = 'Blog categories'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Blogs(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(unique=True, blank=True, null=True, db_index=True)

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
    author = models.CharField(max_length=100, db_index=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    content = CKEditor5Field('Content', config_name='default')
    likes = models.IntegerField(default=0)
    comments = models.ManyToManyField(BlogComments, blank=True)
    published_date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(default='blog_images/default.jpg', upload_to='blog_images/', blank=True, null=True, validators=[validate_image_10mb])

    class Meta:
        verbose_name = 'Blog'
        verbose_name_plural = 'Blogs'
        ordering = ['-published_date']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['slug']),
            models.Index(fields=['author']),
            models.Index(fields=['published_date']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            slug_base = slugify(self.title)[:70] or 'post'
            slug = slug_base
            counter = 1
            while Blogs.objects.filter(slug=slug).exists():
                slug = f"{slug_base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Offer(models.Model):
    """A poster-style travel offer shown in the homepage 'Special Offers' section."""
    title = models.CharField(max_length=160)
    image = models.ImageField(upload_to='offers/', validators=[validate_image_10mb], help_text="The poster. A square or 4:5 image works best.")
    start_date = models.DateField(null=True, blank=True, help_text="Leave empty to show it as 'Active now' straight away.")
    end_date = models.DateField(null=True, blank=True, help_text="The offer disappears after this day. Leave empty for no end.")
    whatsapp_message = models.CharField(max_length=250, blank=True, help_text="Pre-filled WhatsApp message. Leave empty to use the title.")
    is_active = models.BooleanField(default=True, help_text="Untick to hide it without deleting.")
    order = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers show first. Equal numbers: newest first.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_upcoming(self):
        from datetime import date
        return bool(self.start_date and self.start_date > date.today())

    @property
    def whatsapp_url(self):
        from urllib.parse import quote
        text = self.whatsapp_message or f"Hello Day Safaris, I am interested in: {self.title}"
        return f"https://wa.me/254759379600?text={quote(text)}"


class TrustBadge(models.Model):
    """An award or partner logo shown in the homepage 'Why Day Safaris' section (add only ones you truly hold)."""
    KINDS = [('award', 'Award / accreditation'), ('partner', 'Partner / association')]
    name = models.CharField(max_length=100, help_text="Shown as the logo's alt text, e.g. 'IATA' or 'Tripadvisor Travellers' Choice 2025'.")
    image = models.ImageField(upload_to='badges/', validators=[validate_image_10mb])
    url = models.URLField(blank=True, help_text="Optional link when the logo is clicked.")
    kind = models.CharField(max_length=10, choices=KINDS, default='partner')
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['kind', 'order', 'id']
        verbose_name = 'Award / partner logo'
        verbose_name_plural = 'Awards & partner logos'

    def __str__(self):
        return f"{self.get_kind_display()}: {self.name}"


class Brochure(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    pdf_file = models.FileField(upload_to='brochures/', validators=[validate_document_20mb])
    image = models.ImageField(upload_to='brochure_images/', blank=True, null=True, validators=[validate_image_10mb])
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Brochure"
        verbose_name_plural = "Brochures"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title


class ItineraryTreking(models.Model):
    MEAL_CHOICES = [
        ('Breakfast', 'Breakfast Only'),
        ('Half Board', 'Breakfast & Dinner'),
        ('Full Board', 'Breakfast, Lunch & Dinner'),
        ('All Inclusive', 'All Meals & Drinks'),
    ]

    package = models.ForeignKey('Trekking', on_delete=models.CASCADE, related_name='itinerary_days')
    day_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    activities = models.TextField(help_text="List activities for this day, separated by commas", blank=True)
    accommodation = models.CharField(max_length=200, blank=True)
    meals = models.CharField(max_length=100, choices=MEAL_CHOICES, default='Full Board')
    image = models.ImageField(upload_to='itinerary_trekking_images/', blank=True, null=True, validators=[validate_image_10mb])

    class Meta:
        ordering = ['day_number']
        unique_together = ['package', 'day_number']
        indexes = [
            models.Index(fields=['package', 'day_number']),
        ]

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"


class Trekking(models.Model):
    CATEGORY_CHOICES = [
        ("Kilimanjaro", "Kilimanjaro"),
        ("Kenya", "Kenya"),
        ("Longonot", "Longonot"),
        ("Suswa", "Suswa"),
        ("Meru", "Meru")
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
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    image = models.ImageField(default='awesome_packages/default.jpg', upload_to='awesome_packages/', validators=[validate_image_10mb])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Trekking Package'
        verbose_name_plural = 'Trekking Packages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['price']),
            models.Index(fields=['category', 'price']),
        ]

    def __str__(self):
        return self.name

    @property
    def starRating(self):
        """Backward compatibility for templates using starRating"""
        return self.star_rating


class Ad(models.Model):
    """Popup advertisement model"""
    title = models.CharField(max_length=200)
    package = models.ForeignKey('Places.AwesomePackages', on_delete=models.CASCADE, related_name='ads', null=True, blank=True)
    trekking_package = models.ForeignKey('Home.Trekking', on_delete=models.CASCADE, related_name='ads', null=True, blank=True)

    image = models.ImageField(upload_to='ads/', help_text="Main advertisement image", validators=[validate_image_10mb])
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
        return "#"

    def get_package_name(self):
        """Get the name of the associated package"""
        if self.package:
            return self.package.name
        elif self.trekking_package:
            return self.trekking_package.name
        return self.title

    def get_package_price(self):
        """Get the price of the associated package"""
        if self.package:
            return self.package.price
        elif self.trekking_package:
            return self.trekking_package.price
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


# Signal to clear cache when data changes
@receiver([post_save, post_delete], sender=Services)
@receiver([post_save, post_delete], sender=Destinations)
@receiver([post_save, post_delete], sender=Testimonials)
@receiver([post_save, post_delete], sender=Blogs)
@receiver([post_save, post_delete], sender=AboutImage)
def clear_home_cache(sender, **kwargs):
    """Clear homepage cache when any of these models change"""
    try:
        from django.core.cache import cache
        # Try pattern deletion if available
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern('home_context_data_*')
        else:
            # Fallback to deleting specific keys
            keys_to_delete = ['home_context_data_True', 'home_context_data_False', 'about_context_data']
            for key in keys_to_delete:
                try:
                    cache.delete(key)
                except:
                    pass
    except Exception as e:
        # Don't break the application if cache clearing fails
        logger.warning(f"Cache clearing failed during migration: {e}")

GUIDE_DEFAULT_ROLE = 'Professional Safari Guide'
GUIDE_DEFAULT_SHORT_BIO = "Friendly, knowledgeable and safety-focused, with deep local knowledge of East Africa's parks and wildlife."
GUIDE_DEFAULT_BIO = (
    "<p>As a member of the Day Safaris Adventures guiding team, I take guests beyond the sightings and into the story of the land: "
    "how animals live, how the seasons change the landscape, and how local communities and conservation work together.</p>"
    "<p>Every trip starts with listening. Whether you dream of watching big cats at dawn, photographing elephants against "
    "Kilimanjaro, or enjoying a relaxed family getaway, I plan each day around your interests, pace and comfort, "
    "and I always put your safety first.</p>"
    "<p>I am trained in first aid and wildlife safety, I know the best viewpoints and quiet corners of the parks, "
    "and I enjoy sharing practical photography and birdwatching tips along the way. Guests travel with a well-maintained 4x4 "
    "safari vehicle, cold drinking water and clear information at every stop.</p>"
    "<p>I would be delighted to guide you. Send us a message on WhatsApp with your dates and interests, and our team will "
    "prepare a free, no-obligation quote for your safari.</p>"
)
GUIDE_DEFAULT_SPECIALIZATIONS = 'Big Five Game Viewing, Wildlife Photography, Birdwatching, Family Safaris, Cultural Experiences'
GUIDE_DEFAULT_LANGUAGES = 'English, Swahili'
GUIDE_DEFAULT_PARKS = 'Masai Mara, Amboseli, Lake Nakuru, Tsavo, Nairobi National Park'


class Guide(models.Model):
    """A member of the guiding team: shown on the About page, each with a profile page of their own."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    role = models.CharField(max_length=120, default=GUIDE_DEFAULT_ROLE, help_text='e.g. Senior Safari Guide')
    photo = models.ImageField(upload_to='guides/', validators=[validate_image_10mb], blank=True, null=True)
    short_bio = models.CharField(max_length=200, blank=True, default=GUIDE_DEFAULT_SHORT_BIO, help_text='One line shown on the About page card')
    bio = CKEditor5Field('Profile', config_name='default', blank=True, default=GUIDE_DEFAULT_BIO)
    specializations = models.CharField(max_length=300, blank=True, default=GUIDE_DEFAULT_SPECIALIZATIONS, help_text='Separate with commas, e.g. Big Cats, Birding, Photography')
    languages = models.CharField(max_length=200, blank=True, default=GUIDE_DEFAULT_LANGUAGES, help_text='Separate with commas, e.g. English, Swahili, French')
    years_experience = models.PositiveSmallIntegerField(null=True, blank=True, default=5)
    parks = models.CharField('Parks and regions', max_length=300, blank=True, default=GUIDE_DEFAULT_PARKS, help_text='Separate with commas, e.g. Masai Mara, Amboseli')
    is_active = models.BooleanField(default=True, help_text='Untick to hide this guide from the site')
    order = models.PositiveSmallIntegerField(default=0, help_text='Lower numbers show first')

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Guide'
        verbose_name_plural = 'Guides'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.name) or 'guide'
            slug, n = base, 2
            while Guide.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f'{base}-{n}', n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('guide_detail', args=[self.slug])

    @staticmethod
    def _split(text):
        return [x.strip() for x in (text or '').split(',') if x.strip()]

    @property
    def specialization_list(self):
        return self._split(self.specializations)

    @property
    def language_list(self):
        return self._split(self.languages)

    @property
    def park_list(self):
        return self._split(self.parks)
