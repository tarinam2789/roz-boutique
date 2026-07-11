-- Roz — Schema

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    tagline TEXT,
    display_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    category_id INTEGER NOT NULL,
    price REAL NOT NULL,
    compare_at_price REAL,
    description TEXT,
    fabric TEXT,
    swatch INTEGER DEFAULT 0,
    image_path TEXT,
    bottom_type TEXT,
    is_best_seller INTEGER DEFAULT 0,
    is_featured INTEGER DEFAULT 0,
    is_new_arrival INTEGER DEFAULT 0,
    season TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS product_colors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    color_name TEXT NOT NULL,
    hex TEXT NOT NULL,
    UNIQUE(product_id, color_name),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS product_media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    media_type TEXT NOT NULL DEFAULT 'image',
    path TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS product_sizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    size_code TEXT NOT NULL,
    quantity INTEGER DEFAULT 0,
    UNIQUE(product_id, size_code),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS size_guides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE NOT NULL,
    instructions TEXT,
    image_path TEXT,
    unit TEXT DEFAULT 'in',
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS size_guide_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    size_guide_id INTEGER NOT NULL,
    size_code TEXT NOT NULL,
    chest REAL,
    waist REAL,
    hips REAL,
    length REAL,
    sleeve_length REAL,
    shoulder_width REAL,
    bottom_length REAL,
    FOREIGN KEY (size_guide_id) REFERENCES size_guides(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shipping_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT UNIQUE NOT NULL,
    currency TEXT DEFAULT 'USD',
    standard_price REAL NOT NULL,
    free_shipping_threshold REAL NOT NULL DEFAULT 100
);

CREATE TABLE IF NOT EXISTS return_policy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_days INTEGER DEFAULT 14,
    return_fee REAL DEFAULT 12,
    eligibility_rules TEXT,
    refund_method TEXT DEFAULT 'Original payment method (store credit optional)'
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    status TEXT DEFAULT 'Placed',
    subtotal REAL NOT NULL,
    shipping_cost REAL NOT NULL,
    total REAL NOT NULL,
    country TEXT,
    full_name TEXT,
    address TEXT,
    city TEXT,
    postal_code TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    size_code TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS return_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'Pending',
    admin_note TEXT,
    requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_item_id) REFERENCES order_items(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT,
    message TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    location TEXT,
    rating INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS instagram_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caption TEXT,
    swatch INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);
