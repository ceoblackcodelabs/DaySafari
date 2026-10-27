from django.db import models
from Places.models import Destinations
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class Bookings(models.Model):
    """Every booking lead on the site: safari, trekking and hotel enquiries."""
    TYPE_CHOICES = [('safari', 'Safari'), ('trekking', 'Trekking'), ('hotel', 'Hotel')]
    STATUS_CHOICES = [('new', 'New'), ('contacted', 'Contacted'), ('confirmed', 'Confirmed'),
                      ('cancelled', 'Cancelled'), ('spam', 'Spam')]

    client = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    booking_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='safari', db_index=True)
    name = models.CharField(default='', max_length=100)
    email = models.EmailField(default='email@example.com')
    phone = models.CharField(default='', max_length=20)
    destination = models.ForeignKey(Destinations, on_delete=models.CASCADE, blank=True, null=True)
    trekking_package = models.ForeignKey('Home.Trekking', on_delete=models.SET_NULL, blank=True, null=True,
                                         related_name='bookings')
    hotel = models.ForeignKey('Hotels.Hotel', on_delete=models.SET_NULL, blank=True, null=True,
                              related_name='enquiries')
    persons = models.IntegerField(default=1)
    date = models.DateField(default=timezone.now)          # travel date / check-in
    check_out = models.DateField(null=True, blank=True)    # hotel stays
    has_children = models.BooleanField(null=True, blank=True)      # hotel enquiries: travelling with kids?
    children_count = models.PositiveSmallIntegerField(null=True, blank=True)
    children_ages = models.CharField(max_length=60, blank=True)
    message = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new', db_index=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def children_summary(self):
        if self.has_children is None:
            return ''
        if not self.has_children:
            return 'No children'
        ages = f' (ages {self.children_ages})' if self.children_ages else ''
        return f'Yes, {self.children_count or "?"} child{"ren" if (self.children_count or 0) != 1 else ""}{ages}'

    @property
    def item_name(self):
        """What was booked, whichever type it is."""
        item = self.destination or self.trekking_package or self.hotel
        return str(item) if item else 'General enquiry'

    def __str__(self):
        return f"{self.name} - {self.item_name}"


class Contact(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='New', choices=[('New', 'New'), ('Read', 'Read'), ('Closed', 'Closed'), ('Spam', 'Spam')])
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject[:50]}"
    


class QuickLead(models.Model):
    """A visitor who used the 'What's your next adventure?' popup and was sent on to WhatsApp."""
    STATUS = [('New', 'New'), ('Contacted', 'Contacted'), ('Booked', 'Booked'), ('Closed', 'Closed'), ('Spam', 'Spam')]
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=25)
    tour = models.CharField(max_length=160, blank=True)
    message = models.TextField(blank=True)
    page_url = models.CharField(max_length=300, blank=True)
    language = models.CharField(max_length=8, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default='New', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'WhatsApp lead'
        verbose_name_plural = 'WhatsApp leads'

    def __str__(self):
        return f"{self.name} - {self.tour or 'general'}"



class BlockedIP(models.Model):
    """An address that may no longer submit any form on the website. Managed in the admin."""
    ip = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True, help_text='Untick to let this address back in')
    auto = models.BooleanField(default=False, help_text='Added by the system, not by a person')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blocked IP'
        verbose_name_plural = 'Blocked IPs'

    def __str__(self):
        return self.ip


class BotAttempt(models.Model):
    """Automated or spam submissions land here instead of in Bookings, Contact messages or Leads.
    Tick `blacklist` on a row to block its IP address on every form."""
    FORMS = [('contact', 'Contact form'), ('booking', 'Booking form'), ('hotel', 'Hotel enquiry'), ('landing', 'Landing enquiry'),
             ('popup', 'WhatsApp popup'), ('guide', 'Guide lead'), ('register', 'Sign-up'), ('other', 'Other')]
    ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    form = models.CharField(max_length=10, choices=FORMS, default='other', db_index=True)
    reasons = models.CharField(max_length=300, blank=True)
    name = models.CharField(max_length=120, blank=True)
    email = models.CharField(max_length=254, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    message = models.TextField(blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    path = models.CharField(max_length=200, blank=True)
    hits = models.PositiveIntegerField(default=1, help_text='Repeat submissions of the same thing from this address')
    blacklist = models.BooleanField('Blacklist IP', default=False, db_index=True,
                                    help_text='Tick to block this IP address on every form')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bot trap entry'
        verbose_name_plural = 'Bot trap (blocked automations)'

    def __str__(self):
        return f'{self.get_form_display()} from {self.ip or "?"}: {self.reasons[:40]}'

    def save(self, *args, **kwargs):
        adding = self._state.adding
        super().save(*args, **kwargs)
        if not self.ip:
            return
        if self.blacklist:
            set_ip_blocked(self.ip, True, f'Blacklisted from the bot trap ({self.get_form_display()})')
        elif not adding and BlockedIP.objects.filter(ip=self.ip, is_active=True).exists():
            set_ip_blocked(self.ip, False)             # the box was unticked: let the address back in


def set_ip_blocked(ip, blocked, reason='', auto=False):
    """Create/update the block for `ip` and keep every trap row for that address in step."""
    row, _ = BlockedIP.objects.get_or_create(ip=ip, defaults={'reason': reason[:200], 'auto': auto, 'is_active': blocked})
    if row.is_active != blocked:
        row.is_active = blocked
        row.save(update_fields=['is_active'])
    BotAttempt.objects.filter(ip=ip).exclude(blacklist=blocked).update(blacklist=blocked)
    from django.core.cache import cache
    cache.delete('antispam:blocked-ips')
    if not blocked:                                    # also lift the automatic 24h ban and the strike count
        from . import antispam
        cache.delete(antispam._key('block', 'all', ip))
        cache.delete(antispam._key('strike', 'all', ip))
