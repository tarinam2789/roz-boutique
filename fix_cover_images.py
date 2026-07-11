"""
One-time fix: sets each product's cover image (shown on homepage/category
cards) to its first gallery photo, for any products where this is currently
missing. Safe to run anytime — it only reads from product_media and doesn't
delete anything.

Run this once from inside your roz folder:
    python3 fix_cover_images.py
"""
import sqlite3

conn = sqlite3.connect("roz.db")
cur = conn.cursor()

cur.execute("SELECT id, name, image_path FROM products")
products = cur.fetchall()

fixed = 0
for product_id, name, current_image_path in products:
    cur.execute(
        "SELECT path FROM product_media WHERE product_id=? AND media_type='image' "
        "ORDER BY sort_order, id LIMIT 1",
        (product_id,),
    )
    row = cur.fetchone()
    first_image_path = row[0] if row else None

    if first_image_path and first_image_path != current_image_path:
        cur.execute(
            "UPDATE products SET image_path=? WHERE id=?", (first_image_path, product_id)
        )
        print(f"Fixed cover image for: {name}")
        fixed += 1

conn.commit()
conn.close()

if fixed:
    print(f"\nDone — fixed {fixed} product(s). Refresh your site to see the photos on listing pages.")
else:
    print("\nNo products needed fixing — all cover images were already correct.")
