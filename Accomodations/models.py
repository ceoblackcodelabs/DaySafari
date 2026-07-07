from django.db import models

class MealPlan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Create your models here.
class Accomodations(models.Model):
    destinations = models.CharField(max_length=100, blank=True)
    name =  models.CharField(default="house 1", max_length=100)
    location = models.CharField(default="Nairobi", max_length=100)
    specification = models.CharField(max_length=50, choices=(
    ("1b", "1 Bedroom"),
    ("2b", "2 Bedroom"),
    ("3b", "3 Bedroom"),
    ("4b", "4 Bedroom"),
    ("Studio", "Studio"),
    ))
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_guests = models.IntegerField(default=2)
    child_policy = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    contract_validity = models.DateField(blank=True, null=True)
    meal_plan = models.ManyToManyField(MealPlan, blank=True, related_name='accomodations')
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    rating = models.CharField(max_length=10, blank=True, choices=(
        ("1", "1 Star"),
        ("2", "2 Star"),
        ("3", "3 Star"),
        ("4", "4 Star"),
        ("5", "5 Star"),
    ))

    def __str__(self):
        return f"{self.location} - {self.get_specification_display()}"

    @property
    def main_image(self):
        """Get the first image as main image"""
        return self.images.first()

    @property
    def all_images(self):
        """Get all images"""
        return self.images.all()


class AccomodationsImage(models.Model):
    accomodation = models.ForeignKey(Accomodations, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='Accomodations/', default="Accomodations/default.jpg")
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return f"Image for {self.accomodation.location}"


class AirBNB(models.Model):
    location = models.CharField(max_length=100)
    specification = models.CharField(max_length=50, choices=(
        ("1b", "1 Bedroom"),
        ("2b", "2 Bedroom"),
        ("3b", "3 Bedroom"),
        ("4b", "4 Bedroom"),
        ("Studio", "Studio"),
    ))
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_guests = models.IntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.location} - {self.get_specification_display()}"

    @property
    def main_image(self):
        """Get the first image as main image"""
        return self.images.first()

    @property
    def all_images(self):
        """Get all images"""
        return self.images.all()


class AirBNBImage(models.Model):
    airbnb = models.ForeignKey(AirBNB, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='AirBNB/', default="AirBNB/default.jpg")
    caption = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return f"Image for {self.airbnb.location}"

class AirBNBBooking(models.Model):
    airbnb = models.ForeignKey(AirBNB, on_delete=models.CASCADE, related_name='bookings')
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Booking for {self.airbnb.location} by {self.guest_name}"