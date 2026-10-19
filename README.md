# Day Safaris Adventures (Django)

Green-theme site with the full backend of the original DaySafaris project: packages, tours, trekking, hotels,
blog, gallery, brochures, guides, accounts, bookings/contact forms with anti-spam + Brevo emails, i18n (en/sw/fr/de/es/it)
and the JSON API (`/api/v1/...`). Plus landing pages (Kenya, Tanzania, Uganda, Masai Mara, Kilimanjaro, safari + beach,
cruise pages) with an enquiry form that is saved as a booking lead.

## Run
```bash
source ~/CODES/venv/bin/activate     # your virtualenv (Django, whitenoise, ckeditor5, modeltranslation ...)
pip install -r requirements.txt      # only if something is missing
python manage.py migrate
python manage.py runserver           # http://127.0.0.1:8000/
```

* `.env` holds local settings (`DEBUG=True`). Copy your secrets (`BREVO_API_KEY`, `EMAIL_HOST_*`, `SECRET_KEY`...) into it
  from the old project's `.env` to enable emails. Never commit it.
* Database: `db.sqlite3` (SQLite, WAL mode). Uploads: `media/`.
* Theme: `static/css/site.css`, `static/js/site.js`. Static files are indexed at start-up: restart the server after
  editing CSS/JS (or run with `STATIC_AUTOREFRESH=1`).
* Admin: `python manage.py createsuperuser`, then `/en/admin/`. Enquiries from every form land in **Client Requests**.
* Hotels/blog/offers API keys: `python manage.py create_api_key --name "..."` (see `docs/*_API.md`).
* Tests: `python manage.py test`.

## Layout
`DaySafaris/` settings + urls · `Home/` pages, blog, gallery, guides · `Places/` packages & destinations ·
`Hotels/` hotels, API · `ClientRequests/` bookings, contact, anti-spam · `OurClients/` accounts ·
`EmailSetup/` emails · `safaris/` landing pages, shared icons/tags · `Home/templates/Home/base.html` is the shared layout.

## Deploy checklist
1. Upload the project (without `.env`, `__pycache__`, `staticfiles/`) and create the server `.env` from `.env.example`:
   `DEBUG=False`, a long random `SECRET_KEY`, `BREVO_API_KEY`, `EMAIL_HOST_USER/PASSWORD`, and
   `SECURE_SSL_REDIRECT=True` + `TRUST_PROXY_SSL_HEADER=True` once HTTPS works.
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py collectstatic --noinput`
5. Point the host (Passenger: `passenger_wsgi.py`) at `DaySafaris.wsgi`; `touch tmp/restart.txt` after each deploy.
6. Hosts allowed in production are listed in `DaySafaris/settings.py` (`ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`).
7. `db.sqlite3` and `media/` are the live data: back them up (`python manage.py backup_data`) and do not overwrite them on deploy.
