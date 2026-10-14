from django.db import models
from Places.models import Destinations
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class Bookings(models.Model):
    """Every booking lead on the site: safari, trekking and Airbnb enquiries."""
    TYPE_CHOICES = [('safari', 'Safari'), ('trekking', 'Trekking'), ('airbnb', 'Airbnb'), ('hotel', 'Hotel')]
    STATUS_CHOICES = [('new', 'New'), ('contacted', 'Contacted'), ('confirmed', 'Confirmed'),
                      ('cancelled', 'Cancelled'), ('spam', 'Spam')]

    client = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    booking_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='safari', db_index=True)
    name = models.CharField(default='', max_length=100)
    email = models.EmailField(default='email@example.com')
    phone = models.CharField(default='', max_length=20)
    destination = models.ForeignKey(Destinations, on_delete=models.CASCADE, blank=True, null=True)
    trekking_package = models.ForeignKey('Home.Trekking', on_delete=models.SET_NULL, blank=True, null=True,
                                         related_name='bookings')
    airbnb = models.ForeignKey('Hotels.AirBNB', on_delete=models.SET_NULL, blank=True, null=True,
                               related_name='bookings')
    hotel = models.ForeignKey('Hotels.Hotel', on_delete=models.SET_NULL, blank=True, null=True,
                              related_name='enquiries')
    persons = models.IntegerField(default=1)
    date = models.DateField(default=timezone.now)          # travel date / check-in
    check_out = models.DateField(null=True, blank=True)    # Airbnb / hotel stays
    has_children = models.BooleanField(null=True, blank=True)      # hotel enquiries: travelling with kids?
    children_count = models.PositiveSmallIntegerField(null=True, blank=True)
    children_ages = models.CharField(max_length=60, blank=True)
    message = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new', db_index=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def children_summary(self):
        if self.has_children is None:
            return ''
        if not self.has_children:
            return 'No children'
        ages = f' (ages {self.children_ages})' if self.children_ages else ''
        return f'Yes, {self.children_count or "?"} child{"ren" if (self.children_count or 0) != 1 else ""}{ages}'

    @property
    def item_name(self):
        """What was booked, whichever type it is."""
        item = self.destination or self.trekking_package or self.hotel or self.airbnb
        return str(item) if item else 'General enquiry'

    def __str__(self):
        return f"{self.name} - {self.item_name}"


class Contact(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='New', choices=[('New', 'New'), ('Read', 'Read'), ('Closed', 'Closed'), ('Spam', 'Spam')])
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject[:50]}"
    


class QuickLead(models.Model):
    """A visitor who used the 'What's your next adventure?' popup and was sent on to WhatsApp."""
    STATUS = [('New', 'New'), ('Contacted', 'Contacted'), ('Booked', 'Booked'), ('Closed', 'Closed'), ('Spam', 'Spam')]
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=25)
    tour = models.CharField(max_length=160, blank=True)
    message = models.TextField(blank=True)
    page_url = models.CharField(max_length=300, blank=True)
    language = models.CharField(max_length=8, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default='New', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'WhatsApp lead'
        verbose_name_plural = 'WhatsApp leads'

    def __str__(self):
        return f"{self.name} - {self.tour or 'general'}"
