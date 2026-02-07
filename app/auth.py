from app.conn import get_conn
from fastapi import FastAPI, HTTPException, Depends
import psycopg
from psycopg.rows import dict_row
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from pydantic import BaseModel, EmailStr

ALGORITHM = "HS256"
SECRET_KEY = "super-secret-key"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models for validation
class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Security Helpers ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
  
def register_user(user: UserRegister):
    with get_conn() as conn, conn.cursor() as cur:
        # Check if email already exists
        cur.execute("SELECT customer_id FROM customers WHERE email = %s;", (user.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Insert new user
        hashed_pw = hash_password(user.password)
        cur.execute(
            """
            INSERT INTO customers (first_name, last_name, email, password, role)
            VALUES (%s, %s, %s, %s, 'customer')
            RETURNING customer_id;
            """,
            (user.first_name, user.last_name, user.email, hashed_pw)
        )
        user_id = cur.fetchone()["customer_id"]
        return {"user_id": user_id, "email": user.email}
      
def login_user(credentials: UserLogin):
    with get_conn() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT customer_id, password, role FROM customers WHERE email = %s;", (credentials.email,))
        user = cur.fetchone()
        if not user or not verify_password(credentials.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = create_jwt({
          "sub": user["email"],
          "user_id": user["customer_id"],
          "role": user["role"]
          })
        
        return {"access_token": token, "token_type": "bearer"}  