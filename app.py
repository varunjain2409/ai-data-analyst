import os
import base64
import io
import csv
import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, session
from database import (init_db, execute_query, get_schema, register_shop, login_shop,
                      add_product, add_customer, add_order, get_shop_data)
from text_to_sql import convert_to_sql

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

APP_PIN = "1234"

SAMPLE_QUESTIONS = [
    "Total revenue kitna hai?",
    "Top 5 products by sales",
    "Har city me kitne customers hain?",
    "Average order value kya hai?",
    "Sabse zyada orders kaunse product se hue?",
    "Last 30 days me kitne orders aaye?",
    "Har category me kitne products hain?",
    "Top 10 customers by total spending",
    "Monthly revenue trend dikhao",
    "Cancelled orders kitne hain?",
]


def check_pin():
    return session.get("authenticated", False)


def get_current_shop_id():
    return session.get("shop_id", 1)


@app.route("/")
def index():
    if not check_pin():
        return render_template("login.html")
    return render_template("index.html", sample_questions=SAMPLE_QUESTIONS)


@app.route("/shop")
def shop_dashboard():
    if not check_pin():
        return render_template("pin.html")
    shop_id = get_current_shop_id()
    shop_data = get_shop_data(shop_id)
    return render_template("shop.html", shop_data=shop_data, shop_id=shop_id)


@app.route("/api/unlock", methods=["POST"])
def unlock():
    data = request.get_json()
    pin = data.get("pin", "")
    if pin == APP_PIN:
        session["authenticated"] = True
        session["login_time"] = datetime.now().isoformat()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Galat PIN"}), 401


@app.route("/api/shop/register", methods=["POST"])
def shop_register():
    data = request.get_json()
    name = data.get("name", "").strip()
    owner = data.get("owner", "").strip()
    pin = data.get("pin", "").strip()
    if not name or not owner or not pin:
        return jsonify({"success": False, "error": "Saare fields bharein"}), 400
    result = register_shop(name, owner, pin)
    return jsonify(result)


@app.route("/api/shop/login", methods=["POST"])
def shop_login():
    data = request.get_json()
    name = data.get("name", "").strip()
    pin = data.get("pin", "").strip()
    if not name or not pin:
        return jsonify({"success": False, "error": "Shop name aur PIN daalo"}), 400
    result = login_shop(name, pin)
    if result["success"]:
        session["shop_id"] = result["shop_id"]
        session["shop_name"] = result["name"]
    return jsonify(result)


@app.route("/api/shop/data")
def shop_data():
    if not check_pin():
        return jsonify({"error": "Pehle PIN daalo"}), 401
    shop_id = get_current_shop_id()
    return jsonify(get_shop_data(shop_id))


@app.route("/api/shop/add_product", methods=["POST"])
def shop_add_product():
    if not check_pin():
        return jsonify({"error": "Pehle PIN daalo"}), 401
    data = request.get_json()
    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    price = data.get("price", 0)
    stock = data.get("stock", 0)
    if not name or not category:
        return jsonify({"success": False, "error": "Name aur category daalo"}), 400
    result = add_product(get_current_shop_id(), name, category, float(price), int(stock))
    return jsonify(result)


@app.route("/api/shop/add_customer", methods=["POST"])
def shop_add_customer():
    if not check_pin():
        return jsonify({"error": "Pehle PIN daalo"}), 401
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    city = data.get("city", "").strip()
    if not name or not email:
        return jsonify({"success": False, "error": "Name aur email daalo"}), 400
    result = add_customer(get_current_shop_id(), name, email, city)
    return jsonify(result)


@app.route("/api/shop/add_order", methods=["POST"])
def shop_add_order():
    if not check_pin():
        return jsonify({"error": "Pehle PIN daalo"}), 401
    data = request.get_json()
    customer_id = data.get("customer_id", 0)
    product_id = data.get("product_id", 0)
    quantity = data.get("quantity", 1)
    if not customer_id or not product_id:
        return jsonify({"success": False, "error": "Customer aur product daalo"}), 400
    result = add_order(get_current_shop_id(), int(customer_id), int(product_id), int(quantity))
    return jsonify(result)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    if not check_pin():
        return jsonify({"success": False, "error": "Pehle PIN daalo"}), 401

    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"success": False, "error": "Question is required"}), 400

    sql_result = convert_to_sql(question)
    if not sql_result["success"]:
        return jsonify({"success": False, "error": sql_result["error"]}), 400

    sql = sql_result["sql"]

    if not sql.strip().upper().startswith("SELECT"):
        return jsonify({"success": False, "error": "Sirf SELECT queries allowed hain"}), 403

    dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "EXEC", "EXECUTE"]
    for word in dangerous:
        if word in sql.upper():
            return jsonify({"success": False, "error": f"Blocked: {word} not allowed"}), 403

    shop_id = get_current_shop_id()
    query_result = execute_query(sql, shop_id)

    if not query_result["success"]:
        return jsonify({
            "success": False,
            "sql": sql,
            "error": query_result["error"]
        }), 400

    chart = None
    chart_type = "bar"
    if query_result["data"]:
        chart, chart_type = generate_chart(query_result["data"], question)

    insights = generate_insights(query_result["data"], question, sql)

    save_to_history(question, sql, query_result["row_count"], insights)

    return jsonify({
        "success": True,
        "question": question,
        "sql": sql,
        "method": sql_result.get("method", "rule-based"),
        "data": query_result["data"],
        "row_count": query_result["row_count"],
        "chart": chart,
        "chart_type": chart_type,
        "insights": insights
    })


def generate_insights(data, question, sql):
    if not data:
        return "Koi data nahi mila is query ke liye."

    insights = []
    q = question.lower()

    if "total" in q and "revenue" in q:
        val = data[0].get("total_revenue", 0)
        insights.append(f"Total revenue ₹{val:,.0f} hai.")
        if val > 5000000:
            insights.append("Ye ek strong revenue figure hai.")
        else:
            insights.append("Revenue growth ke liye naye products try kar sakte hain.")

    elif "top" in q and "product" in q:
        top = data[0]
        insights.append(f"Sabse zyada sales: {top.get('product', 'N/A')} (₹{top.get('total_sales', 0):,.0f})")
        if len(data) > 1:
            insights.append(f"Second: {data[1].get('product', 'N/A')} (₹{data[1].get('total_sales', 0):,.0f})")

    elif "city" in q and "customer" in q:
        top_city = data[0]
        insights.append(f"Sabse zyada customers: {top_city.get('city', 'N/A')} ({top_city.get('customer_count', 0)})")
        total = sum(d.get("customer_count", 0) for d in data)
        insights.append(f"Total {len(data)} cities me {total} customers hain.")

    elif "average" in q or "avg" in q:
        val = data[0].get("avg_order_value", 0)
        insights.append(f"Average order value ₹{val:,.2f} hai.")

    elif "cancel" in q:
        val = data[0].get("cancelled_orders", 0)
        insights.append(f"{val} cancelled orders hain.")
        if val > 10:
            insights.append("Cancellation rate check karna chahiye.")

    elif "monthly" in q or "month" in q:
        best = max(data, key=lambda x: x.get("revenue", 0))
        insights.append(f"Best month: {best.get('month', 'N/A')} (₹{best.get('revenue', 0):,.0f})")

    elif "category" in q:
        top = data[0]
        insights.append(f"Sabse zyada: {top.get('category', 'N/A')} ({top.get('product_count', 0)} products)")

    else:
        insights.append(f"{len(data)} rows mili is query ke liye.")
        if data:
            keys = list(data[0].keys())
            insights.append(f"Columns: {', '.join(keys)}")

    return " ".join(insights)


def generate_chart(data, question):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if not data:
            return None, "bar"

        keys = list(data[0].keys())
        if len(keys) < 2:
            return None, "bar"

        label_key = keys[0]
        value_key = None
        for k in keys[1:]:
            if isinstance(data[0][k], (int, float)):
                value_key = k
                break

        if not value_key:
            return None, "bar"

        labels = [str(row[label_key])[:20] for row in data[:15]]
        values = [row[value_key] for row in data[:15]]

        q = question.lower()
        if "trend" in q or "monthly" in q or "time" in q:
            chart_type = "line"
        elif "distribution" in q or "breakdown" in q or "status" in q:
            chart_type = "pie"
        else:
            chart_type = "bar"

        fig, ax = plt.subplots(figsize=(8, 4))
        colors = plt.cm.Set3(range(len(labels)))

        if chart_type == "line":
            ax.plot(range(len(labels)), values, marker='o', linewidth=2, color='#38bdf8')
            ax.fill_between(range(len(labels)), values, alpha=0.3, color='#38bdf8')
        elif chart_type == "pie":
            ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        else:
            ax.bar(range(len(labels)), values, color=colors)

        if chart_type != "pie":
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            ax.set_ylabel(value_key.replace("_", " ").title())

        ax.set_title(question[:60], fontsize=11, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return img_base64, chart_type
    except Exception:
        return None, "bar"


def save_to_history(question, sql, row_count, insights):
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "data", "history.db"))
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT, sql TEXT, row_count INTEGER, insights TEXT, created_at TEXT
        )""")
        c.execute("INSERT INTO history (question, sql, row_count, insights, created_at) VALUES (?,?,?,?,?)",
                  (question, sql, row_count, insights, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception:
        pass


@app.route("/api/history")
def history():
    if not check_pin():
        return jsonify({"history": [], "error": "Pehle PIN daalo"}), 401
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "data", "history.db"))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT 20")
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify({"history": rows})
    except Exception as e:
        return jsonify({"history": [], "error": str(e)})


@app.route("/api/export", methods=["POST"])
def export():
    if not check_pin():
        return jsonify({"error": "Pehle PIN daalo"}), 401
    data = request.get_json().get("data", [])
    if not data:
        return jsonify({"error": "No data to export"}), 400

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    output_bytes = io.BytesIO(output.getvalue().encode("utf-8"))
    output_bytes.seek(0)
    return send_file(output_bytes, mimetype="text/csv", as_attachment=True, download_name="query_result.csv")


@app.route("/api/upload", methods=["POST"])
def upload():
    if not check_pin():
        return jsonify({"error": "Pehle PIN daalo"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Only CSV or Excel files allowed"}), 400

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({"error": f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB allowed"}), 400

    filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    table_name = f"user_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        import pandas as pd
        if ext == "csv":
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "data", "sample_data.db"))
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()

        return jsonify({
            "success": True,
            "filename": file.filename,
            "table": table_name,
            "rows": len(df),
            "columns": list(df.columns)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/schema")
def schema():
    if not check_pin():
        return jsonify({"error": "Pehle PIN daalo"}), 401
    return jsonify({"schema": get_schema()})


@app.route("/api/clear_history", methods=["POST"])
def clear_history():
    if not check_pin():
        return jsonify({"error": "Pehle PIN daalo"}), 401
    try:
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "data", "history.db"))
        c = conn.cursor()
        c.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    init_db()
    app.run(debug=False, host="0.0.0.0", port=5000)
