"""Verify DemoECommerceDB contents — print row counts and sample rows."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "DemoECommerceDB.db")

TABLES = [
    "users", "addresses", "categories", "products",
    "orders", "order_items", "shipping", "reviews", "coupons"
]


def verify():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("=" * 60)
    print("DemoECommerceDB — Row Counts")
    print("=" * 60)
    for table in TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table:<20} {count:>5} rows")

    print("\n" + "=" * 60)
    print("Sample: orders with totals")
    print("=" * 60)
    cur.execute("""
        SELECT o.order_id, u.first_name || ' ' || u.last_name AS customer,
               o.status, o.total, o.payment_method, o.created_at
        FROM orders o
        JOIN users u ON u.user_id = o.user_id
        ORDER BY o.created_at DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    print(f"  {'ID':<6} {'Customer':<20} {'Status':<12} {'Total':>10}  {'Payment':<15} {'Date'}")
    print(f"  {'-'*6} {'-'*20} {'-'*12} {'-'*10}  {'-'*15} {'-'*19}")
    for r in rows:
        print(f"  {r['order_id']:<6} {r['customer']:<20} {r['status']:<12} ${r['total']:>9.2f}  {r['payment_method']:<15} {r['created_at']}")

    print("\n" + "=" * 60)
    print("Sample: top products by revenue")
    print("=" * 60)
    cur.execute("""
        SELECT p.name, SUM(oi.line_total) AS revenue, SUM(oi.quantity) AS units_sold
        FROM order_items oi
        JOIN products p ON p.product_id = oi.product_id
        GROUP BY oi.product_id
        ORDER BY revenue DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    print(f"  {'Product':<40} {'Revenue':>12}  {'Units':>6}")
    print(f"  {'-'*40} {'-'*12}  {'-'*6}")
    for r in rows:
        print(f"  {r['name']:<40} ${r['revenue']:>11.2f}  {r['units_sold']:>6}")

    print("\n" + "=" * 60)
    print("Sample: shipping status breakdown")
    print("=" * 60)
    cur.execute("""
        SELECT status, COUNT(*) as cnt FROM shipping GROUP BY status ORDER BY cnt DESC
    """)
    for r in cur.fetchall():
        print(f"  {r['status']:<25} {r['cnt']:>5}")

    conn.close()
    print("\nVerification complete.")


if __name__ == "__main__":
    verify()
