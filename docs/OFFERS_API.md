# Offers API (homepage "Special Offers & Travel Deals")

Add and manage the poster cards on the home page without the admin. It uses the **same API keys** as the hotels API
(see `docs/HOTELS_API.md` for creating and revoking a key).

Base address: `https://daysafarisadventures.co.ke/api/v1/`  (no language prefix)
Send `Authorization: Bearer dsa_xxxxxxxx_...` on every request. A key can add and edit offers; it **cannot delete**.
To take an offer down use `{"is_active": false}` (or an earlier `end_date`).

## Endpoints
| Method | Path | What it does |
|---|---|---|
| GET | `offers/schema/` | Public. Lists the fields and rules |
| GET | `offers/` | List offers (`?active=1`, `?status=active\|upcoming\|expired\|hidden`, `?limit=`) |
| POST | `offers/` | Create an offer (multipart: JSON `data` + poster file `image`) |
| GET | `offers/<id>/` | One offer |
| PATCH | `offers/<id>/` | Change fields (JSON), e.g. dates, title, `is_active` |
| POST | `offers/<id>/image/` | Replace the poster (multipart, field `image`) |

Add **`?dry_run=1`** to any write to validate exactly as a real call but save nothing.

## Fields
| Field | Notes |
|---|---|
| `title` | required, max 160 (shown under the poster) |
| `image` | required file: JPEG / PNG / WebP, at least 640 px wide, up to 8 MB. A square or 4:5 poster works best |
| `start_date` | optional, `YYYY-MM-DD`. Before this date the card shows **Upcoming** |
| `end_date` | optional, `YYYY-MM-DD`. The offer disappears after this day |
| `whatsapp_message` | optional text for the Book Via WhatsApp button (default: "Hello Day Safaris, I am interested in: <title>") |
| `is_active` | true/false, default true |
| `order` | integer, lower first, default 0 (equal: newest first) |

The title and message are stored as English text. The site shows 8 offers per page on the home page.
Creating the same title with the same end date twice returns **409** with the existing offer, so retries are safe.

## Examples
```bash
# check first, saves nothing
curl -X POST "https://daysafarisadventures.co.ke/api/v1/offers/?dry_run=1" -H "Authorization: Bearer $KEY" \
  -F 'data={"title":"4 Days 3 Nights in Bali Island Tours","end_date":"2026-11-30"}' -F image=@bali.jpg

# create
curl -X POST https://daysafarisadventures.co.ke/api/v1/offers/ -H "Authorization: Bearer $KEY" \
  -F 'data={"title":"Travel to Thailand","end_date":"2026-11-30","order":2}' -F image=@thailand.jpg

# hide an offer
curl -X PATCH https://daysafarisadventures.co.ke/api/v1/offers/7/ -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -d '{"is_active": false}'

# replace the poster
curl -X POST https://daysafarisadventures.co.ke/api/v1/offers/7/image/ -H "Authorization: Bearer $KEY" -F image=@new.jpg
```
