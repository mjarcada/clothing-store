from app.conn import get_conn

def get_products():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM products ORDER BY product_id;")
        return cur.fetchall()# GET /products