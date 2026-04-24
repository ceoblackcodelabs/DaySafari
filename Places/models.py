from django.db import models

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
    description = models.TextField()
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
    
class AwesomePackages(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    starRating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], default=5)
    days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    persons = models.IntegerField()
    description = models.TextField()
    category = models.CharField(default="East Africa Tours", max_length=50, choices=(
        ("East Africa Tours", "EA-T"), 
        ("Africa Tours", "A-T"),
        ("International Tours", "I-T"),
    ))
    image = models.ImageField(default='awesome_packages/default.jpg', upload_to='awesome_packages/')

    def __str__(self):
        return self.name
    
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