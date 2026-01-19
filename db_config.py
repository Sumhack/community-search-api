"""
Database Configuration Module
Centralized database connection management for PostgreSQL
"""

import os
import psycopg2
from psycopg2 import pool
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
# Connection String
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Connection Pool Configuration
class DatabasePool:
    """Manages PostgreSQL connection pooling"""
    
    _pool: Optional[pool.SimpleConnectionPool] = None
    
    @classmethod
    def get_pool(cls):
        """Get or create connection pool"""
        if cls._pool is None:
            cls._pool = pool.SimpleConnectionPool(
                1,  # minconn
                20,  # maxconn
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                sslmode="require" if "render.com" in DB_HOST else "prefer"
            )
        return cls._pool
    
    @classmethod
    def get_connection(cls):
        """Get a connection from the pool"""
        return cls.get_pool().getconn()
    
    @classmethod
    def return_connection(cls, conn):
        """Return connection to the pool"""
        cls.get_pool().putconn(conn)
    
    @classmethod
    def close_all(cls):
        """Close all connections in pool"""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None


def get_db_connection():
    """
    Get a database connection (with pooling)
    
    Usage:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # ... do work ...
            conn.commit()
        finally:
            cursor.close()
            DatabasePool.return_connection(conn)
    """
    return DatabasePool.get_connection()


def close_db_connection(conn):
    """Return connection to pool"""
    DatabasePool.return_connection(conn)


def execute_query(query: str, params: tuple = None):
    """
    Execute a SELECT query and return results
    
    Args:
        query: SQL query string
        params: Tuple of query parameters
    
    Returns:
        List of tuples (rows)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        cursor.close()
        return results
    finally:
        close_db_connection(conn)


def execute_insert(query: str, params: tuple = None):
    """
    Execute an INSERT/UPDATE/DELETE query
    
    Args:
        query: SQL query string
        params: Tuple of query parameters
    
    Returns:
        Number of rows affected
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        return rows_affected
    finally:
        close_db_connection(conn)


def execute_insert_returning(query: str, params: tuple = None):
    """
    Execute an INSERT query with RETURNING clause
    
    Args:
        query: SQL query string with RETURNING
        params: Tuple of query parameters
    
    Returns:
        Returned values from RETURNING clause
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result
    finally:
        close_db_connection(conn)
