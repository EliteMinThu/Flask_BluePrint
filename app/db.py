# app/db.py (Updated Version)

import oracledb
import os

pool = None

def init_pool():
    global pool
    
    ORACLE_USER = os.getenv("ORACLE_USER", "ca")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "pro")
    ORACLE_DSN = os.getenv("ORACLE_DSN", "localhost:1521/orcl")

    try:
        pool = oracledb.create_pool(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN, min=2, max=5, increment=1)
        print(">>> Database connection pool created successfully!")
    except Exception as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! DATABASE CONNECTION POOL FAILED TO CREATE !!!")
        print(f"Error: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        pool = None

def get_db_connection():
    if pool:
        return pool.acquire()
    else:
        raise Exception("Database pool is not available. Was init_pool() called?")

def release_db_connection(connection):
    if pool:
        pool.release(connection)

def make_dict_factory(cursor):
    column_names = [d[0].lower() for d in cursor.description]
    def create_row(*args):
        return dict(zip(column_names, args))
    return create_row