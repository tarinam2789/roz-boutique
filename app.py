import os
from dotenv import load_dotenv

load_dotenv()
from dotenv import load_dotenv

load_dotenv()
import sqlite3
from functools import wraps
from datetime import datetime, timedelta

from flask import (
    Flask, g, render_template, request, redirect, url_for,
    session, flash, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.message import EmailMessage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "roz.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

KNOWN_COLOR_HEX = {
    "black": "#1A1A1A", "white": "#FFFFFF", "ivory": "#F8F3E8", "cream": "#FBF6EE",
    "rose": "#C97B86", "rose gold": "#B76E79", "blush": "#F2C9CE", "pink": "#F2C9CE",
    "hot pink": "#E0558E", "gold": "#C7A15A", "maroon": "#6E1F2A", "red": "#B23A48",
    "wine": "#5E1F2E", "navy": "#1F2A44", "blue": "#274B8C", "royal blue": "#274B8C",
    "sky blue": "#7FB3D5", "bottle green": "#2E4A3D", "green": "#3C6B4A", "emerald": "#0F6B4E",
    "olive": "#6B6B3A", "grey": "#8A8A8A", "gray": "#8A8A8A", "silver": "#C0C0C0",
    "mustard": "#C9932F", "yellow": "#E0C440", "peach": "#F0B79A", "orange": "#D2762E",
    "turquoise": "#2E8B8B", "teal": "#1F6F6F", "purple": "#5B3A6E", "lavender": "#B39DC0",
    "lilac": "#C9A8D4", "brown": "#6B4A34", "beige": "#D8C6A8", "coral": "#E08E79",
    "mint": "#9FD4B8", "magenta": "#B23A7A", "charcoal": "#3A3A3A", "off white": "#F5F0E6",
}


def color_name_to_hex(name):
    key = name.strip().lower()
    if key in KNOWN_COLOR_HEX:
        return KNOWN_COLOR_HEX[key]
    # Deterministic fallback: hash the name into a soft, readable color
    h = sum(ord(c) for c in key) * 37
    r = 90 + (h % 120)
    g = 90 + ((h // 3) % 120)
    b = 90 + ((h // 7) % 120)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


BOTTOM_TYPES = ["Trouser", "Shalwar", "Pants"]


# ------------------------------------------------------------- email setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")  # e.g. "tarinaafrozmuna@gmail.com"
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")  # the 16-character Gmail App Password, no spaces
NOTIFY_EMAIL = "tarinaafrozmuna@gmail.com"


def send_contact_email(name, email, subject, message):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Roz Boutique contact form: {subject or 'New message'}"
        msg["From"] = SMTP_USERNAME
        msg["To"] = NOTIFY_EMAIL
        msg["Reply-To"] = email
        msg.set_content(
            f"New message from your Roz Boutique contact form.\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Subject: {subject or '(no subject)'}\n\n"
            f"Message:\n{message}\n\n"
            f"---\nReply directly to this email to respond to {name}."
        )
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[email] Failed to send contact notification: {e}")
        return False


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-fallback-change-me")
app.config["UPLOAD_DIR"] = UPLOAD_DIR


# ---------------------------------------------------------------- database

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    lastid = cur.lastrowid
    cur.close()
    return lastid


# ------------------------------------------------------------------ helpers

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return query_db("SELECT * FROM users WHERE id=?", (uid,), one=True)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "info")
            return redirect(url_for("account_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    cart = session.get("cart", [])
    cart_count = sum(item["qty"] for item in cart)
    wishlist = session.get("wishlist", [])
    unread_messages_count = 0
    if session.get("admin_id"):
        row = query_db("SELECT COUNT(*) c FROM contact_messages WHERE is_read=0", one=True)
        unread_messages_count = row["c"] if row else 0
    return dict(
        current_user=current_user(),
        cart_count=cart_count,
        wishlist_ids=set(wishlist),
        wishlist_count=len(wishlist),
        all_categories=query_db("SELECT * FROM categories ORDER BY display_order"),
        current_year=datetime.now().year,
        unread_messages_count=unread_messages_count,
    )


def get_product_with_sizes(product_id=None, slug=None):
    if slug:
        product = query_db("SELECT * FROM products WHERE slug=? AND active=1", (slug,), one=True)
    else:
        product = query_db("SELECT * FROM products WHERE id=?", (product_id,), one=True)
    if not product:
        return None, []
    sizes = query_db(
        "SELECT * FROM product_sizes WHERE product_id=?", (product["id"],)
    )
    sizes = sorted(sizes, key=lambda r: SIZE_ORDER.index(r["size_code"]) if r["size_code"] in SIZE_ORDER else 99)
    return product, sizes


def get_product_colors(product_id):
    return query_db("SELECT * FROM product_colors WHERE product_id=?", (product_id,))


def get_product_media(product_id):
    rows = query_db(
        "SELECT * FROM product_media WHERE product_id=? ORDER BY sort_order, id", (product_id,)
    )
    images = [r for r in rows if r["media_type"] == "image"]
    videos = [r for r in rows if r["media_type"] == "video"]
    return rows, images, videos


def media_url(path):
    if path.startswith("http"):
        return path
    return url_for("static", filename=path)


def is_embeddable_video_url(url):
    return "youtube.com" in url or "youtu.be" in url or "vimeo.com" in url


def embeddable_video_src(url):
    if "youtube.com/watch?v=" in url:
        vid = url.split("watch?v=")[-1].split("&")[0]
        return f"https://www.youtube.com/embed/{vid}"
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{vid}"
    if "vimeo.com/" in url:
        vid = url.rstrip("/").split("/")[-1]
        return f"https://player.vimeo.com/video/{vid}"
    return url


app.jinja_env.globals["media_url"] = media_url
app.jinja_env.globals["is_embeddable_video_url"] = is_embeddable_video_url
app.jinja_env.globals["embeddable_video_src"] = embeddable_video_src


def compute_shipping(country, subtotal):
    rule = query_db("SELECT * FROM shipping_rules WHERE country=?", (country,), one=True)
    if not rule:
        rule = query_db("SELECT * FROM shipping_rules WHERE country='Other'", one=True)
    if not rule:
        return 0.0, 100.0
    if subtotal >= rule["free_shipping_threshold"]:
        return 0.0, rule["free_shipping_threshold"]
    return rule["standard_price"], rule["free_shipping_threshold"]


def cart_details():
    cart = session.get("cart", [])
    items = []
    subtotal = 0.0
    for entry in cart:
        product = query_db("SELECT * FROM products WHERE id=?", (entry["product_id"],), one=True)
        if not product:
            continue
        line_total = product["price"] * entry["qty"]
        subtotal += line_total
        items.append({
            "product": product,
            "size_code": entry["size_code"],
            "qty": entry["qty"],
            "line_total": line_total,
        })
    return items, subtotal


# --------------------------------------------------------------- public UI

@app.route("/")
def index():
    new_arrivals = query_db(
        "SELECT * FROM products WHERE active=1 AND is_new_arrival=1 ORDER BY created_at DESC LIMIT 8"
    )
    best_sellers = query_db(
        "SELECT * FROM products WHERE active=1 AND is_best_seller=1 ORDER BY created_at DESC LIMIT 8"
    )
    featured = query_db(
        "SELECT * FROM products WHERE active=1 AND is_featured=1 ORDER BY created_at DESC LIMIT 6"
    )
    categories = query_db("SELECT * FROM categories ORDER BY display_order")
    category_previews = {}
    for cat in categories:
        prods = query_db(
            "SELECT * FROM products WHERE active=1 AND category_id=? ORDER BY created_at DESC LIMIT 4",
            (cat["id"],),
        )
        if prods:
            category_previews[cat["slug"]] = prods
    reviews = query_db(
        "SELECT reviews.*, products.name as product_name, products.slug as product_slug "
        "FROM reviews JOIN products ON products.id = reviews.product_id "
        "ORDER BY reviews.id DESC LIMIT 6"
    )
    instagram_posts = query_db("SELECT * FROM instagram_posts ORDER BY sort_order LIMIT 8")
    seasonal = query_db(
        "SELECT * FROM products WHERE active=1 AND season IS NOT NULL AND season != '' ORDER BY created_at DESC LIMIT 6"
    )
    return render_template(
        "index.html",
        new_arrivals=new_arrivals,
        best_sellers=best_sellers,
        featured=featured,
        categories=categories,
        category_previews=category_previews,
        reviews=reviews,
        instagram_posts=instagram_posts,
        seasonal=seasonal,
    )


@app.route("/wishlist/toggle", methods=["POST"])
def wishlist_toggle():
    product_id = int(request.form["product_id"])
    wishlist = session.get("wishlist", [])
    product = query_db("SELECT name FROM products WHERE id=?", (product_id,), one=True)
    if product_id in wishlist:
        wishlist.remove(product_id)
        if product:
            flash(f"Removed {product['name']} from your wishlist.", "info")
    else:
        wishlist.append(product_id)
        if product:
            flash(f"Added {product['name']} to your wishlist.", "success")
    session["wishlist"] = wishlist
    return redirect(request.referrer or url_for("index"))


@app.route("/wishlist")
def wishlist_page():
    wishlist = session.get("wishlist", [])
    products = []
    if wishlist:
        placeholders = ",".join("?" * len(wishlist))
        products = query_db(
            f"SELECT * FROM products WHERE id IN ({placeholders}) AND active=1", tuple(wishlist)
        )
    return render_template("wishlist.html", products=products)


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    products = []
    if q:
        like = f"%{q}%"
        products = query_db(
            "SELECT * FROM products WHERE active=1 AND "
            "(name LIKE ? OR description LIKE ? OR fabric LIKE ?) "
            "ORDER BY created_at DESC",
            (like, like, like),
        )
    return render_template("search_results.html", query=q, products=products)


@app.route("/category/<slug>")
def category_page(slug):
    category = query_db("SELECT * FROM categories WHERE slug=?", (slug,), one=True)
    if not category:
        abort(404)
    sort = request.args.get("sort", "newest")
    order_sql = "created_at DESC"
    if sort == "price_low":
        order_sql = "price ASC"
    elif sort == "price_high":
        order_sql = "price DESC"
    if slug == "new-arrivals":
        # "New Arrivals" is a cross-cutting tag as well as a category: show any
        # product flagged as a new arrival, regardless of its main category,
        # in addition to anything explicitly filed under this category.
        products = query_db(
            f"SELECT * FROM products WHERE active=1 AND (category_id=? OR is_new_arrival=1) ORDER BY {order_sql}",
            (category["id"],),
        )
    else:
        products = query_db(
            f"SELECT * FROM products WHERE active=1 AND category_id=? ORDER BY {order_sql}",
            (category["id"],),
        )
    return render_template("category.html", category=category, products=products, sort=sort)


@app.route("/product/<slug>")
def product_detail(slug):
    product, sizes = get_product_with_sizes(slug=slug)
    if not product:
        abort(404)
    size_guide = query_db("SELECT * FROM size_guides WHERE product_id=?", (product["id"],), one=True)
    guide_rows = []
    if size_guide:
        guide_rows = query_db(
            "SELECT * FROM size_guide_rows WHERE size_guide_id=?", (size_guide["id"],)
        )
        guide_rows = sorted(
            guide_rows, key=lambda r: SIZE_ORDER.index(r["size_code"]) if r["size_code"] in SIZE_ORDER else 99
        )
    reviews = query_db(
        "SELECT * FROM reviews WHERE product_id=? ORDER BY id DESC", (product["id"],)
    )
    avg_rating = None
    if reviews:
        avg_rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1)
    related = query_db(
        "SELECT * FROM products WHERE active=1 AND category_id=? AND id != ? LIMIT 4",
        (product["category_id"], product["id"]),
    )
    return_policy = query_db("SELECT * FROM return_policy LIMIT 1", one=True)
    colors = get_product_colors(product["id"])
    media_rows, media_images, media_videos = get_product_media(product["id"])
    return render_template(
        "product.html",
        product=product,
        sizes=sizes,
        size_guide=size_guide,
        guide_rows=guide_rows,
        reviews=reviews,
        avg_rating=avg_rating,
        related=related,
        return_policy=return_policy,
        colors=colors,
        media=media_rows,
    )


@app.route("/cart/add", methods=["POST"])
def cart_add():
    product_id = int(request.form["product_id"])
    size_code = request.form["size_code"]
    qty = max(1, int(request.form.get("qty", 1)))
    product, sizes = get_product_with_sizes(product_id=product_id)
    valid = {s["size_code"] for s in sizes if s["quantity"] > 0}
    if size_code not in valid:
        flash("Please select an available size.", "error")
        return redirect(request.referrer or url_for("index"))
    cart = session.get("cart", [])
    for item in cart:
        if item["product_id"] == product_id and item["size_code"] == size_code:
            item["qty"] += qty
            break
    else:
        cart.append({"product_id": product_id, "size_code": size_code, "qty": qty})
    session["cart"] = cart
    flash(f"Added {product['name']} ({size_code}) to your bag.", "success")
    return redirect(url_for("cart_page"))


@app.route("/cart")
def cart_page():
    items, subtotal = cart_details()
    return render_template("cart.html", items=items, subtotal=subtotal)


@app.route("/cart/update", methods=["POST"])
def cart_update():
    idx = int(request.form["index"])
    qty = int(request.form.get("qty", 1))
    cart = session.get("cart", [])
    if 0 <= idx < len(cart):
        if qty <= 0:
            cart.pop(idx)
        else:
            cart[idx]["qty"] = qty
    session["cart"] = cart
    return redirect(url_for("cart_page"))


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    idx = int(request.form["index"])
    cart = session.get("cart", [])
    if 0 <= idx < len(cart):
        cart.pop(idx)
    session["cart"] = cart
    return redirect(url_for("cart_page"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, subtotal = cart_details()
    if not items:
        flash("Your bag is empty.", "info")
        return redirect(url_for("index"))
    countries = query_db("SELECT country FROM shipping_rules ORDER BY country")
    return_policy = query_db("SELECT * FROM return_policy LIMIT 1", one=True)
    country = request.values.get("country", "United States")
    shipping_cost, free_threshold = compute_shipping(country, subtotal)
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        postal_code = request.form.get("postal_code", "").strip()
        if not (full_name and address and city):
            flash("Please complete your shipping details.", "error")
            return render_template(
                "checkout.html", items=items, subtotal=subtotal, countries=countries,
                shipping_cost=shipping_cost, free_threshold=free_threshold,
                selected_country=country, return_policy=return_policy,
            )
        total = subtotal + shipping_cost
        order_id = execute_db(
            "INSERT INTO orders (user_id, status, subtotal, shipping_cost, total, country, "
            "full_name, address, city, postal_code) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (session.get("user_id"), "Placed", subtotal, shipping_cost, total, country,
             full_name, address, city, postal_code),
        )
        for item in items:
            execute_db(
                "INSERT INTO order_items (order_id, product_id, product_name, size_code, quantity, price) "
                "VALUES (?,?,?,?,?,?)",
                (order_id, item["product"]["id"], item["product"]["name"], item["size_code"],
                 item["qty"], item["product"]["price"]),
            )
            execute_db(
                "UPDATE product_sizes SET quantity = MAX(0, quantity - ?) WHERE product_id=? AND size_code=?",
                (item["qty"], item["product"]["id"], item["size_code"]),
            )
        session["cart"] = []
        return redirect(url_for("order_confirmation", order_id=order_id))
    return render_template(
        "checkout.html", items=items, subtotal=subtotal, countries=countries,
        shipping_cost=shipping_cost, free_threshold=free_threshold,
        selected_country=country, return_policy=return_policy,
    )


@app.route("/order/confirmation/<int:order_id>")
def order_confirmation(order_id):
    order = query_db("SELECT * FROM orders WHERE id=?", (order_id,), one=True)
    if not order:
        abort(404)
    order_items = query_db("SELECT * FROM order_items WHERE order_id=?", (order_id,))
    return render_template("order_confirmation.html", order=order, order_items=order_items)


@app.route("/newsletter/subscribe", methods=["POST"])
def newsletter_subscribe():
    email = request.form.get("email", "").strip()
    if email:
        try:
            execute_db("INSERT INTO newsletter_subscribers (email) VALUES (?)", (email,))
            flash("Welcome to the Roz Boutique garden — check your inbox soon.", "success")
        except sqlite3.IntegrityError:
            flash("You're already on our list!", "info")
    return redirect(request.referrer or url_for("index"))

# ------------------------------------------------------------ account area

@app.route("/account/register", methods=["GET", "POST"])
def account_register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not (name and email and password):
            flash("Please fill in all fields.", "error")
            return render_template("account/register.html")
        existing = query_db("SELECT id FROM users WHERE email=?", (email,), one=True)
        if existing:
            flash("An account with this email already exists.", "error")
            return render_template("account/register.html")
        uid = execute_db(
            "INSERT INTO users (name, email, password_hash) VALUES (?,?,?)",
            (name, email, generate_password_hash(password)),
        )
        session["user_id"] = uid
        flash("Welcome to Roz Boutique.", "success")
        return redirect(url_for("account_dashboard"))
    return render_template("account/register.html")


@app.route("/account/login", methods=["GET", "POST"])
def account_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query_db("SELECT * FROM users WHERE email=?", (email,), one=True)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash("Signed in successfully.", "success")
            nxt = request.args.get("next")
            return redirect(nxt or url_for("account_dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("account/login.html")


@app.route("/account/logout")
def account_logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))


@app.route("/account/dashboard")
def account_dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("account_login", next=url_for("account_dashboard")))
    orders = query_db(
        "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user["id"],)
    )
    orders_with_items = []
    for order in orders:
        items = query_db("SELECT * FROM order_items WHERE order_id=?", (order["id"],))
        return_map = {}
        for item in items:
            rr = query_db(
                "SELECT * FROM return_requests WHERE order_item_id=?", (item["id"],), one=True
            )
            return_map[item["id"]] = rr
        orders_with_items.append({"order": order, "order_items": items, "returns": return_map})
    return_policy = query_db("SELECT * FROM return_policy LIMIT 1", one=True)
    return render_template(
        "account/dashboard.html", orders_with_items=orders_with_items, return_policy=return_policy
    )


@app.route("/account/return-request", methods=["POST"])
def account_return_request():
    user = current_user()
    if not user:
        return redirect(url_for("account_login"))
    order_item_id = int(request.form["order_item_id"])
    reason = request.form.get("reason", "").strip()
    item = query_db("SELECT * FROM order_items WHERE id=?", (order_item_id,), one=True)
    order = query_db("SELECT * FROM orders WHERE id=?", (item["order_id"],), one=True) if item else None
    if not item or not order or order["user_id"] != user["id"]:
        abort(403)
    policy = query_db("SELECT * FROM return_policy LIMIT 1", one=True)
    ordered_at = datetime.strptime(order["created_at"], "%Y-%m-%d %H:%M:%S")
    deadline = ordered_at + timedelta(days=policy["window_days"])
    if datetime.now() > deadline:
        flash(f"Sorry, the {policy['window_days']}-day return window for this order has passed.", "error")
        return redirect(url_for("account_dashboard"))
    existing = query_db(
        "SELECT id FROM return_requests WHERE order_item_id=?", (order_item_id,), one=True
    )
    if existing:
        flash("A return request already exists for this item.", "info")
        return redirect(url_for("account_dashboard"))
    execute_db(
        "INSERT INTO return_requests (order_item_id, user_id, reason, status) VALUES (?,?,?,'Pending')",
        (order_item_id, user["id"], reason),
    )
    flash("Return request submitted for admin review.", "success")
    return redirect(url_for("account_dashboard"))


@app.route("/policies")
def policies():
    return_policy = query_db("SELECT * FROM return_policy LIMIT 1", one=True)
    shipping_rules = query_db("SELECT * FROM shipping_rules ORDER BY country")
    return render_template("policies.html", return_policy=return_policy, shipping_rules=shipping_rules)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        if not (name and email and message):
            flash("Please fill in your name, email, and message.", "error")
            return render_template("contact.html", form_data=request.form)
        execute_db(
            "INSERT INTO contact_messages (name, email, subject, message) VALUES (?,?,?,?)",
            (name, email, subject, message),
        )
        flash("Thank you — your message has been sent. We'll get back to you soon.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html", form_data={})


# ---------------------------------------------------------------- ADMIN --

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        admin = query_db("SELECT * FROM admin_users WHERE email=?", (email,), one=True)
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "products": query_db("SELECT COUNT(*) c FROM products", one=True)["c"],
        "orders": query_db("SELECT COUNT(*) c FROM orders", one=True)["c"],
        "pending_returns": query_db(
            "SELECT COUNT(*) c FROM return_requests WHERE status='Pending'", one=True
        )["c"],
        "revenue": query_db("SELECT COALESCE(SUM(total),0) t FROM orders", one=True)["t"],
    }
    recent_orders = query_db("SELECT * FROM orders ORDER BY created_at DESC LIMIT 6")
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent_orders)


@app.route("/admin/products")
@admin_required
def admin_products():
    products = query_db(
        "SELECT products.*, categories.name as category_name FROM products "
        "JOIN categories ON categories.id = products.category_id ORDER BY products.created_at DESC"
    )
    return render_template("admin/products.html", products=products)


@app.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    categories = query_db("SELECT * FROM categories ORDER BY display_order")
    if request.method == "POST":
        return _save_product(categories)
    return render_template(
        "admin/product_form.html", product=None, categories=categories, sizes_map={},
        colors_text="", bottom_types=BOTTOM_TYPES, media=[],
    )


@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_edit(product_id):
    categories = query_db("SELECT * FROM categories ORDER BY display_order")
    product = query_db("SELECT * FROM products WHERE id=?", (product_id,), one=True)
    if not product:
        abort(404)
    if request.method == "POST":
        return _save_product(categories, product_id=product_id)
    existing_sizes = query_db("SELECT * FROM product_sizes WHERE product_id=?", (product_id,))
    sizes_map = {s["size_code"]: s["quantity"] for s in existing_sizes}
    existing_colors = get_product_colors(product_id)
    colors_text = ", ".join(c["color_name"] for c in existing_colors)
    media, _, _ = get_product_media(product_id)
    return render_template(
        "admin/product_form.html", product=product, categories=categories, sizes_map=sizes_map,
        colors_text=colors_text, bottom_types=BOTTOM_TYPES, media=media,
    )


def _save_product(categories, product_id=None):
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
    category_id = int(request.form["category_id"])
    price = float(request.form.get("price", 0) or 0)
    compare_at_price = request.form.get("compare_at_price") or None
    description = request.form.get("description", "").strip()
    fabric = request.form.get("fabric", "").strip()
    swatch = int(request.form.get("swatch", 0) or 0)
    season = request.form.get("season", "").strip()
    bottom_type = request.form.get("bottom_type", "").strip() or None
    is_best_seller = 1 if request.form.get("is_best_seller") else 0
    is_featured = 1 if request.form.get("is_featured") else 0
    is_new_arrival = 1 if request.form.get("is_new_arrival") else 0
    active = 1 if request.form.get("active") else 0

    if not (name and slug and price):
        flash("Name, slug and price are required.", "error")
        return redirect(request.referrer)

    existing_product = query_db("SELECT image_path FROM products WHERE id=?", (product_id,), one=True) if product_id else None
    image_path = existing_product["image_path"] if existing_product else None

    if product_id:
        execute_db(
            "UPDATE products SET name=?, slug=?, category_id=?, price=?, compare_at_price=?, "
            "description=?, fabric=?, swatch=?, image_path=?, bottom_type=?, season=?, is_best_seller=?, is_featured=?, "
            "is_new_arrival=?, active=? WHERE id=?",
            (name, slug, category_id, price, compare_at_price, description, fabric, swatch, image_path,
             bottom_type, season, is_best_seller, is_featured, is_new_arrival, active, product_id),
        )
    else:
        product_id = execute_db(
            "INSERT INTO products (name, slug, category_id, price, compare_at_price, description, "
            "fabric, swatch, image_path, bottom_type, season, is_best_seller, is_featured, is_new_arrival, active) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (name, slug, category_id, price, compare_at_price, description, fabric, swatch, image_path,
             bottom_type, season, is_best_seller, is_featured, is_new_arrival, active),
        )

    execute_db("DELETE FROM product_sizes WHERE product_id=?", (product_id,))
    for size_code in SIZE_ORDER:
        if request.form.get(f"size_{size_code}"):
            qty = int(request.form.get(f"qty_{size_code}", 0) or 0)
            execute_db(
                "INSERT INTO product_sizes (product_id, size_code, quantity) VALUES (?,?,?)",
                (product_id, size_code, qty),
            )

    # Free-text colors: comma-separated, deduped, hex auto-generated per name
    execute_db("DELETE FROM product_colors WHERE product_id=?", (product_id,))
    colors_text = request.form.get("colors_text", "").strip()
    seen = set()
    for raw in colors_text.split(","):
        color_name = raw.strip()
        if not color_name:
            continue
        key = color_name.lower()
        if key in seen:
            continue
        seen.add(key)
        execute_db(
            "INSERT INTO product_colors (product_id, color_name, hex) VALUES (?,?,?)",
            (product_id, color_name, color_name_to_hex(color_name)),
        )

    # Media gallery: delete selected, then append new image uploads and video
    delete_ids = request.form.getlist("delete_media")
    for mid in delete_ids:
        execute_db("DELETE FROM product_media WHERE id=? AND product_id=?", (mid, product_id))

    existing_max = query_db(
        "SELECT COALESCE(MAX(sort_order), -1) m FROM product_media WHERE product_id=?", (product_id,), one=True
    )["m"]
    next_order = existing_max + 1

    image_files = request.files.getlist("image_files")
    for f in image_files:
        if f and f.filename:
            filename = secure_filename(f"product_{product_id}_{next_order}_{f.filename}")
            f.save(os.path.join(UPLOAD_DIR, filename))
            execute_db(
                "INSERT INTO product_media (product_id, media_type, path, sort_order) VALUES (?,?,?,?)",
                (product_id, "image", f"uploads/{filename}", next_order),
            )
            next_order += 1

    image_urls_raw = request.form.get("image_urls", "").strip()
    if image_urls_raw:
        for url in image_urls_raw.splitlines():
            url = url.strip()
            if url:
                execute_db(
                    "INSERT INTO product_media (product_id, media_type, path, sort_order) VALUES (?,?,?,?)",
                    (product_id, "image", url, next_order),
                )
                next_order += 1

    video_file = request.files.get("video_file")
    if video_file and video_file.filename:
        filename = secure_filename(f"product_{product_id}_video_{video_file.filename}")
        video_file.save(os.path.join(UPLOAD_DIR, filename))
        execute_db(
            "INSERT INTO product_media (product_id, media_type, path, sort_order) VALUES (?,?,?,?)",
            (product_id, "video", f"uploads/{filename}", next_order),
        )
        next_order += 1
    else:
        video_url = request.form.get("video_url", "").strip()
        if video_url:
            execute_db(
                "INSERT INTO product_media (product_id, media_type, path, sort_order) VALUES (?,?,?,?)",
                (product_id, "video", video_url, next_order),
            )
            next_order += 1

    # Auto-set the cover image (used on listing cards) to the first gallery image
    first_image = query_db(
        "SELECT path FROM product_media WHERE product_id=? AND media_type='image' ORDER BY sort_order, id LIMIT 1",
        (product_id,), one=True,
    )
    execute_db(
        "UPDATE products SET image_path=? WHERE id=?",
        (first_image["path"] if first_image else None, product_id),
    )

    flash("Product saved.", "success")
    return redirect(url_for("admin_products"))


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def admin_product_delete(product_id):
    execute_db("DELETE FROM products WHERE id=?", (product_id,))
    flash("Product deleted.", "success")
    return redirect(url_for("admin_products"))


@app.route("/admin/products/<int:product_id>/size-guide", methods=["GET", "POST"])
@admin_required
def admin_size_guide(product_id):
    product = query_db("SELECT * FROM products WHERE id=?", (product_id,), one=True)
    if not product:
        abort(404)
    guide = query_db("SELECT * FROM size_guides WHERE product_id=?", (product_id,), one=True)

    if request.method == "POST":
        instructions = request.form.get("instructions", "").strip()
        unit = request.form.get("unit", "in")
        image_path = guide["image_path"] if guide else None

        file = request.files.get("image_file")
        if file and file.filename:
            filename = secure_filename(f"sizeguide_{product_id}_{file.filename}")
            file.save(os.path.join(UPLOAD_DIR, filename))
            image_path = f"uploads/{filename}"

        image_url = request.form.get("image_url", "").strip()
        if image_url:
            image_path = image_url

        if guide:
            execute_db(
                "UPDATE size_guides SET instructions=?, image_path=?, unit=? WHERE id=?",
                (instructions, image_path, unit, guide["id"]),
            )
            guide_id = guide["id"]
        else:
            guide_id = execute_db(
                "INSERT INTO size_guides (product_id, instructions, image_path, unit) VALUES (?,?,?,?)",
                (product_id, instructions, image_path, unit),
            )

        execute_db("DELETE FROM size_guide_rows WHERE size_guide_id=?", (guide_id,))
        for size_code in SIZE_ORDER:
            if request.form.get(f"row_{size_code}"):
                execute_db(
                    "INSERT INTO size_guide_rows (size_guide_id, size_code, chest, waist, hips, "
                    "length, sleeve_length, bottom_length) VALUES (?,?,?,?,?,?,?,?)",
                    (
                        guide_id, size_code,
                        request.form.get(f"chest_{size_code}") or None,
                        request.form.get(f"waist_{size_code}") or None,
                        request.form.get(f"hips_{size_code}") or None,
                        request.form.get(f"length_{size_code}") or None,
                        request.form.get(f"sleeve_{size_code}") or None,
                        request.form.get(f"bottom_{size_code}") or None,
                    ),
                )
        flash("Size guide saved.", "success")
        return redirect(url_for("admin_products"))

    rows = []
    if guide:
        rows = query_db("SELECT * FROM size_guide_rows WHERE size_guide_id=?", (guide["id"],))
    rows_map = {r["size_code"]: r for r in rows}
    return render_template(
        "admin/size_guide_form.html", product=product, guide=guide, rows_map=rows_map, sizes=SIZE_ORDER
    )


@app.route("/admin/shipping", methods=["GET", "POST"])
@admin_required
def admin_shipping():
    if request.method == "POST":
        country = request.form.get("country", "").strip()
        standard_price = float(request.form.get("standard_price", 0) or 0)
        free_threshold = float(request.form.get("free_shipping_threshold", 100) or 100)
        if country:
            existing = query_db("SELECT id FROM shipping_rules WHERE country=?", (country,), one=True)
            if existing:
                execute_db(
                    "UPDATE shipping_rules SET standard_price=?, free_shipping_threshold=? WHERE country=?",
                    (standard_price, free_threshold, country),
                )
            else:
                execute_db(
                    "INSERT INTO shipping_rules (country, standard_price, free_shipping_threshold) VALUES (?,?,?)",
                    (country, standard_price, free_threshold),
                )
            flash("Shipping rule saved.", "success")
        return redirect(url_for("admin_shipping"))
    rules = query_db("SELECT * FROM shipping_rules ORDER BY country")
    return render_template("admin/shipping.html", rules=rules)


@app.route("/admin/shipping/<int:rule_id>/delete", methods=["POST"])
@admin_required
def admin_shipping_delete(rule_id):
    execute_db("DELETE FROM shipping_rules WHERE id=?", (rule_id,))
    return redirect(url_for("admin_shipping"))


@app.route("/admin/returns/settings", methods=["GET", "POST"])
@admin_required
def admin_return_settings():
    policy = query_db("SELECT * FROM return_policy LIMIT 1", one=True)
    if request.method == "POST":
        window_days = int(request.form.get("window_days", 14))
        return_fee = float(request.form.get("return_fee", 0) or 0)
        eligibility_rules = request.form.get("eligibility_rules", "").strip()
        refund_method = request.form.get("refund_method", "").strip()
        if policy:
            execute_db(
                "UPDATE return_policy SET window_days=?, return_fee=?, eligibility_rules=?, refund_method=? WHERE id=?",
                (window_days, return_fee, eligibility_rules, refund_method, policy["id"]),
            )
        else:
            execute_db(
                "INSERT INTO return_policy (window_days, return_fee, eligibility_rules, refund_method) VALUES (?,?,?,?)",
                (window_days, return_fee, eligibility_rules, refund_method),
            )
        flash("Return policy updated.", "success")
        return redirect(url_for("admin_return_settings"))
    return render_template("admin/returns_settings.html", policy=policy)


@app.route("/admin/returns/requests")
@admin_required
def admin_return_requests():
    requests_rows = query_db(
        "SELECT return_requests.*, order_items.product_name, order_items.size_code, "
        "order_items.order_id, users.name as customer_name, users.email as customer_email "
        "FROM return_requests "
        "JOIN order_items ON order_items.id = return_requests.order_item_id "
        "JOIN users ON users.id = return_requests.user_id "
        "ORDER BY return_requests.requested_at DESC"
    )
    return render_template("admin/return_requests.html", requests_rows=requests_rows)


@app.route("/admin/returns/requests/<int:req_id>/update", methods=["POST"])
@admin_required
def admin_return_request_update(req_id):
    status = request.form.get("status")
    admin_note = request.form.get("admin_note", "").strip()
    execute_db(
        "UPDATE return_requests SET status=?, admin_note=? WHERE id=?", (status, admin_note, req_id)
    )
    flash("Return request updated.", "success")
    return redirect(url_for("admin_return_requests"))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    orders = query_db("SELECT * FROM orders ORDER BY created_at DESC")
    return render_template("admin/orders.html", orders=orders)


@app.route("/admin/messages")
@admin_required
def admin_messages():
    messages = query_db("SELECT * FROM contact_messages ORDER BY created_at DESC")
    return render_template("admin/messages.html", messages=messages)


@app.route("/admin/messages/<int:message_id>/read", methods=["POST"])
@admin_required
def admin_message_mark_read(message_id):
    execute_db("UPDATE contact_messages SET is_read=1 WHERE id=?", (message_id,))
    return redirect(url_for("admin_messages"))


@app.route("/admin/messages/<int:message_id>/delete", methods=["POST"])
@admin_required
def admin_message_delete(message_id):
    execute_db("DELETE FROM contact_messages WHERE id=?", (message_id,))
    flash("Message deleted.", "success")
    return redirect(url_for("admin_messages"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
