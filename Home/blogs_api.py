"""JSON API for publishing blog posts (create / read / update) with a featured image and inline images.

Same authentication as the hotels API: `Authorization: Bearer dsa_<prefix>_<secret>`.
Every write supports `?dry_run=1`, which validates exactly like a real call but saves nothing.
There is deliberately no delete endpoint: removal stays in the admin. Full guide: docs/BLOGS_API.md
"""
import json
import logging
import re
from html import escape
from html.parser import HTMLParser

from django.db import transaction
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify

from Hotels.api import (api_view, check_photo, error, read_payload, reply, truthy, MIN_PHOTO_WIDTH,
                        MAX_PHOTO_BYTES)

from .models import BlogCategory, Blogs

logger = logging.getLogger('hotels.api')

LANGS = ['fr', 'sw', 'es', 'de', 'it']
TEXT_KEYS = ['title', 'content', 'seo_title', 'seo_description']
MAX_INLINE_IMAGES = 8
MIN_WORDS = 300

# ----------------------------------------------------------------------------- HTML sanitiser (no extra packages)
ALLOWED = {
    'p': [], 'h2': [], 'h3': [], 'h4': [], 'ul': [], 'ol': [], 'li': [], 'strong': [], 'b': [], 'em': [], 'i': [],
    'u': [], 'br': [], 'hr': [], 'blockquote': [], 'figure': [], 'figcaption': [], 'a': ['href', 'title'],
    'img': ['src', 'alt', 'width', 'height', 'loading'], 'table': [], 'thead': [], 'tbody': [], 'tr': [], 'th': [],
    'td': [],
}
VOID = {'br', 'hr', 'img'}
DROP_WITH_CONTENT = {'script', 'style', 'iframe', 'object', 'embed', 'form', 'noscript'}
RENAME = {'h1': 'h2', 'h5': 'h4', 'h6': 'h4', 'div': 'p', 'span': None, 'b': 'strong', 'i': 'em'}


def _safe_url(value, image=False):
    value = (value or '').strip()
    if value.startswith('/') and not value.startswith('//'):
        return value
    if re.match(r'^https://', value, re.I):
        return value
    if not image and re.match(r'^(mailto:|tel:)', value, re.I):
        return value
    return None


class _Sanitiser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.stack = [], 0, []

    def handle_starttag(self, tag, attrs):
        if tag in DROP_WITH_CONTENT:
            self.skip += 1
            return
        if self.skip:
            return
        name = RENAME[tag] if tag in RENAME else tag
        if name is None:
            return
        if name not in ALLOWED:
            return
        keep = []
        for key, value in attrs:
            if key not in ALLOWED[name]:
                continue
            if key in ('href', 'src'):
                value = _safe_url(value, image=(key == 'src'))
                if value is None:
                    continue
            keep.append(f' {key}="{escape(value or "", quote=True)}"')
        if name == 'a' and any(a.startswith(' href=') and 'https://' in a for a in keep):
            keep.append(' rel="noopener"')
        if name == 'img' and not any(a.startswith(' src=') for a in keep):
            return
        self.out.append(f'<{name}{"".join(keep)}>')
        if name not in VOID:
            self.stack.append(name)

    def handle_endtag(self, tag):
        if tag in DROP_WITH_CONTENT:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        name = RENAME[tag] if tag in RENAME else tag
        if name and name in ALLOWED and name not in VOID and name in self.stack:
            while self.stack:
                top = self.stack.pop()
                self.out.append(f'</{top}>')
                if top == name:
                    break

    def handle_data(self, data):
        if not self.skip:
            self.out.append(escape(data, quote=False))

    def result(self):
        while self.stack:
            self.out.append(f'</{self.stack.pop()}>')
        return ''.join(self.out)


def sanitise(html):
    parser = _Sanitiser()
    parser.feed(html or '')
    parser.close()
    return parser.result().strip()


# ----------------------------------------------------------------------------- validation
def find_category(value):
    if value in (None, ''):
        return None
    value = str(value).strip()
    return (BlogCategory.objects.filter(slug__iexact=value).first()
            or BlogCategory.objects.filter(name_en__iexact=value).first()
            or BlogCategory.objects.filter(name__iexact=value).first())


def clean_text(data, errors, instance=None):
    """Validate the English fields. Returns a dict of the values that were sent (and valid)."""
    out = {}
    if 'title' in data or instance is None:
        title = ' '.join(str(data.get('title') or '').split())
        if not title:
            errors['title'] = ['Required.']
        elif len(title) > 100:
            errors['title'] = [f'Max 100 characters ({len(title)} sent).']
        else:
            out['title'] = title
    if 'content' in data or instance is None:
        content = sanitise(str(data.get('content') or ''))
        words = len(strip_tags(content).split())
        if words < MIN_WORDS:
            errors['content'] = [f'Too short ({words} words): write at least {MIN_WORDS} words of real content.']
        else:
            out['content'] = content
    for key, limit in (('seo_title', 70), ('seo_description', 170)):
        if key in data:
            value = ' '.join(str(data.get(key) or '').split())
            if len(value) > limit:
                errors[key] = [f'Max {limit} characters ({len(value)} sent). Aim for 60 / 155 for search results.']
            else:
                out[key] = value
    if 'author' in data:
        out['author'] = ' '.join(str(data.get('author') or '').split())[:100] or 'Day Safaris Adventures'
    if 'schema_markup' in data:
        raw = data['schema_markup']
        raw = json.dumps(raw) if isinstance(raw, (dict, list)) else str(raw or '')
        if raw.strip():
            try:
                json.loads(raw)
            except ValueError:
                errors['schema_markup'] = ['Must be valid JSON-LD.']
        out['schema_markup'] = raw
    if 'category' in data:
        cat = find_category(data['category'])
        if data['category'] not in (None, '') and cat is None:
            errors['category'] = [f'Unknown category. Use one of: {", ".join(BlogCategory.objects.values_list("slug", flat=True))}.']
        out['category'] = cat
    return out


def clean_translations(data, errors):
    result = {}
    trans = data.get('translations') or {}
    if not isinstance(trans, dict):
        errors['translations'] = ['Must be an object like {"fr": {"title": "...", "content": "..."}}.']
        return result
    for lang, fields in trans.items():
        if lang not in LANGS:
            errors.setdefault('translations', []).append(f'Unknown language "{lang}". Use: {", ".join(LANGS)}.')
            continue
        if not isinstance(fields, dict):
            errors.setdefault('translations', []).append(f'{lang} must be an object.')
            continue
        values = {}
        for key in TEXT_KEYS:
            if key in fields:
                value = str(fields[key] or '')
                value = sanitise(value) if key == 'content' else ' '.join(value.split())
                if key == 'title' and len(value) > 100:
                    errors.setdefault('translations', []).append(f'{lang}.title is over 100 characters.')
                values[key] = value
        result[lang] = values
    return result


def apply_translations(blog, translations):
    for lang, values in translations.items():
        for key, value in values.items():
            setattr(blog, f'{key}_{lang}', value)


def inline_images(request):
    """Validate the optional inline images. Returns (list of (upload, ext, alt, caption), error_list)."""
    files = request.FILES.getlist('images')
    if len(files) > MAX_INLINE_IMAGES:
        return [], [f'At most {MAX_INLINE_IMAGES} inline images.']
    try:
        alts = json.loads(request.POST.get('alts') or '[]')
        captions = json.loads(request.POST.get('captions') or '[]')
    except ValueError:
        return [], ['"alts" and "captions" must be JSON lists of strings.']
    items, problems = [], []
    for i, upload in enumerate(files):
        ext, why = check_photo(upload)
        if why:
            problems.append(why)
        else:
            items.append((upload, ext, str(alts[i]) if i < len(alts) else '', str(captions[i]) if i < len(captions) else ''))
    return items, problems


def place_images(content, saved):
    """Replace [[image:N]] markers (1-based) with <figure> blocks; leftovers are removed."""
    content = re.sub(r'<p>\s*(\[\[image:\d+\]\])\s*</p>', r'\1', content)   # a figure must not sit inside <p>

    def repl(m):
        n = int(m.group(1)) - 1
        if 0 <= n < len(saved):
            url, alt, caption = saved[n]
            cap = f'<figcaption>{escape(caption)}</figcaption>' if caption else ''
            return f'<figure><img src="{escape(url, quote=True)}" alt="{escape(alt or caption, quote=True)}" loading="lazy">{cap}</figure>'
        return ''
    return re.sub(r'\[\[image:(\d+)\]\]', repl, content)


def make_slug(data_slug, title, exclude_pk=None):
    base = slugify(data_slug or title)[:70].strip('-') or 'post'
    slug, n = base, 2
    while Blogs.objects.filter(slug=slug).exclude(pk=exclude_pk).exists():
        slug, n = f'{base}-{n}', n + 1
    return slug


def serialise(blog, request, detail=False):
    data = {
        'id': blog.pk, 'slug': blog.slug, 'title': blog.title, 'author': blog.author,
        'category': blog.category.slug if blog.category_id else None,
        'published': blog.published_date.isoformat() if blog.published_date else None,
        'image_url': request.build_absolute_uri(blog.image.url) if blog.image else None,
        'url': request.build_absolute_uri(f'/en/blog/{blog.slug}/'),
        'words': len(strip_tags(blog.content or '').split()),
    }
    if detail:
        data.update({'seo_title': blog.seo_title or '', 'seo_description': blog.seo_description or '',
                     'content': blog.content})
        data['translated'] = [l for l in LANGS if getattr(blog, f'title_{l}', None) and getattr(blog, f'content_{l}', None)]
    return data


# ----------------------------------------------------------------------------- endpoints
@api_view('GET', public=True)
def blogs_schema(request, key):
    return reply({
        'ok': True, 'version': 1, 'auth': 'Authorization: Bearer <api key>',
        'required_fields': ['title', 'content', 'image (featured picture file)'],
        'fields': {
            'title': 'max 100 characters', 'content': f'HTML, at least {MIN_WORDS} words. Use h2/h3, p, ul/ol, strong, em, a, '
                                                     'blockquote, table. [[image:1]] places the first inline image',
            'author': 'default "Day Safaris Adventures"', 'category': 'slug or name: ' +
                      ', '.join(BlogCategory.objects.values_list('slug', flat=True)),
            'seo_title': 'about 60 characters (max 70)', 'seo_description': 'about 155 characters (max 170)',
            'slug': 'optional; generated from the title', 'schema_markup': 'optional JSON-LD',
            'translations': {l: '{"title","content","seo_title","seo_description"}' for l in LANGS},
        },
        'images': {'how': 'multipart/form-data: "data" (JSON), "image" (featured), optional "images" (inline files), '
                          '"alts" and "captions" (JSON lists matching the inline files)',
                   'rules': f'JPEG/PNG/WebP, >= {MIN_PHOTO_WIDTH}px wide, <= {MAX_PHOTO_BYTES // 1048576} MB each, '
                            f'max {MAX_INLINE_IMAGES} inline'},
        'options': {'dry_run': '?dry_run=1 validates and returns what would happen, saving nothing'},
    })


@api_view('GET', 'POST')
def blogs_collection(request, key):
    if request.method == 'GET':
        qs = Blogs.objects.select_related('category')
        if request.GET.get('q'):
            qs = qs.filter(title__icontains=request.GET['q'])
        try:
            limit = min(max(int(request.GET.get('limit', 50)), 1), 200)
        except ValueError:
            limit = 50
        return reply({'ok': True, 'count': qs.count(), 'posts': [serialise(b, request) for b in qs[:limit]]})

    if not (request.content_type or '').startswith('multipart/'):
        return error('Send multipart/form-data: JSON in "data", the featured picture in "image".', 400)
    try:
        data, _ = read_payload(request)
    except ValueError as exc:
        return error(str(exc), 400)
    errors = {}
    values = clean_text(data, errors)
    translations = clean_translations(data, errors)
    featured = request.FILES.get('image')
    f_ext = None
    if featured:
        f_ext, why = check_photo(featured)
        if why:
            errors['image'] = [why]
    else:
        errors['image'] = ['The featured picture is required (multipart field "image").']
    inline, problems = inline_images(request)
    if problems:
        errors['images'] = problems
    used = {int(n) for n in re.findall(r'\[\[image:(\d+)\]\]', data.get('content') or '')}
    if used and max(used) > len(inline) and 'images' not in errors:
        errors['images'] = [f'The content uses [[image:{max(used)}]] but only {len(inline)} inline image(s) were sent.']
    if errors:
        return error('Validation failed.', 400, errors=errors)

    slug = make_slug(data.get('slug'), values['title'])
    duplicate = Blogs.objects.filter(title__iexact=values['title']).first()
    if duplicate:
        return reply({'ok': False, 'error': 'A post with this title already exists.',
                      'existing': serialise(duplicate, request)}, 409)
    warnings = []
    if not values.get('seo_title'):
        warnings.append('No seo_title: the page title will use the post title.')
    if not values.get('seo_description'):
        warnings.append('No seo_description: Google will pick a snippet from the text. Add one of about 155 characters.')
    if not values.get('category'):
        warnings.append('No category: the post will not appear under a category filter.')
    if dry_run := truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_create', 'slug': slug, 'title': values['title'],
                      'words': len(strip_tags(values['content']).split()), 'inline_images': len(inline),
                      'translations': sorted(translations), 'warnings': warnings})
    with transaction.atomic():
        blog = Blogs(slug=slug, author=values.get('author') or 'Day Safaris Adventures', **{
            k: v for k, v in values.items() if k != 'author'})
        stamp = timezone.now().strftime('%Y%m%d%H%M%S')
        featured.name = f'{slug}.{f_ext}'
        blog.image = featured
        saved = []
        from django.core.files.storage import default_storage
        for n, (upload, ext, alt, caption) in enumerate(inline, 1):
            upload.name = f'blog_images/inline/{slug}-{n}-{stamp}.{ext}'
            path = default_storage.save(upload.name, upload)
            saved.append((default_storage.url(path), alt, caption))
        blog.content = place_images(blog.content, saved)
        apply_translations(blog, {l: {**v, **({'content': place_images(v['content'], saved)} if 'content' in v else {})}
                                  for l, v in translations.items()})
        blog.save()
    logger.info('API created blog %s (%s) via key %s', blog.slug, blog.pk, key.name)
    return reply({'ok': True, 'status': 'created', 'post': serialise(blog, request, detail=False), 'warnings': warnings}, 201)


@api_view('GET', 'PATCH')
def blog_detail(request, key, slug):
    blog = Blogs.objects.select_related('category').filter(slug=slug).first()
    if not blog:
        return error('Post not found.', 404)
    if request.method == 'GET':
        return reply({'ok': True, 'post': serialise(blog, request, detail=True)})
    try:
        data, _ = read_payload(request)
    except ValueError as exc:
        return error(str(exc), 400)
    errors = {}
    values = clean_text(data, errors, instance=blog)
    translations = clean_translations(data, errors)
    if errors:
        return error('Validation failed.', 400, errors=errors)
    changed = sorted(list(values) + [f'translations.{l}' for l in translations])
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_update', 'changes': changed})
    for k, v in values.items():
        setattr(blog, k, v)
    apply_translations(blog, translations)
    blog.save()
    logger.info('API updated blog %s fields %s via key %s', blog.slug, changed, key.name)
    return reply({'ok': True, 'status': 'updated', 'changed': changed, 'post': serialise(blog, request, detail=True)})


@api_view('POST')
def blog_image(request, key, slug):
    blog = Blogs.objects.filter(slug=slug).first()
    if not blog:
        return error('Post not found.', 404)
    upload = request.FILES.get('image')
    if not upload:
        return error('Send the picture in the multipart field "image".', 400)
    ext, why = check_photo(upload)
    if why:
        return error('Validation failed.', 400, errors={'image': [why]})
    if truthy(request, 'dry_run'):
        return reply({'ok': True, 'dry_run': True, 'status': 'would_replace_image'})
    upload.name = f'{blog.slug}-{timezone.now():%Y%m%d%H%M%S}.{ext}'
    blog.image = upload
    blog.save()
    return reply({'ok': True, 'status': 'image_replaced', 'post': serialise(blog, request)})
