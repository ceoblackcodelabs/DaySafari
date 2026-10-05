from django.db import models
from Places.models import Destinations
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class Bookings(models.Model):
    """Every booking lead on the site: safari, trekking and Airbnb enquiries."""
    TYPE_CHOICES = [('safari', 'Safari'), ('trekking', 'Trekking'), ('airbnb', 'Airbnb')]
    STATUS_CHOICES = [('new', 'New'), ('contacted', 'Contacted'), ('confirmed', 'Confirmed'),
                      ('cancelled', 'Cancelled')]

    client = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    booking_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='safari', db_index=True)
    name = models.CharField(default='', max_length=100)
    email = models.EmailField(default='email@example.com')
    phone = models.CharField(default='', max_length=20)
    destination = models.ForeignKey(Destinations, on_delete=models.CASCADE, blank=True, null=True)
    trekking_package = models.ForeignKey('Home.Trekking', on_delete=models.SET_NULL, blank=True, null=True,
                                         related_name='bookings')
    airbnb = models.ForeignKey('Accomodations.AirBNB', on_delete=models.SET_NULL, blank=True, null=True,
                               related_name='bookings')
    persons = models.IntegerField(default=1)
    date = models.DateField(default=timezone.now)          # travel date / check-in
    check_out = models.DateField(null=True, blank=True)    # Airbnb only
    message = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new', db_index=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def item_name(self):
        """What was booked, whichever type it is."""
        item = self.destination or self.trekking_package or self.airbnb
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
    status = models.CharField(max_length=20, default='New', choices=[('New', 'New'), ('Read', 'Read'), ('Closed', 'Closed')])
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject[:50]}"
    
