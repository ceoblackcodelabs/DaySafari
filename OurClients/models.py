from django.db import models
from Home.models import Destinations
from django.contrib.auth.models import User

class SavedDestination(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_destinations')
    destination = models.ForeignKey(Destinations, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'destination']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.destination.name}"