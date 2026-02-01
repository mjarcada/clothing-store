from app.conn import get_conn

def get_products():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT products.name as product_name, categories.name as category_name, products.price, products.stock FROM products INNER JOIN categories ON products.category_id = categories.category_id ORDER BY products.name;")

        return cur.fetchall()# GET /products