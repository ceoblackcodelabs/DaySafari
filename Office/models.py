from django.db import models

# Create your models here.
class Employee(models.Model):
    name =  models.CharField(default="employee1", max_length=100)
    email = models.EmailField(default="email@example.com")
    contact = models.CharField(default="+2547", max_length=20)
    role = models.CharField(default="employee", max_length=50)
    salary = models.IntegerField(default=0)
