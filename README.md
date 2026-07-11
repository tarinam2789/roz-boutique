# Roz Boutique — Full-Stack E-Commerce Platform

A complete e-commerce web application built with **Python (Flask)** and **SQLite**,
for a South Asian fashion brand selling to customers in the US, Canada, and UK.
Built end-to-end: customer storefront, admin console, and all the operational
tooling a small fashion business actually needs to run.

**Live demo:** _add your deployed URL here once live_

## Features

**Storefront**
- Homepage with dynamic sections (new arrivals, best sellers, featured/seasonal
  collections, reviews, Instagram-style gallery, newsletter signup)
- 10 product categories, each with its own browsable page
- Product pages with a multi-photo/video gallery, color swatches, size selection
  with live inventory, and a per-product size guide (measurement chart + written
  instructions)
- Site-wide search, wishlist, and cart
- Customer accounts: registration/login, order history, and a return-request
  workflow with a configurable return window
- Contact form with email notifications (SMTP) and admin inbox

**Admin console** (`/admin`)
- Product CRUD: photo/video gallery management, free-text color tagging
  (auto-generates a matching swatch color for any name), per-size inventory,
  category assignment, and cross-tagging (e.g. a product can be both "Semi
  Formals" and "New Arrivals")
- Size-guide builder per product, with dynamic labeling (Trouser/Shalwar/Pants)
- Shipping-rule configuration per country with free-shipping thresholds
- Return-policy configuration and return-request approval workflow
- Contact-message inbox with read/unread tracking

**Engineering notes**
- Server-rendered with Flask + Jinja2, no JS framework — vanilla JS for
  interactivity (image galleries, modals, nav drawer, live search)
- SQLite via raw `sqlite3` (no ORM) — schema in `schema.sql`
- Secrets (Flask session key, SMTP credentials) loaded from environment
  variables via `python-dotenv`, never hardcoded
- File uploads (product photos, size-guide images) handled with Werkzeug's
  `secure_filename`
- Generated SVG product-art system as a graceful fallback for products without
  photos yet — a duotone gradient + botanical line-art motif, procedurally
  varied per product

## Tech stack

Python · Flask · SQLite · Jinja2 · vanilla JavaScript · CSS (no framework)

## Local setup

```bash
git clone <your-repo-url>
cd roz
pip install -r requirements.txt

cp .env.example .env
# then edit .env and fill in a real FLASK_SECRET_KEY and (optionally) SMTP credentials

python3 seed.py      # creates roz.db with sample data
python3 app.py        # runs at http://127.0.0.1:5000
```

Default admin login after seeding: `admin@roz.com` / `roz-admin-2026`
(change this immediately — see below).

## Changing the admin login

```bash
python3 -c "
import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('roz.db')
conn.execute(
    'UPDATE admin_users SET email=?, password_hash=? WHERE email=?',
    ('your-email@example.com', generate_password_hash('your-password'), 'admin@roz.com')
)
conn.commit()
conn.close()
"
```

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `FLASK_SECRET_KEY` | Yes | Signs session cookies. Use a long random string in production. |
| `SMTP_USERNAME` | No | Gmail address used to send contact-form notifications. |
| `SMTP_PASSWORD` | No | A Gmail App Password (not your regular password). |

If SMTP variables are left blank, contact messages are still saved and viewable
in the admin inbox — email notifications are just skipped.

## Known limitations (by design, for this stage of the project)

- Checkout is a working order-creation flow but isn't yet connected to a real
  payment processor (Stripe integration planned).
- Product photos are stored on local disk — fine for development, but on most
  free hosting tiers this storage is ephemeral (cleared on redeploy). A future
  iteration would move this to object storage (e.g. S3).
- SQLite is used for simplicity; a production deployment at scale would move
  to Postgres.

## Project structure
