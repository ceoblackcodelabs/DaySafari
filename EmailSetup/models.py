from django.db import models

# Create your models here.
class EmailLog(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=50)  # e.g., 'sent', 'failed'
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.recipient} - {self.subject} - {self.status}"