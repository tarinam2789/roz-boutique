"""
One-time migration: adds Tops, Skirts, Pants, Kids, and Jewelry as real
categories (each gets its own working page at /category/<slug>), without
touching any of your existing products, orders, or admin login.

Run this once from inside your roz folder:
    python3 migrate_add_more_categories.py
"""
import sqlite3

conn = sqlite3.connect("roz.db")
cur = conn.cursor()

new_categories = [
    ("Tops", "tops", "Blouses, kurtis & shirts", 6),
    ("Skirts", "skirts", "Flowing silhouettes", 7),
    ("Pants", "pants", "Trousers, shalwars & more", 8),
    ("Kids", "kids", "Little ones, dressed in Roz", 9),
    ("Jewelry", "jewelry", "The finishing touch", 10),
]

for name, slug, tagline, order in new_categories:
    cur.execute("SELECT id FROM categories WHERE slug=?", (slug,))
    if cur.fetchone():
        print(f"Category '{name}' already exists — skipped")
        continue
    cur.execute(
        "INSERT INTO categories (name, slug, tagline, display_order) VALUES (?,?,?,?)",
        (name, slug, tagline, order),
    )
    print(f"Added category: {name}")

conn.commit()
conn.close()
print("\nMigration complete. Your existing products, orders, and admin login are untouched.")
