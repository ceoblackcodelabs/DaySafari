# Blogs API

Publish blog posts (with a featured picture and pictures inside the text) without the admin. It uses the **same API
keys** as the hotels API (see `docs/HOTELS_API.md`). A key can add and edit posts; it **cannot delete**.

Base address: `https://daysafarisadventures.co.ke/api/v1/`  (no language prefix)

## Endpoints
| Method | Path | What it does |
|---|---|---|
| GET | `blogs/schema/` | Public. Fields and rules |
| GET | `blogs/` | List posts (`?q=` title search, `?limit=`) |
| POST | `blogs/` | Create a post (multipart: JSON `data` + files) |
| GET | `blogs/<slug>/` | One post with its full text |
| PATCH | `blogs/<slug>/` | Change text, SEO fields, category or translations (JSON) |
| POST | `blogs/<slug>/image/` | Replace the featured picture (multipart, field `image`) |

Add **`?dry_run=1`** to any write to validate exactly as a real call but save nothing.

## Fields (inside the JSON `data`)
| Field | Notes |
|---|---|
| `title` | required, max 100. The address (slug) is made from it, e.g. `best-time-to-visit-kenya` |
| `content` | required HTML, at least 300 words. Allowed: `h2 h3 h4 p ul ol li strong em a blockquote table figure img br hr`. `h1` becomes `h2`; scripts, styles and event handlers are removed |
| `category` | slug or name of an existing category (`planning-tips`, `safari-itineraries`, `wildlife-conservation`, `culture-lifestyle`) |
| `author` | default "Day Safaris Adventures" |
| `seo_title` | about 60 characters (max 70). The browser/Google title |
| `seo_description` | about 155 characters (max 170). The Google snippet |
| `slug` | optional; generated from the title |
| `schema_markup` | optional extra JSON-LD |
| `translations` | optional `{"fr": {"title","content","seo_title","seo_description"}, "sw": {...}, "es", "de", "it"}` |

The text is stored as English; `translations` fill the other languages (a language without a translation shows the
English text).

## Pictures
Send `multipart/form-data`:
* `data` : the JSON above
* `image` : the **featured** picture (required): JPEG/PNG/WebP, at least 640 px wide, up to 8 MB. It is also the
  social-sharing picture
* `images` : optional inline pictures (up to 8). Put `[[image:1]]`, `[[image:2]]` ... on their own line in the content
  where each should appear
* `alts` and `captions` : JSON lists (same order as `images`) used for the picture's description and caption

Posts created with the same title as an existing post return **409**, so retrying is safe.

## Example
```bash
curl -X POST https://daysafarisadventures.co.ke/api/v1/blogs/ -H "Authorization: Bearer $KEY" \
  -F 'data={"title":"Best Time to Visit Amboseli","category":"planning-tips","seo_title":"Best Time to Visit Amboseli","seo_description":"...","content":"<h2>...</h2><p>...</p><p>[[image:1]]</p>"}' \
  -F image=@featured.jpg -F images=@inline1.jpg \
  -F 'alts=["Elephants with Kilimanjaro behind"]' -F 'captions=["Amboseli elephants"]'
```
