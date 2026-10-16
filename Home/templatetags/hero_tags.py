import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()
EMOJI = re.compile('[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]')


@register.filter
def hero_title(value):
    """Colour-code a hero headline.

    Words between *asterisks* get the warm gradient: "Kenya's Best *Safari, Beach & Holiday* Packages".
    Without asterisks the closing words are highlighted automatically (the last sentence, or the last two words).
    """
    text = EMOJI.sub('', str(value or '')).strip()     # headlines carry no emoji (e.g. the lion)
    text = re.sub(r'\s{2,}', ' ', text)
    if not text:
        return ''
    if '*' in text:
        parts = text.split('*')
        out = ''.join(f'<span class="hl">{escape(p)}</span>' if i % 2 else escape(p) for i, p in enumerate(parts) if p)
        return mark_safe(out)
    # keep a trailing emoji / symbols outside the highlight
    m = re.match(r'^(.*?)([^\w.!?\'"\)]*)$', text, re.S)
    body, tail = (m.group(1).rstrip(), m.group(2)) if m else (text, '')
    sentences = re.split(r'(?<=[.!?])\s+', body)
    if len(sentences) > 1:
        lead, mark = ' '.join(sentences[:-1]), sentences[-1]
    else:
        words = body.split()
        if len(words) < 3:
            lead, mark = '', body
        else:
            lead, mark = ' '.join(words[:-2]), ' '.join(words[-2:])
    html = (escape(lead) + ' ' if lead else '') + f'<span class="hl">{escape(mark)}</span>'
    if tail.strip():
        html += ' ' + escape(tail.strip())
    return mark_safe(html)
