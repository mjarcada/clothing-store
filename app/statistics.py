from app.conn import get_conn

def stats_customer_orders():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
              c.customer_id,
              c.first_name,
              c.last_name,
              c.email,
              COUNT(DISTINCT o.order_id) AS order_count,
              SUM(oi.quantity) AS total_items,
              SUM(oi.quantity * oi.price) AS total_spent,
              ROUND(
                SUM(oi.quantity * oi.price) / NULLIF(COUNT(DISTINCT o.order_id), 0),
                2
              ) AS avg_order_value,
              MIN(o.order_date) AS first_order_date,
              MAX(o.order_date) AS last_order_date
            FROM
              customers c
              INNER JOIN orders o ON o.customer_id = c.customer_id
              INNER JOIN order_items oi ON oi.order_id = o.order_id
            GROUP BY
              c.customer_id,
              c.first_name,
              c.last_name,
              c.email
            ORDER BY
              total_spent DESC;
        """)
        return cur.fetchall()

def stats_product_orders():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
              p.product_id,
              p.name AS product_name,
              COUNT(DISTINCT o.order_id) AS order_count,
              SUM(oi.quantity) AS units_sold,
              SUM(oi.quantity * oi.price) AS turnover,
              ROUND(
                SUM(oi.quantity * oi.price) / NULLIF(SUM(oi.quantity), 0),
                2
              ) AS avg_unit_price,
              MIN(o.order_date) AS first_sold_date,
              MAX(o.order_date) AS last_sold_date
            FROM
              products p
              INNER JOIN order_items oi ON oi.product_id = p.product_id
              INNER JOIN orders o ON o.order_id = oi.order_id
            GROUP BY
              p.product_id,
              p.name
            ORDER BY
              turnover DESC;
        """)
        return cur.fetchall()

def stats_top_products(n: int = 10):
    if n <= 0 or n > 10:
        n = 10 # Limit n to max 10
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
              p.product_id,
              p.name AS product_name,
              COUNT(DISTINCT o.order_id) AS order_count,
              SUM(oi.quantity) AS units_sold,
              SUM(oi.quantity * oi.price) AS turnover,
              ROUND(
                SUM(oi.quantity * oi.price) / NULLIF(SUM(oi.quantity), 0),
                2
              ) AS avg_unit_price
            FROM
              products p
              INNER JOIN order_items oi ON oi.product_id = p.product_id
              INNER JOIN orders o ON o.order_id = oi.order_id
            GROUP BY
              p.product_id,
              p.name
            ORDER BY
              turnover DESC
            LIMIT
              %(top_n)s;
        """, {"top_n": n})
        
        return cur.fetchall()
  
def stats_recent_sales(n: int = 30):
    if n <= 0 or n > 90:
        n = 30 # Limit n to max 90 days
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
              p.product_id,
              p.name AS product_name,
              COUNT(DISTINCT o.order_id) AS order_count,
              SUM(oi.quantity) AS units_sold,
              SUM(oi.quantity * oi.price) AS turnover
            FROM
              products p
              INNER JOIN order_items oi ON oi.product_id = p.product_id
              INNER JOIN orders o ON o.order_id = oi.order_id
            WHERE
              o.order_date >= CURRENT_DATE - INTERVAL '%(days)s days'
            GROUP BY
              p.product_id,
              p.name
            ORDER BY
              turnover DESC;
        """, {"days": n})
        
        return cur.fetchall()


  