import os, psycopg2
from psycopg2.extras import RealDictCursor      #Normally returns tuple but this returns as a dictionary
from dotenv import load_dotenv
load_dotenv()

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursor_factory=RealDictCursor
    )
    
def exec_many(sql, rows):
    with get_conn() as conn, conn.cursor() as cur:
        cur.executemany(sql, rows)
        
def exec_one(sql, params=None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        try:
            return cur.fetchall()
        except Exception:
            return None
        