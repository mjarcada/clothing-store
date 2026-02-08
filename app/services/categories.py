from fastapi import HTTPException
from app.conn import get_conn


def get_categories():
  with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT category_id, name FROM categories ORDER BY category_id;")
        return cur.fetchall()


def get_category(category_id: int):
  with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT category_id, name FROM categories WHERE category_id = %s;", (category_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        return row
      
def create_category(data: dict):
  name = data.get("name")
  if not name:
      raise HTTPException(status_code=400, detail="Missing 'name'")
  with get_conn() as conn, conn.cursor() as cur:
      cur.execute("INSERT INTO categories (name) VALUES (%s) RETURNING category_id, name;", (name,))
      return cur.fetchone()