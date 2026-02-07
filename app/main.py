from fastapi import FastAPI, HTTPException, Depends
from app.conn import get_conn
from app.products import get_products
from app.orders import create_order
from app.statistics import stats_customer_orders, stats_product_orders, stats_recent_sales, stats_top_products
from app.auth import UserLogin, UserRegister, login_user, register_user, get_current_user, check_admin

app = FastAPI()

# ===== New endpoints for homework 5 =====

# ----- PUBLIC ENDPOINTS -----

@app.get("/")
def get_root():
    return { "msg": "Clothing Store v0.1" }

@app.post("/users/login")
def login(credentials: UserLogin):
  return login_user(credentials)

@app.post("/users")
def register_new_user(user: UserRegister,):
    return register_user(user)

@app.get("/products")
def get_products_list():
    return get_products()

# GET /categories - List all categories
# GET /categories/{category_id} - Get category details

# ----- CUSTOMER ENDPOINTS (Logged in) -----

@app.get("/orders")
def get_my_orders(current_user = Depends(get_current_user)):
    # Logic to fetch only orders where user_id = current_user["id"]
    pass

@app.post("/orders", status_code=201)
def create_new_order(data: dict, user = Depends(get_current_user)):
    return create_order(data, user["user_id"])

# ----- ADMIN ENDPOINTS -----

@app.get("/stats/customers")
def get_customers_stats(user = Depends(check_admin)):
    return stats_customer_orders()

@app.get("/stats/products")
def get_products_stats(user = Depends(check_admin)):
    return stats_product_orders()

@app.get("/stats/top-products")
def get_top_products_stats(n: int = 10, admin = Depends(check_admin)):
    return stats_top_products(n)

@app.get("/stats/recent-sales")
def get_recent_sales_stats(n: int = 30, admin = Depends(check_admin)):
    return stats_recent_sales(n)

@app.delete("/users/{user_id}")
def delete_user(user_id: int, admin = Depends(check_admin)):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM customers WHERE customer_id = %s", (user_id,))
        return {"msg": "User deleted"}

# POST /categories - Create new category (admin only)
# POST /products - Create new product (admin only)


# ===== The endpoints from original repo =====

@app.get("/categories")
def get_categories():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT category_id, name FROM categories ORDER BY category_id;")
        return cur.fetchall()

@app.get("/categories/{category_id}")
def get_category(category_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT category_id, name FROM categories WHERE category_id = %s;", (category_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        return row

@app.post("/categories", status_code=201)
def create_category(data: dict, user = Depends(check_admin)):
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name'")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO categories (name) VALUES (%s) RETURNING category_id, name;", (name,))
        return cur.fetchone()