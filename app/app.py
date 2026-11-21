"""
CMPE341 - Group 7 - Product Management System
Flask web application: login, two roles (admin / staff), Insert / Update / Delete.
"""
import os
from functools import wraps

import psycopg
from psycopg.rows import dict_row
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, abort)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")


# ---------------------------------------------------------------- database
def get_conn():
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "product_db"),
        user=os.environ.get("DB_USER", "pms_user"),
        password=os.environ.get("DB_PASSWORD", "pms_pass"),
        row_factory=dict_row,
    )


def query(sql, params=None, one=False):
    with get_conn() as conn:
        rows = conn.execute(sql, params or ()).fetchall()
    return (rows[0] if rows else None) if one else rows


def execute(sql, params=None):
    """Run INSERT/UPDATE/DELETE. Returns an error message or None."""
    try:
        with get_conn() as conn:
            conn.execute(sql, params or ())
        return None
    except psycopg.errors.ForeignKeyViolation:
        return "This record is used by another table, so it cannot be deleted."
    except psycopg.errors.UniqueViolation:
        return "This value already exists."
    except psycopg.errors.CheckViolation:
        return "Invalid value (for example a negative price or stock)."
    except psycopg.Error as e:
        return f"Database error: {e.diag.message_primary or e}"


# ------------------------------------------------------------- auth helpers
def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*a, **kw):
        if session.get("role") != "admin":
            abort(403)
        return f(*a, **kw)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = query("SELECT * FROM users WHERE username = %s",
                     (request.form["username"],), one=True)
        if user and check_password_hash(user["password_hash"], request.form["password"]):
            session.clear()
            session.update(user_id=user["user_id"], username=user["username"],
                           role=user["role"])
            return redirect(url_for("index"))
        flash("Wrong username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.errorhandler(403)
def forbidden(_):
    return render_template("403.html"), 403


@app.route("/")
@login_required
def index():
    stats = query("""SELECT (SELECT COUNT(*) FROM product)  AS products,
                            (SELECT COUNT(*) FROM category) AS categories,
                            (SELECT COUNT(*) FROM supplier) AS suppliers,
                            (SELECT COUNT(*) FROM orders)   AS orders""", one=True)
    low = query("SELECT name, stock FROM product WHERE stock < 10 ORDER BY stock")
    return render_template("index.html", stats=stats, low=low)


# ------------------------------------------------- generic CRUD (admin only)
# Table and column names come only from this dict, never from user input.
ENTITIES = {
    "categories": {
        "title": "Categories", "table": "category", "pk": "category_id",
        "fields": [("name", "Name", "text", True),
                   ("description", "Description", "text", False)],
        "list_sql": "SELECT category_id AS id, name, description FROM category ORDER BY name",
        "columns": [("name", "Name"), ("description", "Description")],
    },
    "suppliers": {
        "title": "Suppliers", "table": "supplier", "pk": "supplier_id",
        "fields": [("name", "Name", "text", True),
                   ("phone", "Phone", "text", False),
                   ("email", "Email", "email", False)],
        "list_sql": "SELECT supplier_id AS id, name, phone, email FROM supplier ORDER BY name",
        "columns": [("name", "Name"), ("phone", "Phone"), ("email", "Email")],
    },
    "products": {
        "title": "Products", "table": "product", "pk": "product_id",
        "fields": [("name", "Name", "text", True),
                   ("price", "Price (TL)", "number", True),
                   ("stock", "Stock", "number", True),
                   ("category_id", "Category", "select:category", True),
                   ("supplier_id", "Supplier", "select:supplier", True)],
        "list_sql": """SELECT p.product_id AS id, p.name, p.price, p.stock,
                              c.name AS category, s.name AS supplier
                       FROM product p
                       JOIN category c ON p.category_id = c.category_id
                       JOIN supplier s ON p.supplier_id = s.supplier_id
                       ORDER BY p.name""",
        "columns": [("name", "Name"), ("price", "Price"), ("stock", "Stock"),
                    ("category", "Category"), ("supplier", "Supplier")],
    },
}
SELECT_SOURCES = {
    "category": "SELECT category_id AS id, name FROM category ORDER BY name",
    "supplier": "SELECT supplier_id AS id, name FROM supplier ORDER BY name",
}


def entity_or_404(name):
    if name not in ENTITIES:
        abort(404)
    return ENTITIES[name]


def form_options(ent):
    return {f[0]: query(SELECT_SOURCES[f[2].split(":")[1]])
            for f in ent["fields"] if f[2].startswith("select:")}


def form_values(ent):
    return [request.form.get(f[0]) or None for f in ent["fields"]]


@app.route("/<name>")
@login_required
def entity_list(name):
    ent = entity_or_404(name)
    return render_template("list.html", ent=ent, name=name, rows=query(ent["list_sql"]))


@app.route("/<name>/new", methods=["GET", "POST"])
@admin_required
def entity_new(name):
    ent = entity_or_404(name)
    if request.method == "POST":
        cols = ", ".join(f[0] for f in ent["fields"])
        marks = ", ".join(["%s"] * len(ent["fields"]))
        err = execute(f"INSERT INTO {ent['table']} ({cols}) VALUES ({marks})", form_values(ent))
        if not err:
            flash("Record added.", "success")
            return redirect(url_for("entity_list", name=name))
        flash(err, "danger")
    return render_template("form.html", ent=ent, name=name, row=request.form,
                           options=form_options(ent))


@app.route("/<name>/<int:rid>/edit", methods=["GET", "POST"])
@admin_required
def entity_edit(name, rid):
    ent = entity_or_404(name)
    if request.method == "POST":
        sets = ", ".join(f"{f[0]} = %s" for f in ent["fields"])
        err = execute(f"UPDATE {ent['table']} SET {sets} WHERE {ent['pk']} = %s",
                      form_values(ent) + [rid])
        if not err:
            flash("Record updated.", "success")
            return redirect(url_for("entity_list", name=name))
        flash(err, "danger")
        row = request.form
    else:
        row = query(f"SELECT * FROM {ent['table']} WHERE {ent['pk']} = %s", (rid,), one=True)
        if not row:
            abort(404)
    return render_template("form.html", ent=ent, name=name, row=row, rid=rid,
                           options=form_options(ent))


@app.route("/<name>/<int:rid>/delete", methods=["POST"])
@admin_required
def entity_delete(name, rid):
    ent = entity_or_404(name)
    err = execute(f"DELETE FROM {ent['table']} WHERE {ent['pk']} = %s", (rid,))
    flash(err or "Record deleted.", "danger" if err else "success")
    return redirect(url_for("entity_list", name=name))


# ------------------------------------------------------------------- orders
# staff: list + create orders.  admin: also update and delete orders.
@app.route("/orders")
@login_required
def orders():
    rows = query("""SELECT o.order_id, o.order_date, o.customer_name, p.name AS product,
                           o.quantity, o.quantity * p.price AS total, u.username
                    FROM orders o
                    JOIN product p ON o.product_id = p.product_id
                    JOIN users u   ON o.user_id = u.user_id
                    ORDER BY o.order_date DESC, o.order_id DESC""")
    return render_template("orders.html", rows=rows)


def save_order(old=None):
    """Insert or update an order and keep product stock correct, in one transaction."""
    pid = int(request.form["product_id"])
    qty = int(request.form["quantity"])
    customer = request.form["customer_name"].strip()
    if qty <= 0 or not customer:
        return "Customer name and a positive quantity are required."
    try:
        with get_conn() as conn:
            if old:  # give back the stock of the old order first
                conn.execute("UPDATE product SET stock = stock + %s WHERE product_id = %s",
                             (old["quantity"], old["product_id"]))
            cur = conn.execute("UPDATE product SET stock = stock - %s "
                               "WHERE product_id = %s AND stock >= %s",
                               (qty, pid, qty))
            if cur.rowcount == 0:
                conn.rollback()
                return "Not enough stock for this product."
            if old:
                conn.execute("UPDATE orders SET product_id=%s, customer_name=%s, quantity=%s "
                             "WHERE order_id=%s", (pid, customer, qty, old["order_id"]))
            else:
                conn.execute("INSERT INTO orders (product_id, user_id, customer_name, quantity) "
                             "VALUES (%s, %s, %s, %s)", (pid, session["user_id"], customer, qty))
        return None
    except psycopg.Error as e:
        return f"Database error: {e.diag.message_primary or e}"


def product_choices():
    return query("SELECT product_id AS id, name, stock FROM product ORDER BY name")


@app.route("/orders/new", methods=["GET", "POST"])
@login_required
def order_new():
    if request.method == "POST":
        err = save_order()
        if not err:
            flash("Order created.", "success")
            return redirect(url_for("orders"))
        flash(err, "danger")
    return render_template("order_form.html", row=request.form, products=product_choices())


@app.route("/orders/<int:oid>/edit", methods=["GET", "POST"])
@admin_required
def order_edit(oid):
    old = query("SELECT * FROM orders WHERE order_id = %s", (oid,), one=True)
    if not old:
        abort(404)
    if request.method == "POST":
        err = save_order(old)
        if not err:
            flash("Order updated.", "success")
            return redirect(url_for("orders"))
        flash(err, "danger")
    row = request.form if request.method == "POST" else old
    return render_template("order_form.html", row=row, oid=oid, products=product_choices())


@app.route("/orders/<int:oid>/delete", methods=["POST"])
@admin_required
def order_delete(oid):
    with get_conn() as conn:
        o = conn.execute("DELETE FROM orders WHERE order_id = %s "
                         "RETURNING product_id, quantity", (oid,)).fetchone()
        if o:  # put the items back into stock
            conn.execute("UPDATE product SET stock = stock + %s WHERE product_id = %s",
                         (o["quantity"], o["product_id"]))
    flash("Order deleted, stock restored.", "success")
    return redirect(url_for("orders"))


# -------------------------------------------------------------------- users
@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    if request.method == "POST":
        pw = request.form["password"]
        if len(pw) < 6:
            flash("Password must be at least 6 characters.", "danger")
        else:
            err = execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                          (request.form["username"].strip(), generate_password_hash(pw, method="pbkdf2:sha256"),
                           request.form["role"]))
            flash(err or "User added.", "danger" if err else "success")
        return redirect(url_for("users"))
    return render_template("users.html",
                           rows=query("SELECT user_id, username, role FROM users ORDER BY user_id"))


@app.route("/users/<int:uid>/delete", methods=["POST"])
@admin_required
def user_delete(uid):
    if uid == session["user_id"]:
        flash("You cannot delete your own account.", "danger")
    else:
        err = execute("DELETE FROM users WHERE user_id = %s", (uid,))
        flash(err or "User deleted.", "danger" if err else "success")
    return redirect(url_for("users"))


# ------------------------------------------------------------------ reports
REPORTS = [
    ("Query 1 - JOIN: orders with product, category and user", """
        SELECT o.order_id, o.order_date, o.customer_name, p.name AS product,
               c.name AS category, o.quantity, o.quantity * p.price AS total_price,
               u.username AS entered_by
        FROM orders o
        JOIN product  p ON o.product_id  = p.product_id
        JOIN category c ON p.category_id = c.category_id
        JOIN users    u ON o.user_id     = u.user_id
        ORDER BY o.order_date"""),
    ("Query 2 - GROUP BY + ORDER BY: products per category", """
        SELECT c.name AS category, COUNT(p.product_id) AS product_count,
               ROUND(AVG(p.price), 2) AS avg_price, SUM(p.stock) AS total_stock
        FROM category c
        LEFT JOIN product p ON p.category_id = c.category_id
        GROUP BY c.name
        ORDER BY product_count DESC, avg_price DESC"""),
    ("Query 3 - Subquery: products that were never ordered", """
        SELECT p.product_id, p.name, p.price, p.stock
        FROM product p
        WHERE p.product_id NOT IN (SELECT o.product_id FROM orders o)
        ORDER BY p.price DESC"""),
]


@app.route("/reports")
@login_required
def reports():
    results = [(title, sql.strip(), query(sql)) for title, sql in REPORTS]
    return render_template("reports.html", results=results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
