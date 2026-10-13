#!/usr/bin/env python3
"""Command-line client for the Day Safaris hotels API (standard library only).

    export HOTELS_API_URL=https://daysafarisadventures.co.ke
    export HOTELS_API_KEY=dsa_xxxxxxxx_xxxxxxxx

    python tools/hotels_api.py add hotels.json --dry-run          # validate against the live site, save nothing
    python tools/hotels_api.py add hotels.json --photos-dir ./pics # create hotels (and upload their photos)
    python tools/hotels_api.py list [--country Kenya]
    python tools/hotels_api.py get <slug>
    python tools/hotels_api.py update <slug> changes.json
    python tools/hotels_api.py photos <slug> a.jpg b.jpg

hotels.json is a list of hotel objects. A hotel may contain  "photos": ["file1.jpg", "file2.jpg"]  (paths relative to
--photos-dir); those files are uploaded together with the hotel. See docs/HOTELS_API.md for every field.
"""
import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


def request(method, path, args, body=None, content_type=None):
    url = args.url.rstrip('/') + path
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Authorization', f'Bearer {args.key}')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'hotels-api-client/1')
    if content_type:
        req.add_header('Content-Type', content_type)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.status, json.loads(response.read().decode() or '{}')
    except urllib.error.HTTPError as exc:
        text = exc.read().decode(errors='replace')
        try:
            return exc.code, json.loads(text)
        except ValueError:
            return exc.code, {'ok': False, 'error': text[:300]}


def multipart(fields, files):
    boundary = uuid.uuid4().hex
    lines = []
    for name, value in fields.items():
        lines += [f'--{boundary}'.encode(), f'Content-Disposition: form-data; name="{name}"'.encode(), b'',
                  value.encode()]
    for path in files:
        mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        with open(path, 'rb') as handle:
            lines += [f'--{boundary}'.encode(),
                      f'Content-Disposition: form-data; name="photos"; filename="{os.path.basename(path)}"'.encode(),
                      f'Content-Type: {mime}'.encode(), b'', handle.read()]
    lines += [f'--{boundary}--'.encode(), b'']
    return b'\r\n'.join(lines), f'multipart/form-data; boundary={boundary}'


def load_json(path):
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def show(status, body):
    print(f'HTTP {status}')
    print(json.dumps(body, indent=2, ensure_ascii=False))


def cmd_add(args):
    data = load_json(args.file)
    hotels = data['hotels'] if isinstance(data, dict) and 'hotels' in data else data
    if not isinstance(hotels, list):
        sys.exit('The file must contain a list of hotels (or {"hotels": [...]}).')
    query = '?dry_run=1' if args.dry_run else ''
    failures = 0
    for hotel in hotels:
        hotel = dict(hotel)
        photos = [os.path.join(args.photos_dir or '.', p) for p in hotel.pop('photos', [])]
        missing = [p for p in photos if not os.path.isfile(p)]
        if missing:
            print(f"SKIPPED {hotel.get('name')}: photo file(s) not found: {missing}")
            failures += 1
            continue
        if photos:
            body, ctype = multipart({'data': json.dumps(hotel)}, photos)
        else:
            body, ctype = json.dumps(hotel).encode(), 'application/json'
        status, result = request('POST', '/api/v1/hotels/' + query, args, body, ctype)
        outcome = result.get('status', 'error')
        detail = result.get('hotel', {}).get('url') or result.get('error') or result.get('errors', '')
        print(f"[{outcome:>12}] {hotel.get('name')}  {detail}")
        if status >= 400:
            failures += 1
    print(('DRY RUN: nothing was saved. ' if args.dry_run else '') + f'{len(hotels) - failures} ok, {failures} not created.')
    sys.exit(1 if failures else 0)


def cmd_list(args):
    q = '?' + urllib.parse.urlencode({'country': args.country}) if args.country else ''
    status, body = request('GET', '/api/v1/hotels/' + q, args)
    if status != 200:
        return show(status, body)
    for h in body['hotels']:
        flag = '' if h['is_published'] else ' [draft]'
        print(f"{h['slug']:<55} {h['country']:<10} {h['star_rating']}*  ${h['price_per_night']}  photos:{h['photos']}{flag}")
    print(f"{body['count']} hotels")


def cmd_get(args):
    show(*request('GET', f'/api/v1/hotels/{args.slug}/', args))


def cmd_update(args):
    q = '?dry_run=1' if args.dry_run else ''
    show(*request('PATCH', f'/api/v1/hotels/{args.slug}/' + q, args, json.dumps(load_json(args.file)).encode(), 'application/json'))


def cmd_photos(args):
    body, ctype = multipart({}, args.files)
    show(*request('POST', f'/api/v1/hotels/{args.slug}/photos/' + ('?dry_run=1' if args.dry_run else ''), args, body, ctype))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--url', default=os.environ.get('HOTELS_API_URL'), help='Site address, e.g. https://daysafarisadventures.co.ke')
    parser.add_argument('--key', default=os.environ.get('HOTELS_API_KEY'), help='API key (or set HOTELS_API_KEY)')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('add'); p.add_argument('file'); p.add_argument('--photos-dir'); p.add_argument('--dry-run', action='store_true'); p.set_defaults(fn=cmd_add)
    p = sub.add_parser('list'); p.add_argument('--country'); p.set_defaults(fn=cmd_list)
    p = sub.add_parser('get'); p.add_argument('slug'); p.set_defaults(fn=cmd_get)
    p = sub.add_parser('update'); p.add_argument('slug'); p.add_argument('file'); p.add_argument('--dry-run', action='store_true'); p.set_defaults(fn=cmd_update)
    p = sub.add_parser('photos'); p.add_argument('slug'); p.add_argument('files', nargs='+'); p.add_argument('--dry-run', action='store_true'); p.set_defaults(fn=cmd_photos)
    args = parser.parse_args()
    if not args.url or not args.key:
        sys.exit('Set HOTELS_API_URL and HOTELS_API_KEY (or pass --url / --key).')
    args.fn(args)


if __name__ == '__main__':
    main()
