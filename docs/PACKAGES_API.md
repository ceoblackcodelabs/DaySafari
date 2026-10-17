# Packages API

Improve the text and SEO of packages without the admin. Same API keys as the hotels API. A key can read and change
text; it **cannot** delete, and it never changes prices, pictures or the web address (slug).

Base address: `https://daysafarisadventures.co.ke/api/v1/`

| Method | Path | What it does |
|---|---|---|
| GET | `packages/` | List all packages (`?category=` optional) |
| GET | `packages/<slug>/` | One package with its description and every itinerary day |
| PATCH | `packages/<slug>/` | Change text, SEO fields and itinerary days (JSON) |

Add `?dry_run=1` to a PATCH to validate and see what would change, saving nothing.

## PATCH body (send only what you want to change)
| Field | Notes |
|---|---|
| `name` | package title (max 100). The web address does not change |
| `location` | max 100 |
| `description` | HTML |
| `seo_title` | about 60 characters (max 70) |
| `seo_description` | about 155 characters (max 170) |
| `itineraries` | list of days: `{"day_number": 1, "title", "description", "activities", "accommodation", "meals"}`. Existing days are updated field by field, a new `day_number` is created, nothing is deleted. `meals`: Breakfast, Half Board, Full Board or All Inclusive |

When English text changes, the other languages of that field are cleared so the page shows the new English until a
translation is added.
