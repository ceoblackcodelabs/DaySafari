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
    
    
class UserMessage(models.Model):
    """
    Model for storing messages sent from company to users
    Serves as a backup for email communication
    """
    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    
    # Recipient
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='received_messages')
    
    # Message details
    subject = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unread')
    is_deleted = models.BooleanField(default=False)
    
    # Email backup tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Optional: For bulk messages
    is_bulk = models.BooleanField(default=False)
    bulk_group = models.CharField(max_length=100, blank=True, null=True)
    
    # Attachments (optional)
    has_attachment = models.BooleanField(default=False)
    attachment_url = models.URLField(blank=True, null=True)
    attachment_name = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Message'
        verbose_name_plural = 'User Messages'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Message to {self.user.username}: {self.subject[:50]}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if self.status == 'unread':
            self.status = 'read'
            self.save(update_fields=['status'])
            return True
        return False
    
    def mark_as_archived(self):
        """Archive message"""
        if self.status != 'archived':
            self.status = 'archived'
            self.save(update_fields=['status'])
            return True
        return False
    
    @property
    def priority_class(self):
        """Return CSS class for priority"""
        classes = {
            'low': 'info',
            'medium': 'primary',
            'high': 'warning',
            'urgent': 'danger',
        }
        return classes.get(self.priority, 'secondary')
    
    @property
    def priority_icon(self):
        """Return icon for priority"""
        icons = {
            'low': 'fa-flag',
            'medium': 'fa-flag-checkered',
            'high': 'fa-exclamation',
            'urgent': 'fa-exclamation-triangle',
        }
        return icons.get(self.priority, 'fa-envelope')


class MessageReply(models.Model):
    """
    Model for user replies to messages (if needed)
    """
    original_message = models.ForeignKey(UserMessage, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='message_replies')
    reply_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read_by_admin = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message Reply'
        verbose_name_plural = 'Message Replies'
    
    def __str__(self):
        return f"Reply to {self.original_message.subject[:30]} from {self.user.username}"