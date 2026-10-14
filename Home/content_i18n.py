"""Translate database content (packages, hotels, blog posts...) with a phrase dictionary.

Every text field registered with django-modeltranslation is cut into segments (one per line of plain text,
or one per text node of HTML). A segment found in Home/content_translations/<lang>.json is replaced by its
translation. A field is only translated when *all* of its segments are known, so a page never mixes two
languages in one paragraph; otherwise it keeps falling back to English.
"""
import html
import json
import re
from pathlib import Path

from modeltranslation.translator import translator

DIR = Path(__file__).resolve().parent / 'content_translations'
LANGS = ('fr', 'sw', 'es', 'de', 'it')
TAG_RE = re.compile(r'(<[^>]+>)')
HAS_HTML = re.compile(r'<[a-zA-Z/][^>]*>')
LETTERS = re.compile(r'[^\W\d_]{3,}', re.UNICODE)


def norm(text):
    return ' '.join(html.unescape(text).split())


def _parts(value):
    """Split a field value into [(is_text, raw)] pieces; text pieces are the translatable segments."""
    if HAS_HTML.search(value):
        return [(not p.startswith('<'), p) for p in TAG_RE.split(value) if p != '']
    return [(True, p) for p in re.split(r'(\n)', value) if p != '']


def segments(value):
    """The translatable segments of a value (only those that contain real words)."""
    return [norm(p) for is_text, p in _parts(value or '') if is_text and LETTERS.search(p) and norm(p)]


def translate_value(value, mapping):
    """Return the translated value, or None when any segment is missing from the mapping."""
    if not value or not segments(value):
        return None
    out = []
    for is_text, piece in _parts(value):
        if is_text and LETTERS.search(piece) and norm(piece):
            translated = mapping.get(norm(piece))
            if not translated:
                return None
            lead = piece[:len(piece) - len(piece.lstrip())]
            trail = piece[len(piece.rstrip()):]
            if HAS_HTML.search(value):
                translated = html.escape(translated, quote=False)
            out.append(lead + translated + trail)
        else:
            out.append(piece)
    return ''.join(out)


def load(lang):
    path = DIR / f'{lang}.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def translated_fields():
    """[(model, [field names])] for every model registered with modeltranslation."""
    for model in translator.get_registered_models():
        yield model, list(translator.get_options_for_model(model).fields)
