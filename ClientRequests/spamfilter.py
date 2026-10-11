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
