from fastapi import FastAPI, HTTPException, Depends

from app.services import products as product_service
from app.services import orders as order_service
from app.services import statistics as stats_service
from app.services import auth as auth_service
from app.services import categories as category_service

app = FastAPI()

# ----- PUBLIC ENDPOINTS -----

@app.get("/")
def get_root():
    return { "msg": "Clothing Store v0.1" }

@app.post("/users/login")
def login(credentials: auth_service.UserLogin):
  return auth_service.login_user(credentials)

@app.post("/users")
def register_user(user: auth_service.UserRegister,):
    return auth_service.register_user(user)

@app.get("/products")
def list_products():
    return product_service.get_products()

@app.get("/categories")
def get_categories():
    return category_service.get_categories()

@app.get("/categories/{category_id}")
def get_category(category_id: int):
  return category_service.get_category(category_id)

    
# ----- CUSTOMER ENDPOINTS (Logged in) -----

@app.get("/orders")
def list_my_orders(
  details: bool = False,
  current_user = Depends(auth_service.get_current_user)
  ):
    """
    List user orders. 
    - Default: Returns a summary.
    - ?details=true: Returns orders with all nested items.
    """
    if details:
        return order_service.get_full_user_orders(current_user)
    
    return order_service.get_user_orders(current_user)

@app.post("/orders", status_code=201)
def place_order(data: dict, user = Depends(auth_service.get_current_user)):
    return order_service.create_order(data, user)


# ----- ADMIN ENDPOINTS -----

@app.get("/stats/customers")
def get_customers_stats(admin = Depends(auth_service.check_admin)):
    return stats_service.stats_customer_orders()

@app.get("/stats/products")
def get_products_stats(admin = Depends(auth_service.check_admin)):
    return stats_service.stats_product_orders()

@app.get("/stats/top-products")
def get_top_products_stats(n: int = 10, admin = Depends(auth_service.check_admin)):
    return stats_service.stats_top_products(n)

@app.get("/stats/recent-sales")
def get_recent_sales_stats(n: int = 30, admin = Depends(auth_service.check_admin)):
    return stats_service.stats_recent_sales(n)

@app.delete("/users/{user_id}")
def delete_user(user_id: int, admin = Depends(auth_service.check_admin)):
    return auth_service.delete_user(user_id)

@app.post("/categories", status_code=201)
def create_category(data: dict, user = Depends(auth_service.check_admin)):
    return category_service.create_category(data)

# POST /products - Create new product (admin only)
