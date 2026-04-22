from django.db import models
from Places.models import Destinations
from django.utils import timezone

# Create your models here.
class Bookings(models.Model):
    name = models.CharField(default='', max_length=100)
    email = models.EmailField(default='email@example.com')
    phone = models.CharField(default='', max_length=20)
    destination = models.ForeignKey(Destinations, on_delete=models.CASCADE, blank=True, null=True)
    persons = models.IntegerField(default=1)
    date = models.DateField(default=timezone.now)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.destination}"
        
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject[:50]}"
    
