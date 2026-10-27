import re
from database import get_schema


def parse_question(question):
    q = question.lower().strip()

    sql = None

    # --- Total revenue / sales ---
    if re.search(r"(total|kitna|kitni).*(revenue|sales|amount|earning)", q):
        sql = "SELECT SUM(total_amount) AS total_revenue FROM orders"

    # --- Average order value ---
    elif re.search(r"(average|avg).*(order|value|amount)", q):
        sql = "SELECT ROUND(AVG(total_amount), 2) AS avg_order_value FROM orders"

    # --- Count orders ---
    elif re.search(r"(kitne|how many).*(orders|order)", q) and re.search(r"(last|past|previous|agne|pichle).*(day|month|week|din|mahina|hafta)", q):
        days = 30
        m = re.search(r"(\d+)", q)
        if m:
            days = int(m.group(1))
        sql = f"SELECT COUNT(*) AS total_orders FROM orders WHERE order_date >= date('now', '-{days} days')"

    # --- Cancelled orders ---
    elif re.search(r"(cancel|cancelled|reject)", q):
        sql = "SELECT COUNT(*) AS cancelled_orders FROM orders WHERE status = 'Cancelled'"

    # --- Top N products by sales ---
    elif re.search(r"(top|sabse zyada|best|most).*(product|item)", q):
        limit = 5
        m = re.search(r"(\d+)", q)
        if m:
            limit = int(m.group(1))
        sql = f"""SELECT p.name AS product, SUM(o.total_amount) AS total_sales, SUM(o.quantity) AS total_qty
FROM orders o JOIN products p ON o.product_id = p.id
GROUP BY p.name ORDER BY total_sales DESC LIMIT {limit}"""

    # --- Top N customers by spending ---
    elif re.search(r"(top|sabse zyada|best|most).*(customer|client|buyer)", q):
        limit = 10
        m = re.search(r"(\d+)", q)
        if m:
            limit = int(m.group(1))
        sql = f"""SELECT c.name AS customer, c.city, SUM(o.total_amount) AS total_spent, COUNT(o.id) AS order_count
FROM orders o JOIN customers c ON o.customer_id = c.id
GROUP BY c.name ORDER BY total_spent DESC LIMIT {limit}"""

    # --- Customers by city ---
    elif re.search(r"(city|sheher|shehar).*(customer|client|log|count|kitne)", q) or re.search(r"(kitne|how many).*(customer|client).*(city|sheher)", q):
        sql = "SELECT city, COUNT(*) AS customer_count FROM customers GROUP BY city ORDER BY customer_count DESC"

    # --- Products by category ---
    elif re.search(r"(category|type|category).*(product|item|count|kitne)", q) or re.search(r"(kitne|how many).*(product|item).*(category|type)", q):
        sql = "SELECT category, COUNT(*) AS product_count FROM products GROUP BY category ORDER BY product_count DESC"

    # --- Monthly revenue trend ---
    elif re.search(r"(monthly|month|mahina).*(revenue|sales|trend|report)", q):
        sql = """SELECT strftime('%Y-%m', order_date) AS month, SUM(total_amount) AS revenue, COUNT(*) AS order_count
FROM orders GROUP BY month ORDER BY month"""

    # --- Revenue by category ---
    elif re.search(r"(category).*(revenue|sales|earning)", q):
        sql = """SELECT p.category, SUM(o.total_amount) AS revenue, COUNT(o.id) AS order_count
FROM orders o JOIN products p ON o.product_id = p.id
GROUP BY p.category ORDER BY revenue DESC"""

    # --- Revenue by city ---
    elif re.search(r"(city|sheher).*(revenue|sales|earning)", q):
        sql = """SELECT c.city, SUM(o.total_amount) AS revenue, COUNT(o.id) AS order_count
FROM orders o JOIN customers c ON o.customer_id = c.id
GROUP BY c.city ORDER BY revenue DESC"""

    # --- Order status breakdown ---
    elif re.search(r"(status|breakdown|distribution).*(order|orders)", q):
        sql = "SELECT status, COUNT(*) AS order_count, SUM(total_amount) AS total_amount FROM orders GROUP BY status ORDER BY order_count DESC"

    # --- Low stock products ---
    elif re.search(r"(low|kam|less).*(stock|inventory)", q):
        threshold = 50
        m = re.search(r"(\d+)", q)
        if m:
            threshold = int(m.group(1))
        sql = f"SELECT name, category, stock FROM products WHERE stock < {threshold} ORDER BY stock ASC"

    # --- Recent orders ---
    elif re.search(r"(recent|latest|latest|last|aabhi|abhi).*(order|orders)", q):
        limit = 10
        m = re.search(r"(\d+)", q)
        if m:
            limit = int(m.group(1))
        sql = f"""SELECT o.id, c.name AS customer, p.name AS product, o.quantity, o.total_amount, o.order_date, o.status
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
ORDER BY o.order_date DESC LIMIT {limit}"""

    # --- Customer details by city ---
    elif re.search(r"(customer|client).*(list|detail|show|dikhao|dikha)", q):
        sql = "SELECT name, email, city, joined_date FROM customers ORDER BY joined_date DESC"

    # --- Product list ---
    elif re.search(r"(product|item).*(list|detail|show|dikhao|dikha|all)", q):
        sql = "SELECT name, category, price, stock FROM products ORDER BY category, name"

    # --- Total customers ---
    elif re.search(r"(total|kitne|how many).*(customer|client|log)", q):
        sql = "SELECT COUNT(*) AS total_customers FROM customers"

    # --- Total products ---
    elif re.search(r"(total|kitne|how many).*(product|item)", q):
        sql = "SELECT COUNT(*) AS total_products FROM products"

    # --- Orders by status (specific) ---
    elif re.search(r"(completed|pending|shipped).*(order|orders|kitne)", q):
        status = "Completed"
        if "pending" in q:
            status = "Pending"
        elif "shipped" in q:
            status = "Shipped"
        sql = f"SELECT COUNT(*) AS order_count FROM orders WHERE status = '{status}'"

    # --- Revenue in date range ---
    elif re.search(r"(revenue|sales|earning).*(between|from|to|me|in)", q):
        sql = """SELECT strftime('%Y-%m', order_date) AS month, SUM(total_amount) AS revenue
FROM orders GROUP BY month ORDER BY month"""

    # --- Top products by quantity ---
    elif re.search(r"(top|sabse zyada|most).*(quantity|qty|sold|bikne)", q):
        sql = """SELECT p.name AS product, SUM(o.quantity) AS total_sold
FROM orders o JOIN products p ON o.product_id = p.id
GROUP BY p.name ORDER BY total_sold DESC LIMIT 10"""

    # --- Customer order history ---
    elif re.search(r"(customer).*(order|history|purchase)", q):
        sql = """SELECT c.name AS customer, COUNT(o.id) AS order_count, SUM(o.total_amount) AS total_spent
FROM orders o JOIN customers c ON o.customer_id = c.id
GROUP BY c.name ORDER BY total_spent DESC LIMIT 15"""

    # --- Default: show all orders summary ---
    if not sql:
        sql = """SELECT o.id, c.name AS customer, p.name AS product, o.quantity, o.total_amount, o.order_date, o.status
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN products p ON o.product_id = p.id
ORDER BY o.order_date DESC LIMIT 20"""

    return sql


def convert_to_sql_rule_based(question):
    try:
        sql = parse_question(question)
        return {"success": True, "sql": sql, "method": "rule-based"}
    except Exception as e:
        return {"success": False, "error": str(e)}
