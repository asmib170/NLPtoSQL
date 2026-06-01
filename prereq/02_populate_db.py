"""Populate DemoECommerceDB with realistic sample data."""

import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "DemoECommerceDB.db")

random.seed(42)


def random_date(start_days_ago=365, end_days_ago=0):
    days = random.randint(end_days_ago, start_days_ago)
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


def populate():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ------------------------------------------------------------------ #
    # CATEGORIES
    # ------------------------------------------------------------------ #
    categories = [
        (1, "Electronics",      None),
        (2, "Computers",        1),
        (3, "Smartphones",      1),
        (4, "Audio",            1),
        (5, "Clothing",         None),
        (6, "Men's Clothing",   5),
        (7, "Women's Clothing", 5),
        (8, "Home & Kitchen",   None),
        (9, "Cookware",         8),
        (10,"Furniture",        8),
        (11,"Books",            None),
        (12,"Sports & Outdoors",None),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO categories (category_id, name, parent_id) VALUES (?,?,?)",
        categories
    )

    # ------------------------------------------------------------------ #
    # PRODUCTS
    # ------------------------------------------------------------------ #
    products = [
        # (category_id, name, description, sku, price, stock_qty, weight_kg)
        (2, "Dell XPS 15 Laptop",         "15.6\" 4K OLED, Intel i9, 32GB RAM, 1TB SSD",       "DELL-XPS15-001",  1799.99, 45,  2.1),
        (2, "Apple MacBook Pro 14\"",      "M3 Pro chip, 18GB RAM, 512GB SSD, Space Gray",      "APPL-MBP14-001",  1999.00, 30,  1.6),
        (2, "Logitech MX Keys Keyboard",  "Wireless, backlit, multi-device",                   "LOGI-MXKEYS-001",   109.99, 120, 0.8),
        (2, "LG 27\" 4K Monitor",         "IPS panel, USB-C, HDR400",                          "LG-27UK850-001",   449.99, 60,  5.5),
        (3, "iPhone 15 Pro",              "256GB, Titanium, A17 Pro chip",                     "APPL-IP15P-256",  1199.00, 80,  0.2),
        (3, "Samsung Galaxy S24 Ultra",   "512GB, Phantom Black, 200MP camera",                "SAMS-S24U-512",   1299.99, 55,  0.2),
        (3, "Google Pixel 8",             "128GB, Obsidian, 7 years of updates",               "GOOG-PX8-128",     699.00, 70,  0.2),
        (4, "Sony WH-1000XM5",            "Wireless noise-cancelling headphones",              "SONY-WH1000-001",  349.99, 90,  0.3),
        (4, "Apple AirPods Pro 2nd Gen",  "Active noise cancellation, MagSafe case",           "APPL-APP2-001",    249.00, 150, 0.1),
        (4, "Bose QuietComfort 45",       "Wireless Bluetooth headphones, 24hr battery",       "BOSE-QC45-001",    279.99, 75,  0.2),
        (6, "Levi's 501 Original Jeans",  "Classic straight fit, medium wash, size 32x32",     "LEVI-501-3232",     69.99, 200, 0.6),
        (6, "Nike Dri-FIT T-Shirt",       "Moisture-wicking, crew neck, size L",               "NIKE-DFIT-L",       34.99, 300, 0.2),
        (7, "Zara Floral Midi Dress",     "V-neck, floral print, size M",                      "ZARA-FMD-M",        59.99, 180, 0.3),
        (7, "Adidas Ultraboost 22 Women", "Running shoes, size 8, Cloud White",                "ADID-UB22-W8",     189.99, 95,  0.5),
        (9, "Instant Pot Duo 7-in-1",     "6 quart, pressure cooker, slow cooker, rice cooker","INST-DUO6-001",     99.99, 110, 5.4),
        (9, "Le Creuset Dutch Oven 5.5qt","Enameled cast iron, Flame color",                   "LECR-DO55-001",    399.99, 40,  4.1),
        (10,"IKEA KALLAX Shelf Unit",     "4x4 grid, white, 147x147cm",                        "IKEA-KAL44-001",   219.99, 25,  50.0),
        (10,"Herman Miller Aeron Chair",  "Ergonomic office chair, size B, graphite",          "HERM-AERN-B",     1495.00, 15,  20.0),
        (11,"Clean Code by Robert Martin","Paperback, 431 pages",                              "BOOK-CLNCD-001",    35.99, 500, 0.5),
        (12,"Hydro Flask 32oz Water Bottle","Stainless steel, vacuum insulated, Pacific",      "HYDR-32OZ-PAC",     44.95, 250, 0.4),
    ]
    cur.executemany("""
        INSERT OR IGNORE INTO products
            (category_id, name, description, sku, price, stock_qty, weight_kg)
        VALUES (?,?,?,?,?,?,?)
    """, products)

    # ------------------------------------------------------------------ #
    # USERS
    # ------------------------------------------------------------------ #
    users = [
        ("James",   "Wilson",   "james.wilson@email.com",   "555-0101", "hash_jw1"),
        ("Sarah",   "Johnson",  "sarah.j@email.com",        "555-0102", "hash_sj2"),
        ("Michael", "Brown",    "m.brown@email.com",        "555-0103", "hash_mb3"),
        ("Emily",   "Davis",    "emily.davis@email.com",    "555-0104", "hash_ed4"),
        ("Robert",  "Martinez", "rob.martinez@email.com",   "555-0105", "hash_rm5"),
        ("Jessica", "Taylor",   "jess.taylor@email.com",    "555-0106", "hash_jt6"),
        ("David",   "Anderson", "d.anderson@email.com",     "555-0107", "hash_da7"),
        ("Ashley",  "Thomas",   "ashley.t@email.com",       "555-0108", "hash_at8"),
        ("Daniel",  "Jackson",  "dan.jackson@email.com",    "555-0109", "hash_dj9"),
        ("Amanda",  "White",    "amanda.white@email.com",   "555-0110", "hash_aw10"),
        ("Chris",   "Harris",   "chris.harris@email.com",   "555-0111", "hash_ch11"),
        ("Megan",   "Clark",    "megan.clark@email.com",    "555-0112", "hash_mc12"),
        ("Kevin",   "Lewis",    "kevin.lewis@email.com",    "555-0113", "hash_kl13"),
        ("Lauren",  "Robinson", "lauren.r@email.com",       "555-0114", "hash_lr14"),
        ("Brian",   "Walker",   "brian.walker@email.com",   "555-0115", "hash_bw15"),
    ]
    for u in users:
        cur.execute("""
            INSERT OR IGNORE INTO users (first_name, last_name, email, phone, password_hash, created_at)
            VALUES (?,?,?,?,?,?)
        """, (*u, random_date(730, 180)))

    # ------------------------------------------------------------------ #
    # ADDRESSES
    # ------------------------------------------------------------------ #
    streets = [
        "123 Maple St", "456 Oak Ave", "789 Pine Rd", "321 Elm Blvd",
        "654 Cedar Ln", "987 Birch Dr", "111 Walnut Way", "222 Spruce Ct",
        "333 Ash Pl",   "444 Willow Ter","555 Poplar St", "666 Hickory Ave",
        "777 Chestnut Rd","888 Sycamore Blvd","999 Magnolia Ln"
    ]
    cities_states = [
        ("New York",     "NY", "10001"), ("Los Angeles",  "CA", "90001"),
        ("Chicago",      "IL", "60601"), ("Houston",      "TX", "77001"),
        ("Phoenix",      "AZ", "85001"), ("Philadelphia", "PA", "19101"),
        ("San Antonio",  "TX", "78201"), ("San Diego",    "CA", "92101"),
        ("Dallas",       "TX", "75201"), ("San Jose",     "CA", "95101"),
        ("Austin",       "TX", "73301"), ("Jacksonville", "FL", "32099"),
        ("Fort Worth",   "TX", "76101"), ("Columbus",     "OH", "43085"),
        ("Charlotte",    "NC", "28201"),
    ]
    cur.execute("SELECT user_id FROM users")
    user_ids = [r[0] for r in cur.fetchall()]
    for i, uid in enumerate(user_ids):
        city, state, zipcode = cities_states[i % len(cities_states)]
        cur.execute("""
            INSERT INTO addresses (user_id, label, street, city, state, zip_code, is_default)
            VALUES (?,?,?,?,?,?,1)
        """, (uid, "Home", streets[i % len(streets)], city, state, zipcode))

    # ------------------------------------------------------------------ #
    # COUPONS
    # ------------------------------------------------------------------ #
    coupons = [
        ("SAVE10",   "percent", 10,  0,    1000, 0, "2026-12-31 23:59:59", 1),
        ("SAVE20",   "percent", 20,  50,   500,  0, "2026-06-30 23:59:59", 1),
        ("FLAT15",   "fixed",   15,  75,   200,  0, "2026-09-30 23:59:59", 1),
        ("WELCOME5", "percent",  5,  0,    None, 0, None,                  1),
        ("SUMMER25", "percent", 25,  100,  300,  0, "2026-08-31 23:59:59", 1),
    ]
    cur.executemany("""
        INSERT OR IGNORE INTO coupons
            (code, discount_type, discount_value, min_order_value, max_uses, used_count, expires_at, is_active)
        VALUES (?,?,?,?,?,?,?,?)
    """, coupons)

    # ------------------------------------------------------------------ #
    # ORDERS + ORDER_ITEMS + SHIPPING
    # ------------------------------------------------------------------ #
    cur.execute("SELECT product_id, price FROM products")
    product_prices = {r[0]: r[1] for r in cur.fetchall()}
    product_ids = list(product_prices.keys())

    cur.execute("SELECT address_id, user_id FROM addresses")
    addr_rows = cur.fetchall()
    addr_by_user = {r[1]: r[0] for r in addr_rows}

    carriers = ["FedEx", "UPS", "USPS", "DHL"]
    service_levels = ["standard", "express", "overnight"]
    payment_methods = ["credit_card", "paypal", "bank_transfer"]
    order_statuses = ["delivered", "delivered", "delivered", "shipped", "processing", "cancelled"]
    shipping_statuses = {
        "delivered":  "delivered",
        "shipped":    "in_transit",
        "processing": "label_created",
        "cancelled":  "pending",
        "pending":    "pending",
    }

    tracking_seq = 1000000

    for uid in user_ids:
        num_orders = random.randint(1, 5)
        for _ in range(num_orders):
            order_date = random_date(300, 1)
            status = random.choice(order_statuses)
            payment = random.choice(payment_methods)
            pay_status = "paid" if status not in ("cancelled",) else random.choice(["paid", "failed"])

            # pick 1-4 random products
            items = []
            chosen = random.sample(product_ids, k=random.randint(1, 4))
            subtotal = 0.0
            for pid in chosen:
                qty = random.randint(1, 3)
                unit_price = product_prices[pid]
                line_total = round(qty * unit_price, 2)
                subtotal += line_total
                items.append((pid, qty, unit_price, line_total))

            subtotal = round(subtotal, 2)
            discount = round(subtotal * random.choice([0, 0, 0, 0.05, 0.10, 0.20]), 2)
            tax = round((subtotal - discount) * 0.08, 2)
            total = round(subtotal - discount + tax, 2)

            cur.execute("""
                INSERT INTO orders
                    (user_id, status, subtotal, discount, tax, total,
                     payment_method, payment_status, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (uid, status, subtotal, discount, tax, total,
                  payment, pay_status, order_date, order_date))
            order_id = cur.lastrowid

            for pid, qty, unit_price, line_total in items:
                cur.execute("""
                    INSERT INTO order_items
                        (order_id, product_id, quantity, unit_price, discount, line_total)
                    VALUES (?,?,?,?,?,?)
                """, (order_id, pid, qty, unit_price, 0, line_total))

            # Shipping record
            addr_id = addr_by_user.get(uid, 1)
            carrier = random.choice(carriers)
            service = random.choice(service_levels)
            ship_status = shipping_statuses.get(status, "pending")
            tracking = f"TRK{tracking_seq}" if status not in ("processing", "cancelled") else None
            tracking_seq += 1
            shipped_at = None
            delivered_at = None
            est_delivery = None
            if status in ("shipped", "delivered"):
                shipped_at = (datetime.strptime(order_date, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
                est_delivery = (datetime.strptime(order_date, "%Y-%m-%d %H:%M:%S") + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
            if status == "delivered":
                delivered_at = (datetime.strptime(order_date, "%Y-%m-%d %H:%M:%S") + timedelta(days=random.randint(3, 7))).strftime("%Y-%m-%d %H:%M:%S")

            cur.execute("""
                INSERT INTO shipping
                    (order_id, address_id, carrier, service_level, tracking_number,
                     shipped_at, estimated_delivery, delivered_at, status)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (order_id, addr_id, carrier, service, tracking,
                  shipped_at, est_delivery, delivered_at, ship_status))

    # ------------------------------------------------------------------ #
    # REVIEWS (only for delivered orders)
    # ------------------------------------------------------------------ #
    cur.execute("""
        SELECT DISTINCT oi.product_id, o.user_id
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'delivered'
    """)
    delivered_pairs = cur.fetchall()
    reviewed = set()
    for pid, uid in delivered_pairs:
        if (pid, uid) in reviewed:
            continue
        if random.random() < 0.6:  # 60% chance of leaving a review
            rating = random.choices([3, 4, 4, 5, 5, 5], k=1)[0]
            titles = {5: "Absolutely love it!", 4: "Great product", 3: "Decent, does the job"}
            bodies = {
                5: "Exceeded my expectations. Would definitely buy again.",
                4: "Good quality and fast shipping. Happy with the purchase.",
                3: "It's okay. Does what it says but nothing special.",
            }
            cur.execute("""
                INSERT OR IGNORE INTO reviews (product_id, user_id, rating, title, body, created_at)
                VALUES (?,?,?,?,?,?)
            """, (pid, uid, rating, titles[rating], bodies[rating], random_date(200, 1)))
            reviewed.add((pid, uid))

    conn.commit()
    conn.close()
    print("Sample data inserted successfully.")
    print(f"Database location: {DB_PATH}")


if __name__ == "__main__":
    populate()
