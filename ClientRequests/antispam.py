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


def is_blocked(ip):
    return bool(cache.get(_key('block', 'all', ip)))


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
                                  r'firstmailmorty|microversemail|glorzomail|hypercubemail)', re.I)


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
                    'aria-label', field.widget.attrs.get('placeholder') or name.replace('_', ' ').capitalize())

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
