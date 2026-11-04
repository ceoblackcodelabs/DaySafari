"""Server-side spam classifier for public submissions.

Rate limiting stops one IP from flooding; it cannot stop a botnet that sends
one message per IP. This module looks at the *content* and at campaigns
(the same text arriving many times), which is what rotating-IP bots cannot hide.

    reasons = spam_reasons(name=..., email=..., subject=..., message=...)
    if reasons: quarantine it (save, but never email anyone).

A submission is spam when its score reaches SPAM_THRESHOLD. Strong signals
score 2 (enough alone); weak signals score 1 and need a second one.
"""
import hashlib
import re

from django.core.cache import cache

SPAM_THRESHOLD = 2
CAMPAIGN_TTL = 24 * 3600
CAMPAIGN_REPEATS = 2        # the same text seen this many times before => campaign
SITEWIDE_PER_HOUR = 40      # contact+booking posts per hour before everything is suspect

_STRONG_TEXT = re.compile(
    r"(escort|intimate photos|nude|\bsex(y|ual)?\b|porn|onlyfans|hot (girls|women)|dating site|"
    r"casino|jackpot|slots?\b|betting|poker|viagra|cialis|crypto|bitcoin|\busdt\b|"
    r"your_?balance|tokens? (credited|received)|balance updated|wallet|airdrop|\bnft\b|"
    r"telegra\.ph|t\.me/|bit\.ly|tinyurl|xrumer|backlinks?|guest post|"
    r"seo (service|expert|agency|audit|package)|rank (your|higher)|first page of google|"
    r"web ?site (redesign|design feedback)|explainer video|lead generation|"
    r"loan offer|make \$?\d+ ?(k|usd|dollars)|work from home|investment opportunity|"
    r"restore any site|wayback machine|pippit|ai-v?ideo)", re.I)
# Generated "product review" filler that form-spam bots paste into the message box (nothing to do with travel)
_NONSENSE = re.compile(
    r"(\bthis product\b|improves my [a-z]+ by a lot|loves to play with it|has one of these|heard about this on|"
    r"decided to give it a try|i tried to \w+ it but got \w+ all over it|it only works when i'?m|"
    r"the box this comes in is|i saw one of these in .+ and i bought one|i use it .* when i'?m (in|at) my|"
    r"one of my hobbies is .* this works great|^\s*talk about \w+\.?\s*$|"
    r"works? (great|well) (for|on) my [a-z]+\b.*\bby a lot)", re.I | re.M)
_URL = re.compile(r'(https?://|www\.|\b[\w-]+\.(?:ru|su|xyz|top|click|work|site|online)\b)', re.I)
_CYRILLIC = re.compile(r'[Ѐ-ӿ]')
_LETTER = re.compile(r'[^\W\d_]', re.UNICODE)
_GENERIC_SUBJECTS = {'nice', 'good', 'attention', 'i promised.', 'hello', 'hi', 'test', 'info', 'question'}


def normalise(text):
    return re.sub(r'[^a-z0-9а-я]+', ' ', (text or '').lower()).strip()


def _text_hash(subject, message):
    return hashlib.md5(normalise(f'{subject} {message}')[:400].encode()).hexdigest()


def _gibberish_name(name):
    """Single-token handles like 'mussymync', 'BillyRaw', 'xsjyBldb' (not 'Patricia')."""
    name = (name or '').strip()
    if ' ' in name or not name.isalpha() or len(name) < 7:
        return False
    return bool(re.search(r'[a-z][A-Z]', name)) or name.islower()


def spam_reasons(name='', email='', subject='', message='', count_campaign=True):
    """Return a list of human-readable reasons; empty list means it looks real."""
    score, reasons = 0, []
    text = f'{subject}\n{message}'

    if _STRONG_TEXT.search(text):
        score += 2; reasons.append('spam keywords')
    if _NONSENSE.search(text):
        score += 2; reasons.append('generated filler text')
    letters = _LETTER.findall(text)
    if letters and len(_CYRILLIC.findall(text)) / len(letters) > 0.3:
        score += 2; reasons.append('mostly Cyrillic text')
    if len(_URL.findall(text)) >= 2:
        score += 2; reasons.append('multiple links')
    elif _URL.search(text):
        score += 1; reasons.append('contains a link')
    if (subject or '').strip().lower() in _GENERIC_SUBJECTS:
        score += 1; reasons.append('generic subject')
    if _gibberish_name(name):
        score += 1; reasons.append('handle-style name')
    local = (email or '').split('@')[0]
    if local.count('.') >= 4 or re.search(r'\d{5,}', local):
        score += 1; reasons.append('machine-like email')

    if count_campaign:
        key = f'spam:campaign:{_text_hash(subject, message)}'
        cache.add(key, 0, CAMPAIGN_TTL)
        try:
            seen = cache.incr(key) - 1
        except ValueError:
            cache.set(key, 1, CAMPAIGN_TTL); seen = 0
        if seen >= CAMPAIGN_REPEATS:
            score += 2; reasons.append(f'same text sent {seen + 1} times')

        import time
        hour = f'spam:sitewide:{int(time.time()) // 3600}'
        cache.add(hour, 0, 7200)
        try:
            total = cache.incr(hour)
        except ValueError:
            cache.set(hour, 1, 7200); total = 1
        if total > SITEWIDE_PER_HOUR:
            score += 2; reasons.append('site-wide flood')

    return reasons if score >= SPAM_THRESHOLD else []


# ---- outbound email safety ---------------------------------------------------
CUSTOMER_EMAILS_PER_RECIPIENT_PER_DAY = 1
CUSTOMER_EMAILS_PER_HOUR = 20


def can_email_customer(address):
    """Never let the site be used to mail arbitrary people.

    At most one automatic email per recipient per day and a site-wide hourly cap.
    Staff notifications are not subject to this.
    """
    import time
    address = (address or '').strip().lower()
    if not address:
        return False
    per_recipient = f'mail:rcpt:{hashlib.md5(address.encode()).hexdigest()}'
    if not cache.add(per_recipient, 1, 24 * 3600):
        return False
    hour = f'mail:hour:{int(time.time()) // 3600}'
    cache.add(hour, 0, 7200)
    try:
        sent = cache.incr(hour)
    except ValueError:
        cache.set(hour, 1, 7200); sent = 1
    if sent > CUSTOMER_EMAILS_PER_HOUR:
        cache.delete(per_recipient)
        return False
    return True


# ---- booking history checks (need the database) --------------------------------
BURST_PER_HOUR = 4          # bookings for the same destination within an hour before more are suspect


def booking_history_reasons(email='', name='', destination=None):
    """Patterns only visible across bookings: bursts for one destination, one email under unrelated names."""
    from datetime import timedelta
    from django.utils import timezone
    from .models import Bookings
    now, reasons = timezone.now(), []
    if destination is not None and Bookings.objects.filter(
            destination=destination, created_at__gte=now - timedelta(hours=1)).count() >= BURST_PER_HOUR - 1:
        reasons.append('burst of bookings for one destination')
    email = (email or '').strip().lower()
    if email:
        tokens = set(normalise(name).split())
        for other in Bookings.objects.filter(email__iexact=email, created_at__gte=now - timedelta(days=2)).values_list('name', flat=True)[:5]:
            if tokens and not tokens & set(normalise(other).split()):
                reasons.append('same email under a different name')
                break
    return reasons
