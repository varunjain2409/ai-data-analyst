import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sample_data.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # Shops table
    c.execute("""
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            pin TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Products table with shop_id
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            shop_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
    """)

    # Customers table with shop_id
    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            shop_id INTEGER DEFAULT 1,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            joined_date TEXT NOT NULL,
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
    """)

    # Orders table with shop_id
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            shop_id INTEGER DEFAULT 1,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (shop_id) REFERENCES shops (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    # Insert default shop if not exists
    c.execute("SELECT COUNT(*) FROM shops")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO shops (id, name, owner, pin, created_at) VALUES (1, 'Demo Shop', 'Admin', '1234', ?)",
                  (datetime.now().isoformat(),))

    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    products = [
        (1, "Laptop Pro 15", "Electronics", 129999, 45),
        (1, "Wireless Mouse", "Electronics", 1499, 200),
        (1, "USB-C Hub", "Electronics", 3499, 150),
        (1, "Mechanical Keyboard", "Electronics", 5999, 80),
        (1, "Monitor 27inch", "Electronics", 24999, 35),
        (1, "Desk Chair", "Furniture", 8999, 60),
        (1, "Standing Desk", "Furniture", 18999, 25),
        (1, "Bookshelf", "Furniture", 4999, 40),
        (1, "Notebook A5", "Stationery", 199, 500),
        (1, "Pen Set", "Stationery", 99, 1000),
        (1, "Backpack", "Accessories", 2499, 120),
        (1, "Water Bottle", "Accessories", 799, 300),
    ]
    c.executemany("INSERT INTO products (shop_id, name, category, price, stock) VALUES (?,?,?,?,?)", products)

    cities = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Pune", "Jaipur", "Kolkata"]
    first_names = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Ananya", "Arjun", "Divya", "Karan", "Meera",
                   "Rahul", "Pooja", "Amit", "Neha", "Sahil", "Kavya", "Varun", "Ishita", "Aditi", "Nikhil"]
    last_names = ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Mehta", "Joshi", "Reddy", "Nair", "Iyer"]

    customers = []
    for i in range(1, 51):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"customer{i}@email.com"
        city = random.choice(cities)
        joined = (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d")
        customers.append((i, 1, name, email, city, "India", joined))
    c.executemany("INSERT INTO customers (id, shop_id, name, email, city, country, joined_date) VALUES (?,?,?,?,?,?,?)", customers)

    statuses = ["Completed", "Completed", "Completed", "Pending", "Shipped", "Cancelled"]
    orders = []
    for i in range(1, 201):
        cust_id = random.randint(1, 50)
        prod_id = random.randint(1, 12)
        qty = random.randint(1, 5)
        price = products[prod_id - 1][3]
        total = price * qty
        order_date = (datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
        status = random.choice(statuses)
        orders.append((i, 1, cust_id, prod_id, qty, total, order_date, status))
    c.executemany("INSERT INTO orders (id, shop_id, customer_id, product_id, quantity, total_amount, order_date, status) VALUES (?,?,?,?,?,?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print("Database initialized with sample data!")


def get_schema():
    conn = get_db()
    c = conn.cursor()
    schema = []
    for table in ["shops", "products", "customers", "orders"]:
        c.execute(f"PRAGMA table_info({table})")
        cols = c.fetchall()
        col_names = [col[1] for col in cols]
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        schema.append(f"Table: {table} ({count} rows) - Columns: {', '.join(col_names)}")
    conn.close()
    return "\n".join(schema)


def execute_query(sql, shop_id=None):
    conn = get_db()
    c = conn.cursor()
    try:
        if shop_id and "WHERE" not in sql.upper():
            sql = sql.replace("FROM orders", f"FROM orders WHERE shop_id = {shop_id}")
            sql = sql.replace("FROM products", f"FROM products WHERE shop_id = {shop_id}")
            sql = sql.replace("FROM customers", f"FROM customers WHERE shop_id = {shop_id}")
        c.execute(sql)
        rows = c.fetchall()
        if rows:
            cols = [desc[0] for desc in c.description]
            result = [dict(zip(cols, row)) for row in rows]
        else:
            result = []
        conn.close()
        return {"success": True, "data": result, "row_count": len(result)}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}


def register_shop(name, owner, pin):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM shops WHERE name = ? AND pin = ?", (name, pin))
    if c.fetchone():
        conn.close()
        return {"success": False, "error": "Shop already exists with this PIN"}
    c.execute("INSERT INTO shops (name, owner, pin, created_at) VALUES (?,?,?,?)",
              (name, owner, pin, datetime.now().isoformat()))
    shop_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "shop_id": shop_id, "name": name}


def login_shop(name, pin):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, owner FROM shops WHERE name = ? AND pin = ?", (name, pin))
    shop = c.fetchone()
    conn.close()
    if shop:
        return {"success": True, "shop_id": shop["id"], "name": shop["name"], "owner": shop["owner"]}
    return {"success": False, "error": "Invalid shop name or PIN"}


def add_product(shop_id, name, category, price, stock):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO products (shop_id, name, category, price, stock) VALUES (?,?,?,?,?)",
              (shop_id, name, category, price, stock))
    conn.commit()
    conn.close()
    return {"success": True}


def add_customer(shop_id, name, email, city):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO customers (shop_id, name, email, city, country, joined_date) VALUES (?,?,?,?,?,?)",
              (shop_id, name, email, city, "India", datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()
    return {"success": True}


def add_order(shop_id, customer_id, product_id, quantity, status="Pending"):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT price FROM products WHERE id = ? AND shop_id = ?", (product_id, shop_id))
    product = c.fetchone()
    if not product:
        conn.close()
        return {"success": False, "error": "Product not found"}
    total = product["price"] * quantity
    c.execute("INSERT INTO orders (shop_id, customer_id, product_id, quantity, total_amount, order_date, status) VALUES (?,?,?,?,?,?,?)",
              (shop_id, customer_id, product_id, quantity, total, datetime.now().strftime("%Y-%m-%d"), status))
    conn.commit()
    conn.close()
    return {"success": True}


def get_shop_data(shop_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM products WHERE shop_id = ?", (shop_id,))
    products = c.fetchone()["count"]
    c.execute("SELECT COUNT(*) as count FROM customers WHERE shop_id = ?", (shop_id,))
    customers = c.fetchone()["count"]
    c.execute("SELECT COUNT(*) as count FROM orders WHERE shop_id = ?", (shop_id,))
    orders = c.fetchone()["count"]
    c.execute("SELECT COALESCE(SUM(total_amount), 0) as total FROM orders WHERE shop_id = ?", (shop_id,))
    revenue = c.fetchone()["total"]
    conn.close()
    return {"products": products, "customers": customers, "orders": orders, "revenue": revenue}


if __name__ == "__main__":
    init_db()
    print(get_schema())
