"""
One-time migration: adds the product_media table so products can have
multiple photos and a video, without deleting any of your current
products, orders, or admin login.

Run this once from inside your roz folder:
    python3 migrate_add_gallery.py
"""
import sqlite3

conn = sqlite3.connect("roz.db")
cur = conn.cursor()


def table_exists(table):
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


if not table_exists("product_media"):
    cur.execute(
        """
        CREATE TABLE product_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            media_type TEXT NOT NULL DEFAULT 'image',
            path TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
        """
    )
    print("Created product_media table")

    # Backfill: if any existing products already have a single image_path set
    # (from before this feature existed), copy it in as the first gallery photo
    # so nothing looks empty.
    cur.execute("SELECT id, image_path FROM products WHERE image_path IS NOT NULL AND image_path != ''")
    existing = cur.fetchall()
    for product_id, image_path in existing:
        cur.execute(
            "INSERT INTO product_media (product_id, media_type, path, sort_order) VALUES (?, 'image', ?, 0)",
            (product_id, image_path),
        )
    if existing:
        print(f"Backfilled {len(existing)} existing product photo(s) into the new gallery")
else:
    print("product_media table already exists — skipped")

conn.commit()
conn.close()
print("\nMigration complete. Your existing products, orders, and admin login are untouched.")
