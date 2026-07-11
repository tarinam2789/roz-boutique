"""
One-time migration: adds the contact_messages table so the new Contact page
can store messages, without deleting any of your current products, orders,
or admin login.

Run this once from inside your roz folder:
    python3 migrate_add_contact_messages.py
"""
import sqlite3

conn = sqlite3.connect("roz.db")
cur = conn.cursor()


def table_exists(table):
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


if not table_exists("contact_messages"):
    cur.execute(
        """
        CREATE TABLE contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    print("Created contact_messages table")
else:
    print("contact_messages table already exists — skipped")

conn.commit()
conn.close()
print("\nMigration complete. Your existing products, orders, and admin login are untouched.")
