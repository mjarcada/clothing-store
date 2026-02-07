from fastapi import HTTPException
from app.conn import get_conn
from app.products import get_products

def create_order(data: dict, current_user: dict):
    """
    Takes items from JSON, but uses current_user['id'] for security.
    """
    customer_id = current_user.get("id")
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

