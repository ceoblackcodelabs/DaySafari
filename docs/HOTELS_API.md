# Hotels API

Add and manage hotels on the site without the admin. JSON over HTTPS, token authentication, no extra software needed.

Base address: `https://daysafarisadventures.co.ke/api/v1/`  (no language prefix)

## 1. Get a key
On the server:
```bash
python manage.py create_api_key --name "Claude assistant"    # prints the token once
python manage.py create_api_key --list
python manage.py create_api_key --revoke <prefix>            # stops working immediately
```
Send it as `Authorization: Bearer dsa_xxxxxxxx_...` on every request. Keys are stored only as hashes. A key can add and
edit hotels; it **cannot delete anything and cannot read bookings, contacts or users**. Treat it like a password and
revoke it when the work is finished. Revoking is also possible in the admin (**Hotels → API keys**).

## 2. Endpoints
| Method | Path | What it does |
|---|---|---|
| GET | `hotels/schema/` | Public. Lists every field and allowed value |
| GET | `hotels/` | List hotels (`?country=Kenya&q=lodge&limit=100`), drafts included |
| POST | `hotels/` | Create one hotel, or many with `{"hotels": [...]}` (max 25) |
| GET | `hotels/<slug>/` | One hotel with full details and photo URLs |
| PATCH | `hotels/<slug>/` | Change only the fields you send |
| POST | `hotels/<slug>/photos/` | Upload photos (multipart, field `photos`) |

Add **`?dry_run=1`** to any POST/PATCH to validate exactly as a real call but save nothing.

## 3. Fields
Required: `name`, `country`, `location`. Everything else is optional.

| Field | Notes |
|---|---|
| `property_type` | `hotel` (default), `lodge`, `camp`, `resort`, `villa`, `apartment`, `cabin`. Labels like "Safari Lodge" also work |
| `star_rating` | 1-5, default 4 |
| `rooms` | `Studio`, `1b`, `2b`, `3b`, `4b` (labels like "2 Bedroom" work) |
| `summary` | one line shown on the card (max 220) |
| `description` | max 8000 characters. HTML is stripped |
| `price_per_night` | USD, starting rate. `"$1,200"` is accepted |
| `max_guests` | 1-60, default 2 |
| `meal_plan` | `RO`, `BB`, `HB`, `FB`, `AI` (labels like "Full board" work) |
| `amenities` | list of strings (max 40). Shown on the hotel page only if present |
| `child_policy` | text |
| `is_published` | default `true`; `false` saves a draft that is not shown on the site |
| `is_featured` | default `false`; featured hotels are listed first |
| internal, never shown publicly | `contact_person`, `email`, `phone_number`, `contract_validity` (YYYY-MM-DD), `remarks` |

A hotel with the same name + location + country (case-insensitive) already on the site is refused with **409** and the
existing record is returned, so repeating a request never creates duplicates. The address (`slug`) is generated automatically.

## 4. Examples
Create (JSON):
```bash
curl -X POST https://daysafarisadventures.co.ke/api/v1/hotels/ \
  -H "Authorization: Bearer $HOTELS_API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"Sarova Mara Game Camp","country":"Kenya","location":"Masai Mara","property_type":"camp",
       "star_rating":4,"price_per_night":350,"max_guests":6,"summary":"Tented luxury on the plains.",
       "amenities":["Swimming pool","Free Wi-Fi"]}'
```
Create with photos in one request (multipart: a JSON `data` field plus `photos` files):
```bash
curl -X POST https://daysafarisadventures.co.ke/api/v1/hotels/ -H "Authorization: Bearer $HOTELS_API_KEY" \
  -F 'data={"name":"Sarova Mara Game Camp","country":"Kenya","location":"Masai Mara"}' \
  -F photos=@pool.jpg -F photos=@room.jpg
```
Update one field:
```bash
curl -X PATCH .../api/v1/hotels/sarova-mara-game-camp-masai/ -H "Authorization: Bearer $HOTELS_API_KEY" \
  -H "Content-Type: application/json" -d '{"price_per_night": 320}'
```

## 5. Photos
JPEG, PNG or WebP, at least 640 px wide, up to 8 MB each, at most 12 per hotel. The first photo of a hotel becomes its
main photo; the site resizes and compresses everything automatically. The server never downloads images from URLs: send files.

## 6. Responses
`201` created, `200` ok / dry run, `400` validation errors per field, `401` missing or invalid key, `404` not found,
`405` method not allowed, `409` duplicate, `429` rate limit. Errors look like
`{"ok": false, "error": "...", "errors": {"star_rating": ["..."]}}`.
Limits: 60 requests/minute and 600/hour per key; 10 wrong keys from one address in 10 minutes blocks it for a while.

## 7. Command-line client
`tools/hotels_api.py` (standard library only) wraps the API. Set `HOTELS_API_URL` and `HOTELS_API_KEY`, then:
```bash
python tools/hotels_api.py add hotels.json --dry-run
python tools/hotels_api.py add hotels.json --photos-dir ./pictures
python tools/hotels_api.py list --country Kenya
```
`hotels.json` is a list of hotel objects; a hotel may include `"photos": ["a.jpg", "b.jpg"]`.
