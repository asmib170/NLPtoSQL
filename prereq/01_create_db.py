"""Create DemoECommerceDB SQLite database and all tables."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "DemoECommerceDB.db")


def create_database():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.executescript("""
        -- Users / Customers
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name    TEXT    NOT NULL,
            last_name     TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            phone         TEXT,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
            is_active     INTEGER NOT NULL DEFAULT 1
        );

        -- Addresses (a user can have multiple)
        CREATE TABLE IF NOT EXISTS addresses (
            address_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(user_id),
            label       TEXT    NOT NULL DEFAULT 'Home',  -- Home / Work / Other
            street      TEXT    NOT NULL,
            city        TEXT    NOT NULL,
            state       TEXT    NOT NULL,
            zip_code    TEXT    NOT NULL,
            country     TEXT    NOT NULL DEFAULT 'US',
            is_default  INTEGER NOT NULL DEFAULT 0
        );

        -- Product categories
        CREATE TABLE IF NOT EXISTS categories (
            category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL UNIQUE,
            parent_id     INTEGER REFERENCES categories(category_id)
        );

        -- Products
        CREATE TABLE IF NOT EXISTS products (
            product_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id   INTEGER NOT NULL REFERENCES categories(category_id),
            name          TEXT    NOT NULL,
            description   TEXT,
            sku           TEXT    NOT NULL UNIQUE,
            price         REAL    NOT NULL,
            stock_qty     INTEGER NOT NULL DEFAULT 0,
            weight_kg     REAL,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
            is_active     INTEGER NOT NULL DEFAULT 1
        );

        -- Orders
        CREATE TABLE IF NOT EXISTS orders (
            order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(user_id),
            status          TEXT    NOT NULL DEFAULT 'pending',
                            -- pending | confirmed | processing | shipped | delivered | cancelled | refunded
            subtotal        REAL    NOT NULL,
            discount        REAL    NOT NULL DEFAULT 0,
            tax             REAL    NOT NULL DEFAULT 0,
            total           REAL    NOT NULL,
            payment_method  TEXT    NOT NULL,  -- credit_card | paypal | bank_transfer
            payment_status  TEXT    NOT NULL DEFAULT 'pending',  -- pending | paid | failed | refunded
            notes           TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        -- Order line items
        CREATE TABLE IF NOT EXISTS order_items (
            item_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL REFERENCES orders(order_id),
            product_id  INTEGER NOT NULL REFERENCES products(product_id),
            quantity    INTEGER NOT NULL,
            unit_price  REAL    NOT NULL,
            discount    REAL    NOT NULL DEFAULT 0,
            line_total  REAL    NOT NULL
        );

        -- Shipping
        CREATE TABLE IF NOT EXISTS shipping (
            shipping_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id          INTEGER NOT NULL UNIQUE REFERENCES orders(order_id),
            address_id        INTEGER NOT NULL REFERENCES addresses(address_id),
            carrier           TEXT    NOT NULL,  -- FedEx | UPS | USPS | DHL
            service_level     TEXT    NOT NULL,  -- standard | express | overnight
            tracking_number   TEXT,
            shipped_at        TEXT,
            estimated_delivery TEXT,
            delivered_at      TEXT,
            status            TEXT    NOT NULL DEFAULT 'pending'
                              -- pending | label_created | in_transit | out_for_delivery | delivered | failed
        );

        -- Product reviews
        CREATE TABLE IF NOT EXISTS reviews (
            review_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  INTEGER NOT NULL REFERENCES products(product_id),
            user_id     INTEGER NOT NULL REFERENCES users(user_id),
            rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            title       TEXT,
            body        TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE (product_id, user_id)
        );

        -- Coupons / discounts
        CREATE TABLE IF NOT EXISTS coupons (
            coupon_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            code            TEXT    NOT NULL UNIQUE,
            discount_type   TEXT    NOT NULL,  -- percent | fixed
            discount_value  REAL    NOT NULL,
            min_order_value REAL    NOT NULL DEFAULT 0,
            max_uses        INTEGER,
            used_count      INTEGER NOT NULL DEFAULT 0,
            expires_at      TEXT,
            is_active       INTEGER NOT NULL DEFAULT 1
        );
    """)

    conn.commit()
    conn.close()
    print(f"Database created: {DB_PATH}")
    print("Tables created: users, addresses, categories, products, orders, order_items, shipping, reviews, coupons")


if __name__ == "__main__":
    create_database()
