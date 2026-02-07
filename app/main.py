from fastapi import FastAPI, HTTPException
from app.conn import get_conn
from app.products import get_products
from app.orders import create_order
from app.statistics import stats_customer_orders, stats_product_orders, stats_recent_sales, stats_top_products

app = FastAPI()

# ===== New endpoints for homework 5 =====

# GET /
@app.get("/")
def get_root():
    return { "msg": "Clothing Store v0.1" }

# GET /products
@app.get("/products")
def get_products_endpoint():
    return get_products()

# POST /orders
@app.post("/orders", status_code=201)
def create_order_endpoint(data: dict):
    return create_order(data)

# GET /stats/customers
@app.get("/stats/customers")
def get_customers_stats():
    return stats_customer_orders()

# GET /stats/products
@app.get("/stats/products")
def get_products_stats():
    return stats_product_orders()

@app.get("/stats/top-products")
def get_top_products_stats(n: int = 10):
    return stats_top_products(n)

@app.get("/stats/recent-sales")
def get_recent_sales_stats(n: int = 30):
    return stats_recent_sales(n)



# ===== The endpoints from original repo =====

# GET /categories 
@app.get("/categories")
def get_categories():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT category_id, name FROM categories ORDER BY category_id;")
        return cur.fetchall()

# GET /categories/{id}
@app.get("/categories/{category_id}")
def get_category(category_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT category_id, name FROM categories WHERE category_id = %s;", (category_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        return row

# POST /categories
@app.post("/categories", status_code=201)
def create_category(data: dict):
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name'")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO categories (name) VALUES (%s) RETURNING category_id, name;", (name,))
        return cur.fetchone()