"""Initializes roz.db from schema.sql and populates it with sample brand data."""
import os
import sqlite3
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "roz.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.executescript(open(SCHEMA_PATH).read())
cur = conn.cursor()

# ---------------------------------------------------------------- admin
cur.execute(
    "INSERT INTO admin_users (email, password_hash) VALUES (?,?)",
    ("admin@roz.com", generate_password_hash("roz-admin-2026")),
)

# ------------------------------------------------------------ categories
categories = [
    ("New Arrivals", "new-arrivals", "Fresh from the atelier", 1),
    ("Luxury Pret", "luxury-pret", "Ready-to-wear, elevated", 2),
    ("Formals", "formals", "For occasions that matter", 3),
    ("Semi Formals", "semi-formals", "Effortless refinement", 4),
    ("Luxury Formals", "luxury-formals", "Bridal & couture-grade", 5),
]
cat_ids = {}
for name, slug, tagline, order in categories:
    cur.execute(
        "INSERT INTO categories (name, slug, tagline, display_order) VALUES (?,?,?,?)",
        (name, slug, tagline, order),
    )
    cat_ids[slug] = cur.lastrowid

# ------------------------------------------------------------- products
# (name, category_slug, price, compare, description, fabric, swatch, season,
#  best_seller, featured, new_arrival)
products = [
    ("Gulnaar Rose Embroidered Kurta Set", "new-arrivals", 148, 175,
     "A soft blush kurta set finished with hand-embroidered rose vines along the neckline and hem, paired with matching cigarette trousers and a dupatta edged in gold gota.",
     "Pure lawn cotton", 0, "Spring", 1, 1, 1),
    ("Zoya Blush Chikankari Suit", "new-arrivals", 162, None,
     "Delicate chikankari hand-embroidery on breathable cotton, in a gentle blush that catches the light like petals at dawn.",
     "Cotton chikankari", 1, "Spring", 0, 1, 1),
    ("Anaya Silk Straight Kurta", "luxury-pret", 128, None,
     "A clean-lined silk kurta in dusty rose, cut for everyday elegance with a subtle floral jacquard woven through the fabric.",
     "Silk jacquard", 2, "", 1, 0, 0),
    ("Ishrat Pastel Kaftan", "luxury-pret", 112, 135,
     "Relaxed, breezy, and romantic — an ankle-length kaftan in whisper-soft pink georgette with butterfly sleeves.",
     "Georgette", 3, "Summer", 0, 0, 0),
    ("Mehak Two-Piece Lawn Set", "luxury-pret", 96, None,
     "A crisp two-piece in cream and rose, printed with a hand-illustrated botanical trail.",
     "Premium lawn", 4, "Summer", 1, 0, 0),
    ("Noorjahan Rose Gold Formal Gown", "formals", 385, 450,
     "An architectural silhouette in rose-gold organza with hand-placed floral appliqué cascading from the shoulder.",
     "Organza silk", 5, "", 1, 1, 0),
    ("Saira Embellished Formal Saree", "formals", 340, None,
     "A blush saree with a hand-embroidered pallu of trailing roses, edged in fine gold zari.",
     "Silk chiffon", 0, "", 0, 1, 0),
    ("Devika Gold-Threaded Anarkali", "formals", 298, None,
     "Floor-length Anarkali in soft rose with gold thread florals winding from bodice to hem.",
     "Silk blend", 1, "", 0, 0, 0),
    ("Rania Rose Garden Semi-Formal Suit", "semi-formals", 210, None,
     "Understated luxury for daytime celebrations: a rose-embroidered bodice with a flowing cream skirt.",
     "Silk cotton blend", 2, "", 0, 0, 0),
    ("Farah Blush Sharara Set", "semi-formals", 235, 260,
     "A three-piece sharara set in blush and gold, with delicate floral resham embroidery.",
     "Raw silk", 3, "", 1, 0, 0),
    ("Meherbano Layered Semi-Formal Gown", "semi-formals", 265, None,
     "Soft layers of blush tulle over a rose silk slip, scattered with hand-sewn petals.",
     "Tulle & silk", 4, "", 0, 0, 0),
    ("Roz Signature Bridal Lehenga", "luxury-formals", 1250, 1450,
     "Our most coveted piece: a hand-embroidered bridal lehenga in blush and antique gold, densely worked with rose motifs and zardozi.",
     "Silk velvet, zardozi", 5, "", 1, 1, 0),
    ("Amara Couture Rose Gharara", "luxury-formals", 890, None,
     "A regal gharara set in rose pink silk, embellished with gold dabka and hand-cut floral appliqué.",
     "Silk, dabka work", 0, "", 0, 1, 0),
    ("Yasmeen Heirloom Formal Set", "luxury-formals", 975, None,
     "Designed to be passed down — dense floral zardozi embroidery on a rose silk base, with a matching dupatta.",
     "Pure silk, zardozi", 1, "", 0, 0, 0),
]

product_ids = {}
for (name, cat_slug, price, compare, desc, fabric, swatch, season, best, feat, new) in products:
    slug = name.lower().replace(",", "").replace("'", "")
    slug = "-".join(slug.split())
    cur.execute(
        "INSERT INTO products (name, slug, category_id, price, compare_at_price, description, "
        "fabric, swatch, season, is_best_seller, is_featured, is_new_arrival, active) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1)",
        (name, slug, cat_ids[cat_slug], price, compare, desc, fabric, swatch, season, best, feat, new),
    )
    product_ids[name] = cur.lastrowid

# --------------------------------------------------------- sizes / stock
default_sizes = {"XS": 4, "S": 8, "M": 10, "L": 7, "XL": 5, "XXL": 2}
for pid in product_ids.values():
    for size_code, qty in default_sizes.items():
        cur.execute(
            "INSERT INTO product_sizes (product_id, size_code, quantity) VALUES (?,?,?)",
            (pid, size_code, qty),
        )
# make one product sell out in a size, for realism
cur.execute(
    "UPDATE product_sizes SET quantity=0 WHERE product_id=? AND size_code IN ('XS','XXL')",
    (product_ids["Roz Signature Bridal Lehenga"],),
)

# ------------------------------------------------------------ size guide
guide_text = (
    "Measure yourself in undergarments, standing straight. Chest: measure around the fullest "
    "part of your bust, keeping the tape parallel to the ground. Waist: measure around the "
    "narrowest part of your natural waistline. Hips: measure around the fullest part of your "
    "hips. Length: measure from the base of the neck to your desired hemline. If you fall "
    "between two sizes, we recommend sizing up for comfort, especially for heavily embellished pieces."
)
guide_rows_data = {
    "XS": (32, 26, 34, 42, 22, 13.5),
    "S": (34, 28, 36, 43, 22.5, 14),
    "M": (36, 30, 38, 44, 23, 14.5),
    "L": (38, 32, 40, 45, 23.5, 15),
    "XL": (40, 34, 42, 46, 24, 15.5),
    "XXL": (42, 36, 44, 47, 24.5, 16),
}
for pid in product_ids.values():
    cur.execute(
        "INSERT INTO size_guides (product_id, instructions, image_path, unit) VALUES (?,?,?,?)",
        (pid, guide_text, None, "in"),
    )
    guide_id = cur.lastrowid
    for size_code, (chest, waist, hips, length, sleeve, shoulder) in guide_rows_data.items():
        cur.execute(
            "INSERT INTO size_guide_rows (size_guide_id, size_code, chest, waist, hips, length, "
            "sleeve_length, shoulder_width) VALUES (?,?,?,?,?,?,?,?)",
            (guide_id, size_code, chest, waist, hips, length, sleeve, shoulder),
        )

# ----------------------------------------------------------------- ship
shipping_rules = [
    ("United States", "USD", 9.00, 100),
    ("Canada", "USD", 14.00, 100),
    ("United Kingdom", "USD", 12.00, 100),
    ("Other", "USD", 22.00, 150),
]
for country, currency, price, threshold in shipping_rules:
    cur.execute(
        "INSERT INTO shipping_rules (country, currency, standard_price, free_shipping_threshold) VALUES (?,?,?,?)",
        (country, currency, price, threshold),
    )

# --------------------------------------------------------- return policy
cur.execute(
    "INSERT INTO return_policy (window_days, return_fee, eligibility_rules, refund_method) VALUES (?,?,?,?)",
    (
        7,
        12.00,
        "Items must be unworn, unwashed, and returned with original tags attached. "
        "Bridal and made-to-order luxury formals are final sale. Customers are responsible "
        "for return shipping costs, deducted from the refund.",
        "Refunded to original payment method within 5–7 business days of approval.",
    ),
)

# --------------------------------------------------------------- reviews
reviews = [
    ("Roz Signature Bridal Lehenga", "Sana K.", "Toronto, CA", 5,
     "I felt like royalty. The embroidery is even more stunning in person, and it arrived exactly as pictured."),
    ("Gulnaar Rose Embroidered Kurta Set", "Amara H.", "London, UK", 5,
     "The fabric is so soft and the fit is true to size. Roz has become my go-to for Eid outfits."),
    ("Noorjahan Rose Gold Formal Gown", "Priya D.", "New York, US", 5,
     "Wore this to a wedding and got endless compliments. Worth every penny."),
    ("Farah Blush Sharara Set", "Zainab R.", "Houston, US", 4,
     "Beautiful set, the color is more rose than blush in person but I love it even more."),
    ("Anaya Silk Straight Kurta", "Fatima N.", "Manchester, UK", 5,
     "Simple, elegant, and the silk quality is incredible for the price."),
    ("Amara Couture Rose Gharara", "Nadia S.", "Vancouver, CA", 5,
     "The dabka work is exquisite. Customer service was also lovely when I had sizing questions."),
]
for product_name, customer, location, rating, comment in reviews:
    cur.execute(
        "INSERT INTO reviews (product_id, customer_name, location, rating, comment) VALUES (?,?,?,?,?)",
        (product_ids[product_name], customer, location, rating, comment),
    )

# ------------------------------------------------------------- instagram
captions = [
    "Golden hour in Gulnaar rose \u2728",
    "Bridal season begins \U0001F337",
    "Petals & pret \u2014 new arrivals",
    "Behind the embroidery frame",
    "Styled: blush on blush",
    "From our atelier to your wardrobe",
    "Details that take 40 hours to hand-work",
    "Garden party ready",
]
for i, caption in enumerate(captions):
    cur.execute(
        "INSERT INTO instagram_posts (caption, swatch, sort_order) VALUES (?,?,?)",
        (caption, i % 6, i),
    )

conn.commit()
conn.close()
print("Database seeded at", DB_PATH)
