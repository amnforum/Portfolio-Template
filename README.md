# Open Portfolio

A clean, shareable Django portfolio starter with profile pages, projects, skills, a contact form, local SQLite defaults, and an optional AI assistant.
For Demo like how is this gonna look like check this url : https://www.aman-chauhan.co.in

## Features

- Django portfolio pages for profile, projects, skills, and contact
- Admin-managed content
- SQLite by default for local development
- Optional Cloudinary media storage
- Optional AI assistant with local fallback embeddings
- Public-repo friendly sample data and environment template

## Quick Start

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

Admin: `http://127.0.0.1:8000/admin/`

## Environment

Copy `.env.example` to `.env` and edit values for your machine or deployment. Leave `DATABASE_URL` empty to use local SQLite.

Never commit `.env`, `db.sqlite3`, uploaded media, or virtual environment folders.

## Customize

Use Django admin to update:

- Profile details
- Skills
- Projects and screenshots
- Contact messages
- Knowledge documents for the assistant

## License

MIT
