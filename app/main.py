from fastapi import FastAPI, HTTPException
from app.conn import get_conn
from app.products import get_products
from app.orders import create_order


app = FastAPI()

# GET /
@app.get("/")
def get_root():
    return { "msg": "Clothing Store v0.1" }

# GET /products
@app.get("/products")
def get_products_endpoint():
    return get_products()

@app.post("/orders", status_code=201)
def create_order_endpoint(data: dict):
    return create_order(data)

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