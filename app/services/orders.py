from fastapi import HTTPException
from app.conn import get_conn

def create_order(data: dict, current_user: dict):
    """
    Takes items as JSON, and uses current_user['user_id'] for security.
    """
    customer_id = current_user.get("user_id")
    items = data.get("items")  # [{"product_id": int, "quantity": int}]

    if not customer_id or not items:
      raise HTTPException(status_code=400, detail="Missing 'customer_id' or 'items'")
    
    with get_conn() as conn, conn.cursor() as cur:
        # Create order
        cur.execute(
            """
            INSERT INTO orders (customer_id)
            VALUES (%s)
            RETURNING order_id, customer_id, order_date;
            """,
            (customer_id,)
        )
        order = cur.fetchone()
        order_id = order["order_id"]

        order_items = []
        order_total = 0

        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if not product_id or quantity is None or quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Each item must have 'product_id' and a positive 'quantity'"
                )

            # Fetch product
            cur.execute(
                """
                SELECT product_id, name, price, stock
                FROM products
                WHERE product_id = %s
                FOR UPDATE;
                """,
                (product_id,)
            )
            product = cur.fetchone()
            
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {product_id} not found"
                )

            if product["stock"] < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product['name']}"
                )

            line_total = product["price"] * quantity
            order_total += line_total

            # Insert order item
            cur.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s);
                """,
                (order_id, product_id, quantity, product["price"])
            )

            # Update stock
            cur.execute(
                """
                UPDATE products
                SET stock = stock - %s
                WHERE product_id = %s;
                """,
                (quantity, product_id)
            )

            order_items.append({
                "product_id": product_id,
                "product_name": product["name"],
                "unit_price": product["price"],
                "quantity": quantity,
                "line_total": line_total
            })

        return {
            "order_id": order_id,
            "customer_id": order["customer_id"],
            "order_date": order["order_date"],
            "items": order_items,
            "order_total": order_total
        }

def get_user_orders(current_user: dict):
    customer_id = current_user.get("user_id")
    
    with get_conn() as conn, conn.cursor() as cur:
        # We join orders and order_items to give a detailed history
        cur.execute("""
            SELECT 
                o.order_id, 
                o.order_date,
                SUM(oi.quantity * oi.price) as total_price,
                COUNT(oi.product_id) as unique_items
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.customer_id = %s
            GROUP BY o.order_id, o.order_date
            ORDER BY o.order_date DESC;
        """, (customer_id,))
        
        return cur.fetchall()
  

def get_full_user_orders(current_user: dict):
    # Note: Ensure key matches your JWT payload (you used "id" in previous steps)
    customer_id = current_user.get("id") or current_user.get("user_id")
    
    with get_conn() as conn, conn.cursor() as cur:
        # 1. Fetch all orders for this customer
        cur.execute("""
            SELECT order_id, order_date 
            FROM orders 
            WHERE customer_id = %s 
            ORDER BY order_date DESC;
        """, (customer_id,))
        orders = cur.fetchall()

        if not orders:
            return []

        # 2. Get all order IDs to fetch items in one go
        order_ids = [o["order_id"] for o in orders]

        # 3. Fetch all items for these orders, joining with products to get names
        cur.execute("""
            SELECT 
                oi.order_id, 
                oi.product_id, 
                p.name as product_name, 
                oi.quantity, 
                oi.price as unit_price,
                (oi.quantity * oi.price) as line_total
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ANY(%s);
        """, (order_ids,))
        all_items = cur.fetchall()

        # 4. Group items into their respective orders
        for order in orders:
            # Filter items belonging to this specific order
            order["items"] = [
                item for item in all_items 
                if item["order_id"] == order["order_id"]
            ]
            # Calculate total for the order
            order["total_price"] = sum(item["line_total"] for item in order["items"])

        return orders