"""
One-time migration: adds product photo, color, and bottom-length support
to an EXISTING roz.db without deleting any of your current products, orders,
or admin login.

Run this once from inside your roz folder:
    python3 migrate_add_colors_and_bottom_length.py
"""
import sqlite3

conn = sqlite3.connect("roz.db")
cur = conn.cursor()


def column_exists(table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def table_exists(table):
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


if not column_exists("products", "image_path"):
    cur.execute("ALTER TABLE products ADD COLUMN image_path TEXT")
    print("Added products.image_path")
else:
    print("products.image_path already exists — skipped")

if not column_exists("products", "bottom_type"):
    cur.execute("ALTER TABLE products ADD COLUMN bottom_type TEXT")
    print("Added products.bottom_type")
else:
    print("products.bottom_type already exists — skipped")

if not column_exists("size_guide_rows", "bottom_length"):
    cur.execute("ALTER TABLE size_guide_rows ADD COLUMN bottom_length REAL")
    print("Added size_guide_rows.bottom_length")
else:
    print("size_guide_rows.bottom_length already exists — skipped")

if not table_exists("product_colors"):
    cur.execute(
        """
        CREATE TABLE product_colors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            color_name TEXT NOT NULL,
            hex TEXT NOT NULL,
            UNIQUE(product_id, color_name),
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
        """
    )
    print("Created product_colors table")
else:
    print("product_colors table already exists — skipped")

conn.commit()
conn.close()
print("\nMigration complete. Your existing products, orders, and admin login are untouched.")
