from django.db import models
from PIL import Image   

class Services(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100, default='fa fa-globe')

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
    image = models.ImageField(upload_to='awesome_packages/')

    def __str__(self):
        return self.name

class GalleryCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Gallery(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(GalleryCategory, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='gallery_images/')

    def __str__(self):
        return self.name
    
class Bookings(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    destination = models.CharField(max_length=100)
    persons = models.IntegerField()
    categories = models.CharField(max_length=100, choices=[('children', 'Children'), ('adults', 'Adults')], default='adults')
    message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.destination}"
    
class Testimonials(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    feedback = models.TextField()
    starRating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], default=5)
    image = models.ImageField(upload_to='testimonials/', default='testimonials/default.jpg')

    def __str__(self):
        return self.name
    
class BlogComments(models.Model):
    blog = models.ForeignKey('Blogs', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    published_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.name} on {self.blog.title}"

class Blogs(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    content = models.TextField()
    likes = models.IntegerField(default=0)
    comment = models.ManyToManyField(BlogComments, blank=True)
    published_date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)

    def __str__(self):
        return self.title
    
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

    def __str__(self):
        return self.name