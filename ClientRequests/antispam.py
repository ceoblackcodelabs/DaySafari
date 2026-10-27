"""
Anti-spam / abuse protection for the public forms (contact + booking).

Layers, cheapest first:
  1. IP block list      - blocked IPs get HTTP 429 before any work is done.
  2. Rate limiting      - per-IP sliding limits on POSTs; repeat offenders are blocked.
  3. Honeypot field     - hidden input humans never fill in; bots do.
  4. Time trap          - signed timestamp; instant submissions are bots.
  5. Content validation - strict name/phone rules, link/HTML limits, junk domains.

State lives in Django's cache (shared FileBasedCache, so it works across
Passenger worker processes). Tunable from settings.py:

    ANTISPAM_RATE_LIMITS   list of (max_posts, window_seconds)
    ANTISPAM_BLOCK_SECONDS how long a banned IP stays banned
    ANTISPAM_STRIKES       strikes within the block window before a ban
    ANTISPAM_IP_HEADER     request.META key holding the real client IP
"""
import logging
import re
import time

from django import forms
from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('antispam')

RATE_LIMITS = getattr(settings, 'ANTISPAM_RATE_LIMITS', [(3, 300), (8, 3600), (20, 86400)])
BLOCK_SECONDS = getattr(settings, 'ANTISPAM_BLOCK_SECONDS', 24 * 3600)
STRIKES_BEFORE_BLOCK = getattr(settings, 'ANTISPAM_STRIKES', 3)
IP_HEADER = getattr(settings, 'ANTISPAM_IP_HEADER', 'REMOTE_ADDR')

MIN_FILL_SECONDS = 3          # humans cannot fill a form faster than this
MAX_FORM_AGE_SECONDS = 6 * 3600
TS_SALT = 'clientrequests.antispam.ts'


# --------------------------------------------------------------------------
# IP helpers
# --------------------------------------------------------------------------
def get_client_ip(request):
    """Client IP from ANTISPAM_IP_HEADER (default REMOTE_ADDR).

    Only point ANTISPAM_IP_HEADER at X-Forwarded-For style headers
    (e.g. 'HTTP_X_FORWARDED_FOR') if your host's proxy overwrites it;
    otherwise clients can spoof it to dodge the limits.
    """
    value = request.META.get(IP_HEADER) or request.META.get('REMOTE_ADDR') or 'unknown'
    return value.split(',')[0].strip()


def _key(kind, scope, ip, extra=''):
    # ':' keeps keys readable; IPv6 colons are harmless for FileBasedCache.
    return f'antispam:{kind}:{scope}:{ip}{extra}'


def _admin_blocked():
    """Addresses blacklisted in the admin (cached for a minute; cleared when the list changes)."""
    ips = cache.get('antispam:blocked-ips')
    if ips is None:
        try:
            from .models import BlockedIP
            ips = set(BlockedIP.objects.filter(is_active=True).values_list('ip', flat=True))
        except Exception:
            ips = set()
        cache.set('antispam:blocked-ips', ips, 60)
    return ips


def is_blocked(ip):
    return bool(cache.get(_key('block', 'all', ip))) or ip in _admin_blocked()


def block_ip(ip, reason, seconds=BLOCK_SECONDS):
    cache.set(_key('block', 'all', ip), reason, seconds)
    logger.warning('Blocked %s for %ss: %s', ip, seconds, reason)


def add_strike(ip, reason, weight=1):
    """Record abuse; ban the IP once it accumulates enough strikes."""
    key = _key('strike', 'all', ip)
    strikes = cache.get(key, 0) + weight
    cache.set(key, strikes, BLOCK_SECONDS)
    logger.info('Strike %s/%s for %s: %s', strikes, STRIKES_BEFORE_BLOCK, ip, reason)
    if strikes >= STRIKES_BEFORE_BLOCK:
        block_ip(ip, reason)
        return True
    return False


def hit_rate_limit(ip, scope, limits=None):
    """Count this POST. Returns the seconds to wait if over a limit, else 0."""
    now = int(time.time())
    for max_posts, window in (limits or RATE_LIMITS):
        bucket = now // window  # fixed window; cheap and good enough here
        key = _key('rate', scope, ip, f':{window}:{bucket}')
        cache.add(key, 0, window)
        try:
            count = cache.incr(key)
        except ValueError:      # expired between add and incr
            cache.set(key, 1, window)
            count = 1
        if count > max_posts:
            return window - (now % window)
    return 0


def rate_limited(scope, limits):
    """Decorator for function views / JSON APIs: 429 + strikes when exceeded."""
    from functools import wraps
    from django.http import JsonResponse

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            ip = get_client_ip(request)
            if is_blocked(ip):
                return JsonResponse({'success': False, 'error': 'Too many requests.'}, status=429)
            wait = hit_rate_limit(ip, scope, limits)
            if wait:
                add_strike(ip, f'rate limit exceeded on {scope}')
                response = JsonResponse({'success': False, 'error': 'Too many requests. Please slow down.'},
                                        status=429)
                response['Retry-After'] = str(wait)
                return response
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


# --------------------------------------------------------------------------
# View mixin
# --------------------------------------------------------------------------
class AntiSpamViewMixin:
    """Put first in the MRO of a public form view.

    * blocked IP / over-limit POSTs   -> 429
    * honeypot or too-fast submission -> pretend success is NOT shown;
      the request is dropped with a bland 400 and the IP takes a strike.
    """
    antispam_scope = 'form'

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            ip = get_client_ip(request)
            if is_blocked(ip):
                return self._too_many(3600)
            wait = hit_rate_limit(ip, self.antispam_scope)
            if wait:
                add_strike(ip, f'rate limit exceeded on {self.antispam_scope}')
                return self._too_many(wait)
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        if getattr(form, 'spam_detected', False):
            ip = get_client_ip(self.request)
            # Honeypot hits are near-certain bots: weigh them heavily.
            add_strike(ip, f'bot signature on {self.antispam_scope}: {form.spam_reason}',
                       weight=STRIKES_BEFORE_BLOCK if form.spam_reason == 'honeypot' else 1)
            d = getattr(form, 'data', {})
            trap({'booking': 'booking', 'home-booking': 'booking', 'trekking': 'booking', 'contact': 'contact', 'register': 'register', 'hotel': 'hotel'}.get(self.antispam_scope, 'other'),
                 [form.spam_reason], d.get('name') or d.get('username', ''), d.get('email', ''), d.get('phone', ''),
                 d.get('message', '') or d.get('special_requests', ''), self.request)
            return HttpResponse('Bad request.', status=400)
        return super().form_invalid(form)

    @staticmethod
    def _too_many(retry_after):
        response = HttpResponse('Too many requests. Please try again later.', status=429,
                                content_type='text/plain')
        response['Retry-After'] = str(retry_after)
        return response


# --------------------------------------------------------------------------
# Form mixin
# --------------------------------------------------------------------------
_LINK_RE = re.compile(r'(https?://|www\.|\[url|<a\s|href\s*=)', re.I)
_HTML_RE = re.compile(r'<\s*/?\s*[a-z][^>]*>', re.I)
_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ .'\-]+[^\W\d_]+)*\.?$", re.UNICODE)
_PHONE_RE = re.compile(r'^\+?[\d\s\-().]{9,20}$')
# Reserved/placeholder domains the scanner used (email@example.com etc.)
_JUNK_EMAIL_DOMAINS = {'example.com', 'example.org', 'example.net', 'test.com', 'mailinator.com'}
# Throwaway-mail families seen in the cleaned-up spam.
_JUNK_EMAIL_PATTERNS = re.compile(r'(notboxletters|notlettersmail|belettersmail|nolettersbox|'
                                  r'firstmailmorty|microversemail|glorzomail|hypercubemail|seo|backlink|casino|escort|crypto)', re.I)


# Accessible names for fields that have no placeholder (translated per language)
FIELD_LABELS = {
    'destination': _('Destination'), 'persons': _('Persons'), 'number_of_persons': _('Number of persons'),
    'full_name': _('Full name'), 'email': _('Email'), 'phone_number': _('Phone number'),
    'travel_date': _('Travel date'), 'special_requests': _('Special requests'), 'date': _('Date'),
    'check_out': _('Check out'), 'traveling_with_children': _('Traveling with children'),
    'children_count': _('Number of children'), 'children_ages': _("Children's ages"),
    'name': _('Name'), 'phone': _('Phone'), 'message': _('Message'), 'subject': _('Subject'),
}


class AntiSpamFormMixin(forms.Form):
    """Adds honeypot + time-trap fields and shared content validators.

    Render `{{ form.website }}{{ form.form_ts }}` inside the <form>.
    Max number of links tolerated in free text is `max_links` (default 1).
    """
    max_links = 1
    max_message_length = 3000

    # Looks like a real field to bots; hidden off-screen for humans.
    website = forms.CharField(
        required=False, label='',
        widget=forms.TextInput(attrs={
            'tabindex': '-1', 'autocomplete': 'off', 'aria-hidden': 'true',
            'style': 'position:absolute;left:-5000px;height:0;width:0;opacity:0;',
        }),
    )
    form_ts = forms.CharField(required=False, widget=forms.HiddenInput())

    spam_detected = False
    spam_reason = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fresh signed timestamp every time the form is rendered.
        self.fields['form_ts'].initial = signing.dumps(int(time.time()), salt=TS_SALT)
        # Placeholder-only inputs still need an accessible name
        for name, field in self.fields.items():
            if name not in ('website', 'form_ts'):
                field.widget.attrs.setdefault(
                    'aria-label', field.widget.attrs.get('placeholder') or FIELD_LABELS.get(name)
                    or name.replace('_', ' ').capitalize())

    # -- bot traps (run first so spam never reaches field-level errors) -----
    def _flag(self, reason):
        self.spam_detected = True
        self.spam_reason = reason
        raise forms.ValidationError(_('Invalid submission.'), code='spam')

    def clean_website(self):
        if self.cleaned_data.get('website'):
            self._flag('honeypot')
        return ''

    def clean_form_ts(self):
        token = self.cleaned_data.get('form_ts') or ''
        try:
            issued = signing.loads(token, salt=TS_SALT)
        except signing.BadSignature:
            self._flag('bad-timestamp')          # missing or forged
        age = time.time() - issued
        if age < MIN_FILL_SECONDS:
            self._flag('too-fast')
        if age > MAX_FORM_AGE_SECONDS:
            # Genuine signature, just an old tab: a human, so no strike.
            raise forms.ValidationError(_('This form has expired. Please reload the page and try again.'))
        return token

    def clean(self):
        """Judge the content before anything is saved: spam never reaches Bookings, Contact messages or the CRM webhook."""
        data = super().clean()
        if not self.spam_detected and self.is_bound and not self.errors:      # a human fixing a field error comes first
            from .spamfilter import spam_reasons
            g = lambda *keys: next((str(self.data.get(k)) for k in keys if self.data.get(k)), '')
            reasons = spam_reasons(name=g('name', 'full_name'), email=g('email'), subject=g('subject'),
                                   message=g('message', 'special_requests', 'notes'))
            if reasons:
                self._flag('content: ' + ', '.join(reasons))
        return data

    # -- shared validators -------------------------------------------------
    def clean_name(self):
        name = ' '.join((self.cleaned_data.get('name') or '').split())
        if len(name) < 2:
            raise forms.ValidationError(_('Name must be at least 2 characters long.'))
        if len(name) > 60 or not _NAME_RE.match(name):
            raise forms.ValidationError(_('Please enter a valid name (letters, spaces, hyphens and apostrophes only).'))
        return name

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        domain = email.rsplit('@', 1)[-1]
        if domain in _JUNK_EMAIL_DOMAINS or _JUNK_EMAIL_PATTERNS.search(domain):
            raise forms.ValidationError(_('Please use a real email address.'))
        return email

    def _clean_free_text(self, field, max_length=None):
        text = (self.cleaned_data.get(field) or '').strip()
        if max_length is None:
            max_length = self.max_message_length
        if len(text) > max_length:
            raise forms.ValidationError(_('Please keep this under %(n)d characters.'), params={'n': max_length})
        if _HTML_RE.search(text):
            raise forms.ValidationError(_('HTML is not allowed.'))
        if len(_LINK_RE.findall(text)) > self.max_links:
            raise forms.ValidationError(_('Please remove the links from your message.'))
        return text

    def clean_message(self):
        return self._clean_free_text('message')

    def clean_subject(self):
        return self._clean_free_text('subject', max_length=150)

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if not _PHONE_RE.match(phone) or sum(c.isdigit() for c in phone) < 9:
            raise forms.ValidationError(_('Please enter a valid phone number.'))
        return phone


# --------------------------------------------------------------------------
# WhatsApp lead popup (no email field, so it needs its own checks)
# --------------------------------------------------------------------------
def lead_token():
    """Signed 'page was loaded at' stamp for the popup form."""
    return signing.dumps(int(time.time()), salt=TS_SALT)


_LEAD_URL = re.compile(r'(https?://|www\.|\b[\w-]+\.(?:com|net|org|ru|su|xyz|top|click|work|site|online|me|ly|gl|to|cc)\b|tinyurl|bit\.ly|t\.me|#\w{4,})', re.I)


def lead_spam_reasons(name, tour, message, token):
    """Why a popup lead looks like a bot (empty list = looks human). Genuine leads never need a link."""
    from .spamfilter import spam_reasons
    reasons = []
    try:
        age = time.time() - signing.loads(token or '', salt=TS_SALT)
        if age < MIN_FILL_SECONDS:
            reasons.append('too fast')
        elif age > 3 * 24 * 3600:
            pass                         # an old tab or a cached page: a human, leave it alone
    except signing.BadSignature:
        reasons.append('missing or forged page stamp')
    if _LEAD_URL.search(f'{name} {tour} {message}'):
        reasons.append('contains a link')
    reasons += spam_reasons(name=name, subject=tour, message=message)
    return reasons


# --------------------------------------------------------------------------
# Bot trap: automations are recorded here (admin: Client Requests > Bot trap) instead of in the real lists
# --------------------------------------------------------------------------
import contextvars
_current_request = contextvars.ContextVar('dsa_request', default=None)


class CurrentRequestMiddleware:
    """Remembers the request so spam handlers deep in the code can record who sent it."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _current_request.set(request)
        try:
            return self.get_response(request)
        finally:
            _current_request.reset(token)


def trap(form, reasons, name='', email='', phone='', message='', request=None):
    """Record a bot/spam submission. Never raises. Repeats of the same text from one address only bump a counter."""
    try:
        from .models import BotAttempt
        request = request or _current_request.get()
        ip = get_client_ip(request) if request else ''
        ip = ip if ip and ip != 'unknown' else None
        reason = ', '.join(reasons) if isinstance(reasons, (list, tuple)) else str(reasons)
        message = (message or '')[:1500]
        same = BotAttempt.objects.filter(ip=ip, form=form, message=message, name=(name or '')[:120]).order_by('-id').first() if ip else None
        if same:
            BotAttempt.objects.filter(pk=same.pk).update(hits=same.hits + 1)
            return same
        day_key = f'antispam:trapcount:{ip}:{int(time.time()) // 86400}'
        cache.add(day_key, 0, 90000)
        try:
            if cache.incr(day_key) > 30:      # a flood from one address: keep counting, stop filling the table
                return None
        except ValueError:
            pass
        return BotAttempt.objects.create(
            ip=ip, form=form, reasons=reason[:300], name=(name or '')[:120], email=(email or '')[:254], phone=(phone or '')[:40],
            message=message, blacklist=bool(ip and ip in _admin_blocked()), user_agent=(request.META.get('HTTP_USER_AGENT', '')[:300] if request else ''),
            path=(request.path[:200] if request else ''))
    except Exception:
        logger.exception('Could not record bot attempt')
        return None
