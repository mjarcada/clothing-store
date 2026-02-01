import os
from fastapi import FastAPI
import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()

def get_conn():
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=psycopg.rows.dict_row)