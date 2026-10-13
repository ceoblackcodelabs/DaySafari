# Day Safaris Adventures

Website and booking system for Day Safaris Adventures (Nairobi, Kenya): safari packages, trekking, cruises, **hotels**,
Airbnb-style stays, blog, gallery, enquiries and M-Pesa payments. Built with Django (SQLite, WhiteNoise, Brevo email).

Live site: https://daysafarisadventures.co.ke

## Contents
1. [Run it locally](#run-it-locally)
2. [Settings (`.env`)](#settings-env)
3. [Deploying to the server](#deploying-to-the-server)
4. [Backups](#backups)
5. [Hotels API: create an API key](#hotels-api-create-an-api-key)
6. [Useful commands](#useful-commands)

## Run it locally
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # or create .env by hand (see below)
python manage.py migrate
python manage.py runserver
python manage.py test        # runs the whole test suite
```
Put `DEBUG=True` in your local `.env` for development. The default is `False` (production-safe).

## Settings (`.env`)
Secrets live in `.env`, which is **never committed**. Main variables:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret. Set a long random value on the server |
| `DEBUG` | `True` only on your own computer |
| `BREVO_API_KEY` | Sends booking/enquiry emails (required) |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | SMTP settings (Brevo) |
| `MPESA_*` | M-Pesa credentials (`MPESA_ENVIRONMENT=sandbox` or `production`) |
| `github` | Token for the chatbot's AI provider |
| `SECURE_SSL_REDIRECT`, `TRUST_PROXY_SSL_HEADER` | Set to `True` once HTTPS works behind your host's proxy |
| `DB_PATH` | Optional: use a different SQLite file |

## Deploying to the server
The database (`db.sqlite3`), uploaded `media/` and `.env` live on the server and are **not** replaced by deploys.

```bash
cd ~/DaySafaris
./deploy.sh        # backs up, pulls, protects the live database, migrates, restarts
```
or by hand: `git pull`, `python manage.py migrate`, `python manage.py collectstatic --noinput`, `touch tmp/restart.txt`.

Never run `git reset --hard`, `git checkout .` or `git stash` on the server: they can destroy live data.
`rsync` is not installed on the host; use `cp -a` to copy folders.

## Backups
```bash
python manage.py backup_data            # database + media into ./backups/ (keeps the newest 14)
python manage.py backup_data --no-media # database only
```
Copy `backups/` off the server regularly. To schedule it daily at 02:30 add this cron line:
`30 2 * * * cd ~/DaySafaris && python manage.py backup_data`

## Hotels API: create an API key
Hotels can be added, edited and given photos without the admin, through a secure JSON API
(`/api/v1/hotels/`). Anyone using it needs an **API key**, which you create on the server.

### 1. Create a key
SSH into the server, activate the app's virtualenv, then run:
```bash
cd ~/DaySafaris
python manage.py create_api_key --name "Claude assistant"
```
Use a name that says who or what will use the key. The command prints something like:
```
API key created for "Claude assistant" (prefix 1a2b3c4d).

Copy this token now. It is shown only once and cannot be recovered:

    dsa_1a2b3c4d_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
**Copy the token immediately.** Only a hash is stored, so it can never be shown again. If you lose it, create a new
key and revoke the old one.

### 2. Use it
Send it as a header on every request: `Authorization: Bearer <token>`.
```bash
export HOTELS_API_URL=https://daysafarisadventures.co.ke
export HOTELS_API_KEY=dsa_1a2b3c4d_xxxx...

python tools/hotels_api.py list                              # see the hotels on the site
python tools/hotels_api.py add hotels.json --dry-run         # validate, save nothing
python tools/hotels_api.py add hotels.json --photos-dir pics # create hotels and upload their photos
```
Full guide, every field and curl examples: [docs/HOTELS_API.md](docs/HOTELS_API.md).
A public description of the fields is available without a key at `/api/v1/hotels/schema/`.

### 3. Manage and revoke keys
```bash
python manage.py create_api_key --list                # who has keys, and when each was last used
python manage.py create_api_key --revoke 1a2b3c4d     # stops working immediately (use the prefix)
```
Keys can also be switched off in the admin under **Hotels → API keys** (untick *Is active*).

### Keep keys safe
- Treat a key like a password: share it only with the person or tool that needs it, never in public places,
  screenshots, the repository or `.env.example`.
- Create **one key per user or tool**, so you can revoke one without affecting the others.
- **Revoke a key when the work is finished** and create a new one next time.
- A key can add and edit hotels and upload photos. It **cannot delete anything** and cannot read bookings, contacts
  or users. Every write is recorded in `logs/hotels-api.log`.
- Always try `--dry-run` first: it validates exactly like a real request but saves nothing.

### Add the researched hotels without a key
The 16 researched hotels ship with the project and can be loaded straight from the server:
```bash
python manage.py seed_hotels --dry-run     # preview
python manage.py seed_hotels               # create the missing ones (safe to repeat)
```

## Useful commands
| Command | What it does |
|---|---|
| `python manage.py test` | Run the test suite |
| `python manage.py backup_data` | Back up the database and media |
| `python manage.py warm_thumbnails` | Pre-generate WebP image thumbnails |
| `python manage.py purge_spam` | Dry run: find spam enquiries and bot accounts (`--delete`, `--deactivate-users`) |
| `python manage.py seed_package_details` | Fill star ratings and inclusions on safari packages |
| `python manage.py create_api_key --name "..."` | Create a hotels-API key |

## Brand colours
`#420d24` (maroon), `#f6c582` (gold), `#cba280`, `#eb9e31`
