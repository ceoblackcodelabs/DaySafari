from django.db import models

# Create your models here.
class EmailLog(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=50)  # e.g., 'sent', 'failed'
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient} - {self.subject} - {self.status}"

class CompanyProfile(models.Model):
    name = models.CharField("Company Name", max_length=50, default="Day Safari Adventures")
    booking_confirmation_email = models.EmailField(default="info@daysafariadventures.com")
    company_whatsapp = models.CharField(max_length=20, default=" +254759379600")
    company_phone = models.CharField(max_length=20, default=" +254140919894")
    mpesa_payment_link = models.CharField(max_length=100, default="http://192.168.8.179:8001/")