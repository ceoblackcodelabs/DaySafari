from django.db import models
from Home.models import Destinations
from Places.models import AwesomePackages
from ClientRequests.models import Bookings
from django.contrib.auth.models import User

class UserRecommendations(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    package = models.ForeignKey(AwesomePackages, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'package']

    def __str__(self):
        return f"{self.user.username} - {self.package.name}"