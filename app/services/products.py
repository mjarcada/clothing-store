from app.conn import get_conn

def get_products():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT 
              p.product_id, 
              p.name as product_name, 
              c.name as category_name, 
              p.price, 
              p.stock 
            FROM products p INNER JOIN categories c 
              ON p.category_id = c.category_id 
            ORDER BY p.name;
            """)

        return cur.fetchall()
      