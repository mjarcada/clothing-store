import os
import bcrypt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr,Field
from app.conn import get_conn

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

ALGORITHM = os.getenv("ALGORITHM") or "HS256"
SECRET_KEY = os.getenv("SECRET_KEY")

# Pydantic models for validation
class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(..., max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Security Helpers ---

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt directly.
    Bcrypt has a 72-byte limit, which we handle via Pydantic validation.
    """
    # Convert string to bytes
    pwd_bytes = password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    # Return as string for database storage
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks a plain text password against a stored hash.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def create_jwt(data: dict):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        if email is None or role is None:
            raise credentials_exception
        return {"email": email, "role": role, "user_id": user_id}
    except JWTError:
        raise credentials_exception

def check_admin(user = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

# --- User Management Functions ---

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
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT customer_id, password, email, role FROM customers WHERE email = %s;", (credentials.email,))
        user = cur.fetchone()
        if not user or not verify_password(credentials.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = create_jwt({
          "sub": user["email"],
          "user_id": user["customer_id"],
          "role": user["role"]
          })
        
        return {"access_token": token, "token_type": "bearer"}  
      
def delete_user(user_id: int):
  with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM customers WHERE customer_id = %s", (user_id,))
        return {"msg": "User deleted"}